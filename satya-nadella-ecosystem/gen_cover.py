from PIL import Image, ImageDraw, ImageFont
import os

def create_gradient(w, h, colors):
    """Create a vertical gradient image."""
    img = Image.new('RGB', (w, h))
    draw = ImageDraw.Draw(img)
    n = len(colors) - 1
    for y in range(h):
        ratio = y / (h - 1) if h > 1 else 0
        idx = ratio * n
        i = int(idx)
        t = idx - i
        if i >= n:
            i = n - 1
            t = 1
        r = int(colors[i][0] * (1 - t) + colors[i + 1][0] * t)
        g = int(colors[i][1] * (1 - t) + colors[i + 1][1] * t)
        b = int(colors[i][2] * (1 - t) + colors[i + 1][2] * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    return img

def find_font(size):
    """Find a suitable bold font."""
    candidates = [
        "C:/Windows/Fonts/msyhbd.ttc",   # Microsoft YaHei Bold
        "C:/Windows/Fonts/msyh.ttc",      # Microsoft YaHei
        "C:/Windows/Fonts/simhei.ttf",    # SimHei
        "C:/Windows/Fonts/arialbd.ttf",   # Arial Bold
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()

def wrap_text(text, font, max_width, draw):
    """Wrap text to fit within max_width."""
    words = list(text)
    lines = []
    current_line = ""
    for ch in text:
        test_line = current_line + ch
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w > max_width and current_line:
            lines.append(current_line)
            current_line = ch
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return lines

def make_cover(w, h, title, subtitle, output_path):
    """Generate a cover image with gradient background and text."""
    # Dark blue gradient: top to bottom
    colors = [(10, 15, 40), (20, 30, 70), (15, 25, 60), (5, 10, 30)]
    img = create_gradient(w, h, colors)
    draw = ImageDraw.Draw(img)

    # Font sizes
    title_size = max(int(w / 22), 28)
    subtitle_size = max(int(w / 38), 16)

    font_title = find_font(title_size)
    font_sub = find_font(subtitle_size)

    # Draw title - centered, with word wrap
    margin = int(w * 0.08)
    max_text_w = w - margin * 2
    lines = wrap_text(title, font_title, max_text_w, draw)

    total_h = len(lines) * (title_size + 8)
    start_y = (h - total_h) // 2 - 20

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font_title)
        tw = bbox[2] - bbox[0]
        x = (w - tw) // 2
        y = start_y + i * (title_size + 8)
        # Draw text with shadow for readability
        draw.text((x + 1, y + 1), line, fill=(0, 0, 0, 180), font=font_title)
        draw.text((x, y), line, fill=(220, 230, 255), font=font_title)

    # Draw subtitle
    bbox2 = draw.textbbox((0, 0), subtitle, font=font_sub)
    sw = bbox2[2] - bbox2[0]
    sx = (w - sw) // 2
    sy = start_y + total_h + 20
    draw.text((sx + 1, sy + 1), subtitle, fill=(0, 0, 0, 150), font=font_sub)
    draw.text((sx, sy), subtitle, fill=(160, 180, 220), font=font_sub)

    # Draw a subtle line above subtitle
    line_y = sy - 10
    line_w = int(w * 0.3)
    draw.line([(w // 2 - line_w // 2, line_y), (w // 2 + line_w // 2, line_y)],
              fill=(100, 130, 180), width=2)

    img.save(output_path, quality=95)
    print(f"Saved: {output_path} ({w}x{h})")

base_dir = "D:/06_Hermes/articles/satya-nadella-ecosystem"

# cover.png (900x383) - WeChat article banner
make_cover(
    w=900, h=383,
    title="没有生态系统的前沿\n是不稳定的",
    subtitle="Satya Nadella 谈AI时代的资本与生态",
    output_path=os.path.join(base_dir, "cover.png")
)

# cover-square.png (500x500) - square variant
make_cover(
    w=500, h=500,
    title="没有生态系统的前沿\n是不稳定的",
    subtitle="Satya Nadella",
    output_path=os.path.join(base_dir, "cover-square.png")
)
