import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from digital_wellbeing.core import Observation, Rule
from digital_wellbeing.service import WellbeingService
from digital_wellbeing.storage import Store


class FakePlatform:
    def __init__(self, observation: Observation) -> None:
        self.observation = observation
        self.minimized: list[tuple[int, str]] = []
        self.dims: list[bool] = []
        self.notifications: list[tuple[str, str]] = []

    def sample(self) -> Observation:
        return self.observation

    def minimize(self, hwnd: int, app_id: str) -> bool:
        self.minimized.append((hwnd, app_id))
        return True

    def set_dim(self, enabled: bool) -> None:
        self.dims.append(enabled)

    def notify(self, title: str, message: str) -> None:
        self.notifications.append((title, message))


class ServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "data.sqlite3")
        self.platform = FakePlatform(Observation("game.exe", "Game", 0, True, 91))
        self.service = WellbeingService(self.store, self.platform)
        self.now = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.service.close()
        self.store.close()
        self.temp.cleanup()

    def test_focus_mode_minimizes_selected_apps_once_per_cooldown(self) -> None:
        self.store.save_rule(Rule("game.exe", "Game", None, True, False, "Entertainment"))
        self.service.start_focus(25, self.now)
        self.service.tick(self.now)
        self.service.tick(self.now + timedelta(seconds=2))
        self.assertEqual(self.platform.minimized, [(91, "game.exe")])
        self.assertEqual(self.store.day_report("2026-09-28")["blocked"], 1)

    def test_dashboard_window_can_recover_from_a_browser_limit(self) -> None:
        self.store.save_rule(Rule("chrome.exe", "Chrome", 0, False, False, "Other"))
        self.platform.observation = Observation("chrome.exe", "Chrome", 0, True, 77, "Digital Wellbeing - Chrome")
        self.service.tick(self.now)
        self.assertEqual(self.platform.minimized, [])

    def test_bedtime_schedule_dims_and_blocks_selected_apps(self) -> None:
        self.store.save_rule(Rule("game.exe", "Game", None, False, True, "Entertainment"))
        self.store.set_settings({
            "bedtime_schedule": {"enabled": True, "start": "17:00", "end": "08:00", "days": [0]},
        })
        self.service.tick(self.now)
        self.assertIn(True, self.platform.dims)
        self.assertEqual(self.platform.minimized, [(91, "game.exe")])

    def test_paused_tracking_does_not_store_usage(self) -> None:
        self.store.set_settings({"tracking_paused": True})
        self.service.tick(self.now)
        self.service.tick(self.now + timedelta(seconds=2))
        self.assertEqual(self.store.day_report("2026-09-28")["total_seconds"], 0)

    def test_antigravity_ide_window_is_not_confused_with_dashboard(self) -> None:
        from digital_wellbeing.service import is_digital_wellbeing_title

        self.assertTrue(is_digital_wellbeing_title("Digital Wellbeing", "msedge.exe"))
        self.assertTrue(is_digital_wellbeing_title("Digital Wellbeing - Google Chrome", "chrome.exe"))
        self.assertTrue(is_digital_wellbeing_title("Digital Wellbeing — Mozilla Firefox", "firefox.exe"))

        # Antigravity IDE and VS Code workspace titles
        self.assertFalse(is_digital_wellbeing_title("sites.py - Digital Wellbeing - Antigravity", "antigravity ide.exe"))
        self.assertFalse(is_digital_wellbeing_title("Digital Wellbeing - Antigravity", "antigravity ide.exe"))
        self.assertFalse(is_digital_wellbeing_title("README.md - Digital Wellbeing - Visual Studio Code", "code.exe"))
        self.assertFalse(is_digital_wellbeing_title("Digital Wellbeing", "explorer.exe"))


if __name__ == "__main__":
    unittest.main()
