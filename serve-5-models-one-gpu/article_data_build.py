# -*- coding: utf-8 -*-
"""Superlinked IE 单GPU服务5模型 X Article 标准模板 build"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
tr=json.load(open(os.path.join(_article_dir,"_trans.json"),encoding="utf-8"))
codemap=json.load(open(os.path.join(_article_dir,"_codes.json"),encoding="utf-8"))
T={int(k):v for k,v in tr.items()}
def C(block_idx):
    m=codemap[str(block_idx)]
    return f"__CODE__{m['lang']}::" + m['code'] if m['lang'] else "__CODE__"+m['code']

DATA = {
  "title": "🖥️ 一张 GPU 同时服务 5 个模型：开源 Superlinked IE 如何终结多模型碎片化",
  "summary": [
    {"key":"问题","body":"真实 AI 流水线跑多个小模型，但 vLLM/TEI/自定义服务各自为政，给每模型一块独立 GPU 浪费严重。"},
    {"key":"方案","body":"开源 SIE 把整块 GPU 当成共享池：模型按需加载/卸载、单一共享队列、按计算成本批处理、随负载扩缩容。"},
    {"key":"机制","body":"SIE 用 extract/score/generate 三个原语统一 100+ 模型；洪水保险理赔 5 阶段跑在单个共享集群上。"},
  ],
  "lead": [
    "真实 AI 流水线很少只跑单一模型。**一个解析文档、下一个提取字段、第三个重排搜索、视觉模型读图、最终模型负责生成**。这篇 X 长文讲的是：如何在一块 GPU 上用一套服务层，同时把 SLM、OCR、NER、重排序器、目标检测器一起供起来。",
    "本文为 akshay_pachaar 的长文全中文编译，讲透「为什么小模型流水线会碎片化」「标准服务工具的坑」，再给开源 **Superlinked Inference Engine（SIE）** 的解法，图文全保留。",
  ],
  "sections": [
    {"type":"h2","title":"为什么小模型流水线才是趋势","paras":[
      T[2],
      T[3],
      T[4],
      T[5],
      T[6],
      T[7],
      T[8],
      T[9],
      T[10],
      T[11],
      "减速的钱回来了：**你靠换小模型省下的成本，可能被它的服务方式加倍吐回去。**",
    ],"fig_after":{4:[{"src":"fig01.jpg"}]}},
    {"type":"h2","title":"多模型流水线中的服务工具","paras":[
      T[27],
      T[28],
      "两个常见例子是 **vLLM** 和 **TEI**：",
      T[30],
      T[31],
      T[32],
      T[33],
      T[34],
      T[36],
      T[37],
    ],"fig_after":{7:[{"src":"fig02.jpg"}]}},
    {"type":"h3","title":"洪水理赔：一个五模型流水线的样例","paras":[
      T[38],
      T[39],
      T[40],
    ],"fig_after":{2:[{"src":"fig03.jpg","caption":"图3：一个理赔走完五个阶段"}]}},
    {"type":"h2","title":"标准服务工具的问题","paras":[
      T[42],
      T[43],
      T[45],
    ],"fig_after":{1:[{"src":"fig04.jpg"}]}},
    {"type":"h3","title":"路线一：给每个模型一块自己的 GPU","paras":[
      T[47],
      T[48],
      T[49],
      T[51],
      T[52],
      T[53],
      T[54],
      T[55],
      T[56],
      T[57],
      "于是两难出现：**为了省上模型的钱才换小模型，结果每加一个新的小模型任务，硬件数量反而跟着加**。",
    ],"fig_after":{3:[{"src":"fig05.jpg"}],7:[{"src":"fig06.jpg"}],9:[{"src":"fig07.jpg"}]}},
    {"type":"h3","title":"路线二：多个模型塞进一块 GPU","paras":[
      T[62],
      T[63],
      T[64],
      T[65],
      T[66],
      T[67],
      "现在把 vLLM、TEI 和自定义解析/提取/视觉服务器全打包到同一块 GPU——",
      "· " + T[70],
      "· " + T[71],
      T[72],
      T[73],
      T[74],
      T[75],
      T[76],
    ],"fig_after":{1:[{"src":"fig08.jpg"}],6:[{"src":"fig09.jpg"}],7:[{"src":"fig10.jpg"}],13:[{"src":"fig11.jpg"}]}},
    {"type":"h2","title":"选择：专用 GPU 还是共享 GPU","paras":[
      T[78],
      T[79],
      T[80],
      T[81],
      T[82],
      T[83],
    ],"fig_after":{5:[{"src":"fig12.jpg","caption":"图：走共享 GPU 路线 / 你云里的 SIE"}]}},
    {"type":"h2","title":"小模型服务栈真正需要什么","paras":[
      T[86],
      "**① 广度**：服务器得在一个 API 后面同时跑嵌入、重排序、OCR、视觉、提取与生成。",
      "**② GPU 利用率**：要把不同长度的请求打包进一次处理而不浪费算力，引擎必须为每种架构控制批处理与注意力路径。",
      "**③ 模型内存跟随流量**：流量挪动时能加载/驱逐模型，让忙碌的常驻、空闲的让位。",
      "**④ 生产级行为**：路由、自动扩缩容、监控、GPU 池——不能只像个裸引擎；加副本应是配置变更而非重新部署。",
      "如今这些都得开发者从零搭，数月定制工程——因为不同模型家族底层差异巨大：",
      T[93],
      T[94],
      T[95],
      T[96],
    ],"fig_after":{1:[{"src":"fig13.jpg"}],3:[{"src":"fig14.jpg"}]}},
    {"type":"h2","title":"开源解法：Superlinked Inference Engine","paras":[
      T[99],
      T[100],
      T[101],
      T[102],
    ],"fig_after":{3:[{"src":"fig15.jpg"}]}},
    {"type":"h3","title":"三个原语吃掉五类工作","paras":[
      "面向洪水理赔这类多模型流水线，SIE 把「负载类型」折叠成 3 个功能原语：",
      "**extract（提取）**：一个接口下干三种活——把表单/保单转成干净 Markdown（docling）、抽取姓名/单号/日期等字段（GLiNER）、在图上做视觉检测。底层模型各异，服务接口无需且不和。",
      T[106],
      T[107],
      T[110],
      "API 只是可见部分：真正的工作在底下，SIE 要在共享 GPU 上实际协调这些模型。",
    ]},
    {"type":"h3","title":"底层发生的五件事","paras":[
      "**1. 模型仅在需要时加载**：请求实际需要才加载模型；GPU 内存受限时，驱逐最近最少使用的模型。GPU 不再是某模型的永久私有财产，而是一个可共享的池。",
      "**2. 单一队列统筹所有工作**：独立进程时各模型只看自己的请求；SIE 把工作放进共享队列——网关发布请求、worker 就绪即拉。服务层得以跨模型看到工作负载。",
      "**3. 批处理遵循计算成本**：按请求的预估计算成本分组，而非固定数量一堆——免得短输入被 pad 到长输入长度、GPU 大量时间花在填充上。",
      "**4. 共享服务器随工作负载扩展**：网关 + worker 层包在模型运行时外，迁移到生产也不断档；按需加/减 worker，还带 K8s 基建、监控、AWS/GCP 部署。",
      "**5. 模型自带服务配置**：支持新模型不止下载权重，不同架构有不同内存/批处理/精度要求；SIE 的模型目录（当前 112 个）把服务配置打包，按名引用即用。",
      "把上面几件事叠在一起，得到的一台引擎大致就是这样：一个能同时容纳多种任务形状、共享同一块 GPU、并把批量、路由与扩缩替你管好的服务层。",
    ],"fig_after":{0:[{"src":"fig16.jpg"}],1:[{"src":"fig17.jpg"}],2:[{"src":"fig18.jpg"}],3:[{"src":"fig19.jpg"}],4:[{"src":"fig20.jpg"}],5:[{"src":"fig21.jpg"}]}},
    {"type":"h2","title":"用真实文档验证：一单洪水理赔走一遍","paras":[
      "把上述架构放到真实场景。材料刻意弄得杂乱、来自公共领域，用于给流水线施压：损失证明表单、维修估价、保单文档、+ 实际洪灾照片一批。",
      T[153],
      "五个模型没有一个做同样的事——碎片化下要五套服务设置，SIE 用一个共享集群跑这五个作业。",
    ],"fig_after":{2:[{"src":"fig22.jpg"}]}},
    {"type":"h3","title":"一个集群执行五个不同的作业","paras":[
      "落到真实启动，就是这个集群跑五个不同作业的样子——每阶段命中一个模型，都在同一端点、同一调度之内。",
      "先安装并启动服务器（serve 命令在 8080 端口拉起服务）：",
      C(182),
      "就绪后实例化客户端并指向运行中的服务器——**管道里每个阶段都走这同一个对象、同一个端点，无论它背后命中哪个模型**：",
      C(187),
    ],"fig_after":{0:[{"src":"fig23.jpg"}],1:[{"src":"fig24.jpg"}]}},
    {"type":"h2","title":"五阶段逐个执行","paras":[
      "每个阶段对应任务、模型与 SIE 端点，底层全部走 extract/score/generate 三个原语。",
      "**① 解析保单文档（extract / docling）**：把损失证明表、维修成本、保单转成干净的 Markdown，保留表格与布局。",
      "**② 提取索赔身份（extract / GLiNER）**：把 Markdown 里抽出姓名、损失日期、财产地址等字段——GLiNER 按你提供的标签做命名实体识别，无需预设模式。",
      "**③ 找保单条款（score / bge-reranker）**：保单很长，先按关键词重叠粗筛（“proof of loss”“signed”“60 days”），把最强候选送交叉编码器重排；score() 返回的是排序后的结果，顺序即答案。",
      "**④ 读损坏照片（extract / Grounding DINO 零样本）**：零样本目标检测在图像里找“standing water”“flooded room”等类别——模型从没为此练兵，只是拿到文本描述就地匹配。",
      "**⑤ 写审核结论（generate / Qwen3.5）**：把解析文档、结构化索赔、排序结果、照片分析攒成 context，一次生成最终审核——输出锁 JSON 模式，有固定结构。",
    ]},
    {"type":"h2","title":"自行运行：一份 GPU 或两份都行","paras":[
      T[186],
      T[187],
      T[188],
      "· " + T[189],
      "· " + T[190],
      T[191],
      T[192],
      T[194],
    ]},
    {"type":"h2","title":"实际应用的价值","paras":[
      T[200],
      T[201],
      T[202],
      T[203],
      T[204],
      T[205],
    ],"fig_after":{4:[{"src":"fig25.jpg"}]}},
    {"type":"p","title":"","paras":[
      T[207],
      "生产级多模型推理让单一 GPU 干五份活，成本与自由兼得。开源项目见 Superlinked GitHub（原始图、命令与完整仓库见参考链接）。",
    ]},
  ],
  "conclusion": [
    "一块 L4 能吃下好几个小模型的权重，真正的浪费不是容量，是**怎么协调它们**——给每模型一块独占 GPU 是按持有时间付钱、把空闲算力扔在那；而塞一起又面临内存不随流量分配、各自独立的队列与批处理无人统筹。",
    "Superlinked IE 把 GPU 当成一块活的共享池：按需加载与驱逐、单一共享队列、按计算成本分批、模型目录自带配置，再塞进生产级的扩缩容与监控里。结论一句话——**省到小模型只是开始，会共享 GPU 才能把省下来的钱真正落袋**。",
  ],
  "reference_url": "https://x.com/akshay_pachaar/status/2084992645966016757",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
# 图引用检查
import re
refs=[]
for s in DATA['sections']:
    for v in s.get('fig_after',{}).values():
        for fi in v: refs.append(fi['src'])
have=[f for f in os.listdir(_article_dir) if f.startswith('fig')]
missing=[r for r in refs if r not in have]
toti=sum(len(s['paras']) for s in DATA['sections'])
print(f"sections={len(DATA['sections'])} paras={toti} figs_ref={len(refs)} missing={missing if missing else '无'}")
