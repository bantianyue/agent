import re, io
h = io.open('D:/06_Hermes/articles/cuda-rust-two-tracks/_page.html', encoding='utf-8').read()
m = re.search(r'<div[^>]*class="[^"]*entry-content[^"]*"', h)
s = m.start() if m else 0
e = h.find('About the Author', s)
e = e if e > 0 else len(h)
body = h[s:e]
print('--- imgs inside entry-content ---')
for u in dict.fromkeys(re.findall(r'<img[^>]+src="([^"]+)"', body)):
    print(u)
print('--- all developer-blogs urls on page (dedup) ---')
for u in dict.fromkeys(re.findall(r'(https://developer-blogs\.nvidia\.com/[^"\' )]+)', h)):
    print(u)
