# -*- coding: utf-8 -*-
import json, io
d = json.load(open(r'D:/06_Hermes/articles/_t.json', encoding='utf-8-sig'))
t = d.get('tweet', {})
art = t.get('article') or {}
lines = []
lines.append('TITLE: ' + str(art.get('title')))
lines.append('PREVIEW: ' + str(art.get('preview_text')))
c = art.get('content') or {}
em = c.get('entityMap') or {}
if isinstance(em, list):
    em = {str(i): v for i, v in enumerate(em)}
blocks = c.get('blocks') or []
lines.append('=== entityMap (%d) ===' % len(em))
for k in sorted(em.keys(), key=lambda x: int(x) if str(x).isdigit() else 0):
    e = em[k]
    lines.append('[%s] type=%s value=%s' % (k, e.get('type'), json.dumps(e.get('data'), ensure_ascii=False)))
lines.append('=== blocks (%d) ===' % len(blocks))
for i, b in enumerate(blocks):
    typ = b.get('type')
    txt = b.get('text', '')
    ers = b.get('entityRanges') or []
    isr = b.get('inlineStyleRanges') or []
    head = txt[:40].replace('\n', '\\n')
    lines.append('[%d] %-18s ents=%-30s styles=%-30s text=%s' % (
        i, typ, json.dumps([e.get('key') for e in ers]), json.dumps([s.get('style') for s in isr]), head))
with io.open(r'D:/06_Hermes/articles/_t_dump.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
with io.open(r'D:/06_Hermes/articles/_t_blocks_full.txt', 'w', encoding='utf-8') as f:
    for i, b in enumerate(blocks):
        f.write('--- [%d] type=%s\n' % (i, b.get('type')))
        f.write(b.get('text', '') + '\n')
print('ok')
