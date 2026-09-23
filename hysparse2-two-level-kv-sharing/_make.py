# -*- coding: utf-8 -*-
"""解析 content*.txt 行文件 -> article_data.json（文本 DSL 模式）"""
import json, os, glob, sys

D = os.path.dirname(os.path.abspath(__file__))

G = '<strong style="color:#1a7f5a;">%s</strong>'
BL = '<span style="color:#0F4C81;">%s</span>'

TABLE1 = {"head": ["模型", "全注意力层数", "Heads (Q/KV)", "Head dim. (QK/V)"],
          "rows": [["Hybrid SWA", "9", "64/4", "192/128"],
                   ["HySparse", "5", "64/4", "192/128"],
                   ["HySparse2", G % "5", G % "64/1", G % "256/256"]]}

TABLE2 = {"head": ["任务", "Hybrid SWA", "HySparse", "HySparse2"],
          "rows": [
              [BL % "知识", "", "", ""],
              ["MMLU", "61.48", G % "64.48", "63.92"],
              ["MMLU-Redux", "63.96", G % "68.44", "67.50"],
              ["C-Eval", "65.08", "67.09", G % "67.90"],
              ["CMMLU", "67.41", G % "69.97", "69.90"],
              ["TriviaQA", "60.59", G % "60.67", "59.67"],
              [BL % "推理", "", "", ""],
              ["BBH", "60.14", "61.93", G % "64.29"],
              ["MMLU-Pro", "36.12", "35.74", G % "37.56"],
              ["MATH", G % "36.18", "36.14", "34.32"],
              ["DROP", "60.90", G % "63.78", "58.99"],
              ["GSM8K", G % "64.44", "64.14", "61.94"],
              ["ARC-C", "75.51", G % "79.18", "77.82"],
              ["HellaSwag", "79.38", "79.19", G % "79.54"],
              ["WinoGrande", "73.72", G % "74.19", "71.82"],
              [BL % "代码", "", "", ""],
              ["HumanEval+", G % "35.98", "34.76", "34.15"],
              ["MBPP+", G % "55.56", "52.65", "52.65"],
              ["Repo Code PPL 越低越好", "1.1578", "1.1588", G % "1.1570"],
              [BL % "长上下文", "", "", ""],
              ["RULER", "88.71", "84.89", G % "90.77"],
              ["NoLiMa", "30.13", "40.27", G % "49.76"]]}

TABLE3 = {"head": ["任务", "Block", "Token"],
          "rows": [
              [BL % "预训练", "", ""],
              ["BBH", G % "61.93", "60.70"],
              ["MMLU-Pro", "35.74", G % "36.97"],
              ["NoLiMa", G % "40.27", "38.43"],
              [BL % "长上下文（不超过 32k）", "", ""],
              ["RULER-v2", "49.56", G % "56.13"],
              ["MRCR-v2（2 needle）", "12.94", G % "21.08"],
              ["GraphWalks", "29.38", G % "34.92"]]}

TABLE4 = {"head": ["任务", "Gated SWA", "No SWA", "Forced SWA"],
          "rows": [
              [BL % "推理", "", "", ""],
              ["BBH", "62.23", "60.11", G % "62.25"],
              ["MMLU-Pro", G % "39.15", "37.19", "38.12"],
              ["MATH", G % "35.82", "33.82", "33.38"],
              ["DROP", G % "60.06", "58.94", "56.85"],
              ["GSM8K", G % "64.52", "60.35", "59.44"],
              ["ARC-C", G % "81.06", "79.01", "78.41"],
              ["HellaSwag", G % "79.85", "78.23", "78.42"],
              ["WinoGrande", "73.09", G % "73.95", "72.85"],
              [BL % "长上下文（不超过 32k）", "", "", ""],
              ["NoLiMa", "37.62", G % "38.37", "36.16"],
              ["RULER", "88.19", "84.55", G % "89.84"],
              ["RULER-v2", "53.66", "54.62", G % "55.98"],
              ["MRCR-v2", G % "27.66", "20.73", "22.67"],
              ["GraphWalks", "35.39", "36.48", G % "37.13"],
              ["LongPPL 越低越好", G % "6.8807", "7.1307", "6.9838"]]}

TABLE5 = {"head": ["任务", "不带 KV Bridging", "带 KV Bridging"],
          "rows": [
              ["MMLU", "72.68", G % "72.80"],
              ["TriviaQA", "73.32", G % "74.10"],
              ["BBH", G % "70.65", "69.57"],
              ["DROP", G % "71.37", "68.17"],
              ["GSM8K", G % "77.63", "76.65"],
              ["Repo Code PPL 越低越好", G % "1.1351", "1.1353"],
              ["RULER", G % "96.32", "96.01"],
              ["LongPPL 越低越好", "3.6053", G % "3.4202"]]}

TBL = {"table1": TABLE1, "table2": TABLE2, "table3": TABLE3,
       "table4": TABLE4, "table5": TABLE5}

SUMMARY = [
    {"key": "核心结论", "body": "两级 KV 共享让预填只跑半个模型。1M token 下预填 FLOPs 相对 Hybrid SWA 降 5.02 倍，KV cache 从 12.09 GB 压到 2.69 GB。"},
    {"key": "关键数据", "body": "轻量后训练后，MRCR-v2 与 RULER-v2 平均分相对 HySparse 分别提升 11.30 与 19.81 分；256k 时 RULER-v2 达 58.45，两个基线分别为 32.61 与 35.74。"},
    {"key": "方法创新", "body": "稀疏选择由块级改为 token 级，去掉独立 SWA 分支、把强制局部窗口并入稀疏选择，预填阶段因此不需要任何 cross-decoder 计算。"},
]

LEAD = [
    "多轮智能体的上下文膨胀主要来自工具返回：一次调用带回的检索结果或执行日志，往往比产生它的动作长得多，预填算力与 KV cache 双双被推高。",
    "小米 LLM-Core 的 HySparse2 把 YOCO 式跨层 KV 共享嵌进混合稀疏注意力，让 cross-decoder 的 KV cache 全部由 self-decoder 隐藏状态生成，预填只跑半个模型就能退出。",
]

CONCLUSION = [
    "两级 KV 共享真正改的是预填的经济性：cross-decoder 的 KV cache 全部由 self-decoder 隐藏状态生成，预填因此能在半程退出。",
    "代价也清楚，把独立 SWA 分支换掉、改让局部窗口强制进入稀疏选择，GSM8K 掉 5.08 分、MRCR-v2 掉 4.99 分；换来的是一层全注意力层就够构建预填 KV cache，1M token 下预填 FLOPs 相对 Hybrid SWA 降 5.02 倍，KV cache 从 12.09 GB 压到 2.69 GB，预填节点显存近乎减半。",
    "对做长上下文与智能体推理的人，可迁移的经验是把稀疏预算从块级换到 token 级：同样的注意力预算下，RULER-v2 涨 6.57 分、两 needle 检索涨 8.14 分。要不要跟着重排整个注意力结构，取决于预填是不是当前瓶颈。",
]


def main():
    S = []
    for fp in sorted(glob.glob(os.path.join(D, "content*.txt"))):
        with open(fp, encoding="utf-8") as f:
            for raw in f:
                line = raw.rstrip("\n").strip()
                if not line:
                    continue
                tag, _, body = line.partition(" ")
                if tag == "S#":
                    S.append({"type": "h2", "title": body.strip(), "paras": [], "fig_after": {}})
                elif tag == "H3":
                    S.append({"type": "h3", "title": body.strip(), "paras": [], "fig_after": {}})
                elif tag == "T":
                    S[-1]["paras"].append(body.strip())
                elif tag == "F":
                    name, _, cap = body.strip().partition("|")
                    i = max(0, len(S[-1]["paras"]) - 1)
                    S[-1]["fig_after"].setdefault(str(i), []).append(
                        {"src": name.strip(), "caption": cap.strip()})
                elif tag == "B":
                    S[-1]["table"] = json.loads(json.dumps(TBL[body.strip()]))
                else:
                    raise SystemExit("未知行前缀: " + line[:40])
    # 校验
    nfig = 0
    for s in S:
        for k, v in s["fig_after"].items():
            assert int(k) < len(s["paras"]), "fig_after 越界: %s key=%s paras=%d" % (s["title"], k, len(s["paras"]))
            nfig += len(v)
    data = {"title": "小米:HySparse2两级KV共享,预填算力降5倍、长文检索涨19.8分",
            "summary": SUMMARY, "lead": LEAD, "sections": S,
            "conclusion": CONCLUSION,
            "reference_url": "https://arxiv.org/abs/2609.26368"}
    out = os.path.join(D, "article_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    body = sum(len(p) for s in S for p in s["paras"])
    print("sections=%d paras=%d figs=%d tables=%d bodychars=%d"
          % (len(S), sum(len(s["paras"]) for s in S), nfig,
             sum(1 for s in S if "table" in s), body))


main()
