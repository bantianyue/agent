import sys
path = sys.argv[1]
t = open(path, 'r', encoding='utf-8').read()
import re

# Find all —— or — 
dashes = [(i, t[i]) for i, c in enumerate(t) if c == '\u2014']
print(f"Dashes found: {len(dashes)}")

# Replace with context-appropriate alternatives
# Strategy: —— is used in Chinese to separate clauses, replace with ：(explanation) or ，(parallel) or remove
reps = [
    ("事。**把", "事：**把"),
    ("框架——", "框架"),
    ("普及的。", "普及的。"),
    ("缺陷。**", "缺陷：**"),
    ("超配。", "超配。"),
    ("——今天", "。今天"),
    ("——几乎所有", "，几乎所有"),
    ("——在burst", "，在burst"),
    ("——导致", "，导致"),
]

for old, new in reps:
    t = t.replace(old, new)

# More precise dash replacements
# Show remaining dashes with context
lines = t.split('\n')
for i, line in enumerate(lines, 1):
    if '\u2014' in line:
        idx = line.find('\u2014')
        print(f"L{i}: ...{line[max(0,idx-30):idx+30]}...")

open(path, 'w', encoding='utf-8').write(t)
print(f"Remaining: {t.count(chr(0x2014))}")
