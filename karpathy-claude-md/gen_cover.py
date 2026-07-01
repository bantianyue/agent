from PIL import Image, ImageDraw, ImageFont
import os

OUT_DIR = "D:/06_Hermes/articles/karpathy-claude-md"

# Try to find a monospace font
font_paths = [
    "C:/Windows/Fonts/consola.ttf",   # Consolas
    "C:/Windows/Fonts/cour.ttf",      # Courier New
    "C:/Windows/Fonts/DejaVuSansMono.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
]

font_path = None
for fp in font_paths:
    if os.path.exists(fp):
        font_path = fp
        break

def draw_cover(size, filename):
    W, H = size
    img = Image.new("RGB", (W, H), (13, 17, 23))  # Very dark blue-black
    draw = ImageDraw.Draw(img)

    # Load fonts
    try:
        if font_path:
            title_font = ImageFont.truetype(font_path, int(H * 0.10))
            subtitle_font = ImageFont.truetype(font_path, int(H * 0.045))
            rule_font = ImageFont.truetype(font_path, int(H * 0.035))
            tiny_font = ImageFont.truetype(font_path, int(H * 0.028))
        else:
            title_font = ImageFont.load_default()
            subtitle_font = ImageFont.load_default()
            rule_font = ImageFont.load_default()
            tiny_font = ImageFont.load_default()
    except:
        title_font = ImageFont.load_default()
        subtitle_font = ImageFont.load_default()
        rule_font = ImageFont.load_default()
        tiny_font = ImageFont.load_default()

    # Accent colors
    GREEN = (80, 227, 140)
    BLUE = (100, 180, 255)
    GRAY = (120, 130, 145)
    DIM = (60, 70, 85)
    WHITE = (220, 225, 235)

    # --- Terminal-style header bar ---
    bar_y = int(H * 0.06)
    draw.rectangle([0, 0, W, bar_y], fill=(30, 35, 45))
    # Red/yellow/green dots
    dot_r = int(H * 0.012)
    for i, c in enumerate([(255, 95, 87), (255, 189, 46), (39, 201, 63)]):
        cx = int(W * 0.02) + i * int(H * 0.04)
        draw.ellipse([cx - dot_r, bar_y//2 - dot_r, cx + dot_r, bar_y//2 + dot_r], fill=c)
    # Header text
    draw.text((int(W * 0.14), int(H * 0.015)), "CLAUDE.md — context engineering", fill=GRAY, font=tiny_font)

    # --- Title ---
    title = "CLAUDE.md"
    tw = draw.textlength(title, font=title_font)
    tx = (W - tw) / 2
    ty = int(H * 0.18)
    draw.text((tx, ty), title, fill=GREEN, font=title_font)

    # Subtitle
    sub = "Karpathy's 12 Rules"
    sw = draw.textlength(sub, font=subtitle_font)
    sx = (W - sw) / 2
    sy = int(H * 0.32)
    draw.text((sx, sy), sub, fill=BLUE, font=subtitle_font)

    # --- Divider line ---
    line_y = int(H * 0.42)
    draw.line([(int(W * 0.1), line_y), (int(W * 0.9), line_y)], fill=DIM, width=2)

    # --- Stats line ---
    stats = "41%  ->  11%  ->  3%  error rate"
    stw = draw.textlength(stats, font=rule_font)
    stx = (W - stw) / 2
    sty = int(H * 0.47)
    draw.text((stx, sty), stats, fill=WHITE, font=rule_font)

    # --- Rule list (first 6 shown) ---
    rules = [
        "01  Think before coding",
        "02  Simplicity first",
        "03  Surgical changes",
        "04  Goal-driven execution",
        "05  Judgment calls only",
        "06  Token budgets are hard",
    ]
    start_y = int(H * 0.56)
    for i, r in enumerate(rules):
        ry = start_y + i * int(H * 0.055)
        rw = draw.textlength(r, font=tiny_font)
        rx = (W - rw) / 2
        draw.text((rx, ry), r, fill=GRAY, font=tiny_font)

    # --- Bottom bar ---
    bottom_y = int(H * 0.92)
    draw.rectangle([0, bottom_y, W, H], fill=(30, 35, 45))
    footer = "Context Engineering  |  AI\u5708\u76849527"
    fw = draw.textlength(footer, font=tiny_font)
    fx = (W - fw) / 2
    fy = bottom_y + int(H * 0.015)
    draw.text((fx, fy), footer, fill=DIM, font=tiny_font)

    img.save(os.path.join(OUT_DIR, filename))
    print(f"Saved {filename} ({W}x{H})")

draw_cover((900, 383), "cover.png")
draw_cover((500, 500), "cover-square.png")
print("Done!")
