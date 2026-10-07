"""Capture screenshots of the 4 visual style directions from style_preview.html using Playwright."""

from pathlib import Path
from playwright.sync_api import sync_playwright

def main():
    root = Path(__file__).resolve().parent.parent
    html_path = (root / "artifacts" / "style_preview.html").resolve()
    output_dir = root / "artifacts"
    output_dir.mkdir(exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 950}, device_scale_factor=1)
        page.goto(html_path.as_uri(), wait_until="networkidle")

        styles = [
            ("minimal", "style_1_minimal"),
            ("apple", "style_2_apple"),
            ("material", "style_3_material"),
            ("compact", "style_4_compact")
        ]

        for style_key, file_prefix in styles:
            # Dark mode
            page.evaluate(f"setStyle('{style_key}')")
            page.evaluate("document.documentElement.setAttribute('data-theme', 'dark')")
            page.wait_for_timeout(200)
            page.screenshot(path=str(output_dir / f"{file_prefix}_dark.png"), full_page=False)

            # Light mode
            page.evaluate("document.documentElement.setAttribute('data-theme', 'light')")
            page.wait_for_timeout(200)
            page.screenshot(path=str(output_dir / f"{file_prefix}_light.png"), full_page=False)

        browser.close()
    print("Successfully captured screenshots for all 4 design styles!")

if __name__ == "__main__":
    main()
