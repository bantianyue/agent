import json

bs = [json.loads(l) for l in open('blocks.jsonl', encoding='utf-8')]
out = []
for i, b in enumerate(bs):
    c = b.get('content') or ''
    if isinstance(c, list):
        c = json.dumps(c, ensure_ascii=False)
    out.append(f"{i}\t{b.get('type')}\t{b.get('img') or ''}\t{len(c)}\t{c[:120]}".replace("\n", " / "))
open('_blocks_dump.txt', 'w', encoding='utf-8').write("\n".join(out))
print('written', len(bs))
