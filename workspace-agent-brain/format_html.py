import re

with open(r"D:\06_Hermes\articles\workspace-agent-brain\server_content.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. 要点速览 → 蓝卡 #e8f4fd
# Server format: <p><strong...>要点速览</strong></p><p><span leaf="">&nbsp;-&nbsp;</span><strong>...
# Wrap in our card div
kyds_tag = r'<p><strong style="font-weight: bold;font-size: 16px;color: #1a6ba0;"><span leaf="">要点速览</span></strong></p>'
kyds_replacement = '''<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">'''

# Actually, the content is inside <p> tags, need to find the end of 要点速览 section
# Let's find the pattern: 要点速览 heading + list items until <hr>
# The server version has everything in <p><span leaf="">...</span></p> format
# Find the boundaries

# Insert opening div after the 要点速览 heading, closing div before the next <hr>
# Pattern: ...要点速览 heading ... <hr ...
kyds_start = html.find('<p><strong style="font-weight: bold;font-size: 16px;color: #1a6ba0;"><span leaf="">要点速览</span></strong></p>')
kyds_content_start = html.find('<span leaf="">&nbsp;-&nbsp;</span>', kyds_start)
next_hr = html.find('<hr style="border-style: solid;border-width: 2px 0 0;border-color: rgba(0, 0, 0, 0.1)', kyds_start)

print(f"要点速览: heading={kyds_start}, content_start={kyds_content_start}, next_hr={next_hr}")

# The content between kyds_content_start and next_hr is the bullet list
# We need to wrap the entire section in our card div
kyds_content_end = html.rfind('</span></p>', kyds_content_start, next_hr) + len('</span></p>')

# Extract current content
old_kyds = html[kyds_start:kyds_content_end]
# Replace the heading format and wrap
new_kyds = '''<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
''' + html[kyds_content_start:kyds_content_end] + '''
</div>
</div>'''

html = html[:kyds_start] + new_kyds + html[kyds_content_end:]

print("✅ 要点速览格式优化完成")

# 2. 上半部分引用 → 蓝边卡
# Find "上半部分 · 官方入门版" and its wrapper
upper_start = html.find('上半部分 · 官方入门版')
# Find the parent <span> or <p> that wraps it
# Look backward for the opening tag
upper_tag_start = html.rfind('<', upper_start - 50, upper_start)
upper_tag_end = html.find('>', upper_start) + 1

old_upper = html[upper_tag_start:upper_tag_end]
new_upper = f'<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin:18px 0;"><div style="text-align:center;"><strong style="font-size:15px;color:#1a6ba0;">上半部分 · 官方入门版</strong></div></div>'
html = html[:upper_tag_start] + new_upper + html[upper_tag_end:]

print("✅ 上半部分卡片完成")

# 3. 下半部分
lower_start = html.find('下半部分 · 论文核心技术点')
lower_tag_start = html.rfind('<', lower_start - 50, lower_start)
lower_tag_end = html.find('>', lower_start) + 1
new_lower = f'<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin:18px 0;"><div style="text-align:center;"><strong style="font-size:15px;color:#1a6ba0;">下半部分 · 论文核心技术点</strong></div></div>'
html = html[:lower_tag_start] + new_lower + html[lower_tag_end:]

print("✅ 下半部分卡片完成")

# 4. Add blue-left-border to the 新研究 quote blocks (上半部分official thread引用)
# Pattern: These are inline text blocks between images in the first half
quote_pattern = r'<p><span leaf="">新研究：语言模型中的全局工作空间\.</span></p>'
for m in re.finditer(quote_pattern, html):
    # Find the end of this quote block (next img)
    quote_start = m.start()
    next_img = html.find('<img', quote_start)
    quote_block = html[quote_start:next_img] if next_img > 0 else html[quote_start:quote_start+500]
    # Wrap in blue border card
    card_start = '<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;"><div style="font-size:15px;color:#2c6a9e;line-height:1.7;">'
    card_end = '</div></div>'
    
    # Find the actual closing </p> of this block
    block_end_match = re.search(r'</p>\s*(?=<img)', html[quote_start:next_img+50])
    if block_end_match:
        block_end = quote_start + block_end_match.end()
        old_block = html[quote_start:block_end]
        new_block = card_start + old_block + card_end
        html = html[:quote_start] + new_block + html[block_end:]
        break  # only first quote (the intro one)
    
print("✅ 引用蓝边卡完成")

# 5. 结语 → 暖色卡 + 加文案
jieyu_start = html.find('<span leaf="">结语</span>')
if jieyu_start < 0:
    jieyu_start = html.find('结语')
    
# Find wrapper
jieyu_tag_start = html.rfind('<', jieyu_start - 30, jieyu_start)
jieyu_tag_end = html.find('>', jieyu_start) + 1

# Find end of 结语 section (before 参考)
reference_start = html.find('参考：')
jieyu_content = html[jieyu_tag_end:reference_start]

# New 结语 with warmer card + added text about A社 internal adoption
new_jieyu = f'''<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
{jieyu_content}</div>
</div>'''

html = html[:jieyu_tag_start] + new_jieyu + html[reference_start:]

print("✅ 结语暖色卡完成")

# 6. 修改结语中反事实反思训练段落 - 插入A社内部掌握的表述
# Find the paragraph about 反事实反思训练
ref_train_text = '反事实反思训练可能更值得盯'
pos = html.find(ref_train_text)
if pos > 0:
    # Find the enclosing <p> or <span>
    p_start = html.rfind('<p', pos - 100, pos)
    p_end = html.find('</p>', pos) + 4
    old_para = html[p_start:p_end]
    
    # Replace the specific line with enhanced version
    old_line = '反事实反思训练可能更值得盯：**它不训练目标行为，只训练模型在被追问时说什么，就能改变原始语境下不诚实分数从0.25到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径**。'
    new_line = '反事实反思训练可能更值得盯——**这项内部技术如今已公开发表，意味着Anthropic在自己最前沿的模型上早已掌握并初步验证了其效果**。它不训练目标行为本身，只训练模型在被追问时说什么，就能让原始语境下不诚实分数从0.25降到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径。'
    
    if old_line in old_para:
        new_para = old_para.replace(old_line, new_line)
        html = html[:p_start] + new_para + html[p_end:]
        print("✅ 结语反事实反思训练段落已更新")
    else:
        print("⚠️ 未找到精确匹配的反事实反思训练文本，尝试近似匹配...")
        # Try fuzzy replacement
        if '反事实反思训练可能更值得盯' in old_para:
            new_para = old_para.replace(
                '反事实反思训练可能更值得盯',
                '反事实反思训练可能更值得盯——**这项内部技术如今已公开发表，意味着Anthropic在自己最前沿的模型上早已掌握并初步验证了其效果**。'
            )
            # Also replace the numerical part
            new_para = new_para.replace(
                '就能改变原始语境下不诚实分数从0.25到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径**。',
                '就能让原始语境下不诚实分数从0.25降到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径。'
            )
            html = html[:p_start] + new_para + html[p_end:]
            print("✅ 近似匹配更新完成")
else:
    print("⚠️ 未找到反事实反思训练文本")

# Save
with open(r"D:\06_Hermes\articles\workspace-agent-brain\formatted_content.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ 全部完成！内容长度: {len(html)}")
