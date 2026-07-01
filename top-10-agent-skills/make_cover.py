from PIL import Image, ImageDraw, ImageFont
import os

W, H = 900, 383

DARK_BG = (18, 20, 24)
WHITE = (255, 255, 255)
LIGHT_GRAY = (180, 184, 193)
MID_GRAY = (120, 124, 133)
ACCENT = (255, 200, 50)  # gold accent
BLUE = (80, 160, 255)

img = Image.new('RGB', (W, H), DARK_BG)
draw = ImageDraw.Draw(img)

font_dirs = ['C:/Windows/Fonts', 'C:/Users/twfehh7/AppData/Local/Microsoft/Windows/Fonts']
def find_font(name):
    for d in font_dirs:
        p = os.path.join(d, name)
        if os.path.exists(p): return p
    return None

title_font = None
body_font = None
code_font = None

for f in [find_font('CascadiaCode-Bold.ttf'), find_font('consolab.ttf'), find_font('segoeuib.ttf')]:
    if f: title_font = ImageFont.truetype(f, 38); break
if not title_font: title_font = ImageFont.load_default()

for f in [find_font('CascadiaCode-Regular.ttf'), find_font('segoeui.ttf')]:
    if f: body_font = ImageFont.truetype(f, 18); break
if not body_font: body_font = ImageFont.load_default()

for f in [find_font('CascadiaCode-Regular.ttf'), find_font('consola.ttf')]:
    if f: code_font = ImageFont.truetype(f, 14); break
if not code_font: code_font = body_font

# Accent bar at top - gradient
for i in range(W):
    r = int(50 + (i/W) * 180)
    g = int(120 + (i/W) * 60)
    b = int(200 - (i/W) * 100)
    draw.rectangle([i, 0, i+1, 5], fill=(r, g, b))

# Big number "TOP 10" on the left
draw.text((30, 50), "TOP 10", fill=BLUE, font=ImageFont.truetype(find_font('CascadiaCode-Bold.ttf') or find_font('segoeuib.ttf'), 72))

# Star icon area
draw.text((30, 125), "⭐ 228,740 ★", fill=ACCENT, font=body_font)

# GitHub-style repo list on the right
repos = [
    ("obra/superpowers", "116K ★"),
    ("everything-claude-code", "102K ★"),
    ("anthropics/skills", "45K ★"),
    ("antigravity-skills", "27K ★"),
    ("awesome-agent-skills", "25K ★"),
]

repo_x = 400
repo_y = 45
for i, (name, stars) in enumerate(repos):
    y = repo_y + i * 38
    # Folder icon
    draw.text((repo_x, y), "📁", fill=LIGHT_GRAY, font=code_font)
    draw.text((repo_x + 22, y), name, fill=WHITE, font=code_font)
    draw.text((repo_x + 22, y + 18), stars, fill=ACCENT, font=code_font)

# Bottom title area
draw.text((30, 290), "Agent Skills 的 GitHub 星榜", fill=WHITE, font=title_font)
draw.text((30, 335), "小而精的工作流正在胜出 · 228,740 颗星的总信号", fill=LIGHT_GRAY, font=body_font)
draw.text((30, 358), "Bilgin Ibryam · June 15, 2026", fill=MID_GRAY, font=body_font)

out_path = 'D:/06_Hermes/articles/top-10-agent-skills/cover.png'
os.makedirs(os.path.dirname(out_path), exist_ok=True)
img.save(out_path)
print(f'Cover saved: {out_path}')

# Square cover
W2, H2 = 500, 500
img2 = Image.new('RGB', (W2, H2), DARK_BG)
draw2 = ImageDraw.Draw(img2)

draw2.text((30, 60), "TOP 10", fill=BLUE, font=ImageFont.truetype(find_font('CascadiaCode-Bold.ttf') or find_font('segoeuib.ttf'), 56))
draw2.text((30, 130), "Agent Skills", fill=WHITE, font=title_font)
draw2.text((30, 175), "by GitHub Stars", fill=LIGHT_GRAY, font=body_font)
draw2.text((30, 220), "⭐ 228,740 ★", fill=ACCENT, font=body_font)

repos2 = [
    "obra/superpowers",
    "everything-claude-code",
    "anthropics/skills",
    "antigravity-skills",
    "awesome-agent-skills",
]
for i, r in enumerate(repos2):
    draw2.text((30, 280 + i * 32), f"📁 {r}", fill=LIGHT_GRAY, font=code_font)

draw2.text((30, 450), "Bilgin Ibryam · Jun 15", fill=MID_GRAY, font=body_font)

out_path2 = 'D:/06_Hermes/articles/top-10-agent-skills/cover-square.png'
img2.save(out_path2)
print(f'Square cover saved: {out_path2}')
