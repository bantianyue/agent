import io, os, urllib.request
from PIL import Image

OUT = 'D:/06_Hermes/articles/cuda-rust-two-tracks'
cands = [
    'https://developer-blogs.nvidia.com/wp-content/uploads/2026/09/image1-1.png',
    'https://developer-blogs.nvidia.com/wp-content/uploads/2026/09/image1-1.webp',
    'https://developer-blogs.nvidia.com/wp-content/uploads/2026/09/image1-1-1536x864.png',
    'https://developer-blogs.nvidia.com/wp-content/uploads/2026/09/image1-1-1024x576.png',
]
UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36'
os.environ.setdefault('HTTP_PROXY', 'http://127.0.0.1:7890')
os.environ.setdefault('HTTPS_PROXY', 'http://127.0.0.1:7890')
opener = urllib.request.build_opener(urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'}))

best = None
for u in cands:
    try:
        req = urllib.request.Request(u, headers={'User-Agent': UA, 'Referer': 'https://developer.nvidia.com/'})
        data = opener.open(req, timeout=60).read()
        tmp = os.path.join(OUT, '_tmp_img')
        open(tmp, 'wb').write(data)
        im = Image.open(tmp)
        print('OK', u, len(data), im.size, im.mode, im.format)
        if best is None or im.size[0] * im.size[1] > best[0]:
            best = (im.size[0] * im.size[1], u, data)
    except Exception as e:
        print('FAIL', u, type(e).__name__, e)

if best:
    tmp = os.path.join(OUT, '_tmp_img')
    open(tmp, 'wb').write(best[2])
    im = Image.open(tmp)
    if im.mode in ('RGBA', 'LA', 'P'):
        im = im.convert('RGBA')
        bg = Image.new('RGB', im.size, (255, 255, 255))
        bg.paste(im, mask=im.split()[-1])
        im = bg
    else:
        im = im.convert('RGB')
    im.save(os.path.join(OUT, 'fig01.png'))
    im.save(os.path.join(OUT, 'cover_source.png'))
    print('SAVED fig01.png from', best[1], im.size)
    os.remove(tmp)
