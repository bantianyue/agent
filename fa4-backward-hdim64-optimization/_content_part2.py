# -*- coding: utf-8 -*-
# content part2: 别名guard/dS loop → 移除guard思路 → deque 分配(图4) → 三处改动(code3/code4) → 图5
#                 → results(图6) + ablation(图7,8) + deterministic → conclusion
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
C3 = """
if self.split_P_dS:
    # P/dS are bf16 packed two per column: a 128-wide tile is tile_m // 2 columns
    self.tmem_P_offset = self.tmem_dK_offset + self.tile_hdim   # [384, 448)
    self.tmem_dS_offset = self.tmem_P_offset + self.tile_m // 2 # [448, 512)
"""
C4 = """
cute.copy(thr_copy_t2r, tStS_t2r, tSrS_t2r)   # S -> registers
if const_expr(self.split_P_dS):
    # S is in registers: release it now, before the softmax,
    # so the MMA warp can issue the next QK into the slot.
    cute.arch.fence_view_async_tmem_load()
    cute.arch.sync_warp()
    with cute.arch.elect_one():
        pipeline_S_P.consumer_release(consumer_state_S)
"""

DATA={
"sections":[
 # -- alias guard 落地(code1) --
 {"type":"p"  } if False else None,
 {"type":"h3","title":"别名守卫 alias guard：谁在读 S、谁在写 P",
  "paras":[
   "上图画的现象,用 CUTE 代码表示为一条『P 覆盖 S』的栅栏——每个 warp 装完自己的 S 后才能让别人写 P(下方剪的一小段,去完 tmem fence 后是核级 barrier arrive_and_wait):",
   "__CODE__cpp::"+C1,
   "我们把它叫一个 **alias guard**(P 对 S 一个,dS 对 dP 一个)。它本质是**compute-wide barrier**:一条 named barrier,把全部八个 compute warp(256 线程)同步到同一点。P guard 每轮 mainloop 需要一次;dS guard 在两级 dS 循环里,所以每轮 mainloop 需要两次。baseline 的 TMEM 分配强迫这两个守卫存在,且每个栅栏都把所有 warp 压在最慢那个 pace 上——这就把性能摁在了地板上。",
   "别名还限制了 MMA warp 发 GEMM 的顺序:因为 S 与 P 在 TMEM 里同址,下一 tile 的 S MMA 必须等当前 tile 的 dV MMA 执行完才能发,于是 dV MMA 暴露在它对 P 的依赖上——其间 tensor core 不干实事。baseline 默认发出顺序是:QK_t+1,dK_t,dQ_t,dP_t+1,PdO_t+1。下面 Figure 3 的 trace 显示,hdim 64 下 dK、dQ、dP 这几次 matmul 并不足以藏住 softmax。",
  ],
  "fig_after":{"2":[{"src":"fig03.png","caption":"图 3 基线 mainloop 的一次迭代(kernel 内时间戳测,单 CTA、SM 周期)。上:MMA warp 发的 GEMM;下:八个 compute warp。因为每个 tile 有五道 compute-wide barrier(红虚线画在最慢 warp 到达处),所有 warp 绑在同速上。下一 tile 的 QK 要等 softmax 结束、P 被 dV 消费才发出。softmax 期间 tensor core 只算 dQ_t−1 与 dP_t,大部分时间空置。(注:图里 PdO_t 误标为 PV_t——概念上等价,都是 P 的 mma 消费方。)"}]},
 {"type":"h3","title":"另两道只是『信号栅栏』",
  "paras":[
   "此外每 tile 还有两道 compute-wide barrier:在 compute warps 每次 store 后发的两个 signal 之前。它们不保护任何跨 warp hazard,只是各自 warp 自己的 store fence。合计四个 barrier 站点、每轮 mainloop 执行五道 compute-wide barrier。",
  ]},
 {"type":"h3","title":"baseline 释放 S 用的是融合信号",
  "paras":[
   "在 baseline,compute warps 给 MMA 发的是『S 已被读、P 已写好』的融合信号,代码如(去完 tmem/shared fence 后 arrive_and_wait,再由 elect_one warp 释放两个 pipeline 的消费态):",
   "__CODE__cpp::"+C2,
  ]},
 # -- 优化前结束,优化方案 ---
 {"type":"h2","title":"优化：给 P 与 dS 单独开 TMEM 槽",
  "paras":[
   "方案最重要的一步,是对 P 与 dS **去别名**:给它们各自专属槽,不再叠写到 S/dP 上。拿掉 [384,512) 空闲列按 bf16 每列两个 pack,分配见 Figure 4:",
  ],
  "fig_after":{"0":[{"src":"fig04.png","caption":"图 4 去别名后的 TMEM 分配局部。P 与 dS 是半精度,故逻辑形状 128 宽只需一半列数。"}]}},
 {"type":"h3","title":"随之而来的三处内核改动",
  "paras":[
   "TMEM 分配一变,内核做三处修改。",
   "**1. 移除 alias guards。** 既然 P 与 dS 有专属槽,Figure 2 的跨 warp hazard 不可能发生,于是把两个 alias guard 直接删掉(当然,tmem fence 本身保留)。分配槽时的判断代码大概长这样(split_P_dS 为真时让 P 从 [384,448)、dS 从 [448,512) 起,两段按半精度宽度 tile_m/2 或 tile_hdim 排布):",
   "__CODE__cpp::"+C3,
  ]},
 {"type":"h3","title":"把『S 读 与 P 写』拆成两条流水线",
  "paras":[
   "**2. 更早释放 S。** baseline 里,S 与 P 共用同一个 pipeline 对象,一个信号『S read and P written』在 P store 完之后发,MMA warp 在它前后分别等 QK_t+1 与 该轮 PV_t。拆分 TMEM 之后把这条重建成两条:pipeline_S_P 只载『S read』——compute warps 把 S 一读进寄存器就发,先于 softmax;MMA warp 等它再发 QK_t+1。另起一条单级 pipeline_P 载『P written/P consumed』:write 完发 P written,MMA 等它发 PV_t;compute warps 也要等 P consumed 才能覆写下一轮 P。提前释放的代码见图下:",
   "__CODE__cpp::"+C4,
  ]},
 {"type":"h3","title":"重排 MMA warp 的发出顺序",
  "paras":[
   "**3. 重排 MMA warp。** 拿到独立 P 槽后,QK_t+1 只依赖 S 已被 consume,于是 MMA warp 一收到 S read 信号就能发 QK_t+1,排在 PdO_t 之前。发出顺序变成:QK_t+1,PdO_t,dK_t,dQ_t,dP_t+1。t 轮 softmax 期间能塞的 tensor-core 活多了一块 QK_t+1,差不多填满 Figure 3 里那段空闲。",
   "**剩下三道 barrier。** 每道 signal 前的三个 compute-wide barrier 还留着,但因为不再有跨 warp hazard,可以整体换成 warp sync——八个 warp 就能在 softmax 与 dS 段自由漂移,所有 compute-wide barrier 都被消灭。",
   "改完的 IKET trace 明显更短:",
  ],
  "fig_after":{"2":[{"src":"fig05.png","caption":"图 5 下一 tile 的 QK 现在在 softmax 中段就发出,八个 warp 自由漂移——循环里没有任何东西让它们等待彼此,tile 缩短约 19%(56 个 tile 的中位数)。"}]}},
 # ---------- 实现细节跳过的可读性块, 直接进 Experiments/Results ----------
 {"type":"h2","title":"效果：B200 上的实测",
  "paras":[
   "B200、输入 bf16(另注明的除外)、32 query heads、每 call 64k tokens(batch×sequence)。每个数字为同一内核连续跑多遍的中位数。TFLOP/s 把 backward 计为 forward 的 2.5× FLOPs,利用率相对 2250 TFLOP/s 稠密峰值。deterministic 模式下,每个变体的梯度都与 baseline 逐位一致。测环境:PyTorch 2.13.0、nvidia-cutlass-dsl 4.6.2、driver 595.71.05。kernel 改动在 [PR #2804](https://github.com/Dao-AILab/flash-attention/pull/2804)。",
  ],
  "fig_after":{"0":[{"src":"fig06.png","caption":"图 6 hdim 64 FA4 backward 改前 vs 改后,B200,bf16。右轴是相对 2250 TFLOP/s 稠密峰值的占比。"}]}},
 {"type":"h3","title":"成套吞吐对比表",
  "paras":[
   "下面把几种重点构型的前后 TFLOP/s 与加速比列成表(64k tokens):",
  ],
  "table":{"head":["shape(64k tokens)","mode","before TFLOPS","after TFLOPS","speed-up"],
   "rows":[
    ["b2 s32k h32:32","dense","731","841","1.150×"],
    ["b2 s32k h32:32","causal","705","808","1.147×"],
    ["b4 s16k h32:8","dense","840","903","1.075×"],
    ["b4 s16k h32:8","causal","750","842","1.123×"],
    ["b8 s8k h32:32 fp16","dense","692","782","1.131×"],
    ["b4 s16k h32:32","dense, deterministic","709","774","1.091×"],
    ["b4 s16k h32:32","causal, deterministic","664","725","1.093×"]]}},
 {"type":"h3","title":"消融：把去别名与 per-warp 信令拆开算",
  "paras":[
   "Figure 7 的消融把『去别名』与它使能的『per-warp 信令』分开评估:单开专属槽在 dense 上约值 2%、causal 上 3–4%;只做 per-warp 信令(不动去别名)dense 上游 8–9%,causal 上几乎没收益(1.00–1.01×)——因为两级循环里的两个 alias guard 必须保留,而 causal 的循环又是最短的。合在一起,dense 值 13–15%、causal 11–15%;大头收益只有去掉 alias guard 之后才拿得到。",
  ],
  "fig_after":{"0":[{"src":"fig07.png","caption":"图 7 分别只看某个改动、以及两者一起时相对基线的加速比。"}]}},
 {"type":"h3","title":"只去别名、还带核级栅栏的中间形态",
  "paras":[
   "把『只给 P/dS 专属槽、其余不动』的中间版本单独拿出来看,能确认收益来自哪里:单去掉别名就把 QK 挪进 softmax、warp 开始在其中漂移一步;但它们的 S release(绿)仍对齐、signal P 段同时结束、dS 段同时开始——每 tile 仍要等最慢的 warp 三次。所以 tile 只短约 5%。",
  ],
  "fig_after":{"0":[{"src":"fig08.png","caption":"图 8 同一 tile、只加专属槽(dedicated TMEM slots only),同比例。去别名单独就把 QK 移进 softmax,并让 warp 开始漂移;但它们的 S 释放排成竖线、signal P 段同终、dS 段同起,每 tile 仍三次等最慢 warp,故仅短约 5%。"}]}},
 {"type":"h3","title":"确定性(deterministic)模式",
  "paras":[
   "deterministic 模式里 kernel 受限于 dQ 累加的 semaphore 顺序。但它只是把收益封顶而不抹掉:确定性扫盘的半区改善 1.05×(其余 1.13×),上面的表中 deterministic 行也还有 9%。在 deterministic 模式还要更快,应当像 hdim 128 那样用 2-CTA MMA——dS 经 DSMEM 的 2-CTA 交换把 dQ MMA 的归约延展到 cluster tile 之上,从而砍掉一半的 dQ 原子加。",
  ]},
 {"type":"h2","title":"结语",
  "paras":[
   "FA4 backward 默认设计在 hdim 64 时留了四分之一 TMEM 不用。这篇优化的主菜是:**把这四分之一让给 P 与 dS 开专用槽**,让 compute warps 不再写到自己在读的 S/dP 缓冲上——拿掉因此产生的跨 warp hazard,也就删掉了护着它的两个核级栅栏。删掉之后,剩下的三道 barrier 只护着每个 warp 自己的 store,一道 warp-local sync 就够。mainloop 从此不需要任何核级栅栏,tensor core 在当前 softmax 底下就能起手下一 tile 的 QK。实测 6–15% 的加速,峰值 903 TFLOPS。",
  ]},
],
}
