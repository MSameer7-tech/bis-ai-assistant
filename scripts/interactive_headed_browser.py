"""
Interactive Headed Browser Tour Agent for Official BIS Portals.
Launches a visible Google Chrome window on the user's screen (headless=False),
navigates through BIS portals, interacts with menus, highlights elements,
scrolls through tables and document lists with human-paced visual pauses.
"""
import logging
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("InteractiveBrowserTour")

SNAPSHOTS_DIR = Path("data/browser_snapshots/interactive_tour")
SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def highlight_element(page, selector, text=""):
    """Adds a visual pulse highlight to an element for visual demonstration."""
    try:
        page.evaluate("""(sel) => {
            const el = document.querySelector(sel);
            if (el) {
                el.style.outline = '4px solid #ff4757';
                el.style.backgroundColor = 'rgba(255, 71, 87, 0.15)';
                el.style.transition = 'all 0.5s ease';
                el.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }""", selector)
        if text:
            print(f"    👉 [Interacting] {text}")
        time.sleep(2)
    except Exception as e:
        logger.debug(f"Highlight skipped: {e}")


def run_interactive_tour():
    print("\n" + "=" * 120)
    print("                LAUNCHING VISIBLE GOOGLE CHROME BROWSER ON YOUR SCREEN")
    print("=" * 120)
    print("[*] Starting Playwright with visible Google Chrome window (headless=False)...")

    with sync_playwright() as p:
        browser = p.chromium.launch(
            channel="chrome",
            headless=False,
            args=[
                "--start-maximized",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            ),
            locale="en-US"
        )
        page = context.new_page()

        def take_snap(path_str):
            try:
                page.screenshot(path=path_str, timeout=6000)
            except Exception as e:
                logger.debug(f"Snapshot non-fatal timeout: {e}")

        # -------------------------------------------------------------
        # Step 1: LIMS Recognized Testing Laboratories Directory
        # -------------------------------------------------------------
        print("\n[STEP 1] Navigating to BIS LIMS Testing Laboratories Portal...")
        page.goto("https://lims.bis.gov.in/home/labs/", wait_until="domcontentloaded", timeout=40000)
        time.sleep(2)
        print(f"  ✓ URL: {page.url} | Title: {page.title()}")

        highlight_element(page, "table", "Highlighting LIMS Testing Laboratories Directory Table")
        take_snap(str(SNAPSHOTS_DIR / "01_lims_labs_table.png"))

        # Scroll down through the table rows
        print("    👉 [Scrolling] Inspecting laboratory entries...")
        for i in range(1, 4):
            page.evaluate(f"window.scrollBy(0, {i * 200});")
            time.sleep(1)

        # Highlight first View Scope link
        highlight_element(page, "table tbody tr:first-child a, table tbody tr:nth-child(2) a", "Inspecting 'View Scope' link for Laboratory 1")
        time.sleep(2)

        # -------------------------------------------------------------
        # Step 2: LIMS BIS-Owned Regional Laboratories
        # -------------------------------------------------------------
        print("\n[STEP 2] Navigating to BIS-Owned Regional Laboratories...")
        page.goto("https://lims.bis.gov.in/home/bis_labs/", wait_until="domcontentloaded", timeout=40000)
        time.sleep(2)
        print(f"  ✓ URL: {page.url} | Title: {page.title()}")

        highlight_element(page, "table", "Highlighting Regional & Central Laboratories (CL Sahibabad, BNBL Bengaluru)")
        take_snap(str(SNAPSHOTS_DIR / "02_lims_bis_regional_labs.png"))
        time.sleep(2)

        # -------------------------------------------------------------
        # Step 3: Product Certification Portal
        # -------------------------------------------------------------
        print("\n[STEP 3] Navigating to BIS Product Certification Overview...")
        try:
            page.goto("https://www.bis.gov.in/product-certification/product-certification-overview/?lang=en", wait_until="domcontentloaded", timeout=40000)
        except Exception:
            page.goto("https://www.bis.gov.in/product-certification/product-certification-overview/?lang=hi", wait_until="commit", timeout=40000)

        time.sleep(3)
        print(f"  ✓ URL: {page.url} | Title: {page.title()}")

        # Scroll and inspect main content and menus
        print("    👉 [Scrolling] Inspecting certification schemes & procedure guidelines...")
        page.evaluate("window.scrollBy(0, 300);")
        time.sleep(2)
        take_snap(str(SNAPSHOTS_DIR / "03_product_certification.png"))

        # -------------------------------------------------------------
        # Step 4: Hallmarking Portal & HUID Overview
        # -------------------------------------------------------------
        print("\n[STEP 4] Navigating to BIS Hallmarking & HUID Overview...")
        try:
            page.goto("https://www.bis.gov.in/hallmarking-overview/?lang=en", wait_until="domcontentloaded", timeout=40000)
        except Exception:
            page.goto("https://www.bis.gov.in/hallmarking-overview/?lang=hi", wait_until="commit", timeout=40000)

        time.sleep(3)
        print(f"  ✓ URL: {page.url} | Title: {page.title()}")

        print("    👉 [Scrolling] Inspecting 6-Digit HUID regulations & mandatory district orders...")
        page.evaluate("window.scrollBy(0, 350);")
        time.sleep(2)
        take_snap(str(SNAPSHOTS_DIR / "04_hallmarking_overview.png"))

        # -------------------------------------------------------------
        # Step 5: The BIS Act, Rules & Statutory Regulations
        # -------------------------------------------------------------
        print("\n[STEP 5] Navigating to The BIS Act, Rules & Regulations...")
        try:
            page.goto("https://www.bis.gov.in/the-bis-act-rules-regulations/?lang=en", wait_until="commit", timeout=40000)
        except Exception:
            page.goto("https://www.bis.gov.in/?lang=hi", wait_until="commit", timeout=40000)

        time.sleep(3)
        print(f"  ✓ URL: {page.url} | Title: {page.title()}")

        print("    👉 [Scrolling] Inspecting statutory regulations and legal framework...")
        page.evaluate("window.scrollBy(0, 400);")
        time.sleep(2)
        take_snap(str(SNAPSHOTS_DIR / "05_bis_act_rules.png"))

        # -------------------------------------------------------------
        # Step 6: Consumer Affairs & BIS Care
        # -------------------------------------------------------------
        print("\n[STEP 6] Navigating to BIS Care & Consumer Overview...")
        try:
            page.goto("https://www.bis.gov.in/consumer-overview/?lang=en", wait_until="domcontentloaded", timeout=40000)
        except Exception:
            page.goto("https://www.bis.gov.in/consumer-overview/?lang=hi", wait_until="commit", timeout=40000)

        time.sleep(3)
        print(f"  ✓ URL: {page.url} | Title: {page.title()}")

        print("    👉 [Scrolling] Inspecting consumer protection guidelines and BIS Care verification...")
        page.evaluate("window.scrollBy(0, 300);")
        time.sleep(2)
        take_snap(str(SNAPSHOTS_DIR / "06_consumer_overview.png"))

        print("\n[+] Visual inspection complete! Keeping browser visible for 4 seconds before concluding...")
        time.sleep(4)
        browser.close()

    print("\n" + "=" * 120)
    print("                    INTERACTIVE VISUAL TOUR COMPLETED SUCCESSFULLY")
    print("=" * 120)
    print(f"  • Visual Tour Snapshots Saved To: {SNAPSHOTS_DIR}\n")


if __name__ == "__main__":
    run_interactive_tour()
