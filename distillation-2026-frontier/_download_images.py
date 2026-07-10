import urllib.request, os, sys

PROXY = 'http://127.0.0.1:7890'
proxy_handler = urllib.request.ProxyHandler({'http': PROXY, 'https': PROXY})
opener = urllib.request.build_opener(proxy_handler)

urls = {
    'img1.jpg': 'https://pbs.twimg.com/media/HMpBZjsXoAEv14y?format=jpg&name=900x900',
    'img2.jpg': 'https://pbs.twimg.com/media/HMsc-r6WEAA8NiN?format=jpg&name=900x900',
    'img3.jpg': 'https://pbs.twimg.com/media/HMsdC6tXIAA_57X?format=jpg&name=900x900',
    'img4.jpg': 'https://pbs.twimg.com/media/HMsdGJtWgAAM6_G?format=jpg&name=900x900',
}

hdr = {'User-Agent': 'Mozilla/5.0'}
for fname, url in urls.items():
    try:
        req = urllib.request.Request(url, headers=hdr)
        with opener.open(req, timeout=60) as r:
            data = r.read()
        with open(fname, 'wb') as f:
            f.write(data)
        print(f'OK {fname} ({len(data)//1024}KB)')
    except Exception as e:
        print(f'FAIL {fname}: {e}', file=sys.stderr)
