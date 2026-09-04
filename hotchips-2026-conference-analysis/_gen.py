# -*- coding: utf-8 -*-
"""Hot Chips 2026 全文编译 build 生成器（全量，图按原文位置插入）"""
import json, os, sys
# requires rg-translations file
for VAR in ("D:/06_Hermes/articles/hotchips-2026-conference-analysis",):
    _article_dir = VAR
base=_article_dir
t=json.load(open(os.path.join(base,"_trans.json"),encoding="utf-8"))
tr={int(k):v for k,v in t.items()}
def P(i): return tr[i]
def head1_skip(i):
    return tr[i]

# ---------- 组装 ---- helper: 每个公司一节
S=list()

def add_sec(typ,title=None,plist=None,fig_after=None):
    d={"type":typ}
    if title: d["title"]=title
    if plist: d["paras"]=plist
    if fig_after: d["fig_after"]=fig_after
    S.append(d)

# lead 是 DATA 顶层
# =========== 目录(不要作正文,省略) ===========

# 前瞻 open
intro=[P(0),P(1),P(2)]
# 不做独立section 放 lead

# ---- 内存板块 h2 ----
memory_story=[
 ("HBM 基础知识",[P(13),P(14),P(15)],
   {1:[{"src":"fig01.jpg","caption":"HBM 内部通过上千条走线并行与 GPU 通信"}]},
   P(16) if False else None),
]
# 组织过于繁琐，且易错。为可靠干脆把整个翻译按原文顺序组装成"板块h2 + 公司h3 + 要点h3"。
# 采用第二种更省心写法：把一个板块的所有原段落按书序放，公司标题使用 h3，插对应 fig。
# 写成 DATA 构造（非中间字典），全部显式列出保证每段可用。
