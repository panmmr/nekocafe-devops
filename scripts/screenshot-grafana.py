#!/usr/bin/env python3
"""
Grafana Dashboard 自动截图脚本
使用前请确保：
  1. docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
  2. pip install playwright && playwright install chromium
  3. Grafana 已配置好数据源（可通过 http://localhost:3000 访问）

运行：
  python scripts/screenshot-grafana.py
  python scripts/screenshot-grafana.py --username admin --password admin --url http://localhost:3000
"""
import argparse
import os
import sys
import time

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs", "screenshots")


def wait_for_grafana(url: str, timeout: int = 60):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{url}/api/health", timeout=2)
            return True
        except Exception:
            print(f"Waiting for Grafana at {url}...")
            time.sleep(3)
    return False


def screenshot_dashboard(url: str, username: str, password: str, dashboard_uid: str = "nekocafe-overview"):
    from playwright.sync_api import sync_playwright

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if not wait_for_grafana(url):
        print("ERROR: Grafana not reachable. Start it with: docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d")
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,  # retina quality
        )
        page = context.new_page()

        # Step 1: Login
        print("[1/4] Logging into Grafana...")
        page.goto(f"{url}/login", wait_until="networkidle")
        page.fill('input[name="user"]', username)
        page.fill('input[name="password"]', password)
        page.click('button[type="submit"]')
        page.wait_for_url(f"{url}/**", timeout=10000)
        page.wait_for_timeout(2000)

        # Save login state for future runs
        context.storage_state(path=os.path.join(OUTPUT_DIR, "grafana-auth.json"))
        print(f"  Login state saved to {OUTPUT_DIR}/grafana-auth.json")

        # Step 2: Navigate to dashboard
        print("[2/4] Navigating to NekoCafé dashboard...")
        dash_url = f"{url}/d/{dashboard_uid}"
        page.goto(dash_url, wait_until="networkidle")
        # Set time range to last 15 minutes
        page.goto(f"{dash_url}?from=now-15m&to=now&refresh=5s", wait_until="networkidle")
        page.wait_for_timeout(5000)  # wait for panels to render

        # Step 3: Full dashboard screenshot
        print("[3/4] Taking full dashboard screenshot...")
        page.screenshot(path=os.path.join(OUTPUT_DIR, "grafana-dashboard-full.png"), full_page=True)
        print(f"  Full dashboard → {OUTPUT_DIR}/grafana-dashboard-full.png")

        # Step 4: Individual panel screenshots
        print("[4/4] Capturing individual panels...")
        panels = page.query_selector_all('[data-viz-panel-key]')
        if not panels:
            panels = page.query_selector_all('.panel-container')

        panel_names = ["QPS", "P99-Latency", "ErrorRate", "ResourceUsage"]
        for i, panel in enumerate(panels[:4]):
            panel.screenshot(path=os.path.join(OUTPUT_DIR, f"grafana-panel-{i+1}-{panel_names[i]}.png"))
            print(f"  Panel {i+1} ({panel_names[i]}) → {OUTPUT_DIR}/grafana-panel-{i+1}-{panel_names[i]}.png")

        browser.close()

    print(f"\nDone! {len(panels[:4])} panel screenshots + 1 full dashboard saved to {OUTPUT_DIR}/")
    return True


def screenshot_with_saved_auth(url: str, dashboard_uid: str = "nekocafe-overview"):
    """Try to reuse saved auth state to avoid login"""
    from playwright.sync_api import sync_playwright

    auth_file = os.path.join(OUTPUT_DIR, "grafana-auth.json")
    if not os.path.exists(auth_file):
        print("No saved auth state found. Run with --username and --password first.")
        return False

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=2,
            storage_state=auth_file,
        )
        page = context.new_page()

        dash_url = f"{url}/d/{dashboard_uid}?from=now-15m&to=now&refresh=5s"
        page.goto(dash_url, wait_until="networkidle")
        page.wait_for_timeout(5000)

        # Check if redirected to login
        if "login" in page.url:
            print("Auth state expired. Run with --username and --password to re-login.")
            browser.close()
            return False

        page.screenshot(path=os.path.join(OUTPUT_DIR, "grafana-dashboard-full.png"), full_page=True)
        print(f"Full dashboard → {OUTPUT_DIR}/grafana-dashboard-full.png")

        panels = page.query_selector_all('.panel-container, [data-viz-panel-key]')
        panel_names = ["QPS", "P99-Latency", "ErrorRate", "ResourceUsage"]
        for i, panel in enumerate(panels[:4]):
            panel.screenshot(path=os.path.join(OUTPUT_DIR, f"grafana-panel-{i+1}-{panel_names[i]}.png"))
            print(f"Panel {i+1} → {OUTPUT_DIR}/grafana-panel-{i+1}-{panel_names[i]}.png")

        browser.close()
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grafana Dashboard Screenshot Tool")
    parser.add_argument("--url", default="http://localhost:3000", help="Grafana URL")
    parser.add_argument("--username", default=None, help="Grafana username")
    parser.add_argument("--password", default=None, help="Grafana password")
    parser.add_argument("--dashboard", default="nekocafe-overview", help="Dashboard UID")
    args = parser.parse_args()

    if args.username and args.password:
        screenshot_dashboard(args.url, args.username, args.password, args.dashboard)
    else:
        print("Trying saved auth state...")
        if not screenshot_with_saved_auth(args.url, args.dashboard):
            print("\nUsage for first run:")
            print(f"  python {__file__} --username admin --password admin")
