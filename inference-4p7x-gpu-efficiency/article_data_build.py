# -*- coding: utf-8 -*-
"""Decagon 4.7x GPU 推理效率 X Article 标准模板 build"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
d=json.load(open(os.path.join(_article_dir,"_all.json"),encoding="utf-8"))
tr={b['id']:b['zh'] for b in d['blocks']}

DATA = {
  "title": "📉 让最大推理负载 GPU 效率提升 4.7×：Decagon 的三大服务层改造",
  "summary": [
    {"key":"核心","body":"最大收益不来自单一优化，而在消除服务栈各层瓶颈——集群级 GPU 效率提升 4.7 倍，处理同等流量 GPU 小时减少约 80%。"},
    {"key":"举措1","body":"专用化 prefill 与 decode：换高显存 GPU + P/D 分离，靠更大批次、快速状态传输、拓扑匹配流量来抵消 GPU 间通信成本。"},
    {"key":"举措2·3","body":"突发流量可重分配（前置准入队列），扩容容量尽快可用（预取模型文件启动提速近半）。"},
  ],
  "lead": [
    "这篇文章来自客户支持 AI 公司 **Decagon**：告诉我们最大的收益**不是来自单个推理优化，而是持续找出一连串服务瓶颈**，最终让最大的计划内推理负载**集群级 GPU 效率提升 4.7 倍**。",
    "场景特点：请求是**突发式**到达、单请求延迟不关键、极看重「每 GPU 小时处理的 token 数」。基线是常规自动扩缩容部署。",
  ],
  "sections": [
    {"type":"h2","title":"基线问题：突发流量 + 常规扩缩容的结构性浪费","paras":[
      tr[4],
      "统计口径很严格：**整个扩缩容生命周期内的 GPU 小时**——包括启动、空闲容量、稳态处理与队列排空，不只看峰值。",
      tr[2],
    ],"fig_after":{1:[{"src":"fig01.jpg","caption":"图1：优化前后对比——常规自动扩缩容 → 高显存 GPU + 三项服务层的改动"}]}},
    {"type":"h2","title":"瓶颈一：让人等、贡献聊胜于无的 GPU 分工","paras":[
      tr[0],
      tr[1].replace("@DecagonAI","Decagon"),
    ]},
    {"type":"h3","title":"改造① 专用化 prefill 和 decode（P/D 分离）","paras":[
      tr[7],
      tr[8],
      "要在解耦后拿到提升，关键是三个细节：",
      "· **形成更大的批次**：P/D 在每组有足够并发工作把 GPU 打满时最有效——换更高 VRAM 的 GPU，就能更激进批处理、吃更大的提示块。",
      "· **保持状态传输快速**：prefill 会产出 decode 需要的一大块中间数据。早期构建缺运行时支持，**静默从点内 NVLink 回退到 TCP**——系统还能跑，但通信成了暗藏瓶颈。",
      "· **匹配拓扑与流量**：提示密集型负载适合 2P:1D（2 prefill : 1 decode），生成密集型偏好 1P:2D，用实测决定每类 worker 数量。",
    ]},
    {"type":"h2","title":"瓶颈二：突发流量卡在过载容器里","paras":[
      tr[13],
      tr[14],
      tr[15],
    ]},
    {"type":"h3","title":"改造② 让突发流量可重新分配——准入控制器 + 前置共享队列","paras":[
      "把原本堆在各 GPU 容器**内**的队列，移到容器**前**：",
      tr[17],
      tr[18],
    ],"fig_after":{0:[{"src":"fig02.jpg","caption":"图2：准入控制器把进不去的请求留在共享队列，可路由到新扩容的 worker"}]}},
    {"type":"h2","title":"瓶颈三：新扩容的容量「晚到」了","paras":[
      tr[20],
      tr[21],
    ]},
    {"type":"h3","title":"改造③ 让扩容容量更快投入使用","paras":[
      "突发里每多一分钟启动，请求就多排队一分钟；启动提速后，扩容的新 worker 才能更早接住积压请求。",
    ]},
    {"type":"h2","title":"结果：4.7× GPU 效率","paras":[
      tr[23],
      tr[24],
      tr[25],
    ]},
  ],
  "conclusion": [
    "Decagon 的结论很清醒：**高效推理是持续的瓶颈排查**，瓶颈会从一处挪到另一处——从批处理形成、内存压力，转移到状态传输、突发准入、工作节点启动。修好一个，往往暴露下一个。",
    "他们这一轮把「高显存 GPU」和「三项服务层改动」叠加，就在最大推理负载上换回 **4.7× 集群级 GPU 效率、处理同等流量 GPU 小时省 ~80%**。这些手法（P/D 分离 + 前置准入队列 + 预取启动）对任何突发式、事件驱动的推理负载都可复用。",
  ],
  "reference_url": "https://x.com/NicholasLiu77/status/2094832111945707546",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
toti=sum(len(s['paras']) for s in DATA['sections'])
figs=sum(len(s.get('fig_after',{}).get('0',[])) for s in DATA['sections'])
print(f"OK {len(DATA['sections'])} sections, {toti} paras, {figs} fig")
