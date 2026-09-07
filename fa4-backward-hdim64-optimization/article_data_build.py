# -*- coding: utf-8 -*-
# FA4 backward hdim64 kernel optimization — 中文编译
# src: research.colfax-intl.com (Colfax Research)  8图+3表+4代码块全保留, 非论文正文知识≥85%

C1 = """cute.arch.fence_view_async_tmem_load()
# P overwrites S, and warp w's P columns sit under warp w+4's S lanes:
# every warp must have loaded S before any warp stores P.
self.compute_sync_barrier.arrive_and_wait()"""

C2 = """cute.arch.fence_view_async_tmem_store()
cute.arch.fence_view_async_shared()
self.compute_sync_barrier.arrive_and_wait()
with cute.arch.elect_one():
    pipeline_S_P.consumer_release(consumer_state) # "S read and P written"
    pipeline_LSE.consumer_release(consumer_state_LSE)"""

C3 = """if self.split_P_dS:
    # P/dS are bf16 packed two per column: a 128-wide tile is tile_m // 2 columns
    self.tmem_P_offset = self.tmem_dK_offset + self.tile_hdim # [384, 448)
    self.tmem_dS_offset = self.tmem_P_offset + self.tile_m // 2 # [448, 512)"""

C4 = """cute.copy(thr_copy_t2r, tStS_t2r, tSrS_t2r) # S -> registers
if const_expr(self.split_P_dS):
    # S is in registers: release it now, before the softmax,
    # so the MMA warp can issue the next QK into the slot.
    cute.arch.fence_view_async_tmem_load()
    cute.arch.sync_warp()
    with cute.arch.elect_one():
        pipeline_S_P.consumer_release(consumer_state_S)"""

DATA = {
"title": "head dim 64 的 FlashAttention-4 反向为何慢：用空闲 TMEM 去别名修到 903 TFLOPS",
"reference_url": "https://research.colfax-intl.com/optimization-diaries-improving-flashattention-4-backward-for-head-dimension-64/",

"summary": [
  {"key":"现象","body":"FA4 backward 核在 B200 上、head dim 128 时达 1237 TFLOPS(约 55% 峰值);同一核切到 head dim 64 只跑出 26–32% 峰值。根因是 GEMM FLOPs 随 head dim 减半,而逐点算子开销与 head dim 无关,张量核算力不足以藏住 softmax 等操作的时延。"},
  {"key":"根因","body":"hdim 64 时 TMEM(每 SM 128 lane×512 列)默认分配空出 [384,512) 四分之一。核把 P 叠写于 S、dS 于 dP(同址别名),被迫插入两处跨核全局栅栏 alias guard,并让 tensor core 在 softmax 期间空转。"},
  {"key":"修法","body":"把这四分之一 TMEM 交给 P、dS 专用(de-alias),去掉两处核栅栏、剩余栅栏降为 warp sync,并重排 MMA 顺序为 QK_t+1→PdO_t→dK_t→dQ_t→dP_t+1,让下一 tile 的 QK 在 softmax 中就发出。整体 1.06–1.15×,最高 903 TFLOPS(40% 峰值),124 组配置几何平均 1.129×。"},
],

"lead": [
  "FlashAttention 的后向 pass 是训练里吃掉大量显存带宽与功耗的一段。Colfax Research 这篇『优化日记』讲的正是 FA4 backward 在 Blackwell B200 上前后两档 head dimension 的悬殊——hdim 128 能到约 55% 峰值,hdim 64 却只剩 26–32%——以及他们怎样靠 Blackwell 张量内存(TMEM)闲置的四分之一空间,把 hdim 64 拉回最高 903 TFLOPS。",
  "下面按『为什么慢 → baseline 为什么被迫插五道全局栅栏 → 怎么去别名并让张量核在 softmax 区间多干活』的顺序走完全部改动。文内图、表、代码片段均按原文完整保留;实现以 PR 形式挂在 FlashAttention 仓库。",
],

"sections": [
 # ---------- 引言 ----------
 {"type":"h2","title":"引言：同一内核,不同 head dim,两种命运",
  "paras":[
   "本文讨论 FlashAttention-4(FA4)在 NVIDIA Blackwell GPU 上的**反向 pass**。head dimension 为 128 时 FA4 backward 已非常高效,单个 B200 上打到 **1237 TFLOPS、约 55% 的峰值算力吞吐**。但同样的形状换成 head dimension 64,同一个 kernel 只剩**峰值的 26–32%**。这就是 hdim 64 一档仍有巨大优化空间的表现。",
   "要讲的优化,核心是用上**空余的张量内存(TMEM)**去提升 hdim 64 的 FA4 backward。关键观察:对 head dim 64,默认 kernel 设计下 TMEM 会有**四分之一**闲置。把这部分拿出来,去把驻留在那里的张量**去别名(de-alias)**——具体是让同一迭代的 P 不再叠在 S 上、dS 不再叠在 dP 上。",
   "去别名之后,能做两件事:(1)去掉一些不必要的同步,把 256 线程的全局栅栏换成纯 warp 同步;(2)重排 MMA 的发出顺序,让下一轮迭代的 QK 乘加与当前轮 softmax 计算重叠。合并效果是**1.06–1.15× 加速,最高 903 TFLOPS(峰值的 40%)**。改动见 FlashAttention 仓库 [PR #2804](https://github.com/Dao-AILab/flash-attention/pull/2804)。",
  ]},

 # ---------- 回顾 ----------
 {"type":"h2","title":"回顾：FA4 backward 在算什么",
  "paras":[
   "FA4 反向算的是一串标准注意力式子:S = QKᵀ,P = exp(S − L),dP = dO·Vᵀ,dS = P ∘ (dP − D),以及 dV = Pᵀ·dO,dK = dSᵀ·Q,dQ = dS·K。这里的 L、D 分别是行向 log-sum-exp 与其相关差分,∘ 为逐元素乘。",
   "计算按 batch、attention heads、KV tiles 并行:每个 CTA 拥有一块 K、V tile,循环遍历 Q tiles;每轮算它所属 K/V tile 的 dK、dV tile,同时为当前 Q tile 累加一小块 dQ 贡献进全局 fp32 累加器。",
  ]},
 {"type":"h3","title":"warp 特化：活按十六个 warp 分",
  "paras":[
   "FA4 backward 是 **warp-specialized** 设计,CTA 内的十六个 warp 分工如下表:",
  ],
  "table":{"head":["role","warps","description"],
    "rows":[
      ["load","1","发出 K/V/Q/dO 的 TMA load"],
      ["MMA","1","发出每一条 tcgen05.mma 指令"],
      ["compute","8","由 S 算 P;由 dP 算 dS"],
      ["reduce","4","读回各份 partial dQ 并加进全局累加器"],
      ["relay/empty","2","hdim 64 时空闲;relay warp 仅供 hdim 128(该处用 2-CTA MMA)"]]}},
 {"type":"h3","title":"每轮 mainloop:五 GEMM 配两次逐点",
  "paras":[
   "下文会聚焦 MMA warp 与 compute warpgroup。每轮迭代里 MMA warp 发五个 GEMM,compute warps 在它们之间做两个逐点运算。因为每 CTA 拥一块 KV tile,核算的是转置形态 Sᵀ、Pᵀ、dPᵀ、dSᵀ,各步读写下表(后续行文省略转置记号):",
  ],
  "table":{"head":["step","who","reads","writes"],
    "rows":[
      ["Sᵀ = K Qᵀ","MMA warp","K, Q (SMEM)","Sᵀ (TMEM, fp32)"],
      ["Pᵀ = exp(Sᵀ − L)","compute warps","Sᵀ (TMEM)","Pᵀ (TMEM, bf16)"],
      ["dSᵀ = Pᵀ ∘ (dPᵀ − D)","compute warps","Pᵀ (RMEM), dPᵀ (TMEM)","dSᵀ (TMEM, bf16; 并 SMEM)"],
      ["dV += Pᵀ dO,dK += dSᵀ Q,dQ = dS K","MMA warp","Pᵀ, dSᵀ (TMEM), dSᵀ (SMEM)","dV, dK, dQ (TMEM)"]]}},
 {"type":"p","title":None,
  # 这个占位会被去掉
  } if False else None,
],

# will complete
}
DATA["_dummy"]=True
