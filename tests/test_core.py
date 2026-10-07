import unittest
from datetime import datetime, timedelta, timezone

from digital_wellbeing.core import (
    ActivityTracker,
    Observation,
    Rule,
    Schedule,
    block_reason,
    is_mode_active,
    is_schedule_active,
    split_interval,
)

UTC = timezone.utc
IST = timezone(timedelta(hours=5, minutes=30))


class ScheduleTests(unittest.TestCase):
    def test_overnight_schedule_uses_the_day_it_started(self) -> None:
        monday_only = Schedule(True, "22:00", "07:00", (0,))
        self.assertTrue(is_schedule_active(monday_only, datetime(2026, 9, 28, 23, 0, tzinfo=IST)))
        self.assertTrue(is_schedule_active(monday_only, datetime(2026, 9, 29, 6, 59, tzinfo=IST)))
        self.assertFalse(is_schedule_active(monday_only, datetime(2026, 9, 29, 7, 0, tzinfo=IST)))
        self.assertFalse(is_schedule_active(monday_only, datetime(2026, 9, 29, 23, 0, tzinfo=IST)))

    def test_pause_overrides_a_manual_or_scheduled_mode(self) -> None:
        now = datetime(2026, 9, 28, 23, 0, tzinfo=IST)
        schedule = Schedule(True, "22:00", "07:00", (0,))
        self.assertTrue(is_mode_active(schedule, now, manual_until=now + timedelta(minutes=25)))
        self.assertFalse(
            is_mode_active(
                schedule,
                now,
                manual_until=now + timedelta(minutes=25),
                paused_until=now + timedelta(minutes=5),
            )
        )


class UsageTests(unittest.TestCase):
    def test_usage_is_split_at_local_midnight(self) -> None:
        start = datetime(2026, 9, 28, 18, 29, 58, tzinfo=UTC)
        slices = split_interval(start, start + timedelta(seconds=4), IST)
        self.assertEqual([(s.day, s.hour, s.seconds) for s in slices], [
            ("2026-09-28", 23, 2.0),
            ("2026-09-29", 0, 2.0),
        ])

    def test_tracking_counts_foreground_opens_and_returns_from_idle(self) -> None:
        tracker = ActivityTracker(idle_threshold_seconds=120, max_gap_seconds=5)
        t0 = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
        chrome = Observation("chrome.exe", "Chrome", 0, True, 101)
        code = Observation("code.exe", "VS Code", 0, True, 102)

        first = tracker.step(chrome, t0)
        second = tracker.step(chrome, t0 + timedelta(seconds=2))
        switched = tracker.step(code, t0 + timedelta(seconds=4))
        idle = tracker.step(Observation("code.exe", "VS Code", 122, True, 102), t0 + timedelta(seconds=6))
        returned = tracker.step(code, t0 + timedelta(seconds=70))

        self.assertEqual(first.opened_app, "chrome.exe")
        self.assertTrue(first.session_started)
        self.assertAlmostEqual(second.usage_seconds, 2)
        self.assertEqual(switched.used_app, "chrome.exe")
        self.assertEqual(switched.opened_app, "code.exe")
        self.assertFalse(switched.session_started)
        self.assertEqual(idle.usage_seconds, 0)
        self.assertEqual(returned.opened_app, "code.exe")
        self.assertTrue(returned.session_started)

    def test_tracking_does_not_count_a_sleep_gap(self) -> None:
        tracker = ActivityTracker(idle_threshold_seconds=120, max_gap_seconds=5)
        t0 = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
        obs = Observation("code.exe", "VS Code", 0, True, 1)
        tracker.step(obs, t0)
        result = tracker.step(obs, t0 + timedelta(hours=1))
        self.assertLessEqual(result.usage_seconds, 5)


class PolicyTests(unittest.TestCase):
    def test_limit_focus_and_bedtime_rules_are_enforced(self) -> None:
        rule = Rule("game.exe", "Game", 30, True, True, "Entertainment")
        now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
        self.assertEqual(block_reason(rule, 1800, False, False, now), "limit")
        self.assertEqual(block_reason(rule, 100, True, False, now), "focus")
        self.assertEqual(block_reason(rule, 100, False, True, now), "bedtime")
        self.assertIsNone(block_reason(rule, 100, False, False, now))

    def test_limit_snooze_does_not_disable_focus_mode(self) -> None:
        rule = Rule("game.exe", "Game", 30, True, False, "Entertainment")
        now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
        snooze = now + timedelta(minutes=5)
        self.assertIsNone(block_reason(rule, 1800, False, False, now, snooze))
        self.assertEqual(block_reason(rule, 1800, True, False, now, snooze), "focus")

    def test_protected_system_processes_are_never_blocked(self) -> None:
        rule = Rule("explorer.exe", "Explorer", 1, True, True, "Other")
        now = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
        self.assertIsNone(block_reason(rule, 10000, True, True, now))


if __name__ == "__main__":
    unittest.main()
