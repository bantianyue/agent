"""Extract charts from Cursor Developer Habits Report page using Playwright.
Each chart has a share button that opens a popup with the chart image.
"""
import os
import json
from playwright.sync_api import sync_playwright

OUTPUT_DIR = r"D:\06_Hermes\articles\cursor-developer-habits-report\charts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

urls = [
    "https://cursor.com/cn/insights#developer-acceleration",
]

all_charts = []

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--no-first-run", "--disable-gpu"]
    )
    context = browser.new_context(
        viewport={"width": 1280, "height": 900},
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    )
    page = context.new_page()
    
    # Navigate to page and wait for full load
    for url in urls:
        page.goto(url, wait_until="networkidle", timeout=60000)
        
        # Wait for page to fully render
        page.wait_for_timeout(3000)
    
    # Scroll to bottom to load all content
    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
    page.wait_for_timeout(2000)
    
    # Get all chart/share button info
    chart_info = page.evaluate("""() => {
        const buttons = document.querySelectorAll('button');
        const charts = [];
        buttons.forEach(btn => {
            if (btn.textContent.includes('Share')) {
                charts.push({
                    text: btn.textContent.trim(),
                    rect: btn.getBoundingClientRect()
                });
            }
        });
        return charts;
    }""")
    
    print(f"Found {len(chart_info)} share buttons:")
    for i, c in enumerate(chart_info):
        print(f"  {i}: {c['text']}")
    
    # Get all images with descriptive alt text
    images = page.evaluate("""() => {
        const imgs = document.querySelectorAll('img');
        return Array.from(imgs).filter(img => {
            const alt = img.alt;
            return alt && alt.length > 5 && alt !== 'Quadtree decomposition of a cube';
        }).map(img => ({
            alt: img.alt,
            src: img.src || img.getAttribute('src') || '',
            width: img.width,
            height: img.height
        }));
    }""")
    
    print(f"\nFound {len(images)} images with descriptive alt text:")
    for i, img in enumerate(images):
        print(f"  {i}: alt='{img['alt']}' src='{img['src'][:80]}...' ({img['width']}x{img['height']})")
    
    all_charts = chart_info
    
    # Save screenshot for manual verification
    screenshot_path = os.path.join(OUTPUT_DIR, "full_page.png")
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"\nFull page screenshot saved to: {screenshot_path}")
    
    # Try to get SVG data via canvas conversion
    svg_data = page.evaluate("""() => {
        const svgs = document.querySelectorAll('svg');
        const results = [];
        svgs.forEach((svg, idx) => {
            const w = svg.getAttribute('width');
            if (w && parseInt(w) > 100) {
                const parent = svg.closest('h3, article, section');
                let title = '';
                if (parent) {
                    const h = parent.querySelector('h3');
                    if (h) {
                        title = h.textContent.replace(/[\\d.]+\\.\\s*Link to this slide\\s*/g, '').trim();
                    }
                }
                results.push({
                    idx: idx,
                    width: w,
                    height: svg.getAttribute('height'),
                    title: title
                });
            }
        });
        return results;
    }""")
    
    print(f"\nFound {len(svg_data)} SVGs with width > 100px:")
    for s in svg_data:
        print(f"  SVG #{s['idx']}: {s['width']}x{s['height']} title='{s['title'][:60]}'")
    
    context.close()
    browser.close()

# Save chart metadata
meta_path = os.path.join(OUTPUT_DIR, "charts_metadata.json")
with open(meta_path, 'w', encoding='utf-8') as f:
    json.dump({
        "share_buttons": all_charts,
        "svg_data": svg_data
    }, f, ensure_ascii=False, indent=2)
print(f"\nMetadata saved to: {meta_path}")
