import re

with open(r"D:\06_Hermes\articles\workspace-agent-brain\server_content.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. 要点速览 → 蓝卡
kyds_start = html.find('<p><strong style="font-weight: bold;font-size: 16px;color: #1a6ba0;"><span leaf="">要点速览</span></strong></p>')
kyds_content_start = html.find('<span leaf="">&nbsp;-&nbsp;</span>', kyds_start)
next_hr = html.find('<hr style="border-style: solid;border-width: 2px 0 0;border-color: rgba(0, 0, 0, 0.1)', kyds_start)
kyds_content_end = html.rfind('</span></p>', kyds_content_start, next_hr) + len('</span></p>')
new_kyds = '''<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
''' + html[kyds_content_start:kyds_content_end] + '''
</div>
</div>'''
html = html[:kyds_start] + new_kyds + html[kyds_content_end:]

# 2. 上半部分卡片
upper_start = html.find('上半部分 · 官方入门版')
upper_tag_start = html.rfind('<', upper_start - 50, upper_start)
upper_tag_end = html.find('>', upper_start) + 1
new_upper = '<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin:18px 0;"><div style="text-align:center;"><strong style="font-size:15px;color:#1a6ba0;">上半部分 · 官方入门版</strong></div></div>'
html = html[:upper_tag_start] + new_upper + html[upper_tag_end:]

# 3. 下半部分卡片
lower_start = html.find('下半部分 · 论文核心技术点')
lower_tag_start = html.rfind('<', lower_start - 50, lower_start)
lower_tag_end = html.find('>', lower_start) + 1
new_lower = '<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin:18px 0;"><div style="text-align:center;"><strong style="font-size:15px;color:#1a6ba0;">下半部分 · 论文核心技术点</strong></div></div>'
html = html[:lower_tag_start] + new_lower + html[lower_tag_end:]

# 4. 结语 → 暖色卡 + 增加A社内部掌握文案
jieyu_span = '<span leaf="">结语</span>'
jieyu_start = html.find(jieyu_span)
jieyu_tag_start = html.rfind('<', jieyu_start - 30, jieyu_start)
jieyu_tag_end = html.find('>', jieyu_start) + 1

reference_start = html.find('参考：')
jieyu_inner = html[jieyu_tag_end:reference_start]

# Modify the 反事实反思训练 text inside jieyu_inner
old_text = '&nbsp;反事实反思训练可能更值得盯：**它不训练目标行为，只训练模型在被追问时说什么，就能改变原始语境下不诚实分数从0.25到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径**。'
new_text = '&nbsp;反事实反思训练可能更值得盯——**这项内部技术如今已公开发表，意味着Anthropic在自己最前沿的模型上早已掌握并初步验证了其效果**。它不训练目标行为本身，只训练模型在被追问时说什么，就能让原始语境下不诚实分数从0.25降到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径。'
jieyu_inner = jieyu_inner.replace(old_text, new_text)

new_jieyu = f'''<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
{jieyu_inner}</div>
</div>'''
html = html[:jieyu_tag_start] + new_jieyu + html[reference_start:]

# Save
with open(r"D:\06_Hermes\articles\workspace-agent-brain\formatted_content.html", "w", encoding="utf-8") as f:
    f.write(html)

# Verify
jieyu_pos = html.find('反事实反思训练可能更值得盯')
if jieyu_pos > 0:
    context = html[jieyu_pos:jieyu_pos+300]
    text = re.sub(r'<[^>]+>', ' ', context)
    text = re.sub(r'\s+', ' ', text).strip()
    print("结语修改后:")
    print(text[:200])
else:
    print("⚠️ 未找到")

# Count images
imgs = re.findall(r'<img[^>]*src="([^"]+)"', html)
print(f"\n图片数: {len(imgs)}")
print(f"内容长度: {len(html)}")
