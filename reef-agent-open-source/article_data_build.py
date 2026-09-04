# -*- coding: utf-8 -*-
"""Reef 开源 X Article 标准模板 build —— v2 图按语义挂载"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
tr=json.load(open(os.path.join(_article_dir,"_trans.json"),encoding="utf-8"))
codes=json.load(open(os.path.join(_article_dir,"_codes.json"),encoding="utf-8"))
T={int(k):v for k,v in tr.items()}
def C(block_idx):
    m=[c for c in codes if c['block']==block_idx][0]
    return (f"__CODE__{m['lang']}::" if m['lang'] else "__CODE__") + m['code']

DATA = {
  "title": "🌊 Reef 开源：把推理服务器变成持续自我改进的 Agent（有状态推理基础设施）",
  "summary": [
    {"key":"动机","body":"RSI（递归自我改进）热度落地前开源 Reef——为 Agent 线上持续自我改进提供生产级基础设施。"},
    {"key":"核心","body":"基础设施端到端掌控三件套：经验、完整 Agent（模型+harness）、更新；Reef 用有状态推理打通三者。"},
    {"key":"方法","body":"持续学习方法沿三维度组织（学习信号/经验获取/演化目标），由模块化 learning recipe 在同一基础设施上表达。"},
  ],
  "lead": [
    "在围绕 RSI（递归自我改进）的热潮完全落地前写下本文，把 **Reef** 开源——一套让 Agent 在线上 Serving 的同时不断自我改进的**有状态推理基础设施**。",
    "本文为 X 博主 Ao Qu 的开源公告长文（全中文），覆盖动机、三要素、架构三能力与开箱配置示例，**8 张原图 + 全部示例代码保留**。",
  ],
  "sections": [
    {"type":"h2","title":"一、为什么持续自我改进需要新基础设施","paras":[
      T[4],
      T[5],
      T[6],
      T[7],
      T[8],
    ],"fig_after":{0:[{"src":"fig01.jpg","caption":"图1：从顺序流水线到持续进化环"}]}},
    {"type":"h2","title":"二、开源 Reef：让它成为现实（RSI 之前）","paras":[
      T[1],
      T[2],
    ],"fig_after":{1:[{"src":"fig03.jpg","caption":"图2：Reef 基础设施总览（掌控经验/Agent/更新）"}]}},
    {"type":"h2","title":"三、基础设施要拥有三件事","paras":[
      T[10],
    ]},
    {"type":"h3","title":"1) 掌控经验——学习建立在实时服务之上","paras":[
      T[12],
      T[13],
      C(17),
      T[14],
      C(19),
      T[15],
    ],"fig_after":{5:[{"src":"fig02.jpg","caption":"图3：标准推理端点；/reef/report 把反馈回流"}]}},
    {"type":"h3","title":"2) 掌控整个 Agent——模型与 harness 都要演化","paras":[
      T[17],
      T[18],
      T[19],
      C(25),
      T[20],
      T[21],
      T[22],
    ],"fig_after":{5:[{"src":"fig04.jpg","caption":"图4：Reef 把模型与 harness 一起演化"}]}},
    {"type":"h3","title":"3) 掌控更新——已演化版本被评估与版本化","paras":[
      T[24],
      T[25],
      T[26],
    ],"fig_after":{2:[{"src":"fig05.jpg","caption":"图5：仅追加发布链，compare-and-swap 推进发布头"}]}},
    {"type":"h2","title":"四、Reef 中的持续自我改进方法","paras":[
      T[28],
      T[29],
      T[30],
      "· " + T[31],
      "· " + T[32],
      "· " + T[33],
    ],"fig_after":{0:[{"src":"fig06.jpg","caption":"图6：方法 zoo 沿三维区分"}]}},
    {"type":"h3","title":"用 learning recipe 表达不同方法","paras":[
      T[34],
      "**配置示例（serve.yaml）——插一个演化 recipe：**",
      C(44),
      T[35],
      C(46),
    ]},
    {"type":"h3","title":"两个走截然不同路线的例子","paras":[
      T[36],
    ],"fig_after":{0:[{"src":"fig07.jpg","caption":"图7：示例一架构示意"},{"src":"fig08.jpg","caption":"图8：示例二架构示意"}]}},
    {"type":"h2","title":"五、结论","paras":[
      T[38],
      T[39],
      T[40],
    ]},
  ],
  "conclusion": [
    "Reef 把「推理服务器」从流水线末端重铸为**有状态的学习者**：凡是线上调用与反馈都结构化存成经验流，既可评估，也能离线/在线训练后推回模型或 harness 的新版本。",
    "不用把 Agent 想成静态产物：配置一个 learning recipe，插上 serve.yaml，推理服务就在使用中持续演化。开源地址与贡献者名单见原文。",
  ],
  "reference_url": "https://x.com/ao_qu18465/status/2094867930081337730",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
toti=sum(len(s['paras']) for s in DATA['sections'])
figs=sum(len(v) for s in DATA['sections'] for v in s.get('fig_after',{}).values() if isinstance(v,list))
print(f"OK {len(DATA['sections'])} sections, {toti} paras, {figs} figs")
