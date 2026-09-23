import json, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
blocks = [json.loads(l) for l in open(d + '/blocks.jsonl', encoding='utf-8') if l.strip()]
out = io.open(d + '/_core_full.txt', 'w', encoding='utf-8')
for i in range(0, 54):
    b = blocks[i]
    out.write('=== [%d] %s\n%s\n\n' % (i, b.get('type'), b.get('content', '')))
out.close()
print('ok')
