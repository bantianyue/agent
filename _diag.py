# -*- coding: utf-8 -*-
import io
p = r'D:/06_Hermes/articles/_t.json'
b = open(p, 'rb').read()
out = []
out.append('size=%d' % len(b))
out.append('first160=%r' % b[:160])
import json
try:
    d = json.loads(b.decode('utf-8-sig'))
    t = d['tweet']
    art = t.get('article') or {}
    title = art.get('title')
    out.append('title_raw=%r' % title)
    out.append('title_repaired=%r' % title.encode('latin-1').decode('utf-8'))
except Exception as e:
    out.append('ERR %s' % e)
io.open(r'D:/06_Hermes/articles/_diag.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('ok')
