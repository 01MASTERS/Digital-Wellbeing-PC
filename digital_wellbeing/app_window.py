"""Launches Digital Wellbeing in a dedicated native Windows desktop app window."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import webbrowser
from pathlib import Path

try:
    import psutil  # type: ignore[import-untyped]
    import win32con  # type: ignore[import-untyped]
    import win32gui  # type: ignore[import-untyped]
    import win32process  # type: ignore[import-untyped]
    _WIN32_AVAILABLE = True
except ImportError:
    _WIN32_AVAILABLE = False

LOGGER = logging.getLogger(__name__)

REJECTED_APP_NAMES = frozenset({
    "explorer.exe",
    "antigravity ide.exe",
    "code.exe",
    "cursor.exe",
    "devenv.exe",
    "pycharm.exe",
    "pycharm64.exe",
    "idea.exe",
    "idea64.exe",
    "sublime_text.exe",
    "windowsterminal.exe",
    "cmd.exe",
    "powershell.exe",
    "pwsh.exe",
})

ALLOWED_HOST_APPS = frozenset({
    "msedge.exe",
    "chrome.exe",
    "brave.exe",
    "firefox.exe",
    "opera.exe",
    "opera_gx.exe",
    "vivaldi.exe",
    "arc.exe",
    "waterfox.exe",
    "digitalwellbeing.exe",
    "python.exe",
    "pythonw.exe",
})


def is_digital_wellbeing_window(hwnd: int) -> bool:
    """Check if a window handle corresponds to the actual Digital Wellbeing application window."""
    if not _WIN32_AVAILABLE:
        return False
    try:
        if not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
            return False
        title = win32gui.GetWindowText(hwnd).strip()
        if not title:
            return False
        title_lower = title.casefold()

        # The title must be either exactly 'digital wellbeing' or start with 'digital wellbeing -' / 'digital wellbeing —'
        if title_lower != "digital wellbeing" and not title_lower.startswith(
            ("digital wellbeing -", "digital wellbeing —", "digital wellbeing ·")
        ):
            return False

        # Reject windows from code editors, IDEs, or containing code file extensions
        excluded_keywords = (
            "antigravity",
            "visual studio",
            "vs code",
            "cursor",
            "sublime",
            "pycharm",
            "intellij",
            "terminal",
            "powershell",
            "cmd.exe",
            ".py",
            ".js",
            ".json",
            ".md",
            ".html",
            ".css",
            ".ts",
            ".txt",
            ".spec",
        )
        if any(keyword in title_lower for keyword in excluded_keywords):
            return False

        # Verify owning process
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            proc_name = psutil.Process(pid).name().casefold()
        except (psutil.Error, OSError):
            return False

        if proc_name in REJECTED_APP_NAMES:
            return False

        return proc_name in ALLOWED_HOST_APPS
    except (OSError, win32gui.error, psutil.Error):
        return False


def _find_app_browser() -> str | None:
    """Find Microsoft Edge or Google Chrome executable to use as standalone app host."""
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    local_app_data = os.environ.get("LOCALAPPDATA", "")

    candidates = [
        os.path.join(program_files_x86, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(program_files, "Microsoft", "Edge", "Application", "msedge.exe"),
        os.path.join(local_app_data, "Microsoft", "Edge", "Application", "msedge.exe") if local_app_data else "",
        os.path.join(program_files, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(program_files_x86, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(local_app_data, "Google", "Chrome", "Application", "chrome.exe") if local_app_data else "",
        shutil.which("msedge.exe") or "",
        shutil.which("chrome.exe") or "",
    ]
    for path in candidates:
        if path and os.path.isfile(path):
            return path
    return None


def focus_existing_window() -> bool:
    """If the Digital Wellbeing application window is already open, bring it to front."""
    if not _WIN32_AVAILABLE:
        return False
    found_hwnd = 0

    def enum_cb(hwnd: int, _extra: object) -> int:
        nonlocal found_hwnd
        try:
            if is_digital_wellbeing_window(hwnd):
                found_hwnd = hwnd
                return 0
        except (OSError, win32gui.error) as err:
            LOGGER.debug("Error checking window %s: %s", hwnd, err)
        return 1

    try:
        win32gui.EnumWindows(enum_cb, None)
    except (OSError, win32gui.error) as error:
        LOGGER.debug("EnumWindows finished: %s", error)

    if found_hwnd:
        try:
            if win32gui.IsIconic(found_hwnd):
                win32gui.ShowWindow(found_hwnd, win32con.SW_RESTORE)
            win32gui.SetForegroundWindow(found_hwnd)
            return True
        except (OSError, win32gui.error) as error:
            LOGGER.debug("Could not focus existing window: %s", error)

    return False


def open_app_window(url: str, data_dir: Path | None = None, width: int = 1200, height: int = 820) -> None:
    """Open the dashboard in a dedicated standalone application window, or focus it."""
    if focus_existing_window():
        return

    browser = _find_app_browser()
    if not browser:
        LOGGER.info("No app-host browser found; using default browser tab")
        webbrowser.open(url)
        return

    if data_dir is not None:
        profile_dir = data_dir / "app_profile"
    else:
        local = os.environ.get("LOCALAPPDATA", "")
        base = Path(local) if local else Path.home() / "AppData" / "Local"
        profile_dir = base / "DigitalWellbeing" / "app_profile"

    profile_dir.mkdir(parents=True, exist_ok=True)

    args = [
        browser,
        f"--app={url}",
        f"--user-data-dir={profile_dir}",
        f"--window-size={width},{height}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-extensions",
        "--disable-features=Translate",
        "--app-id=DigitalWellbeing",
    ]

    try:
        subprocess.Popen(
            args,
            creationflags=getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            close_fds=True,
        )
    except OSError:
        LOGGER.exception("Failed to launch standalone app window; falling back to default browser")
        webbrowser.open(url)
