import json, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
data = json.load(open(d + '/article_data.json', encoding='utf-8'))
out = io.open('D:/06_Hermes/articles/_chk_json_out.txt', 'w', encoding='utf-8')
tot = 0
for i, s in enumerate(data['sections']):
    paras = s.get('paras', [])
    tot += len(paras)
    fa = s.get('fig_after', {})
    out.write('[%d] %s %s paras=%d fig_after=%s\n' % (i, s['type'], s['title'], len(paras), fa))
    for k in fa:
        if int(k) >= len(paras):
            out.write('   !! 越界 key=%s\n' % k)
out.write('total paras=%d\n' % tot)
s = json.dumps(data, ensure_ascii=False)
import re
out.write('cjk=%d en=%d\n' % (len(re.findall(r'[\u4e00-\u9fff]', s)), len(re.findall(r'[A-Za-z]', s))))
out.write('dash=%d\n' % s.count('——'))
out.write('at=%s\n' % re.findall(r'@\w+', s))
out.close()
print('ok')
