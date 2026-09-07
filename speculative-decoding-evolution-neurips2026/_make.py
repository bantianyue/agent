# -*- coding: utf-8 -*-
"""合并 _data*.py 的松散结构为 render-article 接受的 article_data.json。
data part约定:每文件导出 SECS(list of dict)。dict 形 =
   {"type":"h2/h3","title":..,"paras":[...]}        普通节
   {"head":[...],"rows":[...]}                       表格 → 附到当前节
   {"code":["__CODE__..."], 或 {"type":"code","texts":[...]}} 代码 → 并入当前节 paras
第一文件还导 SUMMARY/LEAD/TITLE/REFURL。
"""

import json, os, glob, importlib.util, re

D=os.path.dirname(os.path.abspath(__file__))
files=sorted(glob.glob(os.path.join(D,"_data*.py")))
TITLE=None; REFURL=None; SUMMARY=[]; LEAD=[]
allsec=[]
for fp in files:
    spec=importlib.util.spec_from_file_location("dt"+os.path.basename(fp), fp)
    pp=importlib.util.module_from_spec(spec); spec.loader.exec_module(pp)
    if getattr(pp,"TITLE",None): TITLE=pp.TITLE
    if getattr(pp,"REFURL",None): REFURL=pp.REFURL
    SUMMARY+=getattr(pp,"SUMMARY",[]); LEAD+=getattr(pp,"LEAD",[])
    allsec+=getattr(pp,"SECS",[])

# ---- 归一化：把 table/code 粘到上一节 ----
sections=[]; cur=None
css=[]   # 收集图文件(src) 
for it in allsec:
    if not isinstance(it,dict): continue
    typ=it.get("type")
    if typ in ("h2","h3"):
        sec={"type":typ,"title":it.get("title",""),"paras":list(it.get("paras",[]))}
        sections.append(sec); cur=sec
    elif cur is not None and ("head" in it and "rows" in it):
        cur["table"]={"head":it["head"],"rows":it["rows"]}
    elif cur is not None and (typ=="code" or "code" in it or it.get("texts")):
        t=it.get("texts") or it.get("code") or []
        cur["paras"]+=list(t)
    elif cur is not None and it.get("paras"):
        cur["paras"]+=list(it["paras"])
    elif it.get("type")=="h2" and it.get("fig"): #fig 直接给 src+caption挂首段
        pass

# CSS高亮 code 里首行以 __CODE__ 开头已是 lang 前缀
print("sections合并:",len(sections),"段落总数:",sum(len(s.get("paras",[])) for s in sections),
      "表:",sum(1 for s in sections if s.get("table")),
      "code paras:",sum(1 for s in sections for p in s.get("paras",[]) if str(p).startswith("__CODE__")))

# ---- 图 文件检查 ----
import os as _o
need_figs = set()
for s in sections:
    for k,v in (s.get("fig_after") or {}).items():
        for fg in v: need_figs.add(fg["src"])
for fn in sorted(need_figs):
    good=_o.path.exists(_o.path.join(D,fn))
    if not good: print("⚠️ 缺失图文件:",fn)

data={"title":TITLE,"reference_url":REFURL,"summary":SUMMARY,"lead":LEAD,
      "sections":sections,
      "conclusion":["（结语占位，_data4 填充）"] }
open(os.path.join(D,"article_data.json"),"w",encoding="utf-8").write(
    json.dumps(data,ensure_ascii=False,indent=2))
print("written article_data.json ", len(json.dumps(data,ensure_ascii=False)))
