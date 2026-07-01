#!/usr/bin/env python3
"""Render SVGs as PNG using PIL - both are dark-themed diagrams with text and rectangles."""

from PIL import Image, ImageDraw, ImageFont
import os

FONT_DIR = "C:/Windows/Fonts"
FONT_BOLD = ImageFont.truetype(f"{FONT_DIR}/segoeuib.ttf", 13)
FONT_NORM = ImageFont.truetype(f"{FONT_DIR}/segoeui.ttf", 12)
FONT_SM = ImageFont.truetype(f"{FONT_DIR}/segoeui.ttf", 11)

def rounded_rect(draw, xy, radius, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)

def draw_svg1(path):
    """The token cost of a conversation"""
    W, H = 960, 500
    img = Image.new('RGB', (W, H), (3, 7, 16))
    d = ImageDraw.Draw(img)
    sx = lambda v: int(v)
    
    # Title
    d.text((sx(480), sx(34)), "The token cost of a conversation", fill=(200, 221, 240), font=FONT_NORM, anchor="mm")
    
    # Helper: draw a box with label
    def box(x, y, w, h, fill_c, stroke_c, label, label_c=(200,221,240), badge=None):
        rounded_rect(d, [x,y,x+w,y+h], 10, fill=fill_c, outline=stroke_c)
        if badge:
            d.text((x+12, y+22), badge, fill=label_c, font=FONT_SM)
        d.text((x+w//2, y+h//2), label, fill=label_c, font=FONT_NORM, anchor="mm")
    
    def row(x, y, w, h, text, c=(200,221,240)):
        rounded_rect(d, [x,y,x+w,y+h], 6, fill=(22,31,51))
        d.text((x+w//2, y+h//2), text, fill=c, font=FONT_NORM, anchor="mm")
    
    def label(x, y, text, c=(107,130,153)):
        d.text((x, y), text, fill=c, font=FONT_SM, anchor="mm")
    
    # LEFT BOX - Turn 1
    box(sx(28), sx(50), sx(268), sx(278), (11,17,32), (26,39,64), "", badge="5,200 tokens")
    row(sx(40), sx(82), sx(244), sx(48), "System Prompt")
    row(sx(40), sx(142), sx(244), sx(48), "Tools")
    row(sx(40), sx(202), sx(244), sx(48), "Skills")
    d.text((sx(162), sx(277)), "...", fill=(107,130,153), font=FONT_NORM, anchor="mm")
    label(sx(162), sx(345), "+ 3 tokens")
    row(sx(40), sx(358), sx(244), sx(38), "Good morning!", c=(127,200,255))
    
    # RIGHT BOX - Turn 2
    box(sx(372), sx(50), sx(268), sx(324), (11,17,32), (26,39,64), "", badge="5,203 tokens")
    row(sx(384), sx(82), sx(244), sx(48), "System Prompt")
    row(sx(384), sx(142), sx(244), sx(48), "Tools")
    row(sx(384), sx(202), sx(244), sx(48), "Skills")
    d.text((sx(506), sx(277)), "...", fill=(107,130,153), font=FONT_NORM, anchor="mm")
    row(sx(384), sx(290), sx(244), sx(38), "Good morning!", c=(107,130,153))
    label(sx(506), sx(391), "+ 3 tokens")
    row(sx(384), sx(404), sx(244), sx(38), "What's the weather?", c=(127,200,255))
    
    # Arrow
    d.line([(sx(302), sx(212)), (sx(366), sx(212))], fill=(127,200,255), width=2)
    d.polygon([(sx(366), sx(207)), (sx(378), sx(212)), (sx(366), sx(217))], fill=(127,200,255))
    
    # Billing panel
    rounded_rect(d, [sx(700), sx(168), sx(934), sx(212)], 9, fill=(11,17,32))
    d.text((sx(817), sx(190)), "10,403 tokens", fill=(200,221,240), font=FONT_NORM, anchor="mm")
    
    rounded_rect(d, [sx(700), sx(224), sx(934), sx(262)], 9, fill=(17,35,56), outline=(42,90,128))
    d.text((sx(817), sx(243)), "6 tokens", fill=(127,200,255), font=FONT_NORM, anchor="mm")
    
    d.text((sx(817), sx(282)), "Billed at 100% cost", fill=(200,221,240), font=FONT_SM, anchor="mm")
    
    # Connectors
    d.line([(sx(646), sx(190)), (sx(694), sx(190))], fill=(26,39,64), width=1)
    d.line([(sx(646), sx(243)), (sx(694), sx(243))], fill=(42,90,128), width=1)
    
    img.save(path, quality=95)
    print(f"Saved {path}: {os.path.getsize(path)} bytes")

def draw_svg2(path):
    """The token cost of a conversation with prompt caching"""
    W, H = 960, 530
    img = Image.new('RGB', (W, H), (3, 7, 16))
    d = ImageDraw.Draw(img)
    sx = lambda v: int(v)
    
    d.text((sx(480), sx(34)), "The token cost of a conversation with prompt caching", fill=(200, 221, 240), font=FONT_NORM, anchor="mm")
    
    def row(x, y, w, h, text, c=(200,221,240), bg=(22,31,51)):
        rounded_rect(d, [x,y,x+w,y+h], 6, fill=bg)
        d.text((x+w//2, y+h//2), text, fill=c, font=FONT_NORM, anchor="mm")
    
    def label(x, y, text, c=(107,130,153)):
        d.text((x, y), text, fill=c, font=FONT_SM, anchor="mm")
    
    # LEFT BOX - Turn 1 (no cache)
    rounded_rect(d, [sx(28), sx(50), sx(296), sx(328)], 10, fill=(11,17,32), outline=(26,39,64))
    d.text((sx(40), sx(72)), "5,200 tokens", fill=(200,221,240), font=FONT_SM)
    row(sx(40), sx(82), sx(244), sx(48), "System Prompt")
    row(sx(40), sx(142), sx(244), sx(48), "Tools")
    row(sx(40), sx(202), sx(244), sx(48), "Skills")
    d.text((sx(162), sx(277)), "...", fill=(107,130,153), font=FONT_NORM, anchor="mm")
    label(sx(162), sx(345), "+ 3 tokens")
    row(sx(40), sx(358), sx(244), sx(38), "Good morning!", c=(127,200,255))
    
    # RIGHT BOX - Turn 2 (cached)
    rounded_rect(d, [sx(372), sx(50), sx(640), sx(382)], 10, fill=(11,17,32), outline=(26,39,64))
    # Cached badge
    rounded_rect(d, [sx(384), sx(58), sx(540), sx(80)], 5, fill=(14,30,10), outline=(26,64,40))
    d.text((sx(462), sx(73)), "5,203 tokens cached", fill=(227,255,143), font=FONT_SM, anchor="mm")
    
    # Cached rows
    row(sx(384), sx(86), sx(244), sx(48), "System Prompt\nCACHED", bg=(11,26,16))
    d.text((sx(506), sx(124)), "CACHED", fill=(74,128,96), font=ImageFont.truetype(f"{FONT_DIR}/segoeuib.ttf", 9), anchor="mm")
    
    row(sx(384), sx(146), sx(244), sx(48), "Tools\nCACHED", bg=(11,26,16))
    d.text((sx(506), sx(184)), "CACHED", fill=(74,128,96), font=ImageFont.truetype(f"{FONT_DIR}/segoeuib.ttf", 9), anchor="mm")
    
    row(sx(384), sx(206), sx(244), sx(48), "Skills\nCACHED", bg=(11,26,16))
    d.text((sx(506), sx(244)), "CACHED", fill=(74,128,96), font=ImageFont.truetype(f"{FONT_DIR}/segoeuib.ttf", 9), anchor="mm")
    
    d.text((sx(506), sx(277)), "...", fill=(107,130,153), font=FONT_NORM, anchor="mm")
    row(sx(384), sx(286), sx(244), sx(38), "Good morning!", bg=(11,26,16), c=(160,200,168))
    
    label(sx(506), sx(399), "+ 3 tokens")
    row(sx(384), sx(412), sx(244), sx(38), "What's the weather?", c=(127,200,255))
    
    # Snapshot label
    d.line([(sx(302), sx(216)), (sx(366), sx(216))], fill=(127,200,255), width=2)
    d.text((sx(334), sx(208)), "Snapshot", fill=(127,200,255), font=ImageFont.truetype(f"{FONT_DIR}/segoeuib.ttf", 10), anchor="mm")
    
    # Billing panel
    rounded_rect(d, [sx(700), sx(108), sx(934), sx(156)], 9, fill=(11,17,32))
    d.text((sx(817), sx(128)), "5,200 tokens", fill=(200,221,240), font=FONT_NORM, anchor="mm")
    d.text((sx(817), sx(146)), "Billed at 100% cost", fill=(107,130,153), font=FONT_SM, anchor="mm")
    
    rounded_rect(d, [sx(700), sx(216), sx(934), sx(254)], 9, fill=(17,35,56), outline=(42,90,128))
    d.text((sx(817), sx(235)), "6 tokens", fill=(127,200,255), font=FONT_NORM, anchor="mm")
    
    rounded_rect(d, [sx(700), sx(316), sx(934), sx(364)], 9, fill=(14,30,10), outline=(26,64,40))
    d.text((sx(817), sx(336)), "5,203 tokens", fill=(227,255,143), font=FONT_NORM, anchor="mm")
    d.text((sx(817), sx(354)), "Billed at 10% cost", fill=(107,130,153), font=FONT_SM, anchor="mm")
    
    d.line([(sx(646), sx(132)), (sx(694), sx(132))], fill=(26,39,64), width=1)
    d.line([(sx(646), sx(235)), (sx(694), sx(235))], fill=(42,90,128), width=1)
    d.line([(sx(646), sx(340)), (sx(694), sx(340))], fill=(26,64,40), width=1)
    
    img.save(path, quality=95)
    print(f"Saved {path}: {os.path.getsize(path)} bytes")

draw_svg1("D:/06_Hermes/articles/deep-agents-prompt-caching/img1.png")
draw_svg2("D:/06_Hermes/articles/deep-agents-prompt-caching/img2.png")
print("Done!")
