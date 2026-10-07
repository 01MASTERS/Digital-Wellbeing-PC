"""Application lifecycle for the Windows background monitor."""

import argparse
import json
import logging
import os
import threading
import time
import urllib.error
import urllib.request
from logging.handlers import RotatingFileHandler
from pathlib import Path

import win32api  # type: ignore[import-untyped]
import win32event  # type: ignore[import-untyped]
import winerror  # type: ignore[import-untyped]

from digital_wellbeing.app_window import open_app_window
from digital_wellbeing.icons import set_cache_directory
from digital_wellbeing.platform_windows import WindowsPlatform
from digital_wellbeing.server import LocalServer
from digital_wellbeing.service import WellbeingService
from digital_wellbeing.storage import Store
from digital_wellbeing.tray import TrayIcon

LOGGER = logging.getLogger(__name__)
PORTS = range(8765, 8776)
MUTEX_NAME = r"Local\DigitalWellbeingMonitor"


def data_directory() -> Path:
    override = os.environ.get("WELLBEING_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    local = os.environ.get("LOCALAPPDATA")
    return (Path(local) if local else Path.home() / "AppData" / "Local") / "DigitalWellbeing"


def configure_logging(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(directory / "wellbeing.log", maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def find_existing() -> str | None:
    for port in PORTS:
        url = f"http://127.0.0.1:{port}"
        try:
            with urllib.request.urlopen(url + "/api/health", timeout=0.3) as response:
                data = json.load(response)
                if data.get("app") == "digital-wellbeing":
                    return url
        except (OSError, ValueError, urllib.error.URLError):
            continue
    return None


def _monitor_loop(service: WellbeingService, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            service.tick()
        except Exception:
            LOGGER.exception("Activity sample failed")
        stop.wait(2)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Private Digital Wellbeing monitor for Windows")
    parser.add_argument("--no-browser", action="store_true", help="Start in the tray without opening the dashboard")
    parser.add_argument("--no-tray", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    if os.name != "nt":
        parser.error("Digital Wellbeing currently requires Windows 10 or 11")

    mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
    already_running = win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS
    if already_running:
        existing = None
        for _ in range(20):
            existing = find_existing()
            if existing:
                break
            time.sleep(0.25)
        if existing and not args.no_browser:
            open_app_window(existing)
        win32api.CloseHandle(mutex)
        return 0 if existing else 1

    directory = data_directory()
    configure_logging(directory)
    set_cache_directory(directory)
    store: Store | None = None
    platform: WindowsPlatform | None = None
    service: WellbeingService | None = None
    server: LocalServer | None = None
    tray: TrayIcon | None = None
    stop = threading.Event()
    worker: threading.Thread | None = None
    try:
        store = Store(directory / "wellbeing.sqlite3")
        platform = WindowsPlatform()
        service = WellbeingService(store, platform)
        for port in PORTS:
            try:
                candidate = LocalServer(service, store, port=port, on_quit=stop.set)
                candidate.start()
                server = candidate
                break
            except OSError:
                continue
        if server is None:
            raise RuntimeError("No local dashboard port is available")

        url = f"http://127.0.0.1:{server.port}"

        def open_dashboard() -> None:
            open_app_window(url, data_dir=directory)

        def toggle_tracking() -> None:
            assert service is not None
            paused = bool(service.store.get_settings()["tracking_paused"])
            service.update_settings({"tracking_paused": not paused})
            assert platform is not None
            platform.notify("Digital Wellbeing", "Tracking paused" if not paused else "Tracking resumed")

        def quick_focus() -> None:
            assert service is not None
            service.start_focus(25)
            assert platform is not None
            platform.notify("Digital Wellbeing", "Focus mode started for 25 minutes")

        if not args.no_tray:
            tray = TrayIcon(open_dashboard, toggle_tracking, quick_focus, stop.set)
            try:
                tray.start()
                platform.attach_tray(tray)
            except RuntimeError:
                LOGGER.exception("Tray unavailable; dashboard remains available at %s", url)
                tray = None

        worker = threading.Thread(target=_monitor_loop, args=(service, stop), name="wellbeing-monitor", daemon=True)
        worker.start()
        LOGGER.info("Digital Wellbeing started at %s", url)
        if not args.no_browser:
            open_app_window(url, data_dir=directory)
        try:
            while not stop.wait(0.5):
                pass
        except KeyboardInterrupt:
            stop.set()
        return 0
    except Exception:
        LOGGER.exception("Digital Wellbeing could not start")
        return 1
    finally:
        stop.set()
        if worker is not None:
            worker.join(timeout=4)
        if server is not None:
            server.stop()
        if service is not None:
            service.close()
        if platform is not None:
            platform.close()
        if tray is not None:
            tray.stop()
        if store is not None:
            store.close()
        win32api.CloseHandle(mutex)
