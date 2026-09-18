#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Kimi K3 Performance Optimizations in vLLM -> 中文编译（step2a 手工模式）。"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()


def _code(i):
    """从 blocks.jsonl 取第 i 段代码块，原文原样保留、不翻译。"""
    blocks = [json.loads(l) for l in open(os.path.join(_article_dir, "blocks.jsonl"), encoding="utf-8") if l.strip()]
    codes = [b["content"] for b in blocks if b.get("type") == "code"]
    return "__CODE__" + codes[i]


DATA = {
 "title": "Kimi K3 在 vLLM 中的性能优化：通往 2.8 倍吞吐",
 "summary": [
  {"key": "端到端结果", "body": "8K/1K 负载、TP8、8 token DSpark 投机下，相比 v0.27.1，延迟降低 56%–60%，吞吐提升 2.2–2.8 倍，TTFT 降低 72%–85%。"},
  {"key": "四个代表性改动", "body": "自适应调度预算把空闲的 token 额度用起来；内部 KDA 前缀检查点省掉一次整模型前向；零拷贝混合批去掉 6 次 index_select 与 2 次 index_copy；MXFP4 收尾融进 latent tail kernel。"},
  {"key": "状态与并行", "body": "ReplaySSM 用重建替代存储，同等 46.48 GiB 缓存预算下有效容量提升 10.97%；PD 分离要同时搬 MLA KV 与 KDA 状态；DCP 把复制的 latent KV 沿序列切开。"}
 ],
 "lead": [
  "Kimi K3 在 Day-0 就于 vLLM 跑通了，但要把它高效地服务起来，还得再走一遍整个栈。KDA 循环状态、LatentMoE、MXFP4 专家 kernel、投机解码以及 TP/PP 各自暴露出不同的瓶颈，调度器的上限和小张量拷贝有时和大 GEMM 一样要紧。",
  "文章先给端到端结果，再拆开四个有代表性的改动：自适应投机 token 预算、内部 KDA 前缀检查点、零拷贝混合 KDA 批、延迟 MXFP4 收尾；此外覆盖 ReplaySSM、预填充/解码分离与缓存卸载，以及解码上下文并行。"
 ],
 "sections": [
  {
   "type": "h2",
   "title": "性能总览",
   "paras": [
    "测试负载为 8K/1K，TP8，DSpark 投机解码 8 个 token，并发 1、4、16。基线是 v0.27.1，对比对象是提交 82a85dc1（0913），环境为 B300 节点（CUDA 13.3）。",
    "启动服务：",
    _code(0),
    "注意：两次运行都关闭了前缀缓存，因为 v0.27.1 存在一个后来才修复的 Kimi K3 前缀缓存问题。",
    "跑基准测试：",
    _code(1),
    "把两次运行的关键指标放在一起（格式为 v0.27.1 → 0913 main）："
   ],
   "fig_after": {
    "0": [
     {"src": "fig00.png", "caption": "图 1：Kimi K3 的服务性能，从 vLLM v0.27.1 到 main：延迟降低 56%–60%，吞吐提升 2.2–2.8 倍，TTFT 降低 72%–85%（并发 1、4、16）。"}
    ]
   },
   "table": {
    "head": ["并发", "平均延迟（秒）", "吞吐（token/秒）", "平均 TTFT（毫秒）"],
    "rows": [
     ["1", "12.37 → 5.30（−57.2%）", "83.3 → 183.3（+120.0%）", "2262.9 → 376.3（−83.4%）"],
     ["4", "23.67 → 10.50（−55.6%）", "166.7 → 416.7（+150.0%）", "2314.9 → 640.5（−72.3%）"],
     ["16", "55.90 → 22.17（−60.3%）", "258.3 → 725.0（+180.6%）", "7601.1 → 1121.0（−85.3%）"]
    ]
   }
  },
  {
   "type": "h2",
   "title": "端到端优化实例",
   "paras": []
  },
  {
   "type": "h3",
   "title": "自适应调度预算",
   "paras": [
    "请求数少的时候，max_num_batched_tokens 有一大半是用不上的。PR #51725 引入了自适应的可调度 token 预算，PR #51726 把大显存档位的默认上限从 8,192 提到 16,384。在文章报告的 8K/1K 负载上，TTFT 降低 55%–65%，吞吐最多提升 41.5%。",
    "以 max_num_seqs=1024、max_num_batched_tokens=8192、K=8 为例：",
    "关键在于自适应策略：请求数少时把可调度的 token 数放大，这样一个请求就不会被拆到多次前向里。"
   ],
   "table": {
    "head": ["实际请求数", "旧逻辑可调度 token 数", "现在可调度 token 数"],
    "rows": [
     ["1", "1024（8192 − 1024 × (8−1)）", "8185（8192 − 7）"],
     ["32", "1024", "7968"],
     ["128", "1024", "7296"],
     ["1024", "1024", "1024"]
    ]
   }
  },
  {
   "type": "h3",
   "title": "内部 KDA 前缀检查点",
   "paras": [
    "Mamba 风格的前缀缓存在最后一个可缓存块边界处把预填充切开，有时会给很短的一段后缀再补一次整模型前向。PR #52789 把检查点导出放进同一次预填充 pass，TTFT 降低 9%–25%；PR #53614 补上部分前缀命中与投机解码，其中包括 EAGLE 的重放边界对齐。",
    "对 8K 输入来说：",
    "这个改动省掉了第二次穿过 attention、MoE、路由和 TP 通信的整模型前向。"
   ],
   "fig_after": {
    "1": [
     {"src": "fig01.png", "caption": "图 2：内部 KDA 检查点之前，一次 8K 预填充在每个 KDA 层需要两次模型前向和两次 FlashKDA 调用；改动之后，一次 FlashKDA 调用处理全部 8,000 个 token，并在同一次递推里于第 7,680 个 token 处导出检查点状态。"}
    ]
   }
  },
  {
   "type": "h3",
   "title": "零拷贝混合 KDA 批",
   "paras": [
    "投机与非投机混合的批处理，每一层要做 6 次 index_select 和 2 次 index_copy_ 操作。PR #56159 改为连续的零拷贝切片，并把结果直接写入输出。并发 4 和 16 下吞吐提升 5.2%–7.7%，batch size 1 持平。"
   ],
   "fig_after": {
    "0": [
     {"src": "fig02.png", "caption": "图 3：零拷贝混合批之前，每个 KDA 层要用 6 次 index_select 收集非投机与投机输入，再用 2 次 index_copy 把结果散回去；改动之后，连续视图同时喂给两条 KDA 路径，并直接写进最终输出的切片。"}
    ]
   }
  },
  {
   "type": "h3",
   "title": "延迟 MXFP4 收尾",
   "paras": [
    "PR #53152 把 MXFP4 的 top-k 收尾放进 latent tail kernel，省掉一次 kernel 启动和一次中间张量的写回与读取，端到端延迟大约降低 5%。PR #53327 修正了初始化顺序，让这条延迟路径能在权重加载之前生效。",
    "这一步省掉一次 kernel 启动，也不必再把收尾后的中间张量写出去又读回来。"
   ],
   "fig_after": {
    "0": [
     {"src": "fig03.png", "caption": "图 4：MXFP4 的 top-k 收尾融进 latent tail 前后的对比。"}
    ]
   }
  },
  {
   "type": "h2",
   "title": "ReplaySSM：重建 KDA 状态，而不是存储它",
   "paras": [
    "投机解码要在每个草稿位置写一份 KDA 循环状态，好在草稿被拒时回滚。T 个草稿位置就意味着每一步多出 T 次状态写入。ReplaySSM 改为缓存最近的 SSM 输入，在提交时重建出被接受的状态，回滚只需要移动一个缓冲区指针。",
    "PR #51855 在 Model Runner V2 上为 Kimi K3 实现了 ReplaySSM：一个 Triton kernel 在 align 模式下同时提交被接受的状态和下一个前缀缓存边界。同样的 46.48 GiB 缓存预算下，TP8 的有效容量提升 10.97%，精度没有损失。"
   ]
  },
  {
   "type": "h2",
   "title": "预填充/解码分离与混合状态卸载",
   "paras": [
    "PD 分离和缓存卸载要同时搬运 MLA KV 与 KDA 状态。MLA KV 在每个 TP rank 上是复制的，KDA 状态却按 head 和维度分片，Mamba 的 align block table 还可能是稀疏且可变的，纯 attention 那套传输假设在这里并不成立。",
    "PR #51358 让 Mooncake 保存调度器选中的边界状态，并在每个 rank 的异步写入完成之前一直钉住它们。PR #50344 规定：只有能恢复 KDA 状态的 connector 才可以服务按组发散的部分前缀命中。"
   ]
  },
  {
   "type": "h2",
   "title": "解码上下文并行",
   "paras": [
    "TP 会在每个 rank 上复制 MLA 的 latent KV，所以增加 TP rank 并不会增加 KV 缓存容量。解码上下文并行（DCP）沿序列维度把它切开，对长共享前缀的 agentic 负载尤其有用。",
    "PR #50484 为 Kimi K3 的融合 MLA 路径实现了 DCP：对称内存 A2A 负责输出与 LSE 的归约，NVLS multicast 收集 query，multimem 收集分块上下文的 KV，query 分片直接写进消费者的最终缓冲区。在 4×GB200 上，query 交换延迟降低 10.4%–29.9%。",
    "在 120k token 的负载上（114k 共享前缀、6k 后缀、400 输出 token），KV 缓存容量从 1.93M 提升到 19.75M token。TPOT p50 在并发 1 下从 13.8 ms 降到 10.5 ms，并发 2 下从 16.2 ms 降到 11.8 ms。GSM8K：DCP8 为 96.97%，TP8 为 96.21%，零请求错误。"
   ],
   "fig_after": {
    "1": [
     {"src": "fig04.gif", "caption": ""}
    ]
   }
  },
  {
   "type": "h2",
   "title": "更多优化",
   "paras": [
    "这轮优化还覆盖了内存布局、序列并行与流水并行、KDA 预填充与循环状态、MLA、MoE 和 GEMM：切分大投影并共享专家，减少通信与数据搬运，压实小 batch 的 GPU 路径。完整的 PR 列表记录在 issue #50587 中。",
    "社区贡献的 PR 把工作面铺得更宽：Robert Shaw 和 Summer Yang 增加了带 DeepGEMM MXFP4 的 DeepEPv2，以及上面提到的 DCP 支持；Thien Tran 做了序列并行的 GEMM 路径；Nick Hill 和 Xiaolong Xu 在 PR #51540 与 #52458 中收紧了 KDA 预填充。"
   ]
  }
 ],
 "conclusion": [
  "**Kimi K3 的性能不是靠某一个更大的 kernel 救回来的，而是一批各自只有几个百分点的改动叠出来的。** 调度器少浪费 token 额度、前缀检查点省掉一次整模型前向、混合批去掉几次 index_select、MXFP4 少一次 kernel 启动，每一项单看都不惊人。",
  "值得记住的是取舍落在哪里。ReplaySSM 用重建换掉存储，回滚只移动一个指针；PD 分离必须承认 MLA KV 与 KDA 状态的分片方式不同，纯 attention 的传输假设不能直接搬过来；DCP 把只在每个 rank 上重复的 latent KV 沿序列切开，换来近十倍的 KV 容量。",
  "对做推理服务的人来说，这份清单的价值在于它划出了边界：真正拖住吞吐的往往正是调度上限、状态回滚、张量拷贝这类小地方，而不是最大的那个 GEMM。有了 vLLM 里公开的 PR 编号，自己的 Kimi K3 部署也能逐条复现这些收益。"
 ],
 "reference_url": "https://vllm.ai/blog/2026-09-13-kimi-k3-performance-optimization",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print("OK wrote", out_path, len(DATA["sections"]), "sections", sum(len(s["paras"]) for s in DATA["sections"]), "paras")