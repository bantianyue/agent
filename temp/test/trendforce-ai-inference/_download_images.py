#!/usr/bin/env python3
"""Download images in document order. First hero->cover.png, others->figNN.jpg/png.
Robust: derives extension from magic bytes + Content-Type, retries, never overwrites."""
import urllib.request, os, json, time
here = os.path.dirname(os.path.abspath(__file__))
blocks = []
with open(os.path.join(here, 'blocks.jsonl'), encoding='utf-8') as fh:
    for line in fh:
        line = line.strip()
        if line:
            try: blocks.append(json.loads(line))
            except Exception: pass
figs = [b for b in blocks if b.get('type') == 'figure']
hero_seen = False
n = 0
for b in figs:
    src = b['img']
    if b.get('hero') and not hero_seen:
        fname = 'cover.png'   # only the FIRST hero becomes the cover
        hero_seen = True
    else:
        n += 1
        fname = f'fig{n:02d}.jpg'
    # avoid clobbering an existing different file
    base, ext = os.path.splitext(fname)
    cand = fname
    k = 1
    while os.path.exists(os.path.join(here, cand)):
        cand = f'{base}_{k}{ext}'
        k += 1
    ok = False
    for attempt in range(3):
        try:
            req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            # magic bytes: real type beats Content-Type
            real_ext = None
            if data[:3] == b'ÿØÿ': real_ext = '.jpg'
            elif data[:4] == b'PNG': real_ext = '.png'
            elif data[:4] in (b'GIF8',): real_ext = '.gif'
            if real_ext:
                cand = os.path.splitext(cand)[0] + real_ext
            else:
                ct = (r.headers.get('Content-Type', '') or '').lower()
                if 'svg' in ct: cand = os.path.splitext(cand)[0] + '.svg'
                elif ('jpg' in ct or 'jpeg' in ct) and not cand.endswith('.svg'): cand = os.path.splitext(cand)[0] + '.jpg'
                elif 'png' in ct and not cand.endswith('.svg'): cand = os.path.splitext(cand)[0] + '.png'
            with open(os.path.join(here, cand), 'wb') as ff: ff.write(data)
            print(f'  OK {cand} ({len(data)//1024}KB)')
            ok = True
            break
        except Exception as e:
            if attempt < 2: time.sleep(1.5 * (attempt + 1)); continue
            print(f'  FAIL {cand}: {e}')
    if not ok:
        print(f'  SKIP {src[:80]}')
