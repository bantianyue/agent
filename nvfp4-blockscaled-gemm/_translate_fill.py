#!/usr/bin/env python3
"""nvfp4 补全翻译：翻译缺失 block (120+)，分批落盘。"""
import json, os, sys, time

DIR = r"D:/06_Hermes/articles/nvfp4-blockscaled-gemm"
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch, llm_call

content = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
trans_path = os.path.join(DIR, "_translations.json")
trans = json.load(open(trans_path, encoding="utf-8")) if os.path.exists(trans_path) else {}

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
    todo.append({"id": i, "type": "text" if t != 'code' else 'code', "content": txt})

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
        result = translate_batch(chunk, batch_size=6, system_extra="""这是 CUDA/GPU 内核优化教程（NVFP4 block-scaled GEMM 在 Blackwell GPU 上的优化）。
翻译为专业中文技术解读，要求：
1. CUDA/sageite 术语保留或专业翻译（threadblock=线程块, warp=线程束, swizzling=交错, epilogue=尾声/输出阶段, bank conflict=银行冲突, tensor core=张量核心, TMA, cluster, MMA, autotune=自动调优）。
2. 代码块保留原文不翻译。
3. 非论文精读，保留全部技术细节与优化步骤。
4. 枚举/步骤结构完整保留。""")
        for p in result:
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
                        system_message="翻译为专业中文技术解读（CUDA内核优化），术语准确，保留技术细节。", temperature=0.2, stream=False)
            except Exception as e2:
                print(f"    ✗ [{p['id']}] {str(e2)[:40]}", flush=True)
    save()
    time.sleep(1)

print(f"✅ 翻译补齐完成，共 {len(trans)} 条")
