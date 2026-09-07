# -*- coding: utf-8 -*-
# 组装器: 分块构造 article_data 后 dump 成 article_data.json (渲染真相源)
# 数据本身在 _content_part1.py / _content_part2.py 内, 每块严格 python 合法; 合并后校验再落盘。
import json, importlib.util, sys

parts=["_content_part1","_content_part2"]
DATA={"title":None,"reference_url":None,"summary":None,"lead":None,"sections":[],
      "conclusion":None,"tables":[]}
for p in parts:
    spec=importlib.util.spec_from_file_location(p, __file__.rsplit("/",1)[0]+"/"+p+".py")
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    blk=m.DATA
    if DATA["title"] is None:
        DATA["title"]=blk["title"]; DATA["reference_url"]=blk["reference_url"]
        DATA["summary"]=blk["summary"]; DATA["lead"]=blk["lead"]
    DATA["sections"].extend(blk.get("sections",[]))
    if "conclusion" in blk: DATA["conclusion"]=blk["conclusion"]

assert DATA["title"] and DATA["sections"] and DATA["conclusion"]
out=__file__.rsplit("/",1)[0]+"/article_data.json"
json.dump(DATA, open(out,"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"assembled {len(DATA['sections'])} sections -> {out}")
