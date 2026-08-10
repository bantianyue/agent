#!/usr/bin/env python3
"""modular-ttt 全量翻译（精简编译：跳过 Related Work）。"""
import json, os, sys, re

DIR = r"D:/06_Hermes/articles/modular-ttt"
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch

c = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
blocks = c["blocks"]  # list of {type, text}

# 已有的翻译（可能部分存在）
trans_path = os.path.join(DIR, "_translations.json")
trans = json.load(open(trans_path, encoding="utf-8")) if os.path.exists(trans_path) else {}

# 精简编译段选择：
# 跳过 Related Work [8-13]（block 8 是 h2 "2 Related Work", 9-13 是正文）
# 其它全部保留；fig block 的 caption 也要翻译（Figure 1/2 提取图注，Table/Algorithm 保留文字）
SKIP_BLOCKS = set(range(8, 14))  # Related Work

def seg_type(x):
    """返回 translate_batch 用的 type 与 content。"""
    t = x["type"]
    txt = x.get("text", "")
    if t == "code":
        return "code", txt
    if t == "fig":
        # captions: Figure/Table/Algorithm。Table/Algorithm 用文字转述，保留结构
        return "text", txt
    return "text", txt

# 构建批量输入
paras = []
for i, x in enumerate(blocks):
    if i in SKIP_BLOCKS:
        continue
    if not x.get("text", "").strip():
        continue
    typ, content = seg_type(x)
    if not content.strip():
        continue
    paras.append({"id": i, "type": typ, "content": content})

print(f"待翻译段数: {len(paras)} (blocks 总 {len(blocks)}, 跳过 Related Work 6块)")

# 跳过已翻译的（缓存续翻）
todo = [p for p in paras if str(p["id"]) not in trans]
print(f"还需翻译: {len(todo)} / 总 {len(paras)}")

if not todo:
    print("全部已翻译，无需重新翻译")
    sys.exit(0)

# 批量翻译（分块 fallback，translate_batch 内部已分批+落盘缓存）
result = translate_batch(todo, batch_size=8, system_extra="""这是 arXiv 论文（TTT/Test-Time Training 序列建模）。请翻译为专业中文技术解读。要求：
1. 公式 \\(...\\) LaTeX 原样保留，不翻译内部内容。
2. 技术术语专业翻译（如 inner learner=内学习器, fast weights=快速权重, test-time training=测试时训练）。
3. 精简编译风格：保留核心信息，删冗余背景铺垫。
4. final caption 的 "Figure N:", "Table N:", "Algorithm N:" 前缀翻译为"图 N:""表 N:""算法 N:"。
5. 枚举/条目结构（li/text 清单）完整保留，不得合并或减少数量。""")

# 合并进 trans
for p in result:
    key = str(p["id"])
    if p["type"] == "code":
        trans[key] = p["content"]  # 原文
    else:
        trans[key] = p["content"]

json.dump(trans, open(trans_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"翻译完成，共 {len(trans)} 条，已写回 {trans_path}")
