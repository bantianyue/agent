import json, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
blocks = [json.loads(l) for l in open(d + '/blocks.jsonl', encoding='utf-8') if l.strip()]
out = io.open('D:/06_Hermes/articles/_blocks_dump2.txt', 'w', encoding='utf-8')
out.write('KEYS: ' + json.dumps(list(blocks[0].keys()), ensure_ascii=False) + '\n')
for i, b in enumerate(blocks):
    txt = ''
    for k in ('text', 'content', 'html', 'value'):
        if b.get(k):
            txt = str(b[k])
            break
    txt = txt.replace('\n', ' ')
    out.write('[%d] type=%s img=%s len=%d :: %s\n' % (i, b.get('type'), (b.get('img') or '')[-40:], len(txt), txt[:200]))
out.close()
print('ok')
