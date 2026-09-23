import re, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
h = open(d + '/article.html', encoding='utf-8').read()
out = io.open('D:/06_Hermes/articles/_pre_out.txt', 'w', encoding='utf-8')
for m in re.finditer(r'<pre[^>]*>.*?</pre>', h, re.S):
    out.write(m.group(0)[:900] + '\n\n')
out.write('--- numbered spans ---\n')
for m in re.finditer(r'<span style="color:#0F4C81;font-weight:bold;">\d+</span>', h):
    s = m.end()
    out.write(h[m.start():s + 60].replace('\n', ' ') + '\n')
out.close()
print('ok')
