# -*- coding: utf-8 -*-
"""再生-2：分块翻译（占位符保护），产出 _regen_zh.json。"""
import sys, json, re, time, os

sys.path.insert(0, r"C:/Users/twfehh7/.codex/skills/wechat-article-sop/scripts")
from llm_utils import llm_call, TRANSLATE_PROMPT, load_llm_config  # type: ignore

BASE = r"D:/06_Hermes/articles/amd-mi450-lds-opt"

EXTRA = """
本任务：把 AMD ROCm 博客《A Deep Dive into LDS Optimizations on AMD Instinct MI450 GPUs》全文译成中文。
硬性要求：
1. 占位符形如 ？0？、？1？、？2？，代表行内代码/变量高亮。必须原样保留，数量、顺序、位置都不得改变，不得翻译、不得增删。
2. 禁止中文长破折号「——」和单独破折号「—」，改用「，」「：」「，即」或括号。
3. 技术专名保留英文：LDS、GEMM、WMMA、TDM、Triton、Gluon、layout、warp、lane、swizzle、bank conflict、ctaLayout、PartitionedSharedLayout、ds_load_tr、ds_load_b128、num_partitions、num_groups、kernel、tile、register、cycle 等。
4. 图注以「图N：」开头（中文冒号），N 与原文 Figure 编号一致；图注里的变量高亮占位符照旧保留。
5. 术语首次出现时给中文并括注英文，例如：分区冲突（partition conflict）、转置加载（transposed load）。
6. 纯数字/符号块不需要翻译。
7. «B» 与 «/B» 是加粗标记，«I» 与 «/I» 是斜体标记，必须成对原样保留，并用它们包住对应的中文译文；标记本身不要翻译、不要增删、顺序不变。
8. 只输出 JSON 数组，元素为 {"id": 数字, "type": "text", "content": "中文译文"}，不要任何解释。
"""

SYS = TRANSLATE_PROMPT + "\n---\n" + EXTRA

blocks = json.load(open(f"{BASE}/_regen_blocks.json", encoding="utf-8"))
todo = [b for b in blocks if re.search(r"[A-Za-z]{2,}", re.sub(r"？\d+？", "", b["txt"]))]
print("todo blocks:", len(todo), "chars:", sum(len(b["txt"]) for b in todo), flush=True)
cfg = load_llm_config()
print("model:", cfg.get("model"), "base:", cfg.get("base_url"), flush=True)


def batchify(items, budget=8500):
    cur, n = [], 0
    for b in items:
        if cur and n + len(b["txt"]) > budget:
            yield cur
            cur, n = [], 0
        cur.append(b)
        n += len(b["txt"])
    if cur:
        yield cur


def parse_json_array(text):
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    try:
        return json.loads(t)
    except Exception:
        pass
    m = re.search(r"\[\s*\{.*\}\s*\]", t, re.S)
    if m:
        return json.loads(m.group(0))
    raise ValueError("no JSON array in output: " + t[:200])


def ph_seq(s):
    return re.findall(r"？\d+？|«/?[BI]»", s)


def save():
    json.dump({str(k): v for k, v in out.items()},
              open(f"{BASE}/_regen_zh.json", "w", encoding="utf-8"), ensure_ascii=False)


out = {}
if os.path.exists(f"{BASE}/_regen_zh.json"):
    out = {int(k): v for k, v in json.load(open(f"{BASE}/_regen_zh.json", encoding="utf-8")).items()}
    print("resume: already", len(out), flush=True)

batches = list(batchify(todo))
for bi, batch in enumerate(batches, 1):
    batch = [b for b in batch if b["i"] not in out]
    if not batch:
        print(f"批次 {bi}/{len(batches)} 已缓存，跳过", flush=True)
        continue
    payload = json.dumps(
        [{"id": b["i"], "type": "text", "content": b["txt"]} for b in batch], ensure_ascii=False
    )
    t0 = time.time()
    print(f"批次 {bi}/{len(batches)}：{len(batch)} 块 {len(payload)} 字符 ...", flush=True)
    try:
        res = llm_call(user_message=f"翻译：{payload}", system_message=SYS, temperature=0.2, stream=False)
        arr = parse_json_array(res)
        got = {int(x["id"]): x["content"] for x in arr if "id" in x and "content" in x}
        bad = []
        for b in batch:
            if b["i"] not in got:
                continue
            zh = str(got[b["i"]]).strip()
            if ph_seq(zh) == ph_seq(b["txt"]):
                out[b["i"]] = zh
            else:
                bad.append(b["i"])
        miss = [b["i"] for b in batch if b["i"] not in got]
        print(f"  完成 {len(got)}/{len(batch)}，缺 {miss}，占位符异常 {bad}，用时 {time.time()-t0:.0f}s", flush=True)
    except Exception as e:
        print("  批次失败:", str(e)[:200], flush=True)
    save()

need = [b for b in todo if b["i"] not in out]
print("逐块补译:", len(need), flush=True)
for b in need:
    try:
        res = llm_call(
            user_message="翻译：\n" + b["txt"],
            system_message=SYS + "\n只输出译文本身，不要 JSON、不要解释。占位符 ？N？ 原样保留。",
            temperature=0.2,
            stream=False,
        )
        zh = res.strip()
        if ph_seq(zh) == ph_seq(b["txt"]):
            out[b["i"]] = zh
        else:
            fixed = re.sub(r"？\d+？|«/?[BI]»", lambda m, it=iter(ph_seq(b["txt"])): next(it, m.group(0)), zh)
            if ph_seq(fixed) == ph_seq(b["txt"]):
                out[b["i"]] = fixed
            elif re.findall(r"？\d+？", zh) == re.findall(r"？\d+？", b["txt"]):
                out[b["i"]] = re.sub(r"«/?[BI]»", "", zh)
                print("  丢弃强调标记 idx=", b["i"], flush=True)
            else:
                print("  兜底失败 idx=", b["i"], repr(zh[:60]), flush=True)
    except Exception as e:
        print("  逐块失败 idx=", b["i"], str(e)[:120], flush=True)
    save()

print("最终译文块数:", len(out), "/", len(todo), flush=True)
