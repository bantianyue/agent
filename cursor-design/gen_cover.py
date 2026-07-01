from PIL import Image, ImageDraw, ImageFont
import os
import random

random.seed(42)

def create_gradient(draw, w, h, colors):
    """Draw vertical gradient"""
    for y in range(h):
        ratio = y / h
        r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
        g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
        b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

def draw_ui_elements(draw, w, h):
    """Draw abstract UI/design elements"""

    # Grid dots (design grid)
    for x in range(0, w, 30):
        for y in range(0, h, 30):
            draw.point((x, y), fill=(80, 90, 160))

    # Floating UI panels
    panels = [
        (40, 40, 280, 180),
        (w-320, 50, w-50, 200),
        (100, h-160, 400, h-40),
        (w-280, h-130, w-40, h-50),
    ]
    panel_colors = [(40, 55, 140), (55, 40, 150), (30, 85, 150), (70, 35, 130)]
    for (x1, y1, x2, y2), col in zip(panels, panel_colors):
        draw.rounded_rectangle([x1, y1, x2, y2], radius=12, fill=col, outline=(110, 90, 200), width=1)

    # Cursor-like arrow pointer
    cx, cy = w//2 + 60, h//2 - 20
    arrow_pts = [(cx, cy), (cx+30, cy+40), (cx+15, cy+38), (cx+10, cy+50), (cx+2, cy+38)]
    draw.polygon(arrow_pts, fill=(180, 160, 230))

    # Crosshair / selection circle
    draw.ellipse([w//2-80, h//2-80, w//2+80, h//2+80], outline=(100, 150, 230), width=2)
    draw.ellipse([w//2-5, h//2-5, w//2+5, h//2+5], fill=(100, 150, 230))

    # Small dots / nodes around
    for _ in range(30):
        rx = random.randint(0, w)
        ry = random.randint(0, h)
        r = random.randint(2, 5)
        draw.ellipse([rx-r, ry-r, rx+r, ry+r], fill=(120, 110, 200))

def make_cover(size, filename):
    w, h = size
    img = Image.new('RGB', (w, h), (10, 8, 30))
    draw = ImageDraw.Draw(img)

    # Dark gradient background
    create_gradient(draw, w, h, [(15, 10, 40), (25, 15, 60)])

    # Draw UI elements
    draw_ui_elements(draw, w, h)

    # Glow effect in center (semi-transparent overlay)
    overlay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    for r in range(100, 0, -5):
        alpha = max(0, min(30, 30 - (100 - r) // 4))
        overlay_draw.ellipse([w//2-r, h//2-r, w//2+r, h//2+r],
                     fill=(60, 40, 180, alpha))
    img = Image.alpha_composite(img.convert('RGBA'), overlay).convert('RGB')
    draw = ImageDraw.Draw(img)

    # Text
    try:
        font_title = ImageFont.truetype("C:/Windows/Fonts/msyhbd.ttc", 36)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 18)
    except:
        try:
            font_title = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 36)
            font_sub = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 18)
        except:
            font_title = ImageFont.load_default()
            font_sub = ImageFont.load_default()

    # Title
    title = "Cursor Design"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text(((w - tw) // 2, h//2 - 50), title, fill=(220, 210, 255), font=font_title)

    # Subtitle
    sub = "AI 设计工作室 · 开源"
    bbox2 = draw.textbbox((0, 0), sub, font=font_sub)
    sw = bbox2[2] - bbox2[0]
    draw.text(((w - sw) // 2, h//2 + 10), sub, fill=(160, 150, 220), font=font_sub)

    img.save(filename, quality=95)
    print(f"Saved {filename} ({w}x{h})")

out_dir = "D:/06_Hermes/articles/cursor-design"
make_cover((900, 383), os.path.join(out_dir, "cover.png"))
make_cover((500, 500), os.path.join(out_dir, "cover-square.png"))
print("Done!")
