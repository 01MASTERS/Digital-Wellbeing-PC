"""Coordinates sampling, persistence, and wellbeing policies."""

import re
import threading
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol

from digital_wellbeing.core import (
    PROTECTED_APPS,
    ActivityTracker,
    Observation,
    Rule,
    Schedule,
    block_reason,
    is_mode_active,
)
from digital_wellbeing.sites import (
    extract_domain_from_title,
    is_browser_app,
    normalize_domain,
)
from digital_wellbeing.storage import Store

APP_ID_PATTERN = re.compile(r"^[a-z0-9._-]{1,128}$")
TIME_PATTERN = re.compile(r"^([01][0-9]|2[0-3]):[0-5][0-9]$")
CATEGORIES = ("Productive", "Communication", "Social", "Entertainment", "Utilities", "Other")


class Platform(Protocol):
    def sample(self) -> Observation: ...

    def minimize(self, hwnd: int, app_id: str) -> bool: ...

    def set_dim(self, enabled: bool) -> None: ...

    def notify(self, title: str, message: str) -> None: ...


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None


def _schedule(value: dict[str, Any]) -> Schedule:
    return Schedule(bool(value["enabled"]), str(value["start"]), str(value["end"]), tuple(value["days"]))


def _validated_schedule(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError("Schedule must be an object")
    enabled = value.get("enabled")
    start = value.get("start")
    end = value.get("end")
    days = value.get("days")
    if not isinstance(enabled, bool) or not isinstance(start, str) or not TIME_PATTERN.fullmatch(start):
        raise ValueError("Schedule needs an enabled flag and a valid start time")
    if not isinstance(end, str) or not TIME_PATTERN.fullmatch(end):
        raise ValueError("Schedule needs a valid end time")
    if not isinstance(days, list) or any(type(day) is not int or day not in range(7) for day in days):
        raise ValueError("Schedule days must be numbers from 0 to 6")
    return {"enabled": enabled, "start": start, "end": end, "days": sorted(set(days))}


def is_digital_wellbeing_title(title: str | None, app_id: str | None = None) -> bool:
    """Return True if title corresponds to Digital Wellbeing dashboard window, not an IDE editing it."""
    if not title:
        return False
    t = title.strip().casefold()
    if t != "digital wellbeing" and not t.startswith(
        ("digital wellbeing -", "digital wellbeing —", "digital wellbeing ·")
    ):
        return False
    if any(k in t for k in ("antigravity", "visual studio", "vs code", "cursor", "sublime", "pycharm", ".py", ".md", ".json", ".js", ".html", ".css", ".ts")):
        return False
    return not bool(app_id and app_id.casefold() in ("antigravity ide.exe", "code.exe", "cursor.exe", "explorer.exe", "devenv.exe"))


class WellbeingService:
    def __init__(self, store: Store, platform: Platform) -> None:
        self.store = store
        self.platform = platform
        settings = store.get_settings()
        self.tracker = ActivityTracker(settings["idle_threshold_seconds"])
        self._lock = threading.RLock()
        self._last_block: dict[tuple[int, str], datetime] = {}
        self._dimmed = False
        self._grayscaled = False
        self._active_streak = 0.0
        self._break_notified = False
        self._current_app: str | None = None

    def close(self) -> None:
        with self._lock:
            if self._dimmed:
                self.platform.set_dim(False)
                self._dimmed = False
            if self._grayscaled:
                if hasattr(self.platform, "set_grayscale"):
                    self.platform.set_grayscale(False)
                self._grayscaled = False

    def _modes(self, settings: dict[str, Any], now: datetime) -> tuple[bool, bool]:
        local = now.astimezone()
        focus = is_mode_active(
            _schedule(settings["focus_schedule"]),
            local,
            _parse_time(settings["focus_manual_until"]),
            bool(settings["focus_indefinite"]),
            _parse_time(settings["focus_paused_until"]),
        )
        bedtime = is_mode_active(
            _schedule(settings["bedtime_schedule"]),
            local,
            _parse_time(settings["bedtime_manual_until"]),
            False,
            _parse_time(settings["bedtime_paused_until"]),
        )
        return focus, bedtime

    def tick(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        with self._lock:
            settings = self.store.get_settings()
            focus_active, bedtime_active = self._modes(settings, now)
            dim = bedtime_active and bool(settings["bedtime_dim"])
            if dim != self._dimmed:
                self.platform.set_dim(dim)
                self._dimmed = dim

            grayscale = bedtime_active and bool(settings.get("bedtime_grayscale", True))
            if grayscale != self._grayscaled:
                if hasattr(self.platform, "set_grayscale"):
                    self.platform.set_grayscale(grayscale)
                self._grayscaled = grayscale

            observation = self.platform.sample()
            self._current_app = observation.app_name if observation.desktop_active else None
            if settings["tracking_paused"]:
                self.tracker.reset()
                self._active_streak = 0
                self._break_notified = False
            else:
                if self.tracker.idle_threshold_seconds != settings["idle_threshold_seconds"]:
                    self.tracker = ActivityTracker(settings["idle_threshold_seconds"])
                step = self.tracker.step(observation, now)
                self.store.record_step(step, focus_active, bedtime_active)
                if observation.desktop_active and observation.app_id and observation.idle_seconds < settings["idle_threshold_seconds"]:
                    self._active_streak += step.usage_seconds
                    break_seconds = settings["break_interval_minutes"] * 60
                    if break_seconds > 0 and self._active_streak >= break_seconds and not self._break_notified:
                        self.platform.notify("Time for a break", "You've been active for a while. Stretch and rest your eyes.")
                        self.store.record_event("break_reminder", now)
                        self._break_notified = True
                    if is_browser_app(observation.app_id) and observation.window_title:
                        domain = extract_domain_from_title(observation.window_title, observation.app_id)
                        if domain and step.usage_seconds > 0:
                            self.record_site_tick(domain, step.usage_seconds, opened=bool(step.opened_app), now=now)
                else:
                    self._active_streak = 0
                    self._break_notified = False

            if not observation.app_id or observation.hwnd is None or not observation.desktop_active:
                return
            if is_digital_wellbeing_title(observation.window_title, observation.app_id):
                return
            rule = self.store.get_rule(observation.app_id)
            if rule is None:
                return
            day = now.astimezone().date().isoformat()
            used_seconds = self.store.app_seconds_today(observation.app_id, day)
            snooze = _parse_time(settings["snoozes"].get(observation.app_id))
            reason = block_reason(rule, used_seconds, focus_active, bedtime_active, now, snooze)
            if reason is None:
                return
            key = (observation.hwnd, reason)
            last_blocked = self._last_block.get(key)
            if last_blocked is not None and (now - last_blocked).total_seconds() < 15:
                return
            if self.platform.minimize(observation.hwnd, observation.app_id):
                self._last_block[key] = now
                self.store.record_event("blocked", now, observation.app_id, reason)
                self.platform.notify(
                    "Digital Wellbeing",
                    f"{rule.app_name} was minimized because of your {reason} setting.",
                )

    def start_focus(self, minutes: int | None, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        if minutes is not None and (type(minutes) is not int or not 5 <= minutes <= 480):
            raise ValueError("Focus duration must be 5 to 480 minutes")
        self.store.set_settings({
            "focus_manual_until": (now + timedelta(minutes=minutes)).isoformat() if minutes else None,
            "focus_indefinite": minutes is None,
            "focus_paused_until": None,
        })
        self.store.record_event("focus_start", now)

    def stop_focus(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        self.store.set_settings({"focus_manual_until": None, "focus_indefinite": False})
        self.store.record_event("focus_stop", now)

    def pause_focus(self, minutes: int = 5, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        if type(minutes) is not int or not 1 <= minutes <= 60:
            raise ValueError("Focus pause must be 1 to 60 minutes")
        self.store.set_settings({"focus_paused_until": (now + timedelta(minutes=minutes)).isoformat()})
        self.store.record_event("focus_pause", now)

    def start_bedtime(self, minutes: int = 60, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        if type(minutes) is not int or not 15 <= minutes <= 720:
            raise ValueError("Bedtime duration must be 15 to 720 minutes")
        self.store.set_settings({
            "bedtime_manual_until": (now + timedelta(minutes=minutes)).isoformat(),
            "bedtime_paused_until": None,
        })
        self.store.record_event("bedtime_start", now)

    def stop_bedtime(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        self.store.set_settings({
            "bedtime_manual_until": None,
            "bedtime_paused_until": (now + timedelta(hours=8)).isoformat(),
        })
        self.store.record_event("bedtime_stop", now)

    def snooze_app(self, app_id: str, minutes: int = 5, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        if not APP_ID_PATTERN.fullmatch(app_id) or type(minutes) is not int or not 1 <= minutes <= 30:
            raise ValueError("Invalid app or snooze duration")
        settings = self.store.get_settings()
        snoozes = dict(settings["snoozes"])
        snoozes[app_id] = (now + timedelta(minutes=minutes)).isoformat()
        self.store.set_settings({"snoozes": snoozes})
        self.store.record_event("limit_snooze", now, app_id, str(minutes))

    def update_settings(self, values: dict[str, Any]) -> None:
        allowed: dict[str, Any] = {}
        for key, value in values.items():
            if key in ("daily_goal_minutes", "idle_threshold_seconds", "break_interval_minutes"):
                low, high = {
                    "daily_goal_minutes": (15, 1440),
                    "idle_threshold_seconds": (15, 900),
                    "break_interval_minutes": (0, 240),
                }[key]
                if type(value) is not int or not low <= value <= high:
                    raise ValueError(f"{key} must be between {low} and {high}")
                allowed[key] = value
            elif key in ("tracking_paused", "bedtime_dim", "bedtime_grayscale"):
                if not isinstance(value, bool):
                    raise ValueError(f"{key} must be true or false")
                allowed[key] = value
            elif key in ("focus_schedule", "bedtime_schedule"):
                allowed[key] = _validated_schedule(value)
            else:
                raise ValueError(f"Unknown setting: {key}")
        self.store.set_settings(allowed)

    def record_site_tick(
        self,
        domain: str,
        seconds: float,
        opened: bool,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        current_obs = self.platform.sample()
        if not is_browser_app(current_obs.app_id):
            return {"used_seconds": 0, "blocked": False, "reason": None}

        clean_domain = normalize_domain(domain)
        settings = self.store.get_settings()
        focus_active, bedtime_active = self._modes(settings, now)
        day = now.astimezone().date().isoformat()

        if not settings["tracking_paused"]:
            start = now - timedelta(seconds=seconds)
            self.store.record_site_tick(clean_domain, start, now, opened=opened)

        rule = self.store.get_site_rule(clean_domain)
        blocked = False
        reason: str | None = None
        if rule is not None:
            used_seconds = self.store.site_seconds_today(clean_domain, day)
            reason = block_reason(rule, used_seconds, focus_active, bedtime_active, now)
            if reason is not None:
                blocked = True

        return {"used_seconds": seconds, "blocked": blocked, "reason": reason}

    def save_site_rule(self, value: dict[str, Any]) -> Rule:
        domain = value.get("domain") or value.get("app_id")
        if not isinstance(domain, str):
            raise TypeError("Domain is required")
        clean_domain = normalize_domain(domain)
        display_name = value.get("display_name") or value.get("app_name") or clean_domain
        limit = value.get("daily_limit_minutes")
        category = value.get("category", "Social")
        focus_block = value.get("focus_block", False)
        bedtime_block = value.get("bedtime_block", False)
        if limit is not None and (type(limit) is not int or not 1 <= limit <= 1440):
            raise ValueError("Daily limit must be 1 to 1440 minutes")
        if not isinstance(focus_block, bool) or not isinstance(bedtime_block, bool):
            raise TypeError("Block switches must be true or false")
        rule = Rule(clean_domain, str(display_name).strip(), limit, focus_block, bedtime_block, category)
        self.store.save_site_rule(rule)
        return rule

    def save_rule(self, value: dict[str, Any]) -> Rule:
        app_id = value.get("app_id")
        app_name = value.get("app_name")
        limit = value.get("daily_limit_minutes")
        category = value.get("category", "Other")
        focus_block = value.get("focus_block", False)
        bedtime_block = value.get("bedtime_block", False)
        if not isinstance(app_id, str) or not APP_ID_PATTERN.fullmatch(app_id):
            raise ValueError("App id must be a process name such as chrome.exe")
        if not isinstance(app_name, str) or not 1 <= len(app_name.strip()) <= 80:
            raise ValueError("App name must be 1 to 80 characters")
        if limit is not None and (type(limit) is not int or not 1 <= limit <= 1440):
            raise ValueError("Daily limit must be 1 to 1440 minutes")
        if category not in CATEGORIES:
            raise ValueError("Invalid app category")
        if not isinstance(focus_block, bool) or not isinstance(bedtime_block, bool):
            raise TypeError("Block switches must be true or false")
        rule = Rule(app_id, app_name.strip(), limit, focus_block, bedtime_block, category)
        self.store.save_rule(rule)
        return rule

    def snapshot(self, day: str | None = None, now: datetime | None = None) -> dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        local_day = now.astimezone().date().isoformat()
        selected_day = day or local_day
        try:
            datetime.fromisoformat(selected_day).date()
        except ValueError as error:
            raise ValueError("Invalid date") from error
        settings = self.store.get_settings()
        focus_active, bedtime_active = self._modes(settings, now)
        today = self.store.day_report(selected_day)
        today_by_id = {app["app_id"]: app for app in today["apps"]}
        rules = {rule.app_id: rule for rule in self.store.get_rules()}
        apps = []
        for known in self.store.known_apps():
            app_id = known["app_id"]
            usage = today_by_id.get(app_id, {})
            rule = rules.get(app_id)
            apps.append({
                **known,
                "seconds": usage.get("seconds", 0),
                "opens": usage.get("opens", 0),
                "daily_limit_minutes": rule.daily_limit_minutes if rule else None,
                "focus_block": rule.focus_block if rule else False,
                "bedtime_block": rule.bedtime_block if rule else False,
                "category": rule.category if rule else "Other",
                "protected": app_id in PROTECTED_APPS,
            })
        apps.sort(key=lambda app: (-app["seconds"], app["app_name"].casefold()))

        today_sites = self.store.site_day_report(selected_day)
        today_sites_by_domain = {s["domain"]: s for s in today_sites["sites"]}
        site_rules = {rule.app_id: rule for rule in self.store.get_site_rules()}
        sites = []
        for known in self.store.known_sites():
            domain = known["domain"]
            site_usage = today_sites_by_domain.get(domain, {})
            site_rule = site_rules.get(domain)
            sites.append({
                "domain": domain,
                "display_name": site_rule.app_name if site_rule else domain,
                "seconds": site_usage.get("seconds", 0),
                "opens": site_usage.get("opens", 0),
                "daily_limit_minutes": site_rule.daily_limit_minutes if site_rule else None,
                "focus_block": site_rule.focus_block if site_rule else False,
                "bedtime_block": site_rule.bedtime_block if site_rule else False,
                "category": site_rule.category if site_rule else "Social",
            })
        sites.sort(key=lambda s: (-s["seconds"], s["domain"]))

        return {
            "today": today,
            "week": self.store.week_report(selected_day),
            "apps": apps,
            "sites": sites,
            "today_sites": today_sites,
            "settings": settings,
            "modes": {
                "focus_active": focus_active,
                "bedtime_active": bedtime_active,
                "focus_manual_until": settings["focus_manual_until"],
                "focus_indefinite": settings["focus_indefinite"],
                "focus_paused_until": settings["focus_paused_until"],
                "bedtime_manual_until": settings["bedtime_manual_until"],
            },
            "current_app": self._current_app,
            "selected_day": selected_day,
            "local_day": local_day,
            "categories": list(CATEGORIES),
            "protected_apps": sorted(PROTECTED_APPS),
        }

    def rule_as_dict(self, rule: Rule) -> dict[str, Any]:
        return asdict(rule)
