import unittest
from pathlib import Path

from digital_wellbeing.platform_windows import build_autostart_command, display_name


class PlatformHelpersTests(unittest.TestCase):
    def test_display_names_are_readable_and_stable(self) -> None:
        self.assertEqual(display_name("msedge.exe"), "Microsoft Edge")
        self.assertEqual(display_name("code.exe"), "VS Code")
        self.assertEqual(display_name("my_custom-app.exe"), "My Custom App")

    def test_startup_command_uses_pythonw_for_source_and_exe_for_bundle(self) -> None:
        root = Path(r"C:\Apps\Digital Wellbeing")
        python = Path(r"C:\Python312\python.exe")
        bundled = Path(r"C:\Apps\Digital Wellbeing\DigitalWellbeing.exe")
        self.assertEqual(
            build_autostart_command(python, False, root),
            r'"C:\Python312\pythonw.exe" "C:\Apps\Digital Wellbeing\run.py" --no-browser',
        )
        self.assertEqual(
            build_autostart_command(bundled, True, root),
            r'"C:\Apps\Digital Wellbeing\DigitalWellbeing.exe" --no-browser',
        )


if __name__ == "__main__":
    unittest.main()
