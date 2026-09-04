# -*- coding: utf-8 -*-
"""Lightning Lightseek: Kimi K3 Draft Collection (TorchSpec) — 中文编译"""
import json, os, sys
_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
 "title": "Kimi K3 的「猜词器」怎么训：TorchSpec 发布 3 只 draft 模型，并把训练提速固化成 12 张图",
 "lead": [
   "给大模型配「draft 模型」（推测解码的小草稿模型）是提升推理吞吐性价比的做法，但把 draft 训练本身做到又快又稳，门槛不低。Lightning（Lightseek）宣告发布 Kimi K3 的 draft 系列——kimi-k3-eagle3-mla、kimi-k3-dflash2、kimi-k3-dspark——全部用 TorchSpec 在 40 块 GB200 + disaggregated 训练模式下训出，并把 2.5× 训练吞吐、4.5× 预处理提速这些工程成果拆开讲。",
   "这是篇「release + benchmarking + systems 细节」密度相当高的技术文：为什么低并发下 DFlash2 胜过 EAGLE3、K3 的稀疏 MoE 与 KDA/gated-MLA 会怎样抬高额外验证 token 的成本、anchored-EAGLE 如何不再对每一个 token 都做 TTT rollout……下面把关键方法和真实数字一条条还原给你。",
 ],
 "summary": [
   {"key":"发布了什么","body":"TorchSpec 新增支持 Kimi K3 的训练三大 draft：EAGLE3-MLA、DFlash2、DSpark（均 MLA 骨干）；40×GB200、disaggregated 训练。"},
   {"key":"性能结论","body":"DFlash2 @低并发优于 EAGLE3（高并发拉平）：单块多 draft token + 更长 accept 前缀斩掉串行目标步；但 K3 稀疏 MoE + KDA 状态回退使大后段验证更贵，accept 长未必划算。"},
   {"key":"训练提速","body":"4×GB200、bs2 下合计提速 2.5×：pipeline-parallel→Mooncake 异步、anchored EAGLE 锯掉 attention/HBM、length 排序减 padding、去 .item() 同步+fused Adam、预处理 4.5×。"},
 ],
 "sections": [
  {"type":"h2","title":"三只 draft，一份共享的动机","paras":[
    "draft（草稿）模型核心在「一次猜 N 个 token，再让大模型瓶颈层一次性验证」。torch 生态里 TorchSpec 已是把生成 hidden states→丢给 draft 训练器做探索的框架层实现。这次的三个型号都属于同一套 base：都走 **Multi-Latent Attention(MLA)** 骨干——推理时省 KV cache、也好接进 PD disaggregation 与统一 KV 布局；跑在 40 块 GB200 的异步/disaggregated 训练里，配置 recipe 随文公开。",
    "个从 DSpark 的容量说明值得读一遍的注脚：受资源约束，DSpark 的 checkpoint 比 DFlash2 训的 epoch 更少——下文凡涉 DSpark 的对比都要带上这个前提。",
  ]},
  {"type":"h2","title":"评测口径：接受长度与端到端吞吐","paras":[
    "先看「接受长度」。作者跨 10 个常见 benchmark（math / code / retrieval-QA / 中文 / 对话）比较三只 draft，采样统一 temperature 1.0、top_p 0.95、max reasoning effort；档位不同——EAGLE3 以 draft/verify depth 3/4 跑，DFlash2 与 DSpark 用 7/8。接受率越高，代表大模型越常收下草稿、越省再生成本。（源文此处的 acceptance-length 对比图未随文发布，结论以文字为准。）",
    "但 accept rate 只是代理，真实收益要看和引擎接起来的端到端吞吐。他们用 **SPEED-Bench**（混合 low/mid/high 熵负载、同上采样默认）当稳定引擎 TPS，作者认为它贴近生产流量。结论一句话：**低并发时 DFlash2 好于 EAGLE3，并发越高差距越被磨平。**",
  ], "fig_after":{"1":[{"src":"fig02.png","caption":"Kimi K3 SPEED-Bench 吞吐扫描：DFlash2 在低并发占优、高并发与 EAGLE3 靠拢"}]}},
  {"type":"h2","title":"为什么低并发 DFlash2 赢、高并发没那么赢","paras":[
    "DFlash2 的补法是一次出一条更长的 draft block：单块里直接多吐几个候选 token，于是更长的 accepted 前缀会一次砍掉一串串行的目标步（target steps）——batch 小的时候这个收益很实在。",
    "但跨过 batch≈32 后，接受长度变长就不再能补偿「为验证者而多花的开销」了。原因在生产采样这一层：temperature 1.0 会让目标分布熵偏高，靠后的位置越来越难被 accept，于是多出来的那一段验证多半是白做的尾巴；EAGLE3 更短的 3/4 窗口恰好少浪费这截尾。",
    "而 K3 更让「多验证几步」变贵的两条体质必须单独拎出来看——它们是这篇里最重要的 insight：**① K3 是稀疏 MoE**：多一「验证 token」，expert 的 FLOPs 与 dispatch 是按 *验证宽度*(不是幸存 token 数) 同步放大；**② K3 是 KDA 与 gated-MLA 的 3:1 混合**：KDA(延迟的循环/复核状态) 必须随每个推测 token advance-rewind，draft 宽度越宽 replay 的图越多；相比之下像 K2.6 这种纯 MLA 模型能在额外 query token 上复用压缩 KV，多出的验证位从 attention 计算里捡回更多收益。",
  ]},
  {"type":"h2","title":"Draft 骨干：一份 MLA + 一点 SWA","paras":[
    "三只全部 MLA。作者在 benchmark 里发现 DSpark 的长上下文场景脑袋常常卡在 attention，于是让前 4 层换 **Sliding Window Attention（SWA）**。定稿骨架：**DFlash2 = 4 层 SWA + 1 层 full-MLA**；**DSpark = 5 层 full-MLA**（同为 MLA/半窗改动，推理时 KV/Kernel 代价不同）。",
  ], "fig_after":{"0":[{"src":"fig03.png","caption":"draft MLA / kernel 耗时对比：SWA 层数配比影响逐 token 开销"}]}},
  {"type":"h2","title":"训练提速第一斧：pipeline parallel + Mooncake 异步逃生","paras":[
    "Kimi K3 塞不进 8 块 GB200，得先用 16 块把权重 shard 开。他们选 pipeline parallel 而非其它 sharding：因为把 all-reduce 压成只在 pp 边界传 hidden states 的 p2p，能把通信降下来给吞吐让路——TorchSpec 对 vLLM 推理引擎加了通用 pipeline parallel。",
    "为了不白等，每一级 pp rank 攒够 hidden states 就 **异步写进 Mooncake**，让计算别撞上 I/O 的 bubble——prefill 越深、生产队列越多，吞吐延展得越顺。",
  ], "fig_after":{"1":[{"src":"fig04.png","caption":"pipeline-parallel prefill：吞吐随并发 producer 队列上升，Mooncake 把推理与训练解耦"}]}},
  {"type":"h2","title":"把 EAGLE-3 换成「锚点式」：别再对每个 token 做 TTT","paras":[
    "传统 EAGLE-3 训练是在**每一个 token** 上做 TTT(起头-再rollout) rollout——序列一长，全部token都要额外预测与占内存，训练贵。",
    "DFlash 给出另一条路：**随机抽一些“anchor tokens”，从每个 anchor 去预测 N 个块的续写**，实现方式是给每次块预测造一条双向 attention mask；anchor 数量不随序列长度膨胀，长序列下它们“等权贡献”而不是“主导整趟 run”，训练更稳。",
    "把两者一拍：EAGLE 训练不再对每个 token 都 rollout，而是**抽取随机 anchor**。关键点在于——**没被抽中的 token 反正会通过 KV cache 一路贡献给 attention**，所以不需要全覆盖也能拿到很接近的结果。",
    "由此实现了一个等式红利：不同输入长度的样本被**等概率采样**，同样的 drafter 尺寸下能吸进更多数据，同时 attention 侧的昂贵计算与 HBM 占用被大幅锯掉（对 MLA 版 drafter，attention 加速见原文 Table 1）。",
  ], "fig_after":{"0":[{"src":"fig05.png","caption":"KV-cache mask 可视化：EAGLE 的 TTT（逐 token）训练"}],"1":[{"src":"fig06.png","caption":"KV-cache mask 可视化：DFlash 的 anchor + 块式双向 mask 训练"}],"3":[{"src":"fig07.png","caption":"KV-cache mask 可视化：anchored EAGLE——随机 anchor、未被抽中 token 经 KV 兜底"}]}},
  {"type":"h2","title":"训练提速：先把 padding 赶出去（按长度分桶）","paras":[
    "推测解码训练想扩规模可以加 DP worker，也可以加大 batch。大 batch 行之有效，因为训练主要被 EAGLE TTT 那部分 HBM/memory 带宽喂饱。但直接加大 batch 并不会线性加速——浪费来自 padding：一个 batch 里、以及跨 worker 之间，不同长度的序列必须 pad 到同一形状，于是大量 token 只是在“陪跑”，不给训练贡献梯度。",
    "解法很朴素但高效：先把序列**按长度排好**，把长度接近的塞进同一个 batch（图中黄色 = 仍浪费的后补填充，白 = 可跳过的部分）。",
    "按长度分桶后，剩下的黄块更少了，训练每一步做的“有用功”因此变多——这就是那一路 2.5× 里的主要贡献之一。",
  ], "fig_after":{"0":[{"src":"fig08.png","caption":"初始训练序列：黄块表示被浪费的 padding"},{"src":"fig09.png","caption":"按长度排序后的序列：黄=仍剩的填充，白=可跳过的 padding"}]}},
  {"type":"h2","title":"去掉主线程同步 & 换 fused 优化器","paras":[
    "把 .item() 从前端计数里挪走，是最容易见效的一处：主线程调用 .item() 会强制 CPU 等还没落地的 GPU 算子。训练指标这些值最终要到 CPU，但不该阻塞当前 step——所以把指标上报整体**延后一拍**。",
    "组合拳还包括：切到 **fused Adam**，用 `torch._foreach_` 批量替代 Python 循环。三者一起让 CPU 不再无缘无故截停 GPU。Torch Profiler 的 trace 在去除同步前——后也照了下来，供对照“等待的空洞”消失了多少。",
  ], "fig_after":{"0":[{"src":"fig11.png","caption":"去同步前 Torch Profiler trace：主线程等待明显"},{"src":"fig12.png","caption":"去同步后 Torch Profiler trace：等待呈明显减少"}]}},
  {"type":"h2","title":"4.5× 更快的预处理：文件描述符是这样被耗尽的","paras":[
    "训练前 TorchSpec 要把 raw dialog 转成 token id，结果会缓存；但对每份新数据集，预处理仍卡在 critical path。量级到百万条对话时，两个 multiprocessing 行为把阶段拖贵了：",
    "**① 传张量回父进程**——进程间传 torch 张量走 shared memory，而**每个张量要耗一个文件描述符**。少量大张量没问题，但一百万个“小结果”会把父进程的 fd 榨干。改成返回 **NumPy 数组的 bytes**、再由 `torch.from_numpy` 装配，结果收集从 498 秒→23 秒。",
    "**② 建池时机**——先建 worker pool 再加载数据集，让 worker 继承的空列表在队列里收固定分到的输入即可，避免重复搬运整份 dataset：百万行 tokenize 从 1436 秒→319 秒。两项合计即 4.5×。",
    "收尾还有两条工程钩子：**Offline training**——把目标模型在离线先把 hidden states 落盘，draft 再对着文件训练，二者不再抢同一批 GPU、固定数据集反复实验也划算；以及 **Nightly CI + Docker**——把 vLLM patch 打包进 docker 镜像（starts从镜像起，免去每个人本地再打同样的 patch 与重做一致性检查），每日 CI 校验 TorchSpec 工作流收敛行为正常。最终在 4×GB200、bs=2 上训练吞吐合计提升约 2.5×（图 13 为训练容量包络）。",
  ], "fig_after":{"2":[{"src":"fig10.png","caption":"按长度分桶后的训练 batch（剩余潜在填充已显著减少）"}],"3":[{"src":"fig13.png","caption":"4×GB200、bs=2 下最终训练提速：合计约 2.5×"}]}},
 ],
 "conclusion": [
   "这篇是「怎么把 d·raft 训练本身做成工程产品」的示范。若只拿一条结论走：**接收率不是全部——在稀疏 MoE + 混合注意力的大模型上，“多验证几点”的边际成本会被结构放大，真正的胜负手是引擎级优化（pipeline+异步、anchored 采样、去同步、预分区）。**",
   "给你的可复用启发有三点：**① “draft 宽度 vs 目标验证成本”要在部署的并发档位上测**（低并发 DFlash 式长块占优、高并发差点被摊平，别只看 accept 率）；**② 能经 KV 兜底的训练可省掉“全覆盖”**——锚点采样证明了“不预测的 token 仍参与损失”，这是不少半监督/长序列场景可借鉴的节约范式；**③ 1e6 小结果把父进程 fd 打爆这类“小现象”是真实超参**，预处理以 bytes-numpy 往返而非 tensor 跨进程，往往是无痛的 20×。TorchSpec 这套 recipes/镜像/nightly CI 让复现成本显著下降，做 speculative-decoding 系统的人建议对照着自己栈里的 draft 推理侧补一遍。",
 ],
 "reference_url": "https://lightseek.org/blog/kimi-k3-draft-collection.html",
}

out = os.path.join(_dir, "article_data.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("ok sections", len(DATA["sections"]), "paras", sum(len(s['paras']) for s in DATA['sections']))
for s in DATA['sections']:
    for k in s.get('fig_after', {}):
        if int(k) >= len(s['paras']): print('越界 !', s['title'][:14], k, len(s['paras']))
