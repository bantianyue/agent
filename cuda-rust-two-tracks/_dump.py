import json, io, sys
p = 'D:/06_Hermes/articles/cuda-rust-two-tracks/blocks.jsonl'
out = []
for i, l in enumerate(open(p, encoding='utf-8')):
    b = json.loads(l)
    if b['type'] == 'figure':
        out.append('--- [%d] FIGURE %s | caption=%s | after_para=%s' % (i, b.get('img'), b.get('caption'), b.get('after_para')))
        continue
    c = b.get('content') or ''
    out.append('[%d] %s' % (i, c))
io.open('D:/06_Hermes/articles/cuda-rust-two-tracks/_blocks_dump.txt', 'w', encoding='utf-8').write('\n'.join(out))
print('lines', len(out))
