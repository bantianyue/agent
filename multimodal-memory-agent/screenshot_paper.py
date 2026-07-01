"""Screenshot paper header from arxiv HTML — hide sidebar for clean capture."""
import sys, os
sys.path.insert(0, r"C:\Users\twfehh7\AppData\Local\hermes\hermes-agent\venv\Lib\site-packages")

from playwright.sync_api import sync_playwright

URL = "https://arxiv.org/html/2602.07624v1"
OUTPUT = r"D:\06_Hermes\articles\multimodal-memory-agent\paper_header.png"

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome", headless=False)
    page = browser.new_page(viewport={"width": 1280, "height": 1600})
    page.goto(URL, wait_until="networkidle", timeout=30000)
    page.wait_for_timeout(3000)

    # Hide the sidebar nav
    page.evaluate("""
        const nav = document.querySelector('.ltx_page_navbar');
        if (nav) nav.style.display = 'none';
        // Also hide the TOC
        const toc = document.querySelector('.ltx_TOC');
        if (toc) toc.style.display = 'none';
    """)
    page.wait_for_timeout(500)

    # Get title position
    title_el = page.query_selector("h1.ltx_title_document")
    if title_el:
        title_el.scroll_into_view_if_needed()
        page.wait_for_timeout(500)
        box = title_el.bounding_box()
        print(f"Title box: {box}")

        # Capture from just above title to ~1000px down (title + authors + abstract + affiliations)
        y_start = max(0, box["y"] - 30)
        page.screenshot(
            path=OUTPUT,
            clip={"x": 0, "y": y_start, "width": 1280, "height": 1100},
            full_page=False
        )
        print(f"Captured from y={y_start}, height=1100")
    else:
        page.screenshot(
            path=OUTPUT,
            clip={"x": 0, "y": 180, "width": 1280, "height": 1100},
            full_page=False
        )

    print(f"Saved to {OUTPUT}")
    browser.close()
