# -*- coding: utf-8 -*-
"""NVFP4 完整重生成 build"""
import json, os, sys

DATA = {
 "title": "七轮迭代把 NVFP4 块缩放 GEMM 逼近 cuBLAS：RTX PRO 6000 (SM120) 调优实录",
 "lead": [
  "本文是 Colfax Research 针对 RTX Pro 6000 Blackwell Server Edition（SM120）优化 NVFP4 块缩放 GEMM 的完整记录。在 Blackwell SM12x GPU 上做 NVFP4 块缩放 GEMM，难点不仅在 MMA 指令本身，更在缩放因子（SFA/SFB）的布局、bank 冲突、以及如何让 Tensor Core 始终忙碌。",
  "作者从第 1 部分的基线内核出发，经线程块 swizzling、epilogue 改进、warp 专用化存储、消除 SFA bank 冲突、12 路 MMA warp、自动调优共七轮迭代，并在附录补充了 Cluster Launch Control 与缩放因子加载实验。全文保留原文绝大部分技术细节与代码片段。"
 ],
 "summary": [
  {
   "key": "优化路径",
   "body": "从基线内核出发，经线程块swizzling、epilogue改进、warp专用化存储、消除SFA bank冲突、12路MMA warp、自动调优七轮迭代。"
  },
  {
   "key": "关键收益",
   "body": "对比版本1，版本7在2k提升29%、4k提升6%、8k提升4%、16k提升16%、32k提升40%；五种问题形状平均与cuBLAS 13.6相当。"
  },
  {
   "key": "核心难点",
   "body": "NVFP4块缩放GEMM的关键在缩放因子的SMEM布局与bank冲突、以及让Tensor Core持续忙碌的warp调度与流水线同步。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "背景与硬件规格",
   "paras": [
    "本文是 SM12x GPU 上 NVFP4 块缩放系列文章的延续。第 1 部分覆盖了相关 PTX 指令、缩放因子布局细节及 CuTe DSL 实现（如何将 CUTLASS 稠密 GEMM 转换为 NVFP4 块缩放 GEMM）。本文针对 RTX Pro 6000 Blackwell Server Edition（SM120）做具体优化。",
    "本文沿用此前同一内核配置的版本：在前一篇文章的开头已指出，基线版本在中等问题规模上已相当高效，因此这里瞄准两个方向——针对小/大问题规模的已知问题做定向优化；以及累积起来能提升所有规模的微优化。优化阶梯结束时，在 2k 获得 29%、4k 获得 6%、8k 获得 4%、16k 获得 16%、32k 获得 40% 的计算吞吐增益。",
    "所有基准用 Python 3.13.13、PyTorch 2.12.1 与 nvidia-cutlass 相关版本产出；文中所有优化的代码均包含在 Colfax Research 的 GitHub 仓库中。RTX Pro 6000 的规格：96 GB GDDR7 显存、约 1.6 TB/s 带宽；24,064 CUDA 核心；188 个 SM；12 个 GPC；752 个第五代 Tensor Core（每 SM 4 个）；L1 128 KB/SM；L2 128 MB；峰值 FP4 Tensor TFLOP/s（FP32 累加）2015.2；最大 SM 时钟 2.43 GHz。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "版本1：基线内核",
   "paras": [
    "先从上一篇文章的内核结构快速回顾。内核采用 warp 特化设计、生产者-消费者流水线：每个 CTA 含 1 个 TMA 加载 warp 和 8 个 MMA warp。加载 warp 为 A、B、SFA、SFB 操作数发起 TMA 拷贝到 SMEM；主循环结束后，MMA warp 执行尾声（epilogue），把输出写入 SMEM，再由 warp 0 从 SMEM 发起 TMA 存储到全局内存。",
    "内核用静态持久化分块调度器（static persistent tile scheduler），每个 SM 驻留单个 CTA；每个 work tile 被调度到驻留它的 CTA 上。",
    "图 2 包含版本1 的计算吞吐（TFLOP/s）数据，取自 3 次预热迭代后 20 次迭代的平均运行时间。对 8k 方形 GEMM，得到 1476 TFLOP/s，约 73% 利用率。五种问题形状平均，版本1 达到 cuBLAS 13.6 的约 93%，但在 32k 处明显崩塌。此外，较大的问题形状下 SM 时钟会降至 2.15GHz。"
   ],
   "fig_after": {
    "2": [
     {
      "src": "fig01.png",
      "caption": "图 2：版本1 的计算吞吐（TFLOP/s）与 cuBLAS 13.5/13.6 对比。8k 处约 1476 TFLOP/s、73% 利用率；五种形状平均约 cuBLAS 的 93%，32k 下降明显。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "版本2：线程块 Swizzling",
   "paras": [
    "从性能图可见内核在大问题规模下性能下降。用 Nsight Compute 分析这种伸缩行为的来源：2k 到 8k 时 DRAM 吞吐稳定在 10%–14%，到 16k 和 32k 则跃升至 64%–86%；同时 L2 命中率从 8k 到 16k 下降、32k 时跌到 76.31%。对计算密集型 GEMM 而言，这提示问题出在内存（带宽/缓存）扩展性上。",
    "为何高于 8k 会发生陡变？考虑各问题形状的输入内存足迹：输入是形状为 M×K 与 K×N 的矩阵 A、B。对 8k 而言，A、B 各约 0.5 GB，累计输入足迹约 1 GB（若按 FP16，数据约 1GB 分块装载到 L2）。虽然 NVIDIA GPU 的精确 L2 驱逐策略未公开，但一般原则是同一数据越快被复用就越可能驻留在 L2。因此要提高 L2 命中率，就该让工作调度更倾向数据复用。",
    "回忆 CTA 的分配方式：CTA 被分配 C 的工作 tile，并加载同行的 A tile、同列的 B tile。换言之，同一行的 C tile 的 CTA 需要相同的 A tiles，同一列的 C tile 的 CTA 需要相同的 B tiles。考虑一个假想 GPU：8 个 SM、启动 8 个 CTA、C 矩阵切成 8×8 网格。每个 wave 里发出 16 个操作数 tile 集的加载（一个操作数 tile 集即该 wave 需要的全部 A/B tile）。",
    "如果沿 m 维线性分配工作 tile，就处于图 4 最左的情形——需要 9 个不同的操作数 tile 集：8 个 A、1 个 B。但如果把工作 tile 按 swizzled 网格分配（如棋盘式对角分布），同一 wave 的 CTA 会共享更多操作数。图 4 中间和右侧显示 swizzle_size 更大的情形，每个 wave 加载的 A/B tile 集总数从 9 降到 5、再到 3。",
    "再看 32k 情形：CTA tile 128×128 时，得到 256×256 的工作 tile 网格。由于有 188 个 SM，调度时每个 wave 跨 swizzle_size 的整数上界（ceil(188/swizzle_size)）行 × swizzle_size 列的工作 tile。图 5 总结了多种 swizzle_size 选择下单个 wave 加载的不同 A/B tile 数。本版把 swizzle_size 设为 16，因为它给出每 wave 不同分块总数最少（28）。",
    "最大提升出现在 32k，吞吐提升 387 TFLOP/s。再看版本2 的 Nsight 内存工作负载分析输出：16k 和 32k 的 L2 命中率明显上升、对应的 DRAM 吞吐下降——即 swizzle 调度把工作 tile 的操作数分配给更可能在 L2 驻留的 CTA。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 3：Nsight 内存工作负载分析——DRAM/L2 吞吐与命中率随问题规模的变化，决定 swizzle 方向。"
     }
    ],
    "3": [
     {
      "src": "fig03.png",
      "caption": "图 4：不同 swizzle_size 选择下单波次加载的 A/B 分块数量示意。"
     },
     {
      "src": "fig04.png",
      "caption": "图 5：swizzle_size=16 与默认方案下分块加载对比（每 wave 不同分块总数最少为 28）。"
     }
    ],
    "5": [
     {
      "src": "fig05.png",
      "caption": "图 6：版本2 性能（TFLOP/s）与 cuBLAS 对比，32k 提升最显著（+387 TFLOP/s）。"
     },
     {
      "src": "fig06.png",
      "caption": "图 7：版本2 的 Nsight 内存工作负载输出，展示 L2/DRAM 指标改善来源。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "版本3：改进 Epilogue",
   "paras": [
    "要确保内存依赖逻辑之类的东西不会不必要地阻塞内核内的操作。考虑 epilogue：内核已经用了流水线化的异步存储，但有两处可改的同步逻辑。",
    "<pre style=\"background:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,monospace;font-size:13px;line-height:1.5;\"><code>while work_tile.is_valid_tile:\n    . . .\n    tma_store_producer_group = pipeline.CooperativeGroup(\n        pipeline.Agent.Thread,\n        self.num_mma_warps * self.num_threads_per_warp,\n    )\n    tma_store_pipeline = pipeline.PipelineTmaStore.create(\n        num_stages=self.epi_stage,\n        producer_group=tma_store_producer_group,\n    )\n</code></pre>",
    "这段 tma_store_pipeline 的设置原本放在 work-tile 循环之前（即每个 work tile 都重复设置同一 pipeline）。版本3 把它直接移到 work-tile 循环之前，消除了重复设置。",
    "再看来自版本1 与版本2 的这段主体（版本3 的完整 epilogue 循环）：",
    "<pre style=\"background:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,monospace;font-size:13px;line-height:1.5;\"><code>for epi_m in cutlass.range_constexpr(epi_rest_m):\n    for epi_n in cutlass.range_constexpr(epi_rest_n):\n        MmaMPerEpiM = epi_tile_m // mma_tile_m\n        MmaNPerEpiN = epi_tile_n // mma_tile_n\n        for mma_n_in_epi in cutlass.range_constexpr(MmaNPerEpiN):\n            for mma_m_in_epi in cutlass.range_constexpr(MmaMPerEpiM):\n                mma_n = (epi_n * MmaNPerEpiN) + mma_n_in_epi\n                mma_m = (epi_m * MmaMPerEpiM) + mma_m_in_epi\n                tRS_rD_slice = tRS_rD[(None, mma_m_in_epi, mma_n_in_epi)]\n                tRS_rAcc_slice = tRS_rAcc[(None, mma_m, mma_n)]\n                for elem_idx in cutlass.range_constexpr(cute.size(tRS_rD_slice)):\n                    tRS_rD_slice[elem_idx] = tRS_rAcc_slice[elem_idx]\n\n        # Type conversion with alpha scaling\n        tRS_rD_out = cute.make_rmem_tensor(tRS_rD_layout.shape, self.c_dtype)\n        acc_vec = tRS_rD.load()\n        # Multiply alpha in FP32 before converting to c_dtype\n        # to avoid overflow when c_dtype is FP16\n        acc_vec = epilogue_op((alpha_value * acc_vec).to(self.c_dtype))\n        tRS_rD_out.store(acc_vec)\n\n        # Register to shared memory\n        epi_buffer = (epi_m * epi_rest_n + epi_n) % cute.size(tRS_sD, mode=[3])\n        if has_multi_epi_store:\n            self.epilog_sync_barrier.arrive_and_wait()\n        cute.copy(\n            tiled_copy_r2s,\n            tRS_rD_out,\n            tRS_sD[(None, None, None, epi_buffer)],\n        )\n        cute.arch.fence_proxy(\n            \"async.shared\",\n            space=\"cta\",\n        )\n        self.epilog_sync_barrier.arrive_and_wait()\n\n        # Copy from shared memory to global memory\n        gmem_coord = (epi_m, epi_n)\n        if warp_idx == 0:\n            cute.copy(\n                tma_atom_c,\n                bSG_sD[(None, epi_buffer)],\n                bSG_gD[(None, gmem_coord)],\n            )\n            if has_multi_epi_store:\n                tma_store_pipeline.producer_commit()\n                tma_store_pipeline.producer_acquire()\n\n\n# Advance to the next work tile\ntile_sched.advance_to_next_work()\nwork_tile = tile_sched.get_current_work()\nif has_multi_epi_store:\n    tma_store_pipeline.producer_tail()\n</code></pre>",
    "producer_acquire() 调用发生得过早。在当前布局里，即使存在多个 epilogue 阶段，producer_acquire() 也会阻塞；此外 producer_tail() 位于错误的循环深度——它应当在所有 work tile 都处理完之后正确收尾。",
    "版本3 的修复：把 producer_tail 移出 warp 循环，并把 producer_acquire() 调用延后到紧挨着写入共享内存之前（即紧贴在 self.epilog_sync_barrier.arrive_and_wait() 之前）。基准里用两个 epilogue 阶段、64×64 的 epilogue subtile。剖析显示从版本2 到版本3 长 scoreboard stall 略有下降。",
    "总体而言，效果很小，处于基准测试波动范围内（如图 9 所示）。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig07.png",
      "caption": "图 8：epilogue 代码路径中 producer_acquire / producer_tail 同步逻辑的调整示意。"
     }
    ],
    "6": [
     {
      "src": "fig08.png",
      "caption": "图 9：版本3 性能与 cuBLAS 对比——改进影响很小，处于基准波动范围。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "版本4：Warp 专用化存储",
   "paras": [
    "在计算密集型内核（如 GEMM）里，我们希望 Tensor Core 始终忙碌，即总有一个带着 MMA 工作的 warp 随时可被调度。达成的一种方式是对加载路径做 warp 特化；但存储仍由计算（MMA）warp 完成，会与 MMA 争用。版本4 把存储也特化给存储 warp。",
    "实现层面，存储 warp 必须告知 MMA warp：某个 SMEM 阶段何时可安全覆盖；MMA warp 则要告诉存储 warp：该阶段何时已含完整输出。二者通过 CUDA named barrier 协调。",
    "<pre style=\"background:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,monospace;font-size:13px;line-height:1.5;\"><code>self.epilog_free_barrier = pipeline.NamedBarrier(\n    barrier_id=2,\n    num_threads=(self.num_mma_warps + 1) * self.num_threads_per_warp,\n)\nself.epilog_ready_barrier = pipeline.NamedBarrier(\n    barrier_id=3,\n    num_threads=(self.num_mma_warps + 1) * self.num_threads_per_warp,\n)\n</code></pre>",
    "SM120 有 16 个硬件管理的命名屏障，barrier_id 指定用 16 个中的哪一个；num_threads 指定要到达该屏障的总线程数（这里设为 MMA warp 数与存储 warp 数之和、乘以每 warp 线程数）。",
    "存储 warp 先对其内部 TMA 存储流水线调 producer_acquire，然后到达 epilog_free_barrier，向 MMA warp 发出该阶段空闲可写的信号；等待 epilog_ready_barrier 后，它发出 store 完成通知、提交并获取下一阶段。版本4 的 kernel 结构总览见图 10（本图见文末）。",
    "版本4 的基准结果：2k 与 16k 提升约 1%，其余不变（图 11 见文末对应图）。"
   ],
   "fig_after": {
    "3": [
     {
      "src": "fig09.png",
      "caption": "图 10：版本4 warp 专用化存储的 kernel 结构总览——存储 warp 经命名屏障与 MMA warp 协调。"
     }
    ],
    "4": [
     {
      "src": "fig10.png",
      "caption": "图 11：版本4 性能与 cuBLAS 对比——2k 与 16k 约 +1%，其余不变。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "版本5：消除 SFA bank 冲突",
   "paras": [
    "版本5 处理 bank 冲突。虽然本版改动本身不显著影响性能，但消除这类共享内存访问的低效是良好实践，也为后续缩放因子相关改动扫清障碍。SMEM 排成 32 个 4 字节宽的 bank；若一个 warp 对分布在全部 32 个 bank 的不同地址发起访问，SMEM 可在一个周期内服务该请求；若多个地址落在同一 bank，访问就被串行化、需要额外周期。",
    "Nsight 指标 L1 Wavefronts Shared Excessive 是这类冲突的信号。Nsight 对该指标报告 8.39M，且 SMEM 到寄存器的数据搬运（tiled_copy_r2s）耗时异常高。让我们量化这一冲突。回忆上一篇文章中 SFA 的 SMEM 布局：",
    "SFA 布局：((32,4), REST_M) 与 ((16,4), 1, REST_K) 组合成 (((16, 4), 512 * REST_K), ((0, 1), 4, 512))。其中 M 子布局 (32,4):(16,4) 把 128×128 CTA tile 的 m 坐标分解为 m = m0 + 32·m1（m0 = m mod 32，m1 = ⌊m/32⌋ mod 4）；K 子布局 (16,4):(0,1) 反映缩放因子组织，stride 0 把一个缩放因子广播到 NVFP4 元素的 16 个元素。",
    "由此推出的 byte offset = 16·m0 + 4·m1 + b，对应 bank index = ⌊(byte offset/4)⌋ (mod 32)。考虑 SFA 第 0–15 行的元素：此时 m1 = 0，每个 bank index 都是 4 的倍数。观察可知 row 0 与 row 8 的缩放因子地址都落在 bank 0；更一般地，row r 与 row r+8 的缩放因子地址落在同一 bank——16 个地址分布在 8 个 bank 上，每个 bank 有两个地址访问，需要 2 个 wavefront。",
    "SFA 原子的 TV 布局是 ((2, 2, 8), 64): ((8, 0, 1), 16)。回忆上篇：每个 quad 只有两个线程真正向 MMA 指令喂缩放因子数据，因此存在冗余。图 13（见文末）显示了每个 lane 从 SMEM 的哪个 bank 请求 SFA 数据：warp 访问总共 8 个 bank、同一 quad 内 4 个 lane 访问同一 bank……。",
    "要得到 Nsight 报告的数：对 8k 问题形状，M=N=8192，把总指令数分解为 64×64×64×8×4×1 = 8,388,608，与报告的 8.39M 完全吻合。",
    "布局层面的修复很直接：修改 stride——(32, 4):(4, 128)，等价于 rank-1 布局 128:4。现在 byte offset = 4·m0 + 128·m1 + b = 4(m0+32m1)+b = 4m+b，于是每个行有独立 bank index。保持 SFA 的 TV 布局不变，新的 SMEM 到寄存器搬运访问模式使每次 SFA 片段加载在单个 wavefront 内完成。注意 SFA 原子的 cosize 不变——两个布局在相同定义域上都是双射，只是字节在原子内部重排。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig11.png",
      "caption": "图 15：SFA 的 SMEM 布局——行 r 与行 r+8 共享同一 bank，导致冲突的成因图。"
     }
    ],
    "4": [
     {
      "src": "fig12.png",
      "caption": "图 13：SFA 布局的 bank index 分布可视化，展示冲突来源。"
     }
    ],
    "6": [
     {
      "src": "fig13.png",
      "caption": "图 18：消除冲突后的 SFA 布局（stride 改为 128:4）——每个行有独立 bank index。"
     },
     {
      "src": "fig14.png",
      "caption": "图 20：bank 冲突消除前后 SMEM 到寄存器的访问模式对比——单 wavefront 完成。"
     },
     {
      "src": "fig15.png",
      "caption": "图 19：版本5 性能与 cuBLAS 对比——消除 bank 冲突后的提升。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "版本6：12 路 MMA warp",
   "paras": [
    "此阶段最大的绝对提升机会在 2k 问题形状。版本6 的改动正是为 2k 而设。它把 CTA tile 从 128×128 改为 192×128，并把 MMA 布局从 (4, 2, 1) 扩展到 (6, 2, 1)——即沿 m 维排布 12 个 MMA warp（6×2），替代之前的 8 个（4×2）。",
    "由于输出 tile 更大，工作 tile 数量比版本1-5 减少：ceil(2048/192) = 11。图 17（见文末）展示了版本1-5 与版本6 之间跨 wave 的工作 tile 分配差异。",
    "除了针对 2k 改进的工作块分配，更大的 tile 也提高了算术强度。CUTLASS 的缩放因子布局辅助函数假设 CTA tile 的 M 尺幅是 128 的倍数——此处沿 M 有 6 个 warp、即 192 行，需要调整：新布局为 ((32,3), REST_M) 与 ((16,4), 1, REST_K) 组合成 (((12, 4), 384 * REST_K), ((0, 1), 4, 384))。stride 12 的来源：K=64 子块有 4 个缩放因子、SFA 原子覆盖 3 个 32 行块（4×3=12）。",
    "与版本5 只在固定大小原子内置换字节不同，版本6 改变了原子本身的尺寸，因此也改了缩放因子的实际布局。由于更大的 tile 受 SMEM 约束，无法沿用版本1-5 的四路 load/MMA 流水线阶段，此版改用两阶段。",
    "版本6 相对版本5 在 2k 提升 186 TFLOP/s，在 16k 与 32k 各提升 40+ TFLOP/s。"
   ],
   "fig_after": {
    "1": [
     {
      "src": "fig16.png",
      "caption": "图 17：版本1-5 与版本6 之间跨 wave 工作 tile 分配的差异。"
     }
    ],
    "4": [
     {
      "src": "fig17.png",
      "caption": "图：版本6 性能与 cuBLAS 对比——更大 tile + 12 路 MMA warp 的提升。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "版本7：自动调优",
   "paras": [
    "到目前为止，内核参数都是手工选择、并在版本1-6 中保持一致。自动调优对内核参数做大范围扫描，在目标硬件上搜索最优配置：CTA tile 尺寸（bM×bN×bK）、TMA 加载/MMA 计算阶段数、MMA warp 数、swizzle size、epilogue tile（epi_m×epi_n）、epilogue 流水线阶段数、TMA 加载 warp 寄存器分配。",
    "自动调优为给定问题形状识别出的最优配置见图 19（见文末）。用这些配置，版本7 在 2k、4k、8k 各提升数 TFLOP/s，在 16k 与 32k 提升 12 到 13 TFLOP/s。",
    "与版本1 相比，版本7 在 2k 提升 29%、4k 提升 6%、8k 提升 4%、16k 提升 16%、32k 提升 40%；多轮优化使内核在各问题规模上都逼近 cuBLAS。"
   ],
   "fig_after": {
    "1": [
     {
      "src": "fig18.png",
      "caption": "图 19：自动调优对给定问题形状识别的参数配置。"
     },
     {
      "src": "fig19.png",
      "caption": "图：版本7 性能与 cuBLAS 对比——全规模下的最优结果。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "性能概览与收尾",
   "paras": [
    "下面给出本文讨论的全部版本在我们关注的问题形状（2k、4k、8k、16k、32k）上的性能进展快照。总体而言，版本7 的最终表现已全面逼近甚至齐平 cuBLAS——在多轮针对性优化加上最后的自动调优之后。",
    "针对 RTX Pro 6000 Blackwell Server Edition GPU 优化教程 NVFP4 blockscaled GEMM 的改动包括：线程块 swizzling 使一个 wave 的操作数驻留在 L2；改进 epilogue 同步；warp 专用化存储；消除 SFA bank 冲突；更大 tile 与更多 MMA warp；以及最终配置自动调优。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig20.png",
      "caption": "图：最终结果概览（2k 问题规模）——各版本性能对比。"
     },
     {
      "src": "fig21.png",
      "caption": "图：最终结果概览（4k 问题规模）。"
     },
     {
      "src": "fig22.png",
      "caption": "图：最终结果概览（8k 问题规模）。"
     },
     {
      "src": "fig23.png",
      "caption": "图：最终结果概览（16k 问题规模）。"
     },
     {
      "src": "fig24.png",
      "caption": "图：最终结果概览（32k 问题规模）——版本7 较版本1 提升 40%。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "附录：Cluster Launch Control 与其他实验",
   "paras": [
    "Cluster Launch Control（CLC）是 NVIDIA Blackwell GPU 的硬件支持特性，用动态持久调度高效调度 tile：动态持久调度中，持久 CTA 在启动一个 tile 后，继续抓取并处理下一个可用的 tile。",
    "上一篇文章给出了 SM100 实现 CLC 的配方；版本8 用该配方实现 CLC，并为 SM120 做了数处修改。首先，clc_cluster_layout_vmnk 构造如下：",
    "<pre style=\"background:#f6f8fa;padding:12px;border-radius:6px;overflow-x:auto;font-family:Consolas,monospace;font-size:13px;line-height:1.5;\"><code>cute.tiled_divide(cute.make_layout(((1, 1), 1)), (self.tiled_mma.thr_id.shape,))</code></pre>",
    "SM100 用 tcgen05 MMA 指令，因此 tiled_mma.thr_id.shape 为 1 或 2；SM120 用 warp 级 mma.sync，因此 tiled_mma.thr_id.shape 为 32。第二，文章里的实现推迟 CLC 流水线初始化，再一起同步全部流水线屏障；本版改为先立刻初始化再一起同步。第三，CLC 消费者屏障的到达计数需要调整，以适配这里比内核参考实现更多的 MMA warp 数。自动调优后，这个 CLC 内核的性能与版本7 几乎相同。",
    "其余缩放因子实验：本节记录了通过改变缩放因子数据如何被载入寄存器来提升性能的一些尝试。SM120 上 NVFP4 GEMM 最终落到的硬件 MMA 操作只从 warp 的部分线程消费缩放因子，取决于 thread-id；CuTe DSL 不直接暴露 thread-id-a 与 thread-id-b、默认都传 0。第一个方向是限制真正把 SFA 片段载入寄存器的线程数（消除冗余）；第二个方向是在单次加载中载入更多不同的 SFA 片段。"
   ],
   "fig_after": {
    "3": [
     {
      "src": "fig25.png",
      "caption": "图：CLC 内核性能与 cuBLAS 对比（附录）——自动调优后与版本7 几乎相同。"
     }
    ]
   }
  }
 ],
 "conclusion": [
  "优化一个块缩放 GEMM 不是单点突破，而是一条从负载均衡、缓存驻留、线程调度到 SMEM 布局的逐层扫描：每一步都用 Nsight 数据验证，收益从几 TFLOP/s 到几百 TFLOP/s 不等。",
  "最有价值的部分在版本5——bank 冲突这类纯布局问题往往是隐形瓶颈，靠直觉难以发现，只有把它量化成指标才可能拆解。版本7 的自动调优则把最后的人工意志也交给搜索，让内核在每种规模下都取到甜点位。"
 ],
 "reference_url": "https://research.colfax-intl.com/optimizing-an-nvfp4-blockscaled-gemm-on-rtx-pro-6000-blackwell-gpu-sm120/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")