import re

with open(r"D:\06_Hermes\articles\workspace-agent-brain\server_content.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Find everything from the first 结语 to 参考：
first_jieyu = html.find('结语')
ref_pos = html.find('参考：')

# Extract clean text from the first occurrence
jieyu_section = html[first_jieyu:ref_pos]
jieyu_text = re.sub(r'<[^>]+>', '', jieyu_section)
jieyu_text = re.sub(r'\s', ' ', jieyu_text).strip()
jieyu_text = re.sub(r'结语\s*', '', jieyu_text, count=1)  # remove first "结语"
jieyu_text = jieyu_text.strip()

# Modify text
old_t = '反事实反思训练可能更值得盯：**它不训练目标行为，只训练模型在被追问时说什么，就能改变原始语境下不诚实分数从0.25到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径**。'
new_t = '反事实反思训练可能更值得盯——**这项内部技术如今已公开发表，意味着Anthropic在自己最前沿的模型上早已掌握并初步验证了其效果**。它不训练目标行为本身，只训练模型在被追问时说什么，就能让原始语境下不诚实分数从0.25降到0.07。如果这种技术能被泛化到更抽象或更具体的倾向上，它就是一种直接在概念级别植入原则的路径。'
jieyu_text = jieyu_text.replace(old_t, new_t)

# 2. Build clean card
clean_card = f'''<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
{jieyu_text}
</div>
</div>'''

# 3. Find the clean section end
section_end = html.find('</section>', ref_pos)
if section_end < 0:
    section_end = len(html)

# 4. Build clean reference section
clean_ref = '''
<hr style="border-style: solid;border-width: 2px 0 0;border-color: rgba(0, 0, 0, 0.1);-webkit-transform-origin: 0 0;-webkit-transform: scale(1, 0.5);transform-origin: 0 0;transform: scale(1, 0.5);height: 0.4em;margin: 1.5em 0;" />
<p style="margin: 1.5em 8px;letter-spacing: 0.1em;color: #3f3f3f;">
<span style="font-size:12px;color:#888888;font-family:&#39;Courier New&#39;,monospace;">
<span leaf="">参考：https://transformer-circuits.pub/2026/workspace/index.html</span>
</span>
</p>
</section>'''

# 5. Assemble: everything before first_jieyu context + clean_card + clean_ref
# Find the parent context where 结语 starts - look for the nearest < or </p> before
card_context_start = html.rfind('<', first_jieyu - 50, first_jieyu)
if card_context_start < 0:
    card_context_start = first_jieyu - 20

# But we want to keep everything BEFORE the 结语 section - find what's between the end of the last content and 结语
# Just find the </section> or important boundary before 结语
# Actually simpler: just truncate right before where 结语 starts in the original content flow
# The original結語 sits right after the article body - let's find the <hr> or </p> before 结语
pre_jieyu_hr = html.rfind('<hr', first_jieyu - 100, first_jieyu)
if pre_jieyu_hr < 0:
    pre_jieyu_hr = html.rfind('</p>', first_jieyu - 200, first_jieyu) + 4
    if pre_jieyu_hr < 4:
        pre_jieyu_hr = card_context_start

html_before = html[:pre_jieyu_hr]
html_after = clean_card + clean_ref

html = html_before + html_after

with open(r"D:\06_Hermes\articles\workspace-agent-brain\formatted_content.html", "w", encoding="utf-8") as f:
    f.write(html)

# Verify
jieyu_count = html.count('结语')
imgs = re.findall(r'<img[^>]*src="([^"]+)"', html)
print(f"结语出现: {jieyu_count}次 (应为1)")
print(f"图片: {len(imgs)}")
print(f"包含'已公开发表': {'已公开发表' in html}")
assert jieyu_count == 1, f"结语重复: {jieyu_count}"
assert len(imgs) == 16, f"图片数: {len(imgs)}"
assert '已公开发表' in html

# Check 结语 content
jieyu_pos = html.find('结语')
jieyu_text_verify = re.sub(r'<[^>]+>', ' ', html[jieyu_pos:jieyu_pos+1500])
jieyu_text_verify = re.sub(r'\s+', ' ', jieyu_text_verify).strip()[:300]
print(f"结语内容: {jieyu_text_verify}...")
print(f"✅ 全部正确")
