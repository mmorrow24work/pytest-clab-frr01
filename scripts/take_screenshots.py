"""
Capture Grafana dashboards, pytest HTML report, and clab topology screenshots.
Saves PNG files to SCREENSHOTS/. Run with system python3 (playwright must be installed).
Usage: python3 scripts/take_screenshots.py
"""
import os
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

GRAFANA_URL = "http://localhost:5000"
PROJECT_DIR = Path(__file__).parent.parent
REPORT_FILE = str(PROJECT_DIR / "reports" / "report.html")
OUT_DIR = PROJECT_DIR / "SCREENSHOTS"

DASHBOARDS = [
    {
        "url": f"{GRAFANA_URL}/d/pytest-clab-frr01/pytest-clab-frr01-results?orgId=1&from=now-2h&to=now&kiosk",
        "file": "grafana_pytest_results.png",
        "wait_for": ".react-grid-item",
        "label": "pytest Results Dashboard",
    },
    {
        "url": f"{GRAFANA_URL}/d/clab-frr01-hosts/clab-frr01-e28094-zabbix-host-status?orgId=1&from=now-1h&to=now&kiosk",
        "file": "grafana_zabbix_hosts.png",
        "wait_for": ".react-grid-item",
        "label": "Zabbix Host Status Dashboard",
    },
]


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": 1600, "height": 900},
            ignore_https_errors=True,
        )

        for dash in DASHBOARDS:
            page = context.new_page()
            print(f"Capturing: {dash['label']} ...")
            page.goto(dash["url"], wait_until="networkidle", timeout=30000)
            try:
                page.wait_for_selector(dash["wait_for"], timeout=15000)
            except Exception:
                pass
            time.sleep(4)
            out = OUT_DIR / dash["file"]
            page.screenshot(path=str(out), full_page=False)
            print(f"  Saved: {out}")
            page.close()

        # pytest HTML report
        if Path(REPORT_FILE).exists():
            page = context.new_page()
            print("Capturing: pytest HTML report ...")
            page.goto(f"file://{REPORT_FILE}", wait_until="domcontentloaded", timeout=15000)
            time.sleep(1)
            out = OUT_DIR / "pytest_report.png"
            page.screenshot(path=str(out), full_page=False)
            print(f"  Saved: {out}")
            page.close()

        browser.close()

    print(f"\nAll screenshots saved to {OUT_DIR}")


if __name__ == "__main__":
    main()
