import re, io
d = 'D:/06_Hermes/articles/vllm-hardware-agnostic-models'
h = open(d + '/article.html', encoding='utf-8').read()
out = io.open('D:/06_Hermes/articles/_chk_html_out.txt', 'w', encoding='utf-8')
out.write('img=%d pre=%d h2=%d h3=%d strong=%d code_span=%d\n' % (
    len(re.findall(r'<img', h)), len(re.findall(r'<pre', h)),
    len(re.findall(r'<h2', h)), len(re.findall(r'<h3', h)),
    len(re.findall(r'<strong', h)), len(re.findall(r'<code ', h))))
out.write('figrefs=%s\n' % re.findall(r'src="(fig\d+\.png)"', h))
# adjacent images without text between
toks = re.findall(r'<img[^>]*>|<p[^>]*>', h)
bad = 0
for i in range(len(toks) - 1):
    if toks[i].startswith('<img') and toks[i + 1].startswith('<img'):
        bad += 1
out.write('adjacent_img_no_text=%d\n' % bad)
out.write('div=%d section=%d\n' % (len(re.findall(r'<div', h)), len(re.findall(r'<section', h))))
out.write('单星号=%d\n' % len(re.findall(r'(?<!\*)\*([^*\n<]+)\*(?!\*)', h)))
out.close()
print('ok')
