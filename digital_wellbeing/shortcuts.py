"""Create Windows Desktop and Start Menu shortcuts for Digital Wellbeing."""

from __future__ import annotations

import sys
from pathlib import Path


def create_shortcuts() -> list[str]:
    """Create Desktop and Start Menu shortcuts pointing to the executable or run.py."""
    import win32com.client  # type: ignore[import-untyped]

    root = Path(__file__).resolve().parent.parent
    icon_path = root / "assets" / "icon.ico"
    exe_target = root / "dist" / "DigitalWellbeing.exe"

    if getattr(sys, "frozen", False):
        target = sys.executable
        arguments = ""
        root = Path(sys.executable).parent
        icon_path = Path(sys.executable)
    elif exe_target.is_file():
        target = str(exe_target)
        arguments = ""
    else:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        if not pythonw.is_file():
            pythonw = Path(sys.executable)
        target = str(pythonw)
        arguments = f'"{root / "run.py"}"'

    shell = win32com.client.Dispatch("WScript.Shell")
    created: list[str] = []

    destinations = [
        ("Desktop", Path(shell.SpecialFolders("Desktop")) / "Digital Wellbeing.lnk"),
        ("Start Menu", Path(shell.SpecialFolders("Programs")) / "Digital Wellbeing.lnk"),
    ]

    for label, lnk_path in destinations:
        try:
            lnk_path.parent.mkdir(parents=True, exist_ok=True)
            shortcut = shell.CreateShortcut(str(lnk_path))
            shortcut.TargetPath = target
            if arguments:
                shortcut.Arguments = arguments
            shortcut.WorkingDirectory = str(root)
            shortcut.Description = "Private Digital Wellbeing dashboard and monitor for Windows"
            if icon_path.is_file():
                shortcut.IconLocation = f"{icon_path},0"
            shortcut.Save()
            created.append(str(lnk_path))
        except (OSError, RuntimeError) as error:
            print(f"Could not create {label} shortcut: {error}")

    return created
