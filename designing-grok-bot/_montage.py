# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os
os.makedirs('_a', exist_ok=True)
rows1 = [('line', ['line-1','line-2','line-3']),
         ('mix', ['mix-1','mix-2','mix-3']),
         ('new3d', ['new3d-1','new3d-2','new3d-3']),
         ('s32', ['s32-1','s32-2','s32-3'])]
rows2 = [('base', ['base-1','base-2','base-3']),
         ('blob', ['blob-1','blob-2','blob-3']),
         ('emoji', ['emoji-1','emoji-2','emoji-3']),
         ('initials', ['initials-1','initials-2','initials-3'])]
cell, pad, lab = 260, 14, 40
def font(sz):
    for c in ['C:/Windows/Fonts/msyh.ttc','C:/Windows/Fonts/arial.ttf']:
        if os.path.exists(c): return ImageFont.truetype(c, sz)
def sheet(rows, out):
    nrows=len(rows); ncol=len(rows[0][1])
    W=ncol*(cell+pad)+pad; H=nrows*(cell+lab+pad)+pad
    im=Image.new('RGB',(W,H),(250,250,250)); d=ImageDraw.Draw(im)
    for ri,(name,names) in enumerate(rows):
        y=pad+ri*(cell+lab+pad)
        d.text((pad+8, y+18), {False:'',True:''}.get(False,''), font=font(20), fill=(120,120,120))
        # family label at left? put above first for readability small gray at row top-left
        d.text((pad+6, y), name, font=font(20), fill=(90,90,90))
        for ci,n in enumerate(names):
            x=pad+ci*(cell+pad)
            img=Image.open(f"_a/{n}.png").convert('RGBA')
            iw,ih=img.size
            sc=min((cell)/iw,(cell)/ih); nw,nh=int(iw*sc),int(ih*sc)
            img=img.resize((nw,nh))
            # center in tile
            tx=x+(cell-nw)//2; ty=y+lab+(cell-nh)//2
            # paste on white then -> im (handle alpha)
            tile=Image.new('RGBA',(cell,cell),(250,250,250,255))
            tile.paste(img,(tx-(x), ty-(y+lab)) if False else ((cell-nw)//2,(cell-nh)//2), img)
            tile=tile.convert('RGB')
            im.paste(tile,(x,y+lab))
    im.save(out, quality=92, optimize=True)
    print(out, im.size, os.path.getsize(out))
sheet(rows1,'fig01.png'); sheet(rows2,'fig02.png')
# wallpaper time-of-day trio (uniform height)
wp=[('wallpaper-light-noon','noon'),('wallpaper-gray','gray'),('wallpaper-dark-night','night')]
th=430; arts=[]
for name,label in wp:
    a=Image.open(f"_a/{name}.png").convert('RGB')
    sc=th/a.height; a=a.resize((int(a.width*sc),th))
    arts.append((a,label))
gap=12
W=sum(a.width for a,l in arts)+gap*len(arts)+gap
H=th+46
im=Image.new('RGB',(W,H),(18,19,34)); d=ImageDraw.Draw(im)
x=gap
for a,label in arts:
    d.rectangle([x,14,x+a.width-1,th+14],outline=(70,72,90)); 
    im.paste(a,(x,14))
    d.text((x+8, th+18), label, font=font(20), fill=(170,172,190))
    x+=a.width+gap
im.save('fig03.png',quality=92,optimize=True); print('fig03',im.size,os.path.getsize('fig03.png'))
