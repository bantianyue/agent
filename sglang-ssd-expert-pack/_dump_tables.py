import re

h = open(r'C:\Users\twfehh7\AppData\Local\Temp\sglang_probe.html', encoding='utf-8', errors='replace').read()
tables = re.findall(r'<table.*?</table>', h, re.S | re.I)
print('tables:', len(tables))
for i, t in enumerate(tables):
    print('===== TABLE', i, '=====')
    txt = re.sub(r'<t[dh][^>]*>', ' | ', t)
    txt = re.sub(r'</tr>', '\n', txt)
    txt = re.sub(r'<[^>]+>', '', txt)
    txt = re.sub(r'\n\s*\n+', '\n', txt)
    print(txt.strip()[:2500])
    # also find context/before
