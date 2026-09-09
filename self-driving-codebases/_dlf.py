import urllib.request,ssl
from PIL import Image
import io
ctx=ssl.create_default_context()
proxy=urllib.request.ProxyHandler({'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'})
op=urllib.request.build_opener(proxy)
op.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/149.0 Safari/537.36')]
B='https://ptht05hbb1ssoooe.public.blob.vercel-storage.com/assets/blog/'
figs=['autonomy-diagram-1-3','autonomy-diagram-2-3','autonomy-diagram-3-3','autonomy-diagram-4-3']
for i,n in enumerate(figs,1):
    try:
        d=op.open(B+n+'.png',timeout=40).read()
        open(f'fig{i:02d}.png','wb').write(d)
        im=Image.open(io.BytesIO(d)); print(n, len(d), im.size)
    except Exception as e:
        print('FAIL',n,repr(e)[:120])
try:
    d=op.open('https://ptht05hbb1ssoooe.public.blob.vercel-storage.com/assets/blog/og/blog-self-driving-codebases-og-r2.png',timeout=40).read()
    open('hero_src.png','wb').write(d)
    im=Image.open(io.BytesIO(d)); print('og',len(d),im.size)
except Exception as e:
    print('og FAIL',repr(e)[:120])
