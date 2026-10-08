"""Windows notification-area control for the background monitor."""

import logging
import os
import sys
import threading
from collections.abc import Callable
from pathlib import Path

import win32api  # type: ignore[import-untyped]
import win32con  # type: ignore[import-untyped]
import win32gui  # type: ignore[import-untyped]

LOGGER = logging.getLogger(__name__)
TRAY_MESSAGE = win32con.WM_USER + 20
OPEN = 101
PAUSE = 102
FOCUS = 103
QUIT = 104


class TrayIcon:
    def __init__(
        self,
        on_open: Callable[[], None],
        on_pause: Callable[[], None],
        on_focus: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.on_open = on_open
        self.on_pause = on_pause
        self.on_focus = on_focus
        self.on_quit = on_quit
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._hwnd = 0
        self._icon = 0
        self._error: Exception | None = None

    def start(self) -> None:
        if self._thread is not None:
            return
        self._thread = threading.Thread(target=self._run, name="wellbeing-tray", daemon=True)
        self._thread.start()
        self._ready.wait(timeout=5)
        if self._error is not None:
            raise RuntimeError("The Windows tray icon could not start") from self._error

    def stop(self) -> None:
        self._stop.set()
        if self._hwnd:
            win32gui.PostMessage(self._hwnd, win32con.WM_NULL, 0, 0)
        if self._thread is not None and threading.current_thread() is not self._thread:
            self._thread.join(timeout=3)

    def notify(self, title: str, message: str) -> None:
        if not self._hwnd:
            return
        try:
            data = (
                self._hwnd,
                0,
                win32gui.NIF_INFO,
                TRAY_MESSAGE,
                self._icon,
                "Digital Wellbeing",
                message[:255],
                200,
                title[:63],
            )
            win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, data)
        except win32gui.error:
            LOGGER.exception("Could not show tray notification")

    def _window_proc(self, hwnd: int, message: int, wparam: int, lparam: int) -> int:
        if message == TRAY_MESSAGE:
            if lparam == win32con.WM_LBUTTONDBLCLK:
                self.on_open()
            elif lparam == win32con.WM_RBUTTONUP:
                self._show_menu()
            return 0
        return win32gui.DefWindowProc(hwnd, message, wparam, lparam)

    def _show_menu(self) -> None:
        menu = win32gui.CreatePopupMenu()
        try:
            win32gui.AppendMenu(menu, win32con.MF_STRING, OPEN, "Open dashboard")
            win32gui.AppendMenu(menu, win32con.MF_STRING, PAUSE, "Pause / resume tracking")
            win32gui.AppendMenu(menu, win32con.MF_STRING, FOCUS, "Start 25-minute focus")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, QUIT, "Quit Digital Wellbeing")
            x, y = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self._hwnd)
            command = win32gui.TrackPopupMenu(
                menu,
                win32con.TPM_LEFTALIGN | win32con.TPM_BOTTOMALIGN | win32con.TPM_RETURNCMD,
                x,
                y,
                0,
                self._hwnd,
                None,
            )
            win32gui.PostMessage(self._hwnd, win32con.WM_NULL, 0, 0)
            if command == OPEN:
                self.on_open()
            elif command == PAUSE:
                self.on_pause()
            elif command == FOCUS:
                self.on_focus()
            elif command == QUIT:
                self.on_quit()
        finally:
            win32gui.DestroyMenu(menu)

    def _load_icon(self) -> int:
        candidates = []
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "assets" / "icon.ico")
        candidates.append(Path(__file__).resolve().parent.parent / "assets" / "icon.ico")

        for candidate in candidates:
            if candidate.is_file():
                try:
                    icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
                    hicon = win32gui.LoadImage(
                        0, str(candidate), win32con.IMAGE_ICON, 0, 0, icon_flags
                    )
                    if hicon:
                        return hicon
                except (win32gui.error, OSError):
                    LOGGER.debug("Could not load custom tray icon from %s", candidate)
        return win32gui.LoadIcon(0, win32con.IDI_APPLICATION)

    def _run(self) -> None:
        try:
            class_name = f"DigitalWellbeingTray_{os.getpid()}"
            window_class = win32gui.WNDCLASS()
            window_class.hInstance = win32api.GetModuleHandle(None)
            window_class.lpszClassName = class_name
            window_class.lpfnWndProc = self._window_proc
            win32gui.RegisterClass(window_class)
            self._hwnd = win32gui.CreateWindow(
                class_name, class_name, 0, 0, 0, 0, 0, 0, 0, window_class.hInstance, None
            )
            self._icon = self._load_icon()
            data = (
                self._hwnd,
                0,
                win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                TRAY_MESSAGE,
                self._icon,
                "Digital Wellbeing — double-click to open",
            )
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, data)
            self._ready.set()
            while not self._stop.is_set():
                win32gui.PumpWaitingMessages()
                self._stop.wait(0.1)
        except Exception as error:
            self._error = error
            LOGGER.exception("Tray icon could not start")
            self._ready.set()
        finally:
            if self._hwnd:
                try:
                    win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (self._hwnd, 0))
                except win32gui.error:
                    pass
                win32gui.DestroyWindow(self._hwnd)
                self._hwnd = 0
            if self._icon and self._icon != win32gui.LoadIcon(0, win32con.IDI_APPLICATION):
                try:
                    win32gui.DestroyIcon(self._icon)
                except win32gui.error:
                    pass
                self._icon = 0
