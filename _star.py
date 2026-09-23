import re, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
h = open(d + '/article.html', encoding='utf-8').read()
out = io.open('D:/06_Hermes/articles/_star_out.txt', 'w', encoding='utf-8')
for m in re.finditer(r'(?<!\*)\*([^*\n<]+)\*(?!\*)', h):
    s = max(0, m.start() - 80)
    out.write('HIT: ...' + h[s:m.end() + 80].replace('\n', ' ') + '\n')
out.close()
print('ok')
