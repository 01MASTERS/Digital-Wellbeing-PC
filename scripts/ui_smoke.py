"""Exercise the real dashboard in a headless browser with disposable data."""

import tempfile
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from playwright.sync_api import sync_playwright

from digital_wellbeing.core import Observation, Rule, StepResult
from digital_wellbeing.server import LocalServer
from digital_wellbeing.service import WellbeingService
from digital_wellbeing.storage import Store


class QuietPlatform:
    def sample(self) -> Observation:
        return Observation(None, None, 0, False, None)

    def minimize(self, hwnd: int, app_id: str) -> bool:
        return False

    def set_dim(self, enabled: bool) -> None:
        pass

    def notify(self, title: str, message: str) -> None:
        pass


def seed(store: Store) -> None:
    apps = [
        ("chrome.exe", "Google Chrome", 2700, "Social"),
        ("code.exe", "VS Code", 5400, "Productive"),
        ("spotify.exe", "Spotify", 900, "Entertainment"),
    ]
    local_tz = datetime.now().astimezone().tzinfo
    today = datetime.now().astimezone().date()
    for offset in range(7):
        day = today - timedelta(days=offset)
        for index, (app_id, name, base_seconds, category) in enumerate(apps):
            seconds = base_seconds * (0.65 + ((offset + index) % 4) * 0.16)
            start = datetime.combine(day, time(9 + index * 2, 20), local_tz).astimezone(timezone.utc)
            end = start + timedelta(seconds=seconds)
            store.record_step(StepResult(app_id, name, start, end, seconds, app_id, name, True, start))
            store.save_rule(Rule(app_id, name, None, False, False, category))
    now = datetime.now(timezone.utc)
    store.record_site_tick("github.com", now - timedelta(seconds=1200), now, True)


def main() -> None:
    output = Path(__file__).resolve().parent.parent / "artifacts"
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as directory:
        store = Store(Path(directory) / "activity.sqlite3")
        seed(store)
        service = WellbeingService(store, QuietPlatform())
        server = LocalServer(service, store, port=0, autostart_get=lambda: False, autostart_set=lambda _enabled: None)
        server.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True)
                page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
                errors: list[str] = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.goto(f"http://127.0.0.1:{server.port}/", wait_until="networkidle")
                page.get_by_role("heading", name="Overview").wait_for()
                page.get_by_text("Weekly rhythm").wait_for()
                assert page.locator(".donut-svg").is_visible()
                page.screenshot(path=str(output / "overview.png"), full_page=True)

                # Test app details modal
                page.locator('[data-action="open-app-modal"][data-app="chrome.exe"]').first.click()
                page.locator(".modal-backdrop").wait_for()
                assert "Chrome" in page.locator(".modal-title-group h2").inner_text()
                page.locator('.preset-chip[data-minutes="30"]').click()
                page.screenshot(path=str(output / "app-modal.png"))
                page.locator(".modal-close-btn").click()
                page.locator(".modal-backdrop").wait_for(state="detached")

                page.locator('.nav-item[data-page="apps"]').click()
                row = page.locator('.managed-app[data-app="chrome.exe"]')
                row.locator('[data-role="limit"]').fill("45")
                row.get_by_role("button", name="Save app").click()
                page.get_by_text("App rule saved").wait_for()
                chrome_rule = store.get_rule("chrome.exe")
                assert chrome_rule is not None and chrome_rule.daily_limit_minutes == 45

                # Test website tab in App Activity
                page.locator('button[data-action="switch-tab"][data-tab="sites"]').click()
                site_row = page.locator('.managed-app[data-site="github.com"]')
                site_row.locator('[data-role="site-limit"]').fill("25")
                site_row.locator('button[data-action="save-site"]').click()
                page.get_by_text("Website timer saved").wait_for()
                github_rule = store.get_site_rule("github.com")
                assert github_rule is not None and github_rule.daily_limit_minutes == 25

                page.locator('.nav-item[data-page="focus"]').click()
                page.locator('button[data-action="toggle-rule"][data-app="chrome.exe"]').click()
                chrome_rule = store.get_rule("chrome.exe")
                assert chrome_rule is not None and chrome_rule.focus_block
                page.locator('button[data-action="start-focus"][data-minutes="25"]').click()
                page.get_by_text("Focus is active").wait_for()
                page.screenshot(path=str(output / "focus.png"), full_page=True)

                page.locator('.nav-item[data-page="bedtime"]').click()
                page.locator('button[data-action="start-bedtime"][data-minutes="60"]').click()
                page.get_by_text("Wind down is active").wait_for()
                page.locator('button[data-action="toggle-dim"]').click()
                assert not store.get_settings()["bedtime_dim"]
                page.locator('button[data-action="toggle-grayscale"]').click()
                assert not store.get_settings()["bedtime_grayscale"]
                page.screenshot(path=str(output / "bedtime.png"), full_page=True)

                page.locator('.nav-item[data-page="insights"]').click()
                page.get_by_text("Day-by-day Activity").wait_for()
                page.screenshot(path=str(output / "insights.png"), full_page=True)

                page.locator('.nav-item[data-page="settings"]').click()
                page.get_by_text("Appearance & Theme").wait_for()
                page.screenshot(path=str(output / "settings.png"), full_page=True)
                page.locator("#idle-threshold").fill("120")
                page.locator('button[data-action="save-settings"]').click()
                page.get_by_text("Tracking preferences saved").wait_for()
                assert store.get_settings()["idle_threshold_seconds"] == 120

                # Test desktop shortcut creation button
                page.locator('button[data-action="create-shortcut"]').click()
                page.get_by_text("Created Desktop & Start Menu shortcuts!").wait_for()

                # Test dark mode quick toggle and capture dark settings
                page.locator("#theme-toggle-btn").click()
                assert page.evaluate("document.documentElement.getAttribute('data-theme') === 'dark'")
                page.screenshot(path=str(output / "settings-dark.png"), full_page=True)

                # Capture dark mode overview
                page.locator('.nav-item[data-page="overview"]').click()
                page.locator('.donut-svg').wait_for()
                page.wait_for_timeout(300)
                page.screenshot(path=str(output / "overview-dark.png"), full_page=True)

                # Return to settings and test theme segmented button
                page.locator('.nav-item[data-page="settings"]').click()
                page.locator('button[data-action="set-theme"][data-theme="light"]').click()
                assert page.evaluate("document.documentElement.getAttribute('data-theme') === 'light'")

                with page.expect_download() as download_info:
                    page.locator('button[data-action="export"]').click()
                assert download_info.value.suggested_filename == "digital-wellbeing-activity.csv"
                page.screenshot(path=str(output / "settings.png"), full_page=True)

                page.set_viewport_size({"width": 390, "height": 844})
                page.locator('.nav-item[data-page="overview"]').click()
                page.screenshot(path=str(output / "overview-mobile.png"), full_page=True)
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.locator('.nav-item[data-page="settings"]').click()

                page.on("dialog", lambda dialog: dialog.accept("DELETE"))
                page.locator('button[data-action="delete-history"]').click()
                page.get_by_text("Activity history deleted").wait_for()
                assert store.day_report(datetime.now().astimezone().date().isoformat())["total_seconds"] == 0
                assert not errors, errors
                browser.close()
        finally:
            server.stop()
            service.close()
            store.close()
    print("UI smoke passed; screenshots written to artifacts/")


if __name__ == "__main__":
    main()
