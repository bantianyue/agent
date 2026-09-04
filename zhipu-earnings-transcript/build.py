# -*- coding: utf-8 -*-
"""智谱 Earnings Transcript 原文保留 + 问答显式区分"""
import re, json

base=r"D:/06_Hermes/articles/zhipu-earnings-transcript"
main=open(base+"/main.txt",encoding="utf-8").read()
lines=main.split('\n')

speakers={'Tang Jie':'唐杰（Tang Jie）','Liu Debing':'刘德冰（Liu Debing）',
          'Xiao Lei':'萧雷（Xiao Lei）','Liu Debin, Chairman of Zhipu':'智谱董事长 刘德彬（Liu Debin）'}

def clean_para(s):
    s=s.strip()
    # 去 markdown 残留链接
    s=re.sub(r'\[([^\]]*)\]\([^)]*\)', r'\1', s)
    s=s.replace('**','')
    return s

html=[]  # 存（类型,内容）用于 debug，实际存段落块
blocks=[]  # 每个元素: {'type':'h_section'|'h_speaker'|'p'|'qa_head'|'qa_body', ...}
in_qa=False
cur_qa=None

for raw in lines:
    l=raw.strip()
    if not l: continue
    # 标题区
    if l=='Prepared Remarks':
        blocks.append({'type':'h_section','text':'管理层陈述（Prepared Remarks）'}); continue
    if l=='Q&A':
        blocks.append({'type':'h_section','text':'问答环节（Q&A）'}); in_qa=True; continue
    if l in speakers:
        blocks.append({'type':'h_speaker','speaker':speakers[l]}); continue
    # Q&A
    if in_qa:
        if l.startswith('Q:'):
            blocks.append({'type':'q','text':clean_para(l[2:])}); cur_qa='q'; continue
        if l.startswith('A:'):
            blocks.append({'type':'a','text':clean_para(l[2:])}); cur_qa='a'; continue
        # 非Q/A开头的行，若是Q&A正文段落，作为当前回答（或在Q后）的continuation
        if cur_qa=='q':
            # Q 后直接跟正文（罕见），并入上一个 q
            if blocks and blocks[-1]['type']=='q':
                blocks[-1]['text']+=' '+clean_para(l)
            else:
                blocks.append({'type':'q','text':clean_para(l)})
            continue
        else:
            # A 段 continuation
            if blocks and blocks[-1]['type']=='a':
                blocks[-1]['text']+=' '+clean_para(l)
            elif blocks and blocks[-1]['type']=='q':
                blocks.append({'type':'a','text':clean_para(l)})
            else:
                blocks.append({'type':'a','text':clean_para(l)})
            continue
    # Prepared Remarks 正文
    blocks.append({'type':'p','text':clean_para(l)})

# 组装 HTML
OUT=['<section style="font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;max-width:100%;box-sizing:border-box;">']
# 标题
OUT.append('<h1 style="font-weight:bold;font-size:24px;color:#111;margin:18px 0 8px;line-height:1.4;">智谱（Zhipu）2026 中期业绩发布会纪要</h1>')
OUT.append('<p style="font-size:13px;color:#888;margin:0 0 14px;">来源：@zephyr_z9 · 原帖 X · 全文保留 · 2026 业绩发布会纪要</p>')

qa_idx=0
for b in blocks:
    if b['type']=='h_section':
        OUT.append(f'<h2 style="font-weight:bold;font-size:20px;color:#0a7d91;margin:26px 0 10px;padding-bottom:6px;border-bottom:2px solid #0a7d91;">{b["text"]}</h2>')
    elif b['type']=='h_speaker':
        OUT.append(f'<h3 style="font-weight:bold;font-size:17px;color:#334;margin:18px 0 8px;">🎤 {b["speaker"]}</h3>')
    elif b['type']=='p':
        OUT.append(f'<p style="font-size:15px;line-height:1.85;color:#333;margin:9px 0;text-align:justify;">{b["text"]}</p>')
    elif b['type']=='q':
        qa_idx+=1
        OUT.append(f'<div style="background:#e8f4ff;border-left:4px solid #2196F3;border-radius:4px;padding:12px 14px;margin:16px 0 10px;">'
                   f'<span style="display:inline-block;background:#2196F3;color:#fff;font-weight:bold;font-size:13px;border-radius:3px;padding:2px 8px;margin-right:8px;">问 {qa_idx}</span>'
                   f'<span style="font-weight:bold;font-size:15px;color:#0b3d6e;">{b["text"]}</span></div>')
    elif b['type']=='a':
        OUT.append(f'<div style="background:#fafafa;border-left:4px solid #4CAF50;border-radius:4px;padding:12px 14px;margin:0 0 16px 18px;">'
                   f'<span style="display:inline-block;background:#4CAF50;color:#fff;font-weight:bold;font-size:13px;border-radius:3px;padding:2px 8px;margin-right:8px;">答</span>'
                   f'<span style="font-size:15px;line-height:1.85;color:#333;text-align:justify;">{b["text"]}</span></div>')

# 结尾来源
OUT.append('<div style="margin-top:28px;padding:14px;background:#f5f0eb;border-radius:6px;font-size:13px;color:#555;">'
           '<strong>📌 来源</strong><br>智谱2026中期业绩发布会纪要（Earnings Transcript）<br>'
           '原帖：@zephyr_z9 · X · https://x.com/zephyr_z9/status/2094542689002008620</div>')
OUT.append('</section>')

html_str=''.join(OUT)
open(base+"/article.html","w",encoding="utf-8").write(html_str)
print("✅ article.html 生成:", len(html_str))
print("问答组数:", qa_idx)
# debug 统计
print("块类型统计:", {k:sum(1 for b in blocks if b['type']==k) for k in set(b['type'] for b in blocks)})
# 校验正文词
alltext=re.sub(r'<[^>]+>',' ',html_str)
print("正文英文词(原文保留):", len(re.findall(r'[A-Za-z]+', alltext)))
