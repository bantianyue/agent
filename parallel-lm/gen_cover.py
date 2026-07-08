from PIL import Image
img = Image.open('main_figure.png').convert('RGB')
w,h = img.size
print("src", w, h, "ratio", round(w/h,2))
c = img.resize((900,383), Image.LANCZOS); c.save('cover.png')
c2 = img.resize((500,500), Image.LANCZOS); c2.save('cover-square.png')
print("cover done")
