# -*- coding: utf-8 -*-
# FA4 backward hdim64 kernel optimization — 中文编译
# src: research.colfax-intl.com ...(Colfax Research)  8图+3表+4代码块 全保留, 正文知识≥85%

DATA = {
"title": "为什么 head dim 64 的 FlashAttention-4 反向慢,以及怎么用空闲 TMEM 修到 903 TFLOPS",
"reference_url": "https://research.colfax-intl.com/optimization-diaries-improving-flashattention-4-backward-for-head-dimension-64/",

"summary": [
  {"key":"现象","body":"FA4 反向核在 Blackwell B200 上、head dim 128 时达 1237 TFLOPS(约 55% 峰值);但同一核切到 head dim 64,只用出 26–32% 峰值。差距的关键:GEMM FLOPs 随 head dim 减半,而计算 warp 的逐点算子开销与 head dim 无关,于是没有足够张量核算力去藏住软max等操作的时延。"},
  {"key":"根因","body":"head dim 64 下 TMEM(每 SM 128 道口 × 512 列)默认分配空出 [384,512) 四分之一列。核把 P 叠写在 S 上、dS 叠写在 dP 上(重别名),逼出两次核全局栅栏 alias guard,并在软max期间困住整个张量核空转。"},
  {"key":"修法与收益","body":"把这四分之一空闲 TMEM 拿出来给 P、dS 专用槽(de-alias),移除两处核栅栏,剩余栅栏降成 warp sync,并把 MMA 发出顺序改成 QK_{t+1}→PdO_t→dK_t→dQ_t→dP_{t+1},让下一 tile 的 QK 在软max中间就发出。速度提升 1.06–1.15×,最高 903 TFLOPS(40% 峰值),124 组配置几何平均 1.129×。"},
],

"lead": [
  "FlashAttention 的后向 pass,是训练中占大头的一段硬骨头。Colfax Research 这篇『优化日记』讲的是同一套 FA4 backward 核在 Blackwell B200 上,head dimension 128 与 64 表现相差悬殊——128 能打到约 55% 峰值,64 却只剩 26–32%——以及他们如何靠 Blackwell 张量内存(TMEM)里没用上的四分之一空间,把 head dim 64 拉回到最高 903 TFLOPS。",
  "下面是全文主线:先交代 head dim 64 拖慢的物理原因,再完整走一遍 baseline 主循环为何被迫插入五道全局栅栏,最后给出去掉这两道全局栅栏、让张量核在软max区间多干活的完整 kernel 改动。所有性能数字、图表来自原文;改动实现可见文末给出的 FlashAttention 仓库 PR。",
],

"sections": [

# ---------- 引言 ----------
{"type":"h2","title":"引言：同一套 kernel,两种 head dim,两种命运",
 "paras":[
  "本文讨论 FlashAttention-4(FA4)在 NVIDIA Blackwell GPU 上的**后向 pass**。对 head dimension 128,FA4 backward 已非常高效,达到 **1237 TFLOPS**——约为 B200 上 55% 的峰值算力吞吐。然而同样形状、head dimension 64 时,同一个 kernel 只跑出**峰值算力的 26–32%**。这说明 hdim 64 一档仍有大量可优化空间。",
  "作者要讲的优化,核心是**利用空余的张量内存(TMEM)来提升 hdim 64 的 FA4 backward 性能**。关键观察:对 head dim 64,默认 kernel 设计下 TMEM 会有**四分之一**处于闲置;拿这些闲置槽去对某些驻留在那里的张量做**去别名(de-alias)**——具体是把同一轮迭代里的 P 从 S 上脱开、dS 从 dP 上脱开。",
  "去别名之后:(1)可以移除多余的同步,把 256 线程的全局栅栏替换成纯 warp 同步;(2)可以重排 MMA 的发出顺序,让下一轮迭代的 QK 乘加与当前轮迭代的 softmax 计算重叠。合并效果是 **1.06–1.15× 加速**,最高打到 **903 TFLOPS(峰值 40%)**。实现见 FlashAttention 仓库 [PR #2804](https://github.com/Dao-AILab/flash-attention/pull/2804)。",
 ]},

# ---------- FA4 backward 回顾 ----------
{"type":"h2","title":"回顾：FA4 backward 在算什么",
 "paras":[
  "FA4 后向 pass 计算的是一串标准的手写注意力梯度:S = QK^T,P = exp(S − L),dP = dO·V^T,dS = P ∘ (dP − D),然后 dV = P^T·dO,dK = dS^T·Q,dQ = dS·K。(式中 ∘ 为逐元素乘,L、D 为行 logsumexp 与其差分。)",
  "整个计算按 batch、attention heads、KV tiles 并行。每个 CTA 拥有一块 K、V 的 tile,并对 Q tiles 循环;每个 CTA 算它拥有的 K/V tile 对应的 dK 与 dV tile。每轮 mainloop 迭代,它还算当前 Q tile 对应的一小块 dQ 贡献,累加进全局内存里的 fp32 累加器。",
 ],
 "fig_after":{}},
{"type":"h3","title":"核是 warp 特化的,活按 16 个 warp 分",
 "paras":[
  "FA4 backward 核是 **warp-specialized**:工作分给 CTA 内十六个 warp。下表给出分工:",
  "作者把关注点放在 MMA warp 与 compute warpgroup 两组上。对每轮 mainloop 迭代:MMA warp 发出五个 GEMM;夹在它们之间,compute warps 做两个逐点(pwise)计算。因为每个 CTA 拥有一块 KV tile,核实际算的是转置形态 S^T、P^T、dP^T、dS^T 而非 S、P、dP、dS。每轮迭代的计算步骤见下表。",
 ],
 "table":{"head":["role","warps","description"],
   "rows":[
     ["load","1","发出 K、V、Q、dO 的 TMA load"],
     ["MMA","1","发出每一条 tcgen05.mma 指令"],
     ["compute","8","由 S 算 P,由 dP 算 dS"],
     ["reduce","4","从张量内存读回 dQ 的各份 partial 并加进全局累加器"],
     ["relay/empty","2","hdim 64 时空闲;relay warp 仅 hdim 128 用(该构型用 2-CTA MMA 指令)"]]
 }},
{"type":"h3","title":"每轮 mainloop 的五个 GEMM 与两个逐点",
 "paras":[
  "下表把一轮迭代内部谁读谁写列清楚(S、P、dP 等已省略转置记号):",
  "这里其实已能看出 hdim 64 与 hdim 128 性能差距的首要原因:**GEMM 的 FLOPs 随 head dim 缩放**,所以从 hdim 128 降到 hdim 64,每轮迭代的张量核负载**减半**;而 compute warps 算的 FLOPs 与 head dim 无关。于是 hdim 64 时,用来遮掩逐点计算 warp 时延的张量核算力更少了,短板暴露得更充分。",
 ],
 "table":{"head":["step","who","reads","writes"],
   "rows":[
     ["S^T = K Q^T","MMA warp","K, Q (SMEM)","S^T (TMEM, fp32)"],
     ["P^T = exp(S^T − L)","compute warps","S^T (TMEM)","P^T (TMEM, bf16)"],
     ["dS^T = P^T ∘ (dP^T − D)","compute warps","P^T (RMEM), dP^T (TMEM)","dS^T (TMEM, bf16; 并转存 SMEM)"],
     ["dV += P^T dO; dK += dS^T Q; dQ = dS K","MMA warp","P^T, dS^T (TMEM), dS^T (SMEM)","dV, dK, dQ (TMEM)"]]
 }},
{"type":"h3","title":"TMEM 概览",
 "paras":[
  "tcgen05.mma 的累加器住在**张量内存 TMEM**——每 SM 一块 128 lane × 512 列的 32-bit cell 阵列。warp 用 tcgen05.ld / tcgen05.st 分别从 TMEM 读、写。下面这张图就是 hdim 64 FA4 backward 默认的 TMEM 分配:",
 ],
 "fig_after":{"0":[{"src":"fig01.png","caption":"图 1:hdim 64 的 baseline TMEM 分配。上排是 tcgen05.mma 写入的 fp32 累加器;下排是 compute warps 覆盖写上去的 bf16 tile:P 叠到 S 上、dS(和 dQ partial)叠到 dP 上。注意 [384,512) 列没有被用到。"}] }},

# 承接 fig01 的解释段也在本 h3? 但 fig_after 0 段后。把解释段放另一 h? 
],}

DATA["sections"] = DATA["sections"] + [

# 后续在第二段拼出来
]
DATA["caption_placeholder"]=True
