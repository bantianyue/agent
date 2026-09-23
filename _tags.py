import re, io
raw = open('D:/06_Hermes/articles/_src_raw.html', encoding='utf-8').read()
i = raw.find('<article')
j = raw.find('</article>')
art = raw[i:j] if i >= 0 else raw
out = io.open('D:/06_Hermes/articles/_art_tags.txt', 'w', encoding='utf-8')
out.write('article len %d\n' % len(art))
for t in ['ul', 'ol', 'li', 'strong', 'b>', 'em>', 'code', 'pre', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'p>', 'img', 'a ']:
    out.write('%s : %d\n' % (t, len(re.findall(r'<' + t, art))))
# print first 3000 chars of article region around lists
for m in re.finditer(r'<(ul|ol)[^>]*>', art):
    s = max(0, m.start() - 200)
    out.write('\n---LIST at %d---\n' % m.start() + art[s:m.start() + 600].replace('\n', ' ') + '\n')
for m in re.finditer(r'<(strong|b|em)[^>]*>(.*?)</\1>', art, re.S):
    out.write('BOLD: ' + re.sub(r'<[^>]+>', '', m.group(2))[:80] + '\n')
out.close()
print('ok')
