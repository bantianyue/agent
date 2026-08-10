#!/usr/bin/env python3
"""gdn 补全翻译：翻译 _content.json 中缺失的 block (index 75+)。
分批落盘，中断可续。跳过 code 块。"""
import json, os, sys, time

DIR = r"D:/06_Hermes/articles/gdn-train-inference-mismatch"
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch, llm_call

content = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
trans_path = os.path.join(DIR, "_translations.json")
trans = json.load(open(trans_path, encoding="utf-8")) if os.path.exists(trans_path) else {}

# 待翻译：content 中所有 p/h2/h3/h4/li，排除已翻译的
def is_cn(s): return len([c for c in s if '\u4e00' <= c <= '\u9fff']) > len(s)*0.15

todo = []
for i, x in enumerate(content):
    t = x['type']
    if t not in ('p','h2','h3','h4','li'):
        continue
    if str(i) in trans and trans[str(i)]:
        continue
    txt = x.get('text', '').strip()
    if not txt:
        continue
    todo.append({"id": i, "type": "text", "content": txt})

print(f"待翻译补齐: {len(todo)} 块", flush=True)
if not todo:
    print("无缺失翻译")
    sys.exit(0)

def save():
    json.dump(trans, open(trans_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  [save] {len(trans)} 条", flush=True)

CHUNK = 6
for ci in range(0, len(todo), CHUNK):
    chunk = todo[ci:ci+CHUNK]
    print(f"🔄 批次 {ci//CHUNK+1}/{(len(todo)+CHUNK-1)//CHUNK} ({len(chunk)}块)...", flush=True)
    try:
        result = translate_batch(chunk, batch_size=6, system_extra="""这是博客长文（GDN 训练-推理数值不匹配与异步RL实验）。翻译为专业中文技术解读，要求：
1. 技术术语准确（batch invariance=批量不变性, bitwise parity=逐位一致, off-policy=离策略, logprob=对数概率, throughput=吞吐）。
2. 非论文精读，保留全部核心信息与实验结论，删冗余铺垫。
3. 图表标题 caption 本身如出现，翻译为中文。
4. 枚举/条目结构完整保留，不合并。""")
        for p in result:
            if p["type"] == "code":
                trans[str(p["id"])] = p["content"]
            else:
                trans[str(p["id"])] = p["content"]
    except Exception as e:
        print(f"  批次失败({str(e)[:50]})，逐段降级", flush=True)
        for p in chunk:
            if str(p["id"]) in trans and trans[str(p["id"])]:
                continue
            try:
                if p["type"] == "code":
                    trans[str(p["id"])] = p["content"]
                else:
                    trans[str(p["id"])] = llm_call(user_message=p["content"],
                        system_message="翻译为专业中文技术解读，术语准确，保留核心信息。",
                        temperature=0.2, stream=False)
            except Exception as e2:
                print(f"    ✗ [{p['id']}] {str(e2)[:40]}", flush=True)
    save()
    time.sleep(1)

print(f"✅ 翻译补齐完成，共 {len(trans)} 条")
