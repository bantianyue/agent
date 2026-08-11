# -*- coding: utf-8 -*-
"""nvfp4 组装(标准链, 25图, h3拆分)"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
DATA = {
  "summary": [
    {
      "key": "优化路径",
      "body": "从基线内核出发，经线程块swizzling、尾声改进、warp专用化存储、消除SFA bank冲突、12路MMA warp、自动调优七轮迭代，在RTX PRO 6000 (SM120) 上逼近cuBLAS。"
    },
    {
      "key": "关键收益",
      "body": "对比版本1，版本7在32k问题规模吞吐提升40%，2k提升29%；各规模平均与cuBLAS 13.6相当。"
    },
    {
      "key": "核心难点",
      "body": "NVFP4块缩放GEMM的关键在缩放因子的SMEM布局与bank冲突、以及让Tensor Core持续忙碌的warp调度与流水线同步。"
    }
  ],
  "lead": [
    "在 Blackwell SM12x GPU 上做 NVFP4 块缩放 GEMM，难点不仅在 MMA 指令本身，更在缩放因子（SFA/SFB）的布局、bank 冲突、以及如何让 Tensor Core 始终忙碌。这篇 Colfax 的文章用 7 个版本从基线一路优化，给出在 RTX PRO 6000（SM120）上的完整调优路线。",
    "核心思路是迭代式的：每次针对一个瓶颈（扩展性差、epilogue 阻塞、存储抢占计算、SMEM bank 冲突）做一次针对性修改，并配 Nsight Compute 数据佐证。最终版本在 32k 规模较基线提升 40%，整体逼近 cuBLAS。"
  ],
  "sections": [
    {
      "type": "h2",
      "title": "背景与硬件规格",
      "paras": [
        "本文是 SM12x GPU 上 NVFP4 块缩放系列文章的延续。第 1 部分覆盖了相关 PTX 指令、缩放因子布局细节及 CuTe DSL 实现（如何将 CUTLASS 稠密 GEMM 转换为 NVFP4 块缩放 GEMM）。本文针对 RTX Pro 6000 Blackwell Server Edition（SM120）做具体优化。"
      ]
    },
    {
      "type": "h2",
      "title": "版本1：基线内核",
      "paras": [
        "基线内核采用 warp 特化设计、生产者-消费者流水线：每个 CTA 含 1 个 TMA 加载 warp 和 8 个 MMA warp。加载 warp 为 A、B、SFA、SFB 操作数发起 TMA 拷贝到 SMEM；主循环结束后 MMA warp 执行尾声写入 SMEM，warp 0 再从 SMEM 发起 TMA 存储。内核用静态持久化分块调度器，每个 SM 驻留单个 CTA。",
        "对于 8k 方形 GEMM 得到 1476 TFLOP/s（约 73% 利用率）。五种问题形状平均，版本1 约为 cuBLAS 13.6 的 93%，但 32k 处明显下降——较大的形状 SM 时钟降至 2.15GHz，且扩展到 32k 时性能恶化，这是版本2 要解决的扩展性问题。"
      ],
      "figs": [
        {
          "src": "fig01.png",
          "caption": "图 2：版本1 的计算吞吐（TFLOP/s）与 cuBLAS 13.5/13.6 对比，8k 处约 1476 TFLOP/s、73% 利用率，32k 下降明显。"
        }
      ]
    },
    {
      "type": "h2",
      "title": "版本2：线程块 Swizzling",
      "paras": [
        "性能图显示大形状下性能下降，用 Nsight Compute 分析发现：2k–8k 时 DRAM 吞吐仅 10%–14%，16k/32k 跃升至 64%–86%；L2 命中率从 8k 到 16k 下降、32k 时到 76.31%。对计算密集型 GEMM，这是带宽/缓存扩展性问题。",
        "解法是线程块 swizzling：通过改变 CTA 到 tile 的负载均衡，使单个 wave 内各 CTA 加载的不同 A/B 分块更少、驻留在 L2 中，提高数据复用。将 swizzle_size 设为 16（每 wave 不同分块总数最少，28）。**最大提升出现在 32k，吞吐提升 387 TFLOP/s。**"
      ],
      "figs": [
        {
          "src": "fig02.png",
          "caption": "图 3：Nsight 内存工作负载分析——DRAM/L2 吞吐与命中率随问题规模变化的指标（决定 swizzle 方向）。"
        },
        {
          "src": "fig03.png",
          "caption": "图 4：不同 swizzle_size 选择下单个 wave 加载的 A/B 分块数量示意。"
        },
        {
          "src": "fig04.png",
          "caption": "图 5：swizzle_size=16 与默认方案下分块加载情况对比（每 wave 不同分块总数最少为 28）。"
        },
        {
          "src": "fig05.png",
          "caption": "图 6：版本2 性能（TFLOP/s）与 cuBLAS 对比，32k 提升最显著（+387 TFLOP/s）。"
        },
        {
          "src": "fig06.png",
          "caption": "图 7：版本2 的内存工作负载分析输出，展示 L2/DRAM 指标改善来源。"
        }
      ]
    },
    {
      "type": "h2",
      "title": "版本3：改进 Epilogue",
      "paras": [
        "目标是确保内存依赖逻辑不必要地阻塞内核。epilogue 已用流水线化异步存储，但流水线同步可进一步改进：producer_acquire() 调用发生过早——即使存在多个 epilogue 阶段它也会阻塞；producer_tail() 位于错误的循环深度，应当在所有 work tile 处理后正确收尾。",
        "总体而言版本3 的影响很小，在基准测试波动范围内（如版本3 对比图所示）。这提醒我们：不是每个改动都有显著收益，需用数据判断。"
      ],
      "figs": [
        {
          "src": "fig07.png",
          "caption": "图 8：epilogue 代码路径中 producer_acquire/producer_tail 的同步逻辑示意。"
        },
        {
          "src": "fig08.png",
          "caption": "图 9：版本3 性能与 cuBLAS 对比——改进影响很小，处于波动范围。"
        }
      ]
    },
    {
      "type": "h2",
      "title": "版本4：Warp 专用化存储",
      "paras": [
        "计算密集型内核中希望 Tensor Core 始终忙碌，即始终有可调度的 warp 执行 MMA。warp 专用化已在加载路径上实现，但存储仍由计算 warp 完成，会与 MMA 争用。版本4 把存储也 dedicated 给存储 warp。",
        "实现依赖硬件命名屏障：SM120 有 16 个硬件管理屏障，barrier_num 指定用哪个、num_threads 指定必须到达的线程总数（设为 MMA warp 与存储 warp 之和）。存储 warp 先对 TMA 存储流水线调 producer_acquire，再到达 epilog_free_barrier 让 MMA warp 知道该阶段可写。"
      ],
      "figs": [
        {
          "src": "fig09.png",
          "caption": "图 13：warp 专用化存储的流水线结构——存储 warp 与 MMA warp 通过命名屏障协调。"
        },
        {
          "src": "fig10.png",
          "caption": "图 12：版本4 性能与 cuBLAS 对比，专用化存储对 Tensor Core 利用率的影响。"
        }
      ]
    },
    {
      "type": "h2",
      "title": "版本5：消除 SFA bank 冲突",
      "paras": [
        "SFA 的 SMEM 布局为特定分块格式。分析表明，对应第 0–15 行的元素，每个 bank index 都是 4 的倍数，行 r 与行 r+8 的 scale factor 地址共享同一 bank——十六个地址分布在八个 bank 上，导致严重的 bank 冲突，拖慢 SFA 加载。",
        "通过重新安排 SMEM 布局（pad/交错），使每个 warp 访问的 scale factor 落在不同 bank，消除冲突。这是本系列中较难的一步，也是纯数学/布局层面的优化，性能提升随问题形状不同而显著。"
      ],
      "figs": [
        {
          "src": "fig11.png",
          "caption": "图 15：SFA 的 SMEM 布局示意——行 r 与行 r+8 共享 bank 导致冲突的成因图。"
        },
        {
          "src": "fig12.png",
          "caption": "图 17：SFA 布局的 bank index 分布可视化，展示冲突来源。"
        },
        {
          "src": "fig13.png",
          "caption": "图 18：消除冲突后的 SFA 布局示意图。"
        },
        {
          "src": "fig14.png",
          "caption": "图 20：bank 冲突消除前后的访问模式对比。"
        },
        {
          "src": "fig15.png",
          "caption": "图 19：版本5 性能与 cuBLAS 对比，bank 冲突消除后的提升。"
        }
      ]
    },
    {
      "type": "h2",
      "title": "版本6：12 路 MMA warp",
      "paras": [
        "由于输出 tile 尺寸更大，工作 tile 数量比版本1-5 减少。图 17 展示版本1-5 与版本6 间跨波次的工作 tile 分配差异：除了针对 2k 改进的工作块分配之外，更大 tile 也提高了算术强度。",
        "把 MMA warp 从 8 路提升到 12 路，配合更大的输出 tile，提升 Tensor Core 利用率与算术强度。"
      ],
      "figs": [
        {
          "src": "fig16.png",
          "caption": "图 17：版本1-5 与版本6 之间跨波次工作 tile 分配差异。"
        },
        {
          "src": "fig17.png",
          "caption": "图 13：版本6 性能与 cuBLAS 对比，更大 tile + 更多 MMA warp 的提升。"
        }
      ]
    },
    {
      "type": "h2",
      "title": "版本7：自动调优",
      "paras": [
        "内核暴露了许多可调参数（CTA tile、swizzle_size、流水线阶段数、MMA warp 数等）。版本7 引入自动调优（autotuning），在目标硬件上搜索最优配置组合，而非手工指定。",
        "**最终概览**：与版本1 相比，版本7 在 2k 提升 29%、4k 提升 6%、8k 提升 4%、16k 提升 16%、32k 提升 40%。多轮优化使内核在各问题规模上都逼近 cuBLAS。"
      ],
      "figs": [
        {
          "src": "fig18.png",
          "caption": "图 23：自动调优的参数空间与搜索过程示意。"
        },
        {
          "src": "fig19.png",
          "caption": "图：版本7 性能与 cuBLAS 对比——全规模下的最优结果。"
        }
      ]
    },
    {
      "type": "h2",
      "title": "性能概览与收尾",
      "paras": [
        "针对 RTX Pro 6000 Blackwell Server Edition GPU 优化教程 NVFP4 blockscaled GEMM，具体改动包括：线程块 swizzling 使一个 wave 的操作数驻留在 L2；改进 epilogue 同步；warp 专用化存储；消除 SFA bank 冲突；更大 tile 与更多 MMA warp；以及最终配置自动调优。"
      ],
      "figs": [
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
    },
    {
      "type": "h2",
      "title": "附录：Cluster Launch Control 与其他缩放因子实验",
      "paras": [
        "CLC 是 Blackwell 的硬件特性，用动态持久调度高效调度 tile：每个 CTA 先取程序员设计的初始分配，再获取并处理任何可用的新 tile。SM120 使用 warp 级 mma.sync（thr_id.shape=32），与 SM100 的 tcgen05 不同，需调整 CLC 流水线初始化的时放与消费者屏障计数。自动调优后 CLC 内核性能与版本7 几乎相同。",
        "另有缩放因子加载实验：由于 thread-id-a=0，MMA 仅需每个 quad 线程 0/1 的 SFA 片段。两种方向——限制实际加载 SFA 的线程数以消除冗余、或用内联 PTX 改 thread-id 在单次加载中载入更多不同片段。"
      ],
      "figs": [
        {
          "src": "fig25.png",
          "caption": "图：CLC 内核性能与 cuBLAS 对比（附录）——与版本7 几乎相同。"
        }
      ]
    }
  ],
  "conclusion": [
    "优化一个块缩放 GEMM 不是单点突破，而是一条从负载均衡、缓存驻留、线程调度到 SMEM 布局的逐层扫描：每一步都用 Nsight 数据验证，收益从几 TFLOP/s 到几百 TFLOP/s 不等。",
    "最有价值的部分在版本5——bank 冲突这类纯布局问题往往是隐形瓶颈，靠直觉难以发现，只有把它量化成指标才可能拆解。版本7 的自动调优则把最后的手工意志也交给搜索，让内核在每种规模下都取到甜点位。"
  ],
  "reference_url": "https://research.colfax-intl.com/optimizing-an-nvfp4-blockscaled-gemm-on-rtx-pro-6000-blackwell-gpu-sm120/",
  "title": "七轮迭代把 NVFP4 块缩放 GEMM 逼近 cuBLAS：RTX PRO 6000 (SM120) 调优实录"
}

with open(os.path.join(_article_dir, "article_data.json"), "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 article_data.json ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")