# -*- coding: utf-8 -*-
"""中文写回 v2：从 main.txt 解析正文段 -> 与译文 key 精确对应 -> 生成干净中文 HTML"""
import json, re, os

base=r"D:/06_Hermes/articles/zhipu-earnings-transcript"
main=open(base+"/main.txt",encoding="utf-8").read()
lines=main.split('\n')
all_zh=json.load(open(base+"/_all_zh.json",encoding="utf-8"))
speakers={'Tang Jie':'唐杰','Liu Debing':'刘德冰','Xiao Lei':'萧雷','Liu Debin, Chairman of Zhipu':'刘德彬（董事长）'}
def clean_para(s):
    s=s.strip(); s=re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s); s=s.replace('**',''); return s

blocks=[]
in_qa=False; cur_qa=None; p_idx=0; q_idx=0; a_idx=0
start_body=False
for raw in lines:
    l=raw.strip()
    if not l: continue
    # 跳过正文前的 meta（Log in/## Post/头像/标题）
    if l=='Log inSign up' or l.startswith('## Post') or l.startswith('![') or l.startswith('# Zhipu Earnings Transcript'):
        continue
    if l=='Prepared Remarks':
        start_body=True; blocks.append({'type':'h_section','text':'管理层陈述（Prepared Remarks）'}); continue
    if l=='Q&A':
        blocks.append({'type':'h_section','text':'问答环节（Q&A）'}); in_qa=True; continue
    if l in speakers:
        blocks.append({'type':'h_speaker','speaker':speakers[l]}); continue
    if in_qa:
        if l.startswith('Q:'):
            blocks.append({'type':'q','idx':q_idx,'text':l[2:].strip()}); q_idx+=1; cur_qa='q'; continue
        if l.startswith('A:'):
            blocks.append({'type':'a','idx':a_idx,'text':l[2:].strip()}); a_idx+=1; cur_qa='a'; continue
        if cur_qa=='q':
            if blocks and blocks[-1]['type']=='q': blocks[-1]['text']+=' '+l
            else: blocks.append({'type':'q','idx':q_idx,'text':l}); q_idx+=1
            continue
        else:
            if blocks and blocks[-1]['type']=='a': blocks[-1]['text']+=' '+l
            elif blocks and blocks[-1]['type']=='q': blocks.append({'type':'a','idx':a_idx,'text':l}); a_idx+=1
            else: blocks.append({'type':'a','idx':a_idx,'text':l}); a_idx+=1
            continue
    # 正文 p
    blocks.append({'type':'p','idx':p_idx,'text':l}); p_idx+=1

print(f"解析: p 段={p_idx}个(p0-{p_idx-1}), Q={q_idx}, A={a_idx}")
# 检查译文 key 覆盖
zh_keys=set(all_zh.keys())
miss_p=[i for i in range(p_idx) if f'p{i}' not in zh_keys]
print("缺译文 p:", miss_p[:10] if miss_p else "无")

# 组装 HTML（用译文）
OUT=['<section style="font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;max-width:100%;box-sizing:border-box;">']
OUT.append('<h1 style="font-weight:bold;font-size:24px;color:#111;margin:18px 0 8px;line-height:1.4;">智谱（Zhipu）2026 中期业绩发布会纪要</h1>')
OUT.append('<p style="font-size:13px;color:#888;margin:0 0 14px;">来源：@zephyr_z9 · 原帖 X · 全文中文翻译保留</p>')
qa_n=0
for b in blocks:
    if b['type']=='h_section':
        OUT.append(f'<h2 style="font-weight:bold;font-size:20px;color:#0a7d91;margin:26px 0 10px;padding-bottom:6px;border-bottom:2px solid #0a7d91;">{b["text"]}</h2>')
    elif b['type']=='h_speaker':
        OUT.append(f'<h3 style="font-weight:bold;font-size:17px;color:#334;margin:18px 0 8px;">🎤 {b["speaker"]}</h3>')
    elif b['type']=='p':
        txt=all_zh.get(f'p{b["idx"]}', b['text'])
        OUT.append(f'<p style="font-size:15px;line-height:1.85;color:#333;margin:9px 0;text-align:justify;">{txt}</p>')
    elif b['type']=='q':
        qa_n+=1
        txt=all_zh.get(f'Q{b["idx"]}', b['text'])
        if qa_n<3 and 'Q' not in str(b['idx']) and txt==b['text']:
            txt=all_zh.get(f'Q{b["idx"]}','')
        OUT.append(f'<div style="background:#e8f4ff;border-left:4px solid #2196F3;border-radius:4px;padding:12px 14px;margin:16px 0 10px;">'
                   f'<span style="display:inline-block;background:#2196F3;color:#fff;font-weight:bold;font-size:13px;border-radius:3px;padding:2px 8px;margin-right:8px;">问 {qa_n}</span>'
                   f'<span style="font-weight:bold;font-size:15px;color:#0b3d6e;">{txt}</span></div>')
    elif b['type']=='a':
        txt=all_zh.get(f'A{b["idx"]+1}', b['text'])  # A idx 从0但key从A1
        OUT.append(f'<div style="background:#fafafa;border-left:4px solid #4CAF50;border-radius:4px;padding:12px 14px;margin:0 0 16px 18px;">'
                   f'<span style="display:inline-block;background:#4CAF50;color:#fff;font-weight:bold;font-size:13px;border-radius:3px;padding:2px 8px;margin-right:8px;">答</span>'
                   f'<span style="font-size:15px;line-height:1.85;color:#333;text-align:justify;">{txt}</span></div>')
OUT.append('<div style="margin-top:28px;padding:14px;background:#f5f0eb;border-radius:6px;font-size:13px;color:#555;">'
           '<strong>📌 来源</strong><br>智谱2026中期业绩发布会纪要（中文翻译）<br>'
           '原帖：@zephyr_z9 · X · https://x.com/zephyr_z9/status/2094542689002008620</div>')
OUT.append('</section>')
html=''.join(OUT)
open(base+"/article_zh.html","w",encoding="utf-8").write(html)
zh=len(re.findall(r'[\u4e00-\u9fff]', html))
en=len(re.findall(r'[A-Za-z]{4,}', re.sub(r'<[^>]+>',' ',html)))
print(f"✅ 中文:{zh} 英文词残留:{en} 问答:{qa_n} 长度:{len(html)}")
