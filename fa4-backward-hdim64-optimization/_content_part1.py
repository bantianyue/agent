# -*- coding: utf-8 -*-
# content part1: 标题/summary/lead + 引言 + 回顾(到 Figure1) + hazard(code1) + fused(code2) + Figure3

C1 = """
cute.arch.fence_view_async_tmem_load()
# P overwrites S, and warp w's P columns sit under warp w+4's S lanes:
# every warp must have loaded S before any warp stores P.
self.compute_sync_barrier.arrive_and_wait()
"""

C2 = """
cute.arch.fence_view_async_tmem_store()
cute.arch.fence_view_async_shared()
self.compute_sync_barrier.arrive_and_wait()
with cute.arch.elect_one():
    pipeline_S_P.consumer_release(consumer_state) # "S read and P written"
    pipeline_LSE.consumer_release(consumer_state_LSE)
"""

DATA = {
"title": "head dim 64 的 FlashAttention-4 反向为何慢：用空闲 TMEM 去别名修到 903 TFLOPS",
"reference_url": "https://research.colfax-intl.com/optimization-diaries-improving-flashattention-4-backward-for-head-dimension-64/",
"summary": [
  {"key":"现象","body":"FA4 backward 核在 B200 上、head dim 128 时达 1237 TFLOPS,约 55% 峰值;切换到 head dim 64 只剩 26–32% 峰值。根因是 GEMM 的 FLOPs 随 head dim 减半,而逐点算子开销与 head dim 无关,张量核算力不足以藏住 softmax 段时延。"},
  {"key":"根因","body":"hdim 64 下 TMEM(每 SM 128 lane×512 列)默认分配空出 [384,512) 四分之一。核把 P 叠写在 S 上、dS 叠写在 dP 上(同址别名),被迫插两处 kernel-wide 栅栏 alias guard,还让 tensor core 在 softmax 期间空转。"},
  {"key":"修法","body":"把这四分之一 TMEM 交给 P、dS 做专用槽(de-alias),去掉两处核栅栏、其余栅栏降成纯 warp sync,并把 MMA 顺序改成 QK_t+1→PdO_t→dK_t→dQ_t→dP_t+1,让下一 tile 的 QK 在 softmax 中段就发出。整体 1.06–1.15×,最高 903 TFLOPS(40% 峰值);124 组配置几何平均 1.129×。"},
],
"lead": [
  "FlashAttention 的反向 pass,是训练里吃带宽、耗功耗的一段核心。Colfax Research 这篇『优化日记』讲的正是 FA4 backward 在 NVIDIA Blackwell B200 上随 head dimension 的前后两档表现——hdim 128 能到约 55% 峰值,hdim 64 却只到 26–32%——以及他们如何靠 Blackwell 张量内存(TMEM)里闲置的四分之一空间,把 hdim 64 拉回到最高 903 TFLOPS。",
  "下文按『为什么慢 → baseline 为什么被迫插五道全局栅栏 → 如何用闲置 TMEM 去别名并让张量核在 softmax 区间多干活』走完全部改动。文内图、表、代码片段均按原文完整保留;实现以 PR 挂在 FlashAttention 仓库。",
],
"sections": [
 {"type":"h2","title":"引言：同一内核,不同 head dim,两种命运",
  "paras":[
   "本文关心 FlashAttention-4(FA4)在 NVIDIA Blackwell GPU 上的**反向 pass**。head dimension 为 128 时,FA4 backward 已相当高效,B200 上单被 benchmark 到 **1237 TFLOPS,约占峰值算力吞吐的 55%**。但同样的形状、head dimension 64 时,同一个 kernel 只剩**峰值的 26–32%**。这一档正是有大量空间可优化的信号。",
   "要讲的优化,核心在于用足**空余的张量内存(TMEM)**来提升 hdim 64 的 FA4 backward。关键观察:当 head dim 为 64,默认 kernel 设计下 TMEM 有**四分之一**处于闲置;把这部分槽拿出来,去把驻留其中的张量**去别名(de-alias)**——也就是让同一轮迭代里的 P 不再叠写在 S 上、dS 不再叠写在 dP 上。",
   "去别名带来两个改动机会:(1)去掉一些多余同步,把 256 线程的全局栅栏换成纯 warp 同步;(2)重排 MMA 的发出顺序,让下一轮迭代的 QK 乘加与当前轮 softmax 重叠。加起来 **1.06–1.15× 加速,最高 903 TFLOPS,约峰值 40%**。改动见 FlashAttention 仓库 [PR #2804](https://github.com/Dao-AILab/flash-attention/pull/2804)。",
  ]},
 {"type":"h2","title":"回顾：FA4 backward 在算什么",
  "paras":[
   "FA4 反向算的是一串标准式子:S = QKᵀ,P = exp(S − L),dP = dO·Vᵀ,dS = P ∘ (dP − D),dV = Pᵀ·dO,dK = dSᵀ·Q,dQ = dS·K。其中 ∘ 为逐元素乘,L、D 是行 log-sum-exp 及其差分。",
   "计算按 batch、attention heads、KV tiles 并行:每个 CTA 拥有一块 K、V tile,主循环遍历 Q tiles,每轮算它所属 KV tile 的 dK、dV,并把当前 Q tile 的一小片 dQ 累加进全局 fp32 累加器。",
  ]},
 {"type":"h3","title":"warp 特化：活按十六个 warp 分",
  "paras":[
   "FA4 backward 是 **warp-specialized** 内核,CTA 内十六个 warp 分工如下表:",
  ],
  "table":{"head":["role(角色)","warps","description(分工)"],
    "rows":[
      ["load","1","发出 TMA 的 K/V/Q/dO 载入"],
      ["MMA","1","发出每条 tcgen05.mma 指令"],
      ["compute","8","由 S 算 P;由 dP 算 dS"],
      ["reduce","4","读回各 partial dQ 并累加进全局累加器"],
      ["relay/empty","2","hdim 64 时空闲;relay warp 仅供 hdim 128(2-CTA MMA 场景)"]]}},
 {"type":"h3","title":"每轮 mainloop：五个 GEMM 加两个逐点",
  "paras":[
   "关注点放在 MMA warp 与 compute warpgroups。每轮 mainloop 里,MMA warp 发出五个 GEMM,compute warps 在它们之间做两个逐点运算。由于每 CTA 持一块 KV tile,内核算的是转置形态 Sᵀ、Pᵀ、dPᵀ、dSᵀ(下面表即如此;后文为简洁省略转置记号写 S、P、dP、dS):",
  ],
  "table":{"head":["step(计算步)","who(谁)","reads(读)","writes(写)"],
    "rows":[
      ["Sᵀ = K Qᵀ","MMA warp","K,Q (SMEM)","Sᵀ (TMEM, fp32)"],
      ["Pᵀ = exp(Sᵀ − L)","compute warps","Sᵀ (TMEM)","Pᵀ (TMEM, bf16)"],
      ["dSᵀ = Pᵀ ∘ (dPᵀ − D)","compute warps","Pᵀ (RMEM),dPᵀ (TMEM)","dSᵀ (TMEM bf16 + SMEM)"],
      ["dV += Pᵀ dO;dK += dSᵀ Q;dQ = dS K","MMA warp","Pᵀ,dSᵀ (TMEM),dSᵀ (SMEM)","dV,dK,dQ (TMEM)"]]}},
 {"type":"h3","title":"顺带点出性能差异的根源",
  "paras":[
   "这里已经能看出 hdim 64 和 128 悬殊的原因:**GEMM 的 FLOPs 随 head dim 缩放**,128 降到 64 时每轮迭代的张量核负载就直接**减半**;而 compute warps 的逐点 FLOPs 与 head dim 无关。于是 hdim 64 时没有足够张量核算力去藏住逐点 warp 运算的时延,短板立刻暴露。",
  ]},
 {"type":"h2","title":"优化前的基线 mainloop",
  "paras":[
   "先回到底层:t​cgen05.mma 的累加器住 TMEM——每 SM 一块 **128 lane × 512 列**的 32-bit cell 阵列。warp 用 tcgen05.ld / tcgen05.st 对它读、写。hdim 64 的 FA4 backward 默认分配如 Figure 1:",
  ],
  "fig_after":{"0":[{"src":"fig01.png","caption":"图 1 hdim 64 基线 TMEM 分配。上排:tcgen05.mma 写出的 fp32 累加器;下排:compute warps 覆盖写上的 bf16 tile——P 叠在 S 上、(dQ partial 与) dS 叠在 dP 上。列 [384,512) 未使用。"}]}},
 {"type":"h2","title":"别名让谁有风险",
  "paras":[
   "四个 fp32 累加器占列 [0,384);P、dS 是 bf16(每列可 pack 2 个),写进对应 S、dP 的槽。因为同址,就得先保证 S 被它所有消费者读完、任何生产者才写 P,以此类推。",
   "若这些读写作不设防会怎样?TMEM 有一条硬限制:**每个 warp 只能访问自己那 32-lane 扇区**——warpgroup 的 warp 0/1/2/3 分别占 lane [0,32)、[32,64)、[64,96)、[96,128)。FA4 backward 的八个 compute warp 组成两个 warpgroup,所以 warp 4/5/6/7 与 warp 8/9/10/11 共享同一套 TMEM 扇区。再叠加同址别名,就造成下面这张跨 warp hazard:",
  ],
  "fig_after":{"0":[{"src":"fig02.png","caption":"图 2 把 P 存进 S 产生的 hazard。每个 compute warp 只 load 自己的 32 lanes;warp 5 可能在 warp 9 还没读完 S 时就开始往里写 P。"}]}},
  ]}

# 占位保持字典闭合后可追加
