# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont
import os
os.makedirs('_a', exist_ok=True)
rows1 = [('line', ['line-1','line-3','line-5']),
         ('mix', ['mix-2','mix-4','mix-6']),
         ('new3d', ['new3d-1','new3d-3','new3d-5']),
         ('s32', ['s32-2','s32-4','s32-6'])]
rows2 = [('base', ['base-1','base-3','base-5']),
         ('blob', ['blob-2','blob-4','blob-6']),
         ('emoji', ['emoji-1','emoji-3','emoji-5']),
         ('initials', ['initials-1','initials-3','initials-5'])]
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
# wallpaper time-of-day trio (1 hscroll)
wp=[('wallpaper-light-noon','morning-light'),('wallpaper-gray','mid'),('wallpaper-dark-night','night')]
arts=[]
for name,label in wp:
    a=Image.open(f"_a/{name}.png").convert('RGB')
    w=max(int((840/len(wp))),1); sch=(420*w)/a.width   # keep its H via scale to each ~ width 300
    sc=300/a.width; a=a.resize((int(a.width*sc),int(a.height*sc)))
    arts.append(a)
h=arts[0].height+30; W=sum(x.width for x in arts)+ (len(arts)+1)*10
im=Image.new('RGB',(W,h),(15,16,34)); d=ImageDraw.Draw(im); x0=10
for a in arts:
    im.paste(a,(x0,10)); x0+=a.width+10
im.save('fig03.png',quality=90,optimize=True); print('fig03',im.size,os.path.getsize('fig03.png'))
