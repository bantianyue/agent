import urllib.request,ssl
ctx=ssl.create_default_context()
proxy=urllib.request.ProxyHandler({'http':'http://127.0.0.1:7890','https':'http://127.0.0.1:7890'})
op=urllib.request.build_opener(proxy)
op.addheaders=[('User-Agent','Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/149.0 Safari/537.36')]
manifest=[l.strip().split('|') for l in open('_dl.txt',encoding='utf-8') if l.strip()]
ok=0
for row in manifest:
    fig=int(row[0]); url=row[2]
    try:
        d=op.open(url,timeout=40).read()
        ext='.png' if d[:8]==b'\x89PNG\r\n\x1a\n' else '.jpg'
        open(f'fig{fig:02d}{ext}','wb').write(d)
        from PIL import Image
        im=Image.open(f'fig{fig:02d}{ext}'); im.load()
        print('fig%02d'%fig, ext, len(d), im.size)
        ok+=1
    except Exception as e:
        print('FAIL fig%02d'%fig, repr(e)[:120])
try:
    cov='https://pbs.twimg.com/media/HRtYQG5bcAAeXDW.jpg'
    d=op.open(cov,timeout=40).read()
    ext='.png' if d[:8]==b'\x89PNG\r\n\x1a\n' else '.jpg'
    open('hero_src'+ext,'wb').write(d)
    print('cover',ext,len(d))
except Exception as e:
    print('cover FAIL',repr(e)[:120])
print('done ok=',ok,'/14')
