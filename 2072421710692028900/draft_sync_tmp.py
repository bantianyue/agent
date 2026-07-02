"""
draft-sync.py — 从微信草稿箱下载草稿并修复格式

功能：
1. 从 draft.id 或 batchget 查找草稿
2. 下载 HTML + 封面 + 全部 inline 图片
3. 修复要点速览/结语的卡片样式（服务器 HTML 丢失背景盒子）
4. 格式化参考区为单行等宽字体
5. 可选添加传送门

用法：
  python draft-sync.py <article-dir>
  python draft-sync.py <article-dir> --add-portal

输出：
  article_fixed.html  — 修复后的 HTML 文件（可直接推送）
  draft_from_server.html — 原始服务器 HTML
  draft_meta.json     — 元数据（标题、摘要、封面 URL）
  cover_wx.jpg        — 服务器封面图
  server_img_*.jpg/png — 服务器上的 inline 图片
"""

import os, sys, json, re, urllib.request
from datetime import datetime

ARTICLE_DIR = sys.argv[1] if len(sys.argv) > 1 else '.'
ADD_PORTAL = '--add-portal' in sys.argv

# ── 1. 读取凭证 ──
env_path = os.path.expanduser('~/.baoyu-skills/.env')
appid = secret = ''
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('WECHAT_APP_ID'):
            appid = line.split('=', 1)[1].strip()
        elif line.startswith('WECHAT_APP_SECRET'):
            secret = line.split('=', 1)[1].strip()

# ── 2. 获取 token ──
url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    token = json.loads(resp.read())['access_token']

# ── 3. 读取 draft.id ──
draft_path = os.path.join(ARTICLE_DIR, 'draft.id')
if not os.path.exists(draft_path):
    print(f'❌ draft.id not found in {ARTICLE_DIR}')
    sys.exit(1)

with open(draft_path) as f:
    media_id = f.read().strip()

# ── 4. 下载草稿 ──
get_url = f'https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}'
payload = json.dumps({'media_id': media_id}).encode()
req2 = urllib.request.Request(get_url, data=payload, method='POST')
req2.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req2, timeout=15) as resp:
    draft = json.loads(resp.read())

content = draft['news_item'][0]['content']
title = draft['news_item'][0].get('title', '')
digest = draft['news_item'][0].get('digest', '')
thumb_url = draft['news_item'][0].get('thumb_url', '')
update_time = draft.get('update_time', 0)

print(f'Title: {title}')
print(f'Update time: {update_time} ({datetime.fromtimestamp(update_time)})' if update_time else '')
print(f'Content: {len(content)} chars')

meta = {'title': title, 'digest': digest, 'thumb_url': thumb_url, 'update_time': update_time}
with open(os.path.join(ARTICLE_DIR, 'draft_meta.json'), 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

# ── 5. 编码修复 ──
if '要点速览' in content or '结语' in content:
    html = content
else:
    html = content.encode('latin-1', errors='replace').decode('utf-8', errors='replace')

# ── 6. 下载 inline 图片 ──
imgs = re.findall(r'https://mmbiz\.qpic\.cn[^\s"\'<>]+', html)
seen = set()
for i, url in enumerate(imgs):
    url = url.rstrip('&').replace('&amp;', '&')
    if url in seen:
        continue
    seen.add(url)
    ext = 'jpg' if 'wx_fmt=jpeg' in url or 'wx_fmt=jpg' in url else ('png' if 'wx_fmt=png' in url else 'jpg')
    filename = f'server_img_{i+1:02d}.{ext}'
    try:
        req_img = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_img, timeout=30) as r:
            data = r.read()
            with open(os.path.join(ARTICLE_DIR, filename), 'wb') as f:
                f.write(data)
    except Exception:
        pass

print(f'Downloaded {len(seen)} images')

# ── 7. 下载封面 ──
if thumb_url:
    try:
        req_thumb = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_thumb, timeout=15) as r:
            with open(os.path.join(ARTICLE_DIR, 'cover_wx.jpg'), 'wb') as f:
                f.write(r.read())
        print(f'Cover downloaded')
    except Exception as e:
        print(f'Cover download failed: {e}')

# ── 8. 修复要点速览卡片 ──
def fix_yaodian_card(html):
    """修复要点速览的蓝底卡片样式"""
    if '要点速览' not in html:
        return html

    yd_idx = html.index('要点速览')
    # 找到 card 起始位置（最近的 <p 或 <section 开头）
    card_start = html.rfind('<p', yd_idx - 200, yd_idx)
    if card_start < 0:
        card_start = html.rfind('<section', yd_idx - 200, yd_idx)

    # 找到正文起点（美团LongCat Lab 或文章第一个强段落）
    body_markers = ['**美团LongCat Lab', '美团LongCat Lab', '先说美团']
    body_idx = len(html)
    for m in body_markers:
        idx = html.find(m, yd_idx)
        if 0 < idx < body_idx:
            body_idx = idx
    if body_idx == len(html):
        # fallback: 找到要点速览内容后的下一个强标签
        body_idx = html.find('<strong', yd_idx + 100)
        if body_idx < 0:
            body_idx = html.find('<p', yd_idx + 100)

    # 找到 card 结尾（body 前最后一个 </p>）
    card_end = html.rfind('</p>', yd_idx, body_idx)
    if card_end > 0:
        card_end += 4
    else:
        card_end = body_idx

    old_card = html[card_start:card_end]

    # 提取纯文本内容（去掉所有 HTML 标签）
    text_only = re.sub(r'<[^>]+>', '', old_card)
    text_only = re.sub(r'&nbsp;', ' ', text_only)
    text_only = text_only.replace('要点速览', '').strip()
    # 合并连续空格
    text_only = re.sub(r' {2,}', ' ', text_only)

    # 构建新卡片：内容也用 <br> 保留原有换行逻辑
    # 但服务器 HTML 的要点是一段连续文本，保留原样即可
    new_card = f'''<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
{text_only}
</div>
</div>'''

    html = html[:card_start] + new_card + html[card_end:]
    return html

# ── 9. 修复结语卡片 ──
def fix_jieyu_card(html):
    """修复结语的暖灰卡片样式"""
    if '结语' not in html:
        return html

    jieyu_idx = html.index('结语')

    # 找到起始
    jieyu_start = html.rfind('<p', jieyu_idx - 200, jieyu_idx)
    if jieyu_start < 0:
        jieyu_start = html.rfind('<section', jieyu_idx - 200, jieyu_idx)

    # 找到结束（下一个 参考 或 --- 或 末尾）
    ref_marker = '参考'
    ref_idx = html.find(ref_marker, jieyu_idx)
    if ref_idx < 0:
        ref_idx = len(html)

    jieyu_end = html.rfind('</p>', jieyu_idx, ref_idx)
    if jieyu_end > 0:
        jieyu_end += 4
    else:
        jieyu_end = ref_idx

    old_jieyu = html[jieyu_start:jieyu_end]

    # 提取纯文本
    text_only = re.sub(r'<[^>]+>', '', old_jieyu)
    text_only = re.sub(r'&nbsp;', ' ', text_only)
    text_only = text_only.replace('结语', '').strip()
    text_only = re.sub(r' {2,}', ' ', text_only)

    new_card = f'''<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
{text_only}
</div>
</div>'''

    html = html[:jieyu_start] + new_card + html[jieyu_end:]
    return html

# ── 10. 修复参考区格式 ──
def fix_reference(html):
    """参考区统一为单行等宽字体格式"""
    # 找到参考区附近的 ---
    ref_idx = html.find('参考：')
    if ref_idx < 0:
        ref_idx = html.find('参考:')
    if ref_idx < 0:
        return html

    # 找到前面的 ---（可能在参考：前面）
    prev_dash = html.rfind('---', ref_idx - 50, ref_idx)

    ref_url_pattern = re.compile(r'参考[：:]\s*(https?://[^\s<>\'"]+)')
    m = ref_url_pattern.search(html, ref_idx)
    if not m:
        return html

    url = m.group(1).rstrip(',.;')
    ref_span = f'\n<span style="font-size:12px;color:#888888;font-family:\'Courier New\',monospace;">参考：{url}</span>'

    # 如果前面有 ---，保留一个
    if prev_dash >= 0:
        # 只保留一个 ---
        before = html[:prev_dash].rstrip()
        after = html[m.end():]
        # 去掉 after 开头的空白和多余标签
        after = re.sub(r'^[\s<>&nbsp;/]+', '', after)
        html = before + '\n\n---\n' + ref_span + '\n' + after
    else:
        html = html[:ref_idx] + ref_span + html[m.end():]

    return html

# ── 11. 添加传送门 ──
def add_portal(html):
    portal = '''---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/9QtSgk3jn5JSqcCB1ZKinA" target="_blank" data-linktype="2">Anthropic 3亿收购Stainless：CEO详解MCP协议未来</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/o6pnSWW01pahFQelJSbSPA" target="_blank" data-linktype="2">华为「韬定律」全解析：从 τ 常数到 4GHz 麒麟</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/xP1cEoO_plRpWItxhqeQnQ" target="_blank" data-linktype="2">Agent Harness Engineering：为什么Agent可靠性的天花板不是模型，而是基础</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/PLNx54PxO1A0oYc47hz99g" target="_blank" data-linktype="2">Anthropic三连：Claude Opus 4.8-更聪明+诚实</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/Pdjz39WG9SS6IpWWAJ6pPw" target="_blank" data-linktype="2">Claude Opus 4.8 击败 Opus 4.7、GPT-5.5 和 Gemini 3.1 P</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/mFuUJ79DRodIK6shVWOgpw" target="_blank" data-linktype="2">OpenAI GPT-5.6: 安全之外新增Prompt Cache断点+两种推理模式</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/aiJs5CC8Gb6qa_xDRNEjTA" target="_blank" data-linktype="2">Dynamic Subagents：用代码编排Agents，告别逐轮工具调用</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/qcIFzXsBalSGpca5fzJKxg" target="_blank" data-linktype="2">Claude Code 动态Workflow Vs. SubAgent Vs. Skill</a></span>

---'''

    ref_idx = html.find('参考：')
    if ref_idx < 0:
        ref_idx = html.find('参考:')
    if ref_idx < 0:
        html += '\n' + portal
    else:
        html = html[:ref_idx] + portal + '\n\n' + html[ref_idx:]
    return html

# ── 执行全部修复 ──
html = fix_yaodian_card(html)
html = fix_jieyu_card(html)
html = fix_reference(html)
if ADD_PORTAL:
    html = add_portal(html)

# ── 保存 ──
with open(os.path.join(ARTICLE_DIR, 'draft_from_server.html'), 'w', encoding='utf-8') as f:
    f.write(html)

fixed_path = os.path.join(ARTICLE_DIR, 'article_fixed.html')
with open(fixed_path, 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Saved article_fixed.html ({len(html)} chars)')
print('Done')
