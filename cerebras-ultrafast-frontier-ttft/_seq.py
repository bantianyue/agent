# -*- coding: utf-8 -*-
import re
h = open('article_data_dump_for_check.html', encoding='utf-8').read() if False else open('article.html', encoding='utf-8').read()
# tokenize sequentially: paragraphs blocks and images (block-level order via figure/.. wrapper)
seq = []
# figure wrapper contains the <figure> including caption and image; but our figs may be <figure> elements.
# simpler: find all block-ish tags at top narrative flow and order by pos.
pos = []
for m in re.finditer(r'<h2[^>]*>(.*?)</h2>', h, re.S):
    pos.append((m.start(), 'H2', re.sub(r'<[^>]+>', '', m.group(1)).strip()[:14]))
for m in re.finditer(r'<h3[^>]*>(.*?)</h3>', h, re.S):
    pos.append((m.start(), 'H3', re.sub(r'<[^>]+>', '', m.group(1)).strip()[:14]))
for m in re.finditer(r'<p[^>]*>(.*?)</p>', h, re.S):
    txt = re.sub(r'<[^>]+>', '', m.group(1)).strip()
    pos.append((m.start(), 'P', 'len=' + str(len(txt)) + ' ' + txt[:12]))
for m in re.finditer(r'<img[^>]*src="([^"]+)"', h):
    pos.append((m.start(), 'IMG', m.group(1)))
pos.sort()
for _, kind, label in pos:
    if kind == 'H2':
        print('\n## ' + label)
    elif kind == 'P':
        print('   [text ' + label + ']')
    elif kind == 'IMG':
        print('   >>>IMG ' + label)
