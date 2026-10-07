import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from digital_wellbeing.core import ActivityTracker, Observation, Rule
from digital_wellbeing.storage import Store


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "wellbeing.sqlite3"
        self.store = Store(self.path)

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_usage_opens_sessions_and_focus_time_survive_reopen(self) -> None:
        tracker = ActivityTracker()
        t0 = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
        obs = Observation("code.exe", "VS Code", 0, True, 1)
        self.store.record_step(tracker.step(obs, t0), focus_active=True)
        self.store.record_step(tracker.step(obs, t0 + timedelta(seconds=2)), focus_active=True)
        self.store.close()
        self.store = Store(self.path)

        report = self.store.day_report("2026-09-28")
        self.assertAlmostEqual(report["total_seconds"], 2)
        self.assertAlmostEqual(report["focus_seconds"], 2)
        self.assertEqual(report["opens"], 1)
        self.assertEqual(report["sessions"], 1)
        self.assertEqual(report["apps"][0]["app_id"], "code.exe")

    def test_rule_and_settings_are_persisted_and_history_can_be_cleared(self) -> None:
        rule = Rule("game.exe", "Game", 45, True, True, "Entertainment")
        self.store.save_rule(rule)
        self.store.set_settings({"daily_goal_minutes": 180, "break_interval_minutes": 45})
        tracker = ActivityTracker()
        t0 = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)
        obs = Observation("game.exe", "Game", 0, True, 1)
        self.store.record_step(tracker.step(obs, t0))
        self.store.record_step(tracker.step(obs, t0 + timedelta(seconds=2)))

        self.assertEqual(self.store.get_rule("game.exe"), rule)
        self.assertEqual(self.store.get_settings()["daily_goal_minutes"], 180)
        self.store.clear_history()
        self.assertEqual(self.store.day_report("2026-09-28")["total_seconds"], 0)
        self.assertEqual(self.store.get_rule("game.exe"), rule)


if __name__ == "__main__":
    unittest.main()
