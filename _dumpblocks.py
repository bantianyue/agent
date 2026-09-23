import json, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
blocks = [json.loads(l) for l in open(d + '/blocks.jsonl', encoding='utf-8') if l.strip()]
out = io.open('D:/06_Hermes/articles/_blocks_dump.txt', 'w', encoding='utf-8')
for i, b in enumerate(blocks):
    t = b.get('type')
    txt = (b.get('text') or '').replace('\n', ' ')
    img = b.get('img') or ''
    cap = b.get('caption') or ''
    out.write('[%d] type=%s img=%s cap=%s len=%d\n    %s\n' % (i, t, img, cap, len(txt), txt[:160]))
out.close()
print('blocks', len(blocks))
