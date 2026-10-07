import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from digital_wellbeing.core import Observation, Rule
from digital_wellbeing.service import WellbeingService
from digital_wellbeing.sites import normalize_domain
from digital_wellbeing.storage import Store


class BrowserPlatform:
    def __init__(self) -> None:
        self.observation = Observation("chrome.exe", "Google Chrome", 0, True, 10)

    def sample(self) -> Observation:
        return self.observation

    def minimize(self, hwnd: int, app_id: str) -> bool:
        return False

    def set_dim(self, enabled: bool) -> None:
        pass

    def notify(self, title: str, message: str) -> None:
        pass


class SiteTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "data.sqlite3")
        self.platform = BrowserPlatform()
        self.service = WellbeingService(self.store, self.platform)
        self.now = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)

    def tearDown(self) -> None:
        self.service.close()
        self.store.close()
        self.temp.cleanup()

    def test_domain_normalization_rejects_invalid_hosts(self) -> None:
        self.assertEqual(normalize_domain("WWW.Example.com."), "example.com")
        with self.assertRaises(ValueError):
            normalize_domain("example.com/path")
        with self.assertRaises(ValueError):
            normalize_domain("localhost")

    def test_site_usage_and_rules_persist(self) -> None:
        start = self.now - timedelta(seconds=5)
        self.store.record_site_tick("example.com", start, self.now, opened=True)
        self.store.save_site_rule(Rule("example.com", "example.com", 30, True, False, "Social"))
        day = self.now.astimezone().date().isoformat()
        report = self.store.site_day_report(day)
        self.assertAlmostEqual(report["total_seconds"], 5)
        self.assertEqual(report["opens"], 1)
        self.assertEqual(report["sites"][0]["domain"], "example.com")
        self.assertTrue(self.store.get_site_rule("example.com").focus_block)
        self.store.clear_history()
        self.assertEqual(self.store.site_day_report(day)["total_seconds"], 0)
        self.assertIsNotNone(self.store.get_site_rule("example.com"))

    def test_browser_pulse_respects_focus_rule_and_tracking_pause(self) -> None:
        self.store.save_site_rule(Rule("example.com", "example.com", None, True, False, "Social"))
        self.service.start_focus(25, self.now)
        result = self.service.record_site_tick("www.example.com", 5, True, self.now)
        self.assertEqual(result["reason"], "focus")
        self.assertTrue(result["blocked"])
        self.assertAlmostEqual(result["used_seconds"], 5)

        self.store.set_settings({"tracking_paused": True})
        paused = self.service.record_site_tick("example.com", 5, False, self.now + timedelta(seconds=5))
        self.assertEqual(paused["used_seconds"], 5)

    def test_site_pulse_requires_an_active_browser(self) -> None:
        self.platform.observation = Observation("code.exe", "VS Code", 0, True, 11)
        result = self.service.record_site_tick("example.com", 5, True, self.now)
        self.assertEqual(result["used_seconds"], 0)


if __name__ == "__main__":
    unittest.main()
