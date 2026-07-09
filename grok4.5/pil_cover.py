import os
from PIL import Image, ImageDraw, ImageFont
os.chdir("D:/06_Hermes/articles/grok4.5")

img=Image.open("gemini_cover.png").convert("RGB")
img=img.resize((900,383), Image.LANCZOS)
# darken top and bottom for text legibility
from PIL import ImageEnhance
ov=Image.new("RGB",(900,383),(0,0,0))
top=Image.new("L",(900,128),180)
bot=Image.new("L",(900,71),200)
mask=Image.new("L",(900,383),0)
mask.paste(top,(0,0))
mask.paste(bot,(0,312))
img=Image.composite(img, Image.blend(img,ov,0.55), mask)

d=ImageDraw.Draw(img)
fb=os.path.abspath("msyhbd0.ttf")
f_title=ImageFont.truetype(fb,48)
f_sub=ImageFont.truetype(fb,30)
f_bot=ImageFont.truetype(fb,23)

d.text((24,18),"Grok 4.5",font=f_title,fill=(255,255,255))
d.text((26,80),"马斯克的翻身仗",font=f_sub,fill=(255,200,50))
d.text((24,342),"Opus 4.8 的性能   ×   中国开源模型的价格",font=f_bot,fill=(160,180,200))
img.save("cover.png")
img.resize((500,500),Image.LANCZOS).save("cover-square.png")
print("OK", Image.open("cover.png").size, Image.open("cover-square.png").size)
