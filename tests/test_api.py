import json
import tempfile
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from digital_wellbeing.core import Observation
from digital_wellbeing.server import LocalServer
from digital_wellbeing.service import WellbeingService
from digital_wellbeing.storage import Store


class FakePlatform:
    def sample(self) -> Observation:
        return Observation(None, None, 0, False, None)

    def minimize(self, hwnd: int, app_id: str) -> bool:
        return False

    def set_dim(self, enabled: bool) -> None:
        pass

    def notify(self, title: str, message: str) -> None:
        pass


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.temp.name) / "data.sqlite3")
        self.service = WellbeingService(self.store, FakePlatform())
        self.server = LocalServer(self.service, self.store, port=0)
        self.server.start()
        self.base = f"http://127.0.0.1:{self.server.port}"

    def tearDown(self) -> None:
        self.server.stop()
        self.service.close()
        self.store.close()
        self.temp.cleanup()

    def get_json(self, path: str) -> dict:
        with urllib.request.urlopen(self.base + path, timeout=3) as response:
            return json.load(response)

    def post(self, path: str, payload: dict, token: str | None = None) -> dict:
        headers = {"Content-Type": "application/json"}
        if token is not None:
            headers["X-Wellbeing-Token"] = token
        request = urllib.request.Request(
            self.base + path, json.dumps(payload).encode(), headers, method="POST"
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            return json.load(response)

    def test_dashboard_serves_real_snapshot(self) -> None:
        token = self.get_json("/api/bootstrap")["token"]
        snapshot = self.get_json("/api/snapshot")
        self.assertTrue(token)
        self.assertIn("today", snapshot)
        self.assertEqual(snapshot["today"]["total_seconds"], 0)
        with urllib.request.urlopen(self.base + "/", timeout=3) as response:
            self.assertIn(b"Digital Wellbeing", response.read())

    def test_mutations_require_token_and_validate_values(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as denied:
            self.post("/api/settings", {"daily_goal_minutes": 180})
        self.assertEqual(denied.exception.code, 403)

        token = self.get_json("/api/bootstrap")["token"]
        self.assertTrue(self.post("/api/settings", {"daily_goal_minutes": 180}, token)["ok"])
        self.assertEqual(self.store.get_settings()["daily_goal_minutes"], 180)
        with self.assertRaises(urllib.error.HTTPError) as invalid:
            self.post("/api/rule", {"app_id": "game.exe", "app_name": "Game", "daily_limit_minutes": -5}, token)
        self.assertEqual(invalid.exception.code, 400)

    def test_export_requires_token(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as denied:
            urllib.request.urlopen(self.base + "/api/export.csv", timeout=3)
        self.assertEqual(denied.exception.code, 403)
        token = self.get_json("/api/bootstrap")["token"]
        request = urllib.request.Request(self.base + "/api/export.csv", headers={"X-Wellbeing-Token": token})
        with urllib.request.urlopen(request, timeout=3) as response:
            self.assertIn("day,hour,app_id", response.read().decode())

    def test_icon_and_site_endpoints(self) -> None:
        with urllib.request.urlopen(self.base + "/api/icon/notepad.exe", timeout=3) as response:
            self.assertIn(response.headers.get("Content-Type"), ("image/png", "image/svg+xml"))
            self.assertGreater(len(response.read()), 0)

        with urllib.request.urlopen(self.base + "/api/icon/digitalwellbeing.exe", timeout=3) as response:
            self.assertEqual(response.headers.get("Content-Type"), "image/png")
            self.assertGreater(len(response.read()), 0)

        with urllib.request.urlopen(self.base + "/api/icon/site/youtube.com", timeout=3) as response:
            self.assertIn(response.headers.get("Content-Type"), ("image/png", "image/svg+xml"))
            self.assertGreater(len(response.read()), 0)

    def test_site_rules_via_api(self) -> None:
        token = self.get_json("/api/bootstrap")["token"]
        res = self.post("/api/site/rule", {
            "domain": "reddit.com",
            "daily_limit_minutes": 30,
            "focus_block": True,
            "bedtime_block": False,
            "category": "Social",
        }, token)
        self.assertTrue(res["ok"])
        rule = self.store.get_site_rule("reddit.com")
        self.assertIsNotNone(rule)
        if rule:
            self.assertEqual(rule.daily_limit_minutes, 30)
            self.assertTrue(rule.focus_block)


if __name__ == "__main__":
    unittest.main()
