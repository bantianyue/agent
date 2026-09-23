import os, io, urllib.request
from PIL import Image
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
urls = {
    'fig01.png': 'https://pytorch.org/wp-content/uploads/2026/09/fig1-model-definitions-scaled.png',
    'fig02.png': 'https://pytorch.org/wp-content/uploads/2026/09/fig2-hw-agnostic-layers-scaled.png',
    'fig03.png': 'https://pytorch.org/wp-content/uploads/2026/09/fig3-h100-performance.png',
}
proxy = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
op = urllib.request.build_opener(proxy)
op.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)')]
log = io.open('D:/06_Hermes/articles/_prep_figs.txt', 'w', encoding='utf-8')
for fn, u in urls.items():
    p = os.path.join(d, fn)
    if not os.path.exists(p):
        data = op.open(u, timeout=120).read()
        open(p, 'wb').write(data)
        log.write('DL %s %d\n' % (fn, len(data)))
    im = Image.open(p)
    w, h = im.size
    log.write('%s orig %dx%d size=%dKB mode=%s\n' % (fn, w, h, os.path.getsize(p) // 1024, im.mode))
    if w > 1400 or os.path.getsize(p) > 900 * 1024:
        im2 = im.convert('RGB')
        nw = 1200
        im2 = im2.resize((nw, int(h * nw / w)), Image.LANCZOS)
        im2.save(p, quality=90, optimize=True)
        log.write('  -> resized %dx%d %dKB\n' % (im2.size[0], im2.size[1], os.path.getsize(p) // 1024))
    else:
        if im.mode in ('P', 'RGBA'):
            im.convert('RGB').save(p, quality=92, optimize=True)
            log.write('  -> rgb %dKB\n' % (os.path.getsize(p) // 1024))
# remove old names
for old in ['fig1-model-definitions-scaled.png', 'fig2-hw-agnostic-layers-scaled.png']:
    p = os.path.join(d, old)
    if os.path.exists(p):
        os.remove(p)
        log.write('removed %s\n' % old)
log.close()
print('ok')
