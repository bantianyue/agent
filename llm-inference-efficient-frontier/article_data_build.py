# -*- coding: utf-8 -*-
"""LLM Inference Efficient Frontier（Philip Kiely X Article）标准模板 build"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
tr=json.load(open(os.path.join(_article_dir,"_translations_full.json"),encoding="utf-8"))
# tr[i] = 中文译文（i 对应 _texts.json 索引）
# fig 文件已复制为 fig01.png fig02.png fig03.jpg fig04.jpg fig05.jpg

DATA = {
  "title": "🎯 LLM 推理的有效边界：管理权衡 vs 推动前沿的工程技术（含批量/并行/量化/投机解码/分离部署）",
  "summary": [
    {"key":"核心概念","body":"从经济学借「效率前沿」：推理工程有两类技术——在权衡中定位前沿点 vs 整体推动前沿外移。"},
    {"key":"权衡技术","body":"批量大小、并行策略（TP/EP/ADP）、量化：在延迟/吞吐/质量间取舍，前沿通常崎岖不平需扫描。"},
    {"key":"前沿技术","body":"内核优化、投机解码（EAGLE-3/DSpark/DFlash）、P/D 分离部署：整体提升性能，且常能叠加（硬件×软件=4倍）。"},
  ],
  "lead": [
    "LLM 推理也有一道「效率前沿」：最常见的是**延迟与吞吐（成本）的权衡**，也可以拿质量换吞吐（量化/蒸馏/剪枝）、拿智能换速度（推理等级）。engineer 能用的技术分两类——在权衡中把部署**移动**到前沿上某一点，或把**整个前沿推开**。",
    "本文是 X 博主 Philip Kiely 的同名长文全中文编译，以 GLM-5.3 / Kimi K3 做 agentic coding 且开启 KV cache 复用与 KV-aware 路由为假设场景，系统梳理批量、并行、量化、内核优化、投机解码、P/D 分离部署。",
  ],
  "sections": [
    {"type":"h2","title":"效率前沿：两类推理工程技术","paras":[
      tr["0"],
      tr["1"],
    ],"fig_after":{0:[{"src":"fig01.png","caption":"图1：AI 行业的「效率前沿」概念"}]}},
    {"type":"h3","title":"两类技术","paras":[
      tr["2"],
      "**第一类（在效率前沿上移动部署）**：" + tr["3"].lstrip(),
      "**第二类（推动整个前沿外移）**：" + tr["4"].lstrip(),
      tr["5"],
      tr["6"],
      tr["7"],
      tr["8"],
    ]},
    {"type":"h2","title":"管理权衡的技术","paras":[
      tr["10"],
      tr["11"],
    ]},
    {"type":"h3","title":"批量大小（Batch sizing）","paras":[
      tr["13"],
      tr["14"],
    ],"fig_after":{1:[{"src":"fig02.png","caption":"图2：批量大小对延迟 vs 吞吐的影响"}]}},
    {"type":"h3","title":"并行策略（Parallelism strategy）","paras":[
      tr["16"],
      tr["17"],
      tr["18"],
      tr["19"],
    ],"fig_after":{3:[{"src":"fig03.jpg","caption":"图3：并行策略对延迟/吞吐的影响"}]}},
    {"type":"h3","title":"量化（Quantization）","paras":[
      tr["21"],
      tr["22"],
    ]},
    {"type":"h2","title":"推动前沿的技术","paras":[
      tr["24"],
      tr["25"],
    ],"fig_after":{1:[{"src":"fig04.jpg","caption":"图4：整体推动前沿外移"}]}},
    {"type":"h3","title":"内核优化与运行时改进（Kernel optimization）","paras":[
      tr["27"],
      tr["28"],
    ]},
    {"type":"h3","title":"投机解码（Speculative decoding）","paras":[
      tr["30"],
      tr["31"],
    ]},
    {"type":"h3","title":"分离部署（P/D disaggregation）","paras":[
      tr["33"],
    ],"fig_after":{0:[{"src":"fig05.jpg","caption":"图5：预填充/解码分离部署"}]}},
    {"type":"h2","title":"结语","paras":[
      "本文提供了一个基础概览：**引擎工程师如何在「管理权衡」与「提升系统级性能」两类技术之间取舍**。要深入每一项技术，可读作者的开源书籍《Inference Engineering》。",
    ]},
  ],
  "conclusion": [
    "推理优化的本质是在「效率前沿」上做两件事：要么精调配置，在延迟、吞吐、质量、成本这条（往往崎岖不平的）曲线上定位到所需的点；要么用内核优化、投机解码、P/D 分离部署这类手段，把整条曲线向外推。",
    "两类技术并非对立——权衡术解决「当下怎么配置」，前沿术解决「能效边界能抬多高」；后者常能叠加（硬件×软件），是长期性价比的真正来源。",
  ],
  "reference_url": "https://x.com/philipkiely/status/2094916428076106029",
}

out_path = os.path.join(_article_dir, "article_data.json")
os.makedirs(_article_dir, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

# 校验
import re
toti=0
for s in DATA['sections']:
    toti+=len(s['paras'])
print(f"✅ 写入 {len(DATA['sections'])} sections, {toti} paras")
