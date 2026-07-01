from PIL import Image, ImageDraw, ImageFont
import os

def create_cover(width, height, output_path, is_square=False):
    img = Image.new('RGB', (width, height), color='#0a0a0f')
    draw = ImageDraw.Draw(img)

    # Try to find a good font
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
    ]
    font_large = None
    font_medium = None
    font_small = None
    for fp in font_paths:
        if os.path.exists(fp):
            font_large = ImageFont.truetype(fp, 72 if not is_square else 56)
            font_medium = ImageFont.truetype(fp, 36 if not is_square else 28)
            font_small = ImageFont.truetype(fp, 24 if not is_square else 18)
            break
    if font_large is None:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw subtle grid pattern
    grid_color = (20, 20, 40)
    for x in range(0, width, 40):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 40):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # Draw accent lines
    accent_color = (0, 200, 150)
    draw.rectangle([0, 0, width, 4], fill=accent_color)
    draw.rectangle([0, height-4, width, height], fill=accent_color)

    # Glow circle
    cx, cy = width//2, height//2 - 20 if not is_square else height//2 - 40
    for r in range(180, 60, -10):
        alpha = int(255 * (1 - r/180))
        color = (0, 180, 140, alpha)
        draw.ellipse([cx-r, cy-r, cx+r, cy+r], outline=(0, int(180*(1-r/180)), int(140*(1-r/180))), width=1)

    # Main title
    title = "Vercel eve"
    bbox = draw.textbbox((0, 0), title, font=font_large)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((width - tw)//2, cy - th - 10), title, fill='#ffffff', font=font_large)

    # Subtitle
    subtitle = "开源 Agent 框架"
    bbox = draw.textbbox((0, 0), subtitle, font=font_medium)
    tw = bbox[2] - bbox[0]
    draw.text(((width - tw)//2, cy + 20), subtitle, fill='#00cc99', font=font_medium)

    if not is_square:
        # Tagline
        tagline = "Like Next.js, for agents."
        bbox = draw.textbbox((0, 0), tagline, font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw)//2, cy + 70), tagline, fill='#888899', font=font_small)

        # Bottom label
        label = "AI圈的9527"
        bbox = draw.textbbox((0, 0), label, font=font_small)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw)//2, height - 50), label, fill='#555566', font=font_small)

    # Decorative dots
    dot_positions = [(50, 50), (width-50, 50), (50, height-50), (width-50, height-50)]
    for dx, dy in dot_positions:
        draw.ellipse([dx-3, dy-3, dx+3, dy+3], fill=accent_color)

    img.save(output_path, quality=95)
    print(f"Saved {output_path} ({width}x{height})")

base = 'D:/06_Hermes/articles/vercel-eve'
create_cover(900, 383, os.path.join(base, 'cover.png'), is_square=False)
create_cover(500, 500, os.path.join(base, 'cover-square.png'), is_square=True)
