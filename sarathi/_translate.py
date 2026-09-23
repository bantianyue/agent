# -*- coding: utf-8 -*-
import sys, os, json, re, time
sys.path.insert(0, r"C:\Users\twfehh7\.workbuddy\skills\wechat-article-sop\scripts")
import llm_utils

ART = r"D:\06_Hermes\articles\sarathi"
items = json.load(open(os.path.join(ART, "_items.json"), encoding="utf-8"))

# collect translatable paragraphs: skip References / reporting-errors sections
paras = []
skip_sec = False
for it in items:
    if it["kind"] == "head":
        t = it["text"].strip().lower()
        skip_sec = t in ("references", "instructions for reporting errors")
        continue
    if skip_sec:
        continue
    if it["kind"] == "p":
        paras.append({"id": len(paras), "type": "text", "content": it["text"]})

json.dump(paras, open(os.path.join(ART, "_paras.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

TPATH = os.path.join(ART, "_translations.json")
done = {}
if os.path.exists(TPATH):
    done = json.load(open(TPATH, encoding="utf-8"))
    done = {int(k): v for k, v in done.items()}

TODO = [p for p in paras if p["id"] not in done]
LOG = os.path.join(ART, "_trans_log.txt")

def log(s):
    with open(LOG, "a", encoding="utf-8") as f:
        f.write("%s %s\n" % (time.strftime("%H:%M:%S"), s))

log("START total=%d todo=%d" % (len(paras), len(TODO)))

EXTRA = (
    "本任务是英文学术论文（SARATHI，LLM 推理加速）的中文翻译，额外要求：\n"
    "A. 通用技术术语一律译成中文并在首次出现时保留英文括注，例如：prefill=预填充(prefill)、decode=解码(decode)、"
    "chunked-prefills=分块预填充、chunk=分块、batch=批次、batch size=批大小、throughput=吞吐、"
    "pipeline bubble=流水线气泡、tensor parallelism=张量并行、pipeline parallelism=流水线并行、"
    "micro-batch=微批、sequence length=序列长度、KV cache=KV 缓存、arithmetic intensity=算术强度、"
    "memory-bound=内存受限、compute-bound=计算受限、iteration-level scheduling=迭代级调度、"
    "tile quantization=分块量化、attention=注意力、FFN=前馈网络、latency=延迟。\n"
    "B. 数学记号转成纯文本可读形式，禁止输出反斜杠命令与下加上标源码："
    "W^{Q} → W(Q)、W_{o} → W(o)、H_{2} → H2、m_{kv} → m(kv)、M_{G} → M(G)、M_{S} → M(S)、"
    "PB_{1} → PB1、q_{i} → q(i)、P:D=C/(B-1) 保留、O(n^{2}) → O(n²)、[B,L,H] 保留方括号写法、"
    "200 \\times → 200 倍、1.33 \\times → 1.33 倍。数字倍率统一用「X 倍」或「X×」表达。\n"
    "C. 不要写「本文」「我们」「这篇论文」等自称，也不要写「原文」「原作者」；直接陈述论文的技术内容。\n"
    "D. 保持段落完整，不要合并或拆分段落，不要加小标题。\n"
)

CHUNK = 10
for i in range(0, len(TODO), CHUNK):
    batch = TODO[i:i + CHUNK]
    try:
        out = llm_utils.translate_batch(batch, batch_size=CHUNK, system_extra=EXTRA)
        for o in out:
            done[o["id"]] = o["content"]
        json.dump({str(k): v for k, v in done.items()},
                  open(TPATH, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        log("chunk %d/%d ok (%d..%d)" % (i // CHUNK + 1, (len(TODO) + CHUNK - 1) // CHUNK,
                                         batch[0]["id"], batch[-1]["id"]))
    except Exception as e:
        log("chunk FAIL %d: %s" % (i, e))
log("DONE saved=%d" % len(done))
