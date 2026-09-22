# -*- coding: utf-8 -*-
"""生成 _caption_review.html：图 + 图注 + 所在段落，供逐张核对配对。"""
import html
import json

ART = r"D:\06_Hermes\articles\mimo-v26-scaling-rl"
j = json.load(open(ART + r"\article_data.json", encoding="utf-8"))

rows = []
for s in j["sections"]:
    for k, items in sorted((s.get("fig_after") or {}).items(), key=lambda x: int(x[0])):
        idx = int(k)
        ctx = s["paras"][idx] if idx < len(s["paras"]) else ""
        for it in items:
            rows.append((s["title"], it["src"], it["caption"], ctx))

html_parts = [
    "<!doctype html><meta charset='utf-8'>",
    "<title>MiMo-V2.6 图注核对</title>",
    "<style>body{font-family:'Microsoft YaHei',sans-serif;background:#fafafa;margin:24px;}",
    ".card{display:flex;gap:18px;background:#fff;border:1px solid #e2e2e2;border-radius:8px;",
    "padding:14px;margin-bottom:16px;}",
    ".card img{width:460px;height:auto;border:1px solid #eee;border-radius:4px;flex:0 0 460px;}",
    ".meta{font-size:14px;line-height:1.7;color:#333;}",
    ".sec{color:#1a6ba0;font-weight:700;}",
    ".cap{color:#0F4C81;font-weight:700;margin:6px 0;}",
    ".ctx{color:#666;}</style>",
    f"<h2>MiMo-V2.6 技术报告 · 图注核对（共 {len(rows)} 张）</h2>",
]
for i, (sec, src, cap, ctx) in enumerate(rows, 1):
    html_parts.append(
        "<div class='card'>"
        f"<img src='{src}'>"
        "<div class='meta'>"
        f"<div class='sec'>{i}. {html.escape(sec)}</div>"
        f"<div class='cap'>{html.escape(cap)}</div>"
        f"<div class='ctx'>图前一段：{html.escape(ctx[:220])}</div>"
        "</div></div>"
    )
out = ART + r"\_caption_review.html"
open(out, "w", encoding="utf-8").write("\n".join(html_parts))
print("written", out, len(rows), "cards")
