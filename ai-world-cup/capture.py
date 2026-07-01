"""Capture p5.js AI World Cup animation and render to MP4"""
import asyncio
import os
import subprocess
from playwright.async_api import async_playwright

OUTPUT_DIR = r"D:\06_Hermes\articles\ai-world-cup"
HTML_PATH = os.path.join(OUTPUT_DIR, "sketch.html")
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
OUTPUT_VIDEO = os.path.join(OUTPUT_DIR, "ai-world-cup.mp4")
FPS = 30
TOTAL_FRAMES = 900  # 30 seconds

async def capture_frames():
    os.makedirs(FRAMES_DIR, exist_ok=True)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            channel="chrome",
            headless=True,
            args=[
                '--no-sandbox',
                '--disable-gpu',
                '--disable-software-rasterizer',
                '--use-gl=angle',
                '--use-angle=swiftshader',
            ]
        )
        
        page = await browser.new_page(
            viewport={"width": 1080, "height": 1080},
            device_scale_factor=1
        )
        
        await page.goto(f"file://{HTML_PATH}", wait_until="networkidle")
        
        # Wait for p5 to initialize
        await page.wait_for_function("window._p5Ready === true", timeout=15000)
        await asyncio.sleep(1)
        
        print("Starting frame capture...")
        
        for i in range(TOTAL_FRAMES):
            # Advance one frame
            await page.evaluate("redraw()")
            
            # Screenshot
            await page.screenshot(
                path=os.path.join(FRAMES_DIR, f"frame_{i:04d}.png"),
                full_page=False
            )
            
            if i % 60 == 0:
                print(f"  Captured frame {i}/{TOTAL_FRAMES} ({i//FPS}s)")
        
        await browser.close()
    
    print(f"All {TOTAL_FRAMES} frames captured.")

def render_video():
    """Convert frames to MP4 using ffmpeg"""
    cmd = [
        "ffmpeg", "-y",
        "-framerate", str(FPS),
        "-i", os.path.join(FRAMES_DIR, "frame_%04d.png"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        "-vf", "scale=1080:1080:flags=lanczos",
        OUTPUT_VIDEO
    ]
    print("Rendering video...")
    subprocess.run(cmd, check=True)
    print(f"Video saved to: {OUTPUT_VIDEO}")

if __name__ == "__main__":
    asyncio.run(capture_frames())
    render_video()
