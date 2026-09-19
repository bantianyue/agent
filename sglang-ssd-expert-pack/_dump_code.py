import json

bs = [json.loads(l) for l in open('blocks.jsonl', encoding='utf-8')]
out = []
for i, b in enumerate(bs):
    if b.get('type') == 'code':
        out.append(f"===== block {i} =====")
        out.append(b.get('content') or '')
open('_code_dump.txt', 'w', encoding='utf-8').write("\n".join(out))
print('ok')
