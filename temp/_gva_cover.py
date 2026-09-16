# -*- coding: utf-8 -*-
import os
from PIL import Image, ImageDraw, ImageFont
DIR=r"D:/06_Hermes/articles/gva-grouped-value-attention"
def findfont(cands):
    for c in cands:
        if os.path.exists(c): return c
    return cands[0]
def vfont(size,bold=False):
    if bold:
        for c in [r"C:/Windows/Fonts/msyhbd.ttc",r"C:/Windows/Fonts/msyh.ttc",r"C:/Windows/Fonts/simhei.ttf"]:
            if os.path.exists(c): return ImageFont.truetype(c,size)
    else:
        for c in [r"C:/Windows/Fonts/msyh.ttc",r"C:/Windows/Fonts/msyhbd.ttc",r"C:/Windows/Fonts/simhei.ttf"]:
            if os.path.exists(c): return ImageFont.truetype(c,size)
    raise FileNotFoundError('no CJK font')
def wrap(dr,txt,font,wmax):
    lines=[]; cur=''
    for ch in txt:
        if dr.textlength(cur+ch,font=font)<=wmax: cur+=ch
        else: lines.append(cur); cur=ch
    if cur: lines.append(cur)
    return lines
def make(W,H,path):
    im=Image.new('RGB',(W,H)); dr=ImageDraw.Draw(im)
    for y in range(H):
        tt=y/H
        col=(int(10+(18-10)*tt),int(22+(46-22)*tt),int(48+(92-48)*tt))
        dr.line([(0,y),(W,y)],fill=col)
    # side accent
    dr.rectangle([0,0,10,H],fill=(64,190,255))
    tag=vfont(int(H*0.115),True)
    dr.text((W*0.055,H*0.10),'视频缓存 / Attention 架构',font=tag,fill=(164,214,255))
    title_font=vfont(int(H*0.16),True)
    tw=W*0.90
    lines=wrap(dr,'只缓存 value、在线重建 key 的 GVA',title_font,int(tw))
    y=H*0.30
    for ln in lines:
        dr.text((W*0.055,y),ln,font=title_font,fill=(255,255,255)); y+=H*0.18
    sub=vfont(int(H*0.10),False)
    dr.text((W*0.055,y+6),'Grouped Value Attention · KV 节省~45-47%',font=sub,fill=(200,222,246))
    dr.line([(int(W*0.055),H-int(H*0.13)),(int(W*0.72),H-int(H*0.13))],fill=(64,190,255),width=3)
make(900,383,os.path.join(DIR,'cover.png'))
make(500,500,os.path.join(DIR,'cover-square.png'))
print('covers done')
from PIL import Image as I
print('cover',I.open(os.path.join(DIR,'cover.png')).size,'sq',I.open(os.path.join(DIR,'cover-square.png')).size)
