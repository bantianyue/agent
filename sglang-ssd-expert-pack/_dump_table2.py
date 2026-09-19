import json
import re
from html.parser import HTMLParser

h = open(r'C:\Users\twfehh7\AppData\Local\Temp\sglang_probe.html', encoding='utf-8', errors='replace').read()
tables = re.findall(r'<table.*?</table>', h, re.S | re.I)
t = tables[2]


class P(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.rows = []
        self.cur = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self.cur = []
        elif tag in ('td', 'th'):
            self.cell = []

    def handle_endtag(self, tag):
        if tag == 'tr' and self.cur is not None:
            self.rows.append(self.cur)
            self.cur = None
        elif tag in ('td', 'th') and self.cell is not None:
            self.cur.append(' '.join(''.join(self.cell).split()))
            self.cell = None

    def handle_data(self, d):
        if self.cell is not None:
            self.cell.append(d)


p = P()
p.feed(t)
out = json.dumps(p.rows, ensure_ascii=False, indent=1)
open('_table2.json', 'w', encoding='utf-8').write(out)
print(out)
