#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手动 build 路径：从 fxtwitter Draft.js 原文批量翻译成本地 _trans.json。
不新增流程：翻译一律走 llm_utils.translate_batch（既有脚本）。
"""
import json
import os
import sys

SKILL = r"C:\Users\twfehh7\.codex\skills\wechat-article-sop\scripts"
sys.path.insert(0, SKILL)
from llm_utils import translate_batch  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SKIP = {"atomic"}

TERMS = """术语统一（务必照此翻译）：tensor=张量, model weights=模型权重, activations=激活值,
layer=层, tensor parallelism=张量并行, pipeline parallelism=流水线并行, expert parallelism=专家并行,
replica=副本, all-reduce=all-reduce（全规约）, pipeline bubble=流水线气泡, bandwidth=带宽,
latency=延迟, throughput=吞吐, bias=偏置, runtime=运行时, serving=推理服务, rank=rank,
KV cache=KV cache, attention=注意力, weights partition=权重分片, peak=峰值。
函数名/类名/变量名/命令行/数值表达式一律保留原文不翻译。
禁止使用中文长破折号「——」和英文 em dash，改用逗号或冒号。
不要写「原文」「本文」「这篇文章」等元引用，不要写「编者注」。"""

CAPTIONS = {
    "cap01": "The vLLM document question-answering example shows document splitting, retrieval, and answer generation. It loads web documents and does not implement this illustration's upload interface or citation requirement.",
    "cap02": "In vLLM, Worker.determine_available_memory() profiles memory use and calculates the remaining KV-cache budget. Actual allocations depend on the model, runtime, input lengths, and concurrency: the number of requests active at once.",
    "cap03": "Replicas can add capacity for more questions when each complete model fits. Model parallelism can help a selected model fit, or improve performance in a suitable setup. Neither arrangement establishes a speedup without measurements.",
    "cap05": "GPU 1 initially waits for GPU 0. Idle intervals are called pipeline bubbles.",
}


def main():
    raw = json.load(open(os.path.join(HERE, "_src_tweet.json"), encoding="utf-8"))
    art = raw["tweet"]["article"]
    blocks = art["content"]["blocks"]
    items = []
    for i, b in enumerate(blocks):
        if b["type"] in SKIP:
            continue
        txt = b.get("text", "").strip()
        if not txt:
            continue
        items.append({"id": i, "type": "text", "content": txt})
    for k, v in CAPTIONS.items():
        items.append({"id": k, "type": "text", "content": v})

    print(f"待翻译：{len(items)} 段（正文 {len(items) - len(CAPTIONS)} + 图注 {len(CAPTIONS)}）")
    out = translate_batch(items, batch_size=6, system_extra=TERMS)
    res = {str(o["id"]): o["content"] for o in out}
    json.dump(res, open(os.path.join(HERE, "_trans.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    missing = [str(i["id"]) for i in items if not res.get(str(i["id"]))]
    print(f"完成 {len(res)} 条；空译文 {missing}")
    # 抽查残留英文比例
    bad = []
    import re
    for k, v in res.items():
        zh = len(re.findall(r"[\u4e00-\u9fff]", v))
        if zh < 5:
            bad.append((k, v[:60]))
    print("疑似未翻译：", bad)


if __name__ == "__main__":
    main()
