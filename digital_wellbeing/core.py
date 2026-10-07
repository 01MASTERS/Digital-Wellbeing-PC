"""Pure usage, schedule, and restriction decisions."""

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone, tzinfo

PROTECTED_APPS = frozenset({
    "explorer.exe",
    "searchhost.exe",
    "shellexperiencehost.exe",
    "startmenuexperiencehost.exe",
    "lockapp.exe",
    "logonui.exe",
    "taskmgr.exe",
    "systemsettings.exe",
    "python.exe",
    "pythonw.exe",
    "digitalwellbeing.exe",
})


@dataclass(frozen=True)
class Schedule:
    enabled: bool
    start: str
    end: str
    days: tuple[int, ...]


@dataclass(frozen=True)
class Rule:
    app_id: str
    app_name: str
    daily_limit_minutes: int | None
    focus_block: bool
    bedtime_block: bool
    category: str


@dataclass(frozen=True)
class Observation:
    app_id: str | None
    app_name: str | None
    idle_seconds: float
    desktop_active: bool
    hwnd: int | None
    window_title: str = ""


@dataclass(frozen=True)
class UsageSlice:
    day: str
    hour: int
    seconds: float


@dataclass(frozen=True)
class StepResult:
    used_app: str | None
    used_name: str | None
    usage_start: datetime | None
    usage_end: datetime | None
    usage_seconds: float
    opened_app: str | None
    opened_name: str | None
    session_started: bool
    at: datetime


def split_interval(start: datetime, end: datetime, local_tz: tzinfo | None = None) -> list[UsageSlice]:
    """Split a UTC interval into local date and hour buckets.

    Minute boundaries are used because they also handle DST changes safely.
    Tracking samples are only a few seconds long in normal operation.
    """
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("Usage timestamps must include a timezone")
    if end <= start:
        return []
    current = start.astimezone(timezone.utc)
    finish = end.astimezone(timezone.utc)
    slices: list[UsageSlice] = []
    while current < finish:
        next_minute = current.replace(second=0, microsecond=0) + timedelta(minutes=1)
        stop = min(finish, next_minute)
        local = current.astimezone(local_tz)
        day = local.date().isoformat()
        hour = local.hour
        seconds = (stop - current).total_seconds()
        if slices and slices[-1].day == day and slices[-1].hour == hour:
            previous = slices[-1]
            slices[-1] = UsageSlice(day, hour, previous.seconds + seconds)
        else:
            slices.append(UsageSlice(day, hour, seconds))
        current = stop
    return slices


def _minute_of_day(value: str) -> int:
    parts = value.split(":")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError("Time must be HH:MM")
    hour, minute = (int(part) for part in parts)
    if not 0 <= hour < 24 or not 0 <= minute < 60:
        raise ValueError("Time must be HH:MM")
    return hour * 60 + minute


def is_schedule_active(schedule: Schedule, now: datetime) -> bool:
    if not schedule.enabled or not schedule.days:
        return False
    start = _minute_of_day(schedule.start)
    end = _minute_of_day(schedule.end)
    minute = now.hour * 60 + now.minute
    today = now.weekday()
    if start == end:
        return today in schedule.days
    if start < end:
        return today in schedule.days and start <= minute < end
    if minute >= start:
        return today in schedule.days
    return (today - 1) % 7 in schedule.days and minute < end


def is_mode_active(
    schedule: Schedule,
    now: datetime,
    manual_until: datetime | None = None,
    indefinite: bool = False,
    paused_until: datetime | None = None,
) -> bool:
    if paused_until is not None and paused_until > now:
        return False
    return indefinite or (manual_until is not None and manual_until > now) or is_schedule_active(schedule, now)


def block_reason(
    rule: Rule,
    used_seconds: float,
    focus_active: bool,
    bedtime_active: bool,
    now: datetime,
    snooze_until: datetime | None = None,
) -> str | None:
    if rule.app_id.casefold() in PROTECTED_APPS:
        return None
    if focus_active and rule.focus_block:
        return "focus"
    if bedtime_active and rule.bedtime_block:
        return "bedtime"
    if (
        rule.daily_limit_minutes is not None
        and used_seconds >= rule.daily_limit_minutes * 60
        and (snooze_until is None or snooze_until <= now)
    ):
        return "limit"
    return None


class ActivityTracker:
    def __init__(self, idle_threshold_seconds: int = 120, max_gap_seconds: int = 5) -> None:
        if idle_threshold_seconds < 1 or max_gap_seconds < 1:
            raise ValueError("Tracking thresholds must be positive")
        self.idle_threshold_seconds = idle_threshold_seconds
        self.max_gap_seconds = max_gap_seconds
        self.previous: Observation | None = None
        self.previous_at: datetime | None = None
        self.last_active_at: datetime | None = None

    def reset(self) -> None:
        self.previous = None
        self.previous_at = None
        self.last_active_at = None

    def _active(self, observation: Observation | None) -> bool:
        return bool(
            observation is not None
            and observation.desktop_active
            and observation.app_id
            and observation.idle_seconds < self.idle_threshold_seconds
        )

    def step(self, observation: Observation, at: datetime) -> StepResult:
        if at.tzinfo is None:
            raise ValueError("Observation timestamps must include a timezone")
        previous = self.previous
        previous_at = self.previous_at
        elapsed = max(0.0, (at - previous_at).total_seconds()) if previous_at else 0.0
        continuous = previous is not None and elapsed <= self.max_gap_seconds
        was_active = self._active(previous) and continuous
        is_active = self._active(observation)

        used_seconds = 0.0
        used_app: str | None = None
        used_name: str | None = None
        usage_start: datetime | None = None
        usage_end: datetime | None = None
        if was_active and previous is not None and previous_at is not None:
            if observation.desktop_active:
                used_seconds = min(elapsed, float(self.max_gap_seconds))
                if observation.idle_seconds >= self.idle_threshold_seconds:
                    idle_at_start = max(0.0, observation.idle_seconds - elapsed)
                    used_seconds = min(used_seconds, max(0.0, self.idle_threshold_seconds - idle_at_start))
            if used_seconds > 0:
                used_app = previous.app_id
                used_name = previous.app_name
                usage_start = previous_at
                usage_end = previous_at + timedelta(seconds=used_seconds)

        opened = bool(is_active and (not was_active or previous is None or previous.app_id != observation.app_id))
        session_started = bool(
            is_active
            and (self.last_active_at is None or (at - self.last_active_at).total_seconds() >= 60)
            and (not was_active or not continuous)
        )
        result = StepResult(
            used_app,
            used_name,
            usage_start,
            usage_end,
            used_seconds,
            observation.app_id if opened else None,
            observation.app_name if opened else None,
            session_started,
            at,
        )
        if is_active:
            self.last_active_at = at
        self.previous = observation
        self.previous_at = at
        return result

