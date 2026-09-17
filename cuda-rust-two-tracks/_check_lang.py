import json, re, io
d = json.load(open('D:/06_Hermes/articles/cuda-rust-two-tracks/article_data.json', encoding='utf-8'))
prose = []
for sec in d['sections']:
    for p in sec['paras']:
        if p.startswith('__CODE__'):
            continue
        prose.append(p)
prose += d['lead'] + d['conclusion']
blob = '\n'.join(prose)
blob = re.sub(r'<[^>]+>', '', blob)
print('prose paras:', len(prose))
print('cjk:', len(re.findall(r'[\u4e00-\u9fa5]', blob)), 'latin:', len(re.findall(r'[A-Za-z]', blob)))
# any prose para that is mostly english?
for i, p in enumerate(prose):
    plain = re.sub(r'<[^>]+>', '', p)
    cj = len(re.findall(r'[\u4e00-\u9fa5]', plain))
    en = len(re.findall(r'[A-Za-z]', plain))
    if cj < en:
        print('SUSPECT', i, plain[:120])
