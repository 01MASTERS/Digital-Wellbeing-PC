"""SQLite persistence for local activity and user preferences."""

import csv
import io
import json
import sqlite3
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from digital_wellbeing.core import Rule, StepResult, split_interval

DEFAULT_SETTINGS: dict[str, Any] = {
    "daily_goal_minutes": 240,
    "idle_threshold_seconds": 120,
    "break_interval_minutes": 60,
    "tracking_paused": False,
    "bedtime_dim": True,
    "bedtime_grayscale": True,
    "focus_schedule": {"enabled": False, "start": "09:00", "end": "17:00", "days": [0, 1, 2, 3, 4]},
    "bedtime_schedule": {"enabled": False, "start": "22:30", "end": "07:00", "days": [0, 1, 2, 3, 4, 5, 6]},
    "focus_manual_until": None,
    "focus_indefinite": False,
    "focus_paused_until": None,
    "bedtime_manual_until": None,
    "bedtime_paused_until": None,
    "snoozes": {},
}


class Store:
    """Thread-safe store shared by the sampler and the dashboard server."""

    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.RLock()
        self._db = sqlite3.connect(path, check_same_thread=False, timeout=10)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        with self._db:
            self._db.executescript(
                """
                CREATE TABLE IF NOT EXISTS usage (
                    day TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    app_id TEXT NOT NULL,
                    app_name TEXT NOT NULL,
                    seconds REAL NOT NULL DEFAULT 0,
                    opens INTEGER NOT NULL DEFAULT 0,
                    focus_seconds REAL NOT NULL DEFAULT 0,
                    bedtime_seconds REAL NOT NULL DEFAULT 0,
                    PRIMARY KEY (day, hour, app_id)
                );
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    at TEXT NOT NULL,
                    day TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    app_id TEXT,
                    detail TEXT
                );
                CREATE INDEX IF NOT EXISTS events_day_kind ON events(day, kind);
                CREATE TABLE IF NOT EXISTS rules (
                    app_id TEXT PRIMARY KEY,
                    app_name TEXT NOT NULL,
                    daily_limit_minutes INTEGER,
                    focus_block INTEGER NOT NULL DEFAULT 0,
                    bedtime_block INTEGER NOT NULL DEFAULT 0,
                    category TEXT NOT NULL DEFAULT 'Other'
                );
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS site_usage (
                    day TEXT NOT NULL,
                    hour INTEGER NOT NULL,
                    domain TEXT NOT NULL,
                    seconds REAL NOT NULL DEFAULT 0,
                    opens INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (day, hour, domain)
                );
                CREATE TABLE IF NOT EXISTS site_rules (
                    domain TEXT PRIMARY KEY,
                    display_name TEXT NOT NULL,
                    daily_limit_minutes INTEGER,
                    focus_block INTEGER NOT NULL DEFAULT 0,
                    bedtime_block INTEGER NOT NULL DEFAULT 0,
                    category TEXT NOT NULL DEFAULT 'Social'
                );
                """
            )

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def _add_usage(
        self,
        day: str,
        hour: int,
        app_id: str,
        app_name: str,
        seconds: float = 0.0,
        opens: int = 0,
        focus_seconds: float = 0.0,
        bedtime_seconds: float = 0.0,
    ) -> None:
        self._db.execute(
            """
            INSERT INTO usage(day, hour, app_id, app_name, seconds, opens, focus_seconds, bedtime_seconds)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(day, hour, app_id) DO UPDATE SET
                app_name=excluded.app_name,
                seconds=usage.seconds + excluded.seconds,
                opens=usage.opens + excluded.opens,
                focus_seconds=usage.focus_seconds + excluded.focus_seconds,
                bedtime_seconds=usage.bedtime_seconds + excluded.bedtime_seconds
            """,
            (day, hour, app_id, app_name, seconds, opens, focus_seconds, bedtime_seconds),
        )

    def record_step(self, step: StepResult, focus_active: bool = False, bedtime_active: bool = False) -> None:
        with self._lock, self._db:
            if step.used_app and step.used_name and step.usage_start and step.usage_end:
                for part in split_interval(step.usage_start, step.usage_end):
                    self._add_usage(
                        part.day,
                        part.hour,
                        step.used_app,
                        step.used_name,
                        seconds=part.seconds,
                        focus_seconds=part.seconds if focus_active else 0.0,
                        bedtime_seconds=part.seconds if bedtime_active else 0.0,
                    )
            local = step.at.astimezone()
            day = local.date().isoformat()
            if step.opened_app and step.opened_name:
                self._add_usage(day, local.hour, step.opened_app, step.opened_name, opens=1)
                self._db.execute(
                    "INSERT INTO events(at, day, kind, app_id) VALUES (?, ?, 'app_open', ?)",
                    (step.at.isoformat(), day, step.opened_app),
                )
            if step.session_started:
                self._db.execute(
                    "INSERT INTO events(at, day, kind, app_id) VALUES (?, ?, 'session_start', ?)",
                    (step.at.isoformat(), day, step.opened_app),
                )

    def record_event(self, kind: str, at: datetime, app_id: str | None = None, detail: str | None = None) -> None:
        day = at.astimezone().date().isoformat()
        with self._lock, self._db:
            self._db.execute(
                "INSERT INTO events(at, day, kind, app_id, detail) VALUES (?, ?, ?, ?, ?)",
                (at.isoformat(), day, kind, app_id, detail),
            )

    def day_report(self, day: str) -> dict[str, Any]:
        with self._lock:
            rows = self._db.execute(
                """
                SELECT app_id, MAX(app_name) AS app_name, SUM(seconds) AS seconds,
                       SUM(opens) AS opens, SUM(focus_seconds) AS focus_seconds,
                       SUM(bedtime_seconds) AS bedtime_seconds
                FROM usage WHERE day=? GROUP BY app_id ORDER BY seconds DESC, app_name
                """,
                (day,),
            ).fetchall()
            hour_rows = self._db.execute(
                "SELECT hour, SUM(seconds) AS seconds FROM usage WHERE day=? GROUP BY hour",
                (day,),
            ).fetchall()
            event_rows = self._db.execute(
                "SELECT kind, COUNT(*) AS count FROM events WHERE day=? GROUP BY kind",
                (day,),
            ).fetchall()
        apps = [dict(row) for row in rows]
        hourly = [0.0] * 24
        for row in hour_rows:
            hourly[row["hour"]] = float(row["seconds"])
        events = {row["kind"]: row["count"] for row in event_rows}
        return {
            "day": day,
            "total_seconds": sum(float(app["seconds"]) for app in apps),
            "focus_seconds": sum(float(app["focus_seconds"]) for app in apps),
            "bedtime_seconds": sum(float(app["bedtime_seconds"]) for app in apps),
            "opens": sum(int(app["opens"]) for app in apps),
            "sessions": events.get("session_start", 0),
            "blocked": events.get("blocked", 0),
            "apps": apps,
            "hourly": hourly,
        }

    def week_report(self, end_day: str) -> list[dict[str, Any]]:
        last = datetime.fromisoformat(end_day).date()
        return [self.day_report((last - timedelta(days=offset)).isoformat()) for offset in range(6, -1, -1)]

    def app_seconds_today(self, app_id: str, day: str) -> float:
        with self._lock:
            row = self._db.execute(
                "SELECT COALESCE(SUM(seconds), 0) AS seconds FROM usage WHERE day=? AND app_id=?",
                (day, app_id),
            ).fetchone()
        return float(row["seconds"])

    def save_rule(self, rule: Rule) -> None:
        with self._lock, self._db:
            self._db.execute(
                """
                INSERT INTO rules(app_id, app_name, daily_limit_minutes, focus_block, bedtime_block, category)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(app_id) DO UPDATE SET
                    app_name=excluded.app_name,
                    daily_limit_minutes=excluded.daily_limit_minutes,
                    focus_block=excluded.focus_block,
                    bedtime_block=excluded.bedtime_block,
                    category=excluded.category
                """,
                (
                    rule.app_id,
                    rule.app_name,
                    rule.daily_limit_minutes,
                    int(rule.focus_block),
                    int(rule.bedtime_block),
                    rule.category,
                ),
            )

    @staticmethod
    def _rule_from_row(row: sqlite3.Row) -> Rule:
        return Rule(
            row["app_id"],
            row["app_name"],
            row["daily_limit_minutes"],
            bool(row["focus_block"]),
            bool(row["bedtime_block"]),
            row["category"],
        )

    def get_rule(self, app_id: str) -> Rule | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM rules WHERE app_id=?", (app_id,)).fetchone()
        return self._rule_from_row(row) if row else None

    def get_rules(self) -> list[Rule]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM rules ORDER BY app_name").fetchall()
        return [self._rule_from_row(row) for row in rows]

    def known_apps(self) -> list[dict[str, Any]]:
        with self._lock:
            usage = self._db.execute(
                "SELECT app_id, MAX(app_name) AS app_name, MAX(day) AS last_seen "
                "FROM usage GROUP BY app_id ORDER BY last_seen DESC, app_name"
            ).fetchall()
        apps = {row["app_id"]: dict(row) for row in usage}
        for rule in self.get_rules():
            apps.setdefault(rule.app_id, {"app_id": rule.app_id, "app_name": rule.app_name, "last_seen": None})
        return list(apps.values())

    def set_settings(self, values: dict[str, Any]) -> None:
        with self._lock, self._db:
            self._db.executemany(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                [(key, json.dumps(value)) for key, value in values.items()],
            )

    def get_settings(self) -> dict[str, Any]:
        with self._lock:
            rows = self._db.execute("SELECT key, value FROM settings").fetchall()
        return {**DEFAULT_SETTINGS, **{row["key"]: json.loads(row["value"]) for row in rows}}

    def clear_history(self) -> None:
        with self._lock, self._db:
            self._db.execute("DELETE FROM usage")
            self._db.execute("DELETE FROM events")
            self._db.execute("DELETE FROM site_usage")

    def record_site_tick(
        self,
        domain: str,
        start: datetime,
        end: datetime,
        opened: bool = False,
    ) -> None:
        with self._lock, self._db:
            first = True
            for part in split_interval(start, end):
                self._db.execute(
                    """
                    INSERT INTO site_usage(day, hour, domain, seconds, opens)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(day, hour, domain) DO UPDATE SET
                        seconds=site_usage.seconds + excluded.seconds,
                        opens=site_usage.opens + excluded.opens
                    """,
                    (part.day, part.hour, domain, part.seconds, 1 if (opened and first) else 0),
                )
                first = False

    def save_site_rule(self, rule: Rule) -> None:
        with self._lock, self._db:
            self._db.execute(
                """
                INSERT INTO site_rules(domain, display_name, daily_limit_minutes, focus_block, bedtime_block, category)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(domain) DO UPDATE SET
                    display_name=excluded.display_name,
                    daily_limit_minutes=excluded.daily_limit_minutes,
                    focus_block=excluded.focus_block,
                    bedtime_block=excluded.bedtime_block,
                    category=excluded.category
                """,
                (
                    rule.app_id,
                    rule.app_name,
                    rule.daily_limit_minutes,
                    int(rule.focus_block),
                    int(rule.bedtime_block),
                    rule.category,
                ),
            )

    def get_site_rule(self, domain: str) -> Rule | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM site_rules WHERE domain=?", (domain,)).fetchone()
        return (
            Rule(
                row["domain"],
                row["display_name"],
                row["daily_limit_minutes"],
                bool(row["focus_block"]),
                bool(row["bedtime_block"]),
                row["category"],
            )
            if row
            else None
        )

    def get_site_rules(self) -> list[Rule]:
        with self._lock:
            rows = self._db.execute("SELECT * FROM site_rules ORDER BY domain").fetchall()
        return [
            Rule(
                row["domain"],
                row["display_name"],
                row["daily_limit_minutes"],
                bool(row["focus_block"]),
                bool(row["bedtime_block"]),
                row["category"],
            )
            for row in rows
        ]

    def site_seconds_today(self, domain: str, day: str) -> float:
        with self._lock:
            row = self._db.execute(
                "SELECT COALESCE(SUM(seconds), 0) AS seconds FROM site_usage WHERE day=? AND domain=?",
                (day, domain),
            ).fetchone()
        return float(row["seconds"])

    def site_day_report(self, day: str) -> dict[str, Any]:
        with self._lock:
            rows = self._db.execute(
                """
                SELECT domain, SUM(seconds) AS seconds, SUM(opens) AS opens
                FROM site_usage WHERE day=? GROUP BY domain ORDER BY seconds DESC, domain
                """,
                (day,),
            ).fetchall()
        sites = [dict(row) for row in rows]
        return {
            "day": day,
            "total_seconds": sum(float(site["seconds"]) for site in sites),
            "opens": sum(int(site["opens"]) for site in sites),
            "sites": sites,
        }

    def known_sites(self) -> list[dict[str, Any]]:
        with self._lock:
            usage = self._db.execute(
                "SELECT domain, MAX(day) AS last_seen FROM site_usage GROUP BY domain ORDER BY last_seen DESC, domain"
            ).fetchall()
        sites = {row["domain"]: {"domain": row["domain"], "last_seen": row["last_seen"]} for row in usage}
        for rule in self.get_site_rules():
            sites.setdefault(rule.app_id, {"domain": rule.app_id, "last_seen": None})
        return list(sites.values())

    def export_csv(self) -> str:
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(("day", "hour", "app_id", "app_name", "seconds", "opens", "focus_seconds", "bedtime_seconds"))
        with self._lock:
            rows = self._db.execute(
                "SELECT day, hour, app_id, app_name, seconds, opens, focus_seconds, bedtime_seconds "
                "FROM usage ORDER BY day, hour, app_id"
            ).fetchall()
        writer.writerows(tuple(row) for row in rows)
        return output.getvalue()
