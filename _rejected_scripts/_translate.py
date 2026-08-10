#!/usr/bin/env python3
"""modular-ttt 全量翻译（精简编译：跳过 Related Work），分批落盘防进程死亡丢数据。

每翻译一批立即写 _translations.json，中断可续翻、已完成批次不丢。
"""
import json, os, sys, time

DIR = r"D:/06_Hermes/articles/modular-ttt"
sys.path.insert(0, r"C:/Users/twfehh7/AppData/Local/hermes/skills/content-creation/wechat-article-sop/scripts")
from llm_utils import translate_batch, llm_call

c = json.load(open(os.path.join(DIR, "_content.json"), encoding="utf-8"))
blocks = c["blocks"]

trans_path = os.path.join(DIR, "_translations.json")
trans = json.load(open(trans_path, encoding="utf-8")) if os.path.exists(trans_path) else {}
# 在 lru_cache 基线：llm_utils 的 _translate_cache 是进程内, 但我们可以用已有的 trans 判断
 
SKIP_BLOCKS = set(range(8, 14))  # Related Work 精简跳过

# 组装待翻译段（含 abstract 单独处理）
todo_blocks = []
for i, x in enumerate(blocks):
    if i in SKIP_BLOCKS:
        continue
    if not x.get("text", "").strip():
        continue
    todo_blocks.append((i, x))
# abstract
todo_blocks.append((-1, {"type": "p", "text": c["abstract"]}))

def save():
    json.dump(trans, open(trans_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"  [save] 已落盘 {len(trans)} 条翻译")

# 需要翻译的（无缓存）
todo = [{"id": i, "type": "code" if x["type"] == "code" else "text", "content": x.get("text", "").strip()}
        for i, x in todo_blocks if str(i) not in trans]
print(f"需翻译: {len(todo)} 段 (总 {len(todo_blocks)})")

if not todo:
    print("全部已翻译")
    sys.exit(0)

# 按 CHUNK=6 分批，每批落盘一次（modular 公式密集，用小批）
CHUNK = 6
for ci in range(0, len(todo), CHUNK):
    chunk = todo[ci:ci+CHUNK]
    print(f"🔄 批次 {ci//CHUNK+1}/{(len(todo)+CHUNK-1)//CHUNK}，共 {len(chunk)} 段...", flush=True)
    try:
        result = translate_batch(chunk, batch_size=8, system_extra="""这是 arXiv 论文（TTT/Test-Time Training 序列建模）。请翻译为专业中文技术解读。要求：
1. 公式 \\(...\\) LaTeX 原样保留，不翻译内部内容。
2. 技术术语专业翻译（inner learner=内学习器, fast weights=快速权重, test-time training=测试时训练）。
3. 精简编译风格：保留核心信息，删冗余背景铺垫。
4. Figure/Table/Algorithm 前缀翻译为"图/表/算法"，caption 内容翻译。
5. 枚举/条目结构完整保留。""")
        for p in result:
            key = str(p["id"])
            trans[key] = p["content"]
        save()
    except KeyError as e:
        # type=code 原样保留
        for p in chunk:
            key = str(p["id"])
            if p["type"] == "code":
                trans[key] = p["content"]
        save()
        print(f"  ⚠️ KeyError({e})，code 段已原样保留")
    except Exception as e:
        print(f"  ❌ 批次 {ci//CHUNK+1} 失败: {e}")
        # 该批整体失败则逐段降级
        for p in chunk:
            key = str(p["id"])
            if key in trans:
                continue
            try:
                if p["type"] == "code":
                    trans[key] = p["content"]
                else:
                    trans[key] = llm_call(user_message=p["content"], system_message="翻译为中文技术解读，LaTeX 公式原样保留，专业术语准确翻译。", temperature=0.2, stream=False)
                save()
                print(f"    ✓ [{key}] 逐段翻译完成")
            except Exception as e2:
                print(f"    ✗ [{key}] 失败: {e2}")
        # 每个 chunk 结束后停顿，降低流控风险
    time.sleep(1)

print(f"✅ 翻译全部完成，共 {len(trans)} 条，已写回 {trans_path}")
