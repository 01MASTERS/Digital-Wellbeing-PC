"""Windows foreground observation, screen dimming, and startup integration."""

from __future__ import annotations

import ctypes
import logging
import os
import re
import sys
import threading
import winreg
from ctypes import wintypes
from pathlib import Path
from typing import Any, Protocol

import psutil  # type: ignore[import-untyped]
import win32api  # type: ignore[import-untyped]
import win32con  # type: ignore[import-untyped]
import win32gui  # type: ignore[import-untyped]
import win32process  # type: ignore[import-untyped]

from digital_wellbeing.core import Observation

LOGGER = logging.getLogger(__name__)


class NotificationSink(Protocol):
    def notify(self, title: str, message: str) -> None: ...


APP_NAMES = {
    "chrome.exe": "Google Chrome",
    "msedge.exe": "Microsoft Edge",
    "firefox.exe": "Firefox",
    "code.exe": "VS Code",
    "discord.exe": "Discord",
    "spotify.exe": "Spotify",
    "slack.exe": "Slack",
    "teams.exe": "Microsoft Teams",
    "msteams.exe": "Microsoft Teams",
    "zoom.exe": "Zoom",
    "steam.exe": "Steam",
    "notepad.exe": "Notepad",
    "winword.exe": "Word",
    "excel.exe": "Excel",
    "powerpnt.exe": "PowerPoint",
    "explorer.exe": "File Explorer",
    "whatsapp.exe": "WhatsApp",
    "obs64.exe": "OBS Studio",
    "applicationframehost.exe": "Windows App",
}
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_NAME = "DigitalWellbeing"


def display_name(app_id: str) -> str:
    known = APP_NAMES.get(app_id.casefold())
    if known:
        return known
    stem = Path(app_id).stem
    words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", stem).replace("_", " ").replace("-", " ").strip()
    return words.title() if words else "Unknown app"


def build_autostart_command(executable: Path, frozen: bool, root: Path) -> str:
    if frozen:
        return f'"{executable}" --no-browser'
    pythonw = executable.with_name("pythonw.exe")
    return f'"{pythonw}" "{root / "run.py"}" --no-browser'


def autostart_command() -> str:
    return build_autostart_command(
        Path(sys.executable),
        bool(getattr(sys, "frozen", False)),
        Path(__file__).resolve().parent.parent,
    )


def is_autostart_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ) as key:
            value, _ = winreg.QueryValueEx(key, RUN_NAME)
            return value == autostart_command()
    except FileNotFoundError:
        return False


def set_autostart(enabled: bool) -> None:
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, RUN_NAME, 0, winreg.REG_SZ, autostart_command())
        else:
            try:
                winreg.DeleteValue(key, RUN_NAME)
            except FileNotFoundError:
                pass


class LastInputInfo(ctypes.Structure):
    _fields_ = (("cbSize", wintypes.UINT), ("dwTime", wintypes.DWORD))


_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
_user32.GetLastInputInfo.argtypes = (ctypes.POINTER(LastInputInfo),)
_user32.GetLastInputInfo.restype = wintypes.BOOL
_kernel32.GetTickCount.restype = wintypes.DWORD
_user32.OpenInputDesktop.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
_user32.OpenInputDesktop.restype = wintypes.HANDLE
_user32.GetUserObjectInformationW.argtypes = (
    wintypes.HANDLE,
    ctypes.c_int,
    ctypes.c_void_p,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
)
_user32.GetUserObjectInformationW.restype = wintypes.BOOL
_user32.CloseDesktop.argtypes = (wintypes.HANDLE,)
_user32.CloseDesktop.restype = wintypes.BOOL


def idle_seconds() -> float:
    info = LastInputInfo()
    info.cbSize = ctypes.sizeof(LastInputInfo)
    if not _user32.GetLastInputInfo(ctypes.byref(info)):
        return 0.0
    elapsed_ms = (_kernel32.GetTickCount() - info.dwTime) & 0xFFFFFFFF
    return elapsed_ms / 1000


def desktop_is_active() -> bool:
    desktop = _user32.OpenInputDesktop(0, False, 0x0001)
    if not desktop:
        return False
    try:
        name = ctypes.create_unicode_buffer(256)
        needed = wintypes.DWORD()
        if not _user32.GetUserObjectInformationW(
            desktop, 2, name, ctypes.sizeof(name), ctypes.byref(needed)
        ):
            return False
        return name.value.casefold() == "default"
    finally:
        _user32.CloseDesktop(desktop)


def _process_id_for_window(hwnd: int) -> int:
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    if win32gui.GetClassName(hwnd) != "ApplicationFrameWindow":
        return pid
    child_pids: list[int] = []

    def collect(child: int, _extra: object) -> None:
        _, child_pid = win32process.GetWindowThreadProcessId(child)
        if child_pid != pid:
            child_pids.append(child_pid)

    win32gui.EnumChildWindows(hwnd, collect, None)
    return child_pids[0] if child_pids else pid


def _app_id_for_window(hwnd: int) -> str | None:
    try:
        pid = _process_id_for_window(hwnd)
        proc = psutil.Process(pid)
        app_id = proc.name().casefold()
        try:
            exe_path = proc.exe()
            if exe_path:
                from digital_wellbeing.icons import record_app_exe
                record_app_exe(app_id, exe_path)
        except (psutil.Error, OSError):
            pass
        return app_id
    except (psutil.Error, OSError, win32gui.error):
        return None


class DimOverlay:
    """Click-through desktop tint used only while bedtime dimming is active."""

    def __init__(self) -> None:
        self._enabled = threading.Event()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None

    def set_enabled(self, enabled: bool) -> None:
        if enabled:
            self._enabled.set()
            if self._thread is None:
                self._thread = threading.Thread(target=self._run, name="bedtime-overlay", daemon=True)
                self._thread.start()
        else:
            self._enabled.clear()

    def close(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2)

    @staticmethod
    def _window_proc(hwnd: int, message: int, wparam: int, lparam: int) -> int:
        if message == win32con.WM_NCHITTEST:
            return win32con.HTTRANSPARENT
        if message == win32con.WM_MOUSEACTIVATE:
            return win32con.MA_NOACTIVATE
        return win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    def _run(self) -> None:
        hwnd = 0
        brush = 0
        try:
            class_name = f"DigitalWellbeingDim_{os.getpid()}_{id(self)}"
            window_class = win32gui.WNDCLASS()
            window_class.hInstance = win32api.GetModuleHandle(None)
            window_class.lpszClassName = class_name
            window_class.lpfnWndProc = self._window_proc
            brush = win32gui.CreateSolidBrush(win32api.RGB(18, 20, 36))
            window_class.hbrBackground = brush
            win32gui.RegisterClass(window_class)
            x = win32api.GetSystemMetrics(win32con.SM_XVIRTUALSCREEN)
            y = win32api.GetSystemMetrics(win32con.SM_YVIRTUALSCREEN)
            width = win32api.GetSystemMetrics(win32con.SM_CXVIRTUALSCREEN)
            height = win32api.GetSystemMetrics(win32con.SM_CYVIRTUALSCREEN)
            ex_style = (
                win32con.WS_EX_LAYERED
                | win32con.WS_EX_TRANSPARENT
                | win32con.WS_EX_TOOLWINDOW
                | win32con.WS_EX_TOPMOST
                | win32con.WS_EX_NOACTIVATE
            )
            hwnd = win32gui.CreateWindowEx(
                ex_style,
                class_name,
                "Digital Wellbeing bedtime tint",
                win32con.WS_POPUP,
                x,
                y,
                width,
                height,
                0,
                0,
                window_class.hInstance,
                None,
            )
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 80, win32con.LWA_ALPHA)
            visible = False
            while not self._stop.is_set():
                desired = self._enabled.is_set()
                if desired and not visible:
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNOACTIVATE)
                    win32gui.SetWindowPos(
                        hwnd, win32con.HWND_TOPMOST, x, y, width, height,
                        win32con.SWP_NOACTIVATE | win32con.SWP_SHOWWINDOW,
                    )
                    visible = True
                elif not desired and visible:
                    win32gui.ShowWindow(hwnd, win32con.SW_HIDE)
                    visible = False
                win32gui.PumpWaitingMessages()
                self._stop.wait(0.1)
        except Exception:
            LOGGER.exception("Bedtime tint could not start")
        finally:
            if hwnd:
                win32gui.DestroyWindow(hwnd)
            if brush:
                win32gui.DeleteObject(brush)


class GrayscaleManager:
    """Manages fullscreen grayscale effect using Windows Magnification API."""

    def __init__(self) -> None:
        self._enabled = False
        self._mag: Any = None
        self._initialized = False
        try:
            self._mag = ctypes.WinDLL("Magnification.dll")
            self._mag.MagInitialize.restype = wintypes.BOOL
            self._mag.MagUninitialize.restype = wintypes.BOOL
            self._mag.MagSetFullscreenColorEffect.argtypes = [ctypes.POINTER(ctypes.c_float * 25)]
            self._mag.MagSetFullscreenColorEffect.restype = wintypes.BOOL
        except OSError as error:
            LOGGER.debug("Magnification API unavailable: %s", error)
            self._mag = None

    def set_enabled(self, enabled: bool) -> None:
        if not self._mag or self._enabled == enabled:
            return
        try:
            if enabled:
                if not self._initialized:
                    self._mag.MagInitialize()
                    self._initialized = True
                gray_matrix = (ctypes.c_float * 25)(
                    0.2126, 0.2126, 0.2126, 0.0, 0.0,
                    0.7152, 0.7152, 0.7152, 0.0, 0.0,
                    0.0722, 0.0722, 0.0722, 0.0, 0.0,
                    0.0,    0.0,    0.0,    1.0, 0.0,
                    0.0,    0.0,    0.0,    0.0, 1.0,
                )
                self._mag.MagSetFullscreenColorEffect(ctypes.byref(gray_matrix))
                self._enabled = True
            else:
                identity_matrix = (ctypes.c_float * 25)(
                    1.0, 0.0, 0.0, 0.0, 0.0,
                    0.0, 1.0, 0.0, 0.0, 0.0,
                    0.0, 0.0, 1.0, 0.0, 0.0,
                    0.0, 0.0, 0.0, 1.0, 0.0,
                    0.0, 0.0, 0.0, 0.0, 1.0,
                )
                self._mag.MagSetFullscreenColorEffect(ctypes.byref(identity_matrix))
                self._enabled = False
        except OSError:
            LOGGER.exception("Failed to toggle bedtime grayscale")

    def close(self) -> None:
        if self._enabled:
            self.set_enabled(False)
        if self._mag and self._initialized:
            try:
                self._mag.MagUninitialize()
            except OSError as error:
                LOGGER.debug("MagUninitialize failed: %s", error)
            self._initialized = False


class WindowsPlatform:
    def __init__(self) -> None:
        self.overlay = DimOverlay()
        self.grayscale = GrayscaleManager()
        self.tray: NotificationSink | None = None

    def attach_tray(self, tray: NotificationSink) -> None:
        self.tray = tray

    def sample(self) -> Observation:
        idle = idle_seconds()
        if not desktop_is_active():
            return Observation(None, None, idle, False, None)
        hwnd = win32gui.GetForegroundWindow()
        if not hwnd:
            return Observation(None, None, idle, False, None)
        app_id = _app_id_for_window(hwnd)
        if not app_id:
            return Observation(None, None, idle, True, hwnd)
        title = win32gui.GetWindowText(hwnd)
        return Observation(app_id, display_name(app_id), idle, True, hwnd, title)

    def minimize(self, hwnd: int, app_id: str) -> bool:
        try:
            if not win32gui.IsWindow(hwnd) or _app_id_for_window(hwnd) != app_id:
                return False
            win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
            return bool(win32gui.IsIconic(hwnd))
        except (OSError, win32gui.error):
            LOGGER.exception("Could not minimize %s", app_id)
            return False

    def set_dim(self, enabled: bool) -> None:
        self.overlay.set_enabled(enabled)

    def set_grayscale(self, enabled: bool) -> None:
        self.grayscale.set_enabled(enabled)

    def notify(self, title: str, message: str) -> None:
        if self.tray:
            self.tray.notify(title, message)
        else:
            LOGGER.info("%s: %s", title, message)

    def close(self) -> None:
        self.overlay.close()
        self.grayscale.close()
