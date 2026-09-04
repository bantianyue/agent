# -*- coding: utf-8 -*-
"""Agentic Kernels in Production（Baseten）编译 build——原样保留"""
import json

with open("_data_seed.json", "r", encoding="utf-8") as f:
    DATA = json.load(f)

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("✅ 写入 article_data.json")
