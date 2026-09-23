import re, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
h = open(d + '/article.html', encoding='utf-8').read()
out = io.open('D:/06_Hermes/articles/_style_out.txt', 'w', encoding='utf-8')
out.write('pre=%d p_re=%d\n' % (len(re.findall(r'<pre', h)), len(re.findall(r'<p re', h))))
for w in ['我们', '我', '它']:
    hits = [m.start() for m in re.finditer(w, h)]
    out.write('%s : %d\n' % (w, len(hits)))
    for s in hits[:20]:
        out.write('   ...' + h[max(0, s - 60):s + 60].replace('\n', ' ') + '\n')
out.close()
print('ok')
