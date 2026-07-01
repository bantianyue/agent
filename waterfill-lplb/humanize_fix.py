import re

with open('D:/06_Hermes/articles/waterfill-lplb/article.md', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
changes = []

em_dash = '\u2014'

for i, line in enumerate(lines):
    stripped = line.strip()
    # Skip table rows
    if stripped.startswith('|') and stripped.endswith('|'):
        new_lines.append(line)
        continue
    
    new_line = line
    # Replace all em dashes with ：
    count = new_line.count(em_dash)
    if count > 0:
        new_line = new_line.replace(em_dash, '：')
        changes.append((i+1, count, line[:70]))
    new_lines.append(new_line)

new_content = '\n'.join(new_lines)

# Humanize fixes
new_content = new_content.replace(
    '精妙在差一点点语义无关',
    '巧妙在刚好不碰语义边界'
)

new_content = new_content.replace(
    '展示了"把优化问题藏在系统层"的工程品味',
    '算是"把优化问题藏在系统层"的好工程'
)

with open('D:/06_Hermes/articles/waterfill-lplb/article_human.md', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f'Fixed {len(changes)} lines with em dashes')
for line_no, cnt, snippet in changes:
    print(f'  L{line_no} ({cnt}x): {snippet}')

remaining = new_content.count(em_dash)
print(f'Remaining em dashes: {remaining}')
