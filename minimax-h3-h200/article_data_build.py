# -*- coding: utf-8 -*-
"""MiniMax-H3 on 8xH200 编译 build（原样保留）"""
import json

DATA = {
 "title": "MiniMax-H3 在 8×H200 上：无损 1.95×，SSIM 0.76–0.91 下最高 6.24×",
 "lead": [
  "我们在 8× NVIDIA H200 上，用 SGLang Diffusion 对 MiniMax-H3 视频生成做了基准测试——六个工作负载固定 prompt、seed、分辨率、帧率、去噪步数。",
  "对比覆盖 SGLang Diffusion 的三个加速 knobs（它还支持更多有损路径——量化、渐进分辨率等没有包含在本轮里，所以这里的数字是可实现的子集、不是天花板）。一切是实测而非预估；文末的 clip 让你自己判断质量代价。",
  "摘要：无损约 2×（相对匹配的 Diffusers 基线）；平衡速度/质量的 SubBlock 0.75 + Cache-DiT stride 达 4.90–5.64×（5s）/5.44–5.93×（10s）。"
 ],
 "summary": [
  {
   "key": "三加速可组合",
   "body": "视频扩散两大成本：denoising loop 跑同一 transformer 数十次 + 每步注意力花在超长 token 序列上。三个加速从不同方向攻击并叠加：① 无损的 fused kernels（降低每步成本）；② Cache-DiT（跨去噪步复用中间结果、少跑步骤）；③ SubBlock 稀疏注意力（降低仍在算的步的注意力成本）。无损 + 两个有损（每数字带 vs 无损基线的 SSIM）。"
  },
  {
   "key": "结果",
   "body": "相对匹配 Diffusers：无损路径两任务两时长约 2×。质量优先用 Cache-DiT conservative/stride（无 SubBlock）；平衡用 SubBlock 0.75+Cache-DiT stride（4.90–5.64×@5s、5.44–5.93×@10s）；标题上端含最激进行的 6.24×（SSIM 0.76–0.91 区间，详见图表）。"
  },
  {
   "key": "机制",
   "body": "H3 路径融合 indexed AdaLN 更新、gated residuals、SwiGLU 激活、QK RMSNorm+3D RoPE，减少中间张量/内存流量/kernel 启动。Cache-DiT 对共享 DiT block stack 附一个 DBCache 上下文（Fn=1、Bn=0、4 warmup）比较边界块归一化残差。SubBlock 是训练-free 路由器：64-token 块分 4×16 子块（n_q=n_k=4），log-sum-exp 评分保最高分 key 块；sparsity=允许丢弃的 key 块比例（0.75 保约 25%）。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "背景与范围",
   "paras": [
    "**TL;DR**：我们在 8× NVIDIA H200 上用 SGLang Diffusion 对 MiniMax-H3 视频生成做了基准，六个工作负载固定 prompt/seed/分辨率/帧率/去噪步数。",
    "**范围**：对比覆盖 SGLang Diffusion 的三个加速 knobs。它还支持更有损的路径——量化、渐进分辨率等不在本轮，所以这里数字是可实现包络的切片、不是天花板。全部为实测非预估；文末 clip 让你自己判断质量代价。",
    "虽然 SGLang Diffusion 已为 MiniMax-H3 提供快速无损路径，社区一直期待更快的高质量有损视频生成。SGLang Diffusion 基于其长期积累的可塑有损加速 knobs 栈积极工作于过去几周；本文是第一篇这些 knobs 落地后的实测记录。",
    "视频扩散由两大成本主导：**去噪循环把同一个 transformer 跑几十次**，且**每步大部分预算花在超长 token 序列的注意力**。一个 5 秒 1344×768 clip（24 FPS、50 个去噪步）远超单 GPU 可行点——问题不是要不要并行、而是能避免多少剩余工作。",
    "三个加速从不同方向进攻、且可组合：",
    "第一个无损；另两个用相似度换速度——这就是为什么本文每个数字都附相对无损基线的 SSIM。",
    "答案取决于基线。相对匹配的 Diffusers 案例，SGLang 的稠密无损路径对两任务两时长都已是约 2×。Cache-DiT 复用去噪步之间的工作，SubBlock 稀疏注意力降低仍在跑的步的成本——合起来构成这个矩阵里最快的路径。",
    "**质量优先的加速默认**：用 Cache-DiT conservative 或 Cache-DiT stride（不加 SubBlock）。**平衡速度/质量**：用 SubBlock 0.75 + Cache-DiT stride——5s 给 4.90–5.64×、10s 给 5.44–5.93×。",
    "每个配置都可用 SGLang 的 MiniMax-H3 cookbook 页复现（带各模式精确启动 flags）。我们报告生成侧推理时间；排除 server 启动、warmup、HTTP 轮询、MP4 下载时间。每任务每时长时延与 SSIM 在三个不同 prompt 上评估；提速相对匹配的 Diffusers 案例；SSIM 相对匹配的 SGLang 无损视频在所有帧上算（YUV420）。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：六工作负载延迟（latency）汇总。"
     }
    ],
    "1": [
     {
      "src": "fig02.png",
      "caption": "图 2：相对 Diffusers 基线的提速（speedup）汇总。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "At a Glance 与详细结果",
   "paras": [
    "下面的图表汇总了聚合基准表（本节的 At a Glance 架构图与关键词见原文）。",
    "**T2VA / FL2VA**：每个任务在每个时长跨三个 prompt 测 latency 和 SSIM。两个任务（text-to-video、frame-to-video）两时长（5s/10s）的详细吞吐数字见原文表格。",
    "**Key takeaways**：无损路径约 2×（相对 Diffusers）；Cache-DiT 复用跨步工作、SubBlock 降每步成本；平衡配置 SubBlock 0.75+stride 达 ~5×；质量优先用 Cache-DiT conservative/stride。标题与图表中的上端数字（最高 6.24×、SSIM 0.76–0.91）对应最激进的稀疏/缓存配置行。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：质量-速度权衡（quality tradeoff，SSIM 标注）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "提速从哪来：三种机制驱动 profile 级增益",
   "paras": [
    "三个机制驱动 profile 级增益。",
    "**Fused kernels** 降低每个仍在跑的步的成本。H3 路径把 indexed AdaLN 更新、gated residuals、SwiGLU 激活、QK RMSNorm 与 3D RoPE 融合，减少中间张量、内存流量和 kernel 启动。下一节给分离的 kernel 测量；它们是每步实现的一部分，而 Cache-DiT 和 SubBlock 决定这套实现被执行多少。",
    "**Cache-DiT** 对 MiniMax-H3 的共享 DiT block stack 附一个 DBCache 上下文。warmup 后评估配置的 boundary blocks、比较归一化残差变化与前缓存状态。变化低于阈值且连续缓存上限允许时，中间块复用缓存结果；否则重算 stack 并刷新缓存。所有 cache 模式用 Fn=1、Bn=0、四个 warmup 步。MiniMax-H3 只有一个 MiniMaxH3DiTModel、block stack 带打包的 video+audio token——所以 Cache-DiT 对整个打包栈做一个共享决策、不维护独立 video/audio 缓存；worker 记录一个合并的 Cache-DiT 步表。",
    "**SubBlock 稀疏注意力** 降低已计算步的 KV 块读取。用 n_k=n_q=4；前十步去噪用稠密注意力、之后启用 SubBlock；最小序列长 4096。矩阵测 sparsity 0.75 与 0.80——后者更快但在若干 T2VA 案例 SSIM 更低。",
    "聚合 profile 结果显示各 profile 端到端行为；不分离 kernel 时间、也不给每步成本细分。工作量配 50 个推理步；因 sigma schedule 含两个区间端点，去噪循环执行 49 次模型评估（len(sigmas)-1）；「49 步 trace」指这些模型评估。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 4：6 个 profile 的 49 步执行 trace（cached_steps 列表）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "一个实测的 49 步 trace",
   "paras": [
    "为让执行模式具体化，一个 5 秒 T2VA 请求跑六个 profile：lossless、Cache-DiT conservative、SubBlock 0.75、SubBlock 0.75 + conservative Cache-DiT、Cache-DiT stride、SubBlock 0.80 + stride。worker 记录每请求实际的 cached_steps 列表。因 video/audio token 共享一个打包 H3 block stack，cache hit 复用合并输出；此路径无独立的「video 缓存、audio 计算」态。SubBlock 行的蓝色格子标记前十步之后用稀疏注意力的计算步骤。",
    "trace 运行时间：37.78s（lossless）、26.82s（Cache-DiT conservative）、29.97s（SubBlock 0.75）、22.18s（SubBlock 0.75+conservative Cache-DiT）、17.23s（Cache-DiT stride）、14.34s（SubBlock 0.80+stride）。这些标识 trace 运行、不代表三 prompt 聚合中位数。",
    "**Caching 决定多少去噪步运行；kernels 决定每步多快**。MiniMax-H3 把 video/audio token 打进一个序列，非 GEMM 路径全程受益同一基本原则：更少内存流量、更少中间张量、更少 kernel 启动。AdaLN modulation 和 gated residuals 按 token 索引查参数、单 pass 更新激活；SwiGLU 直接在融合 gate_up buffer 上操作；QK RMSNorm 和 3D RoPE 融合进单核、而非独立 eager 操作。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Kernel 层：隔离微基准",
   "paras": [
    "下表用真实的 per-rank shape（5 秒 T2VA 请求、1344×768×124 帧）：SP/Ulysses-8 padding 后 4,722 行、hidden size 5,376、56 注意力头、head dim 128、RoPE dim 96、BF16 输入。每数字是 10 轮×20 次调用里每次调用的 CUDA-event 时间中位数；基线是对应的 eager 组合。",
    "这些是隔离位点的微基准、不是可叠加的端到端时延节省。融合 QK-Norm+RoPE 的结果用 main 上可用的 exact-rounding 路径（round_norm_before_rope=True）。",
    "（各融合算子的具体加速倍数见原图 5 的 kernel-speedup-chart。）"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 5：隔离 kernel 提速图（fused kernel speedups）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "SubBlock 稀疏注意力原理",
   "paras": [
    "SubBlock 是训练-free 的块稀疏注意力路由器。把序列分成 64-token query 和 key 块，再把每块两侧各分成四个 16-token 子块（n_q=n_k=4）。轻量 pooling 和 log-sum-exp score 估计每个 key 块对每个 query 块和 head 的未归一化 softmax mass。路由器保留最高分的 key 块、把它们的索引传给块稀疏注意力 kernel；完整注意力矩阵从不物化。",
    "**sparsity 值是被允许丢弃的 key 块比例、不是保留比例**。所以 sparsity=0.75 对每个 query 块保留约 25% 的 key 块。更激进的 0.80 更快但有更大的近似误差预算——与最激进行观察到的更低 SSIM 一致。",
    "曲线显示分数分布；垂直线显示两个展示预算的逐行路由截止中位数。这里 sparsity=0.50 作为诊断参考；基准 profile 用 0.75 和 0.80。因为路由器对每 query 块和每 head 独立排名 key 块，sparsity=0.50/0.75 大致保留该行前一半/前四分之一可用 key 块（受 8 块预算取整约束）。跨这些工作负载，0.75 预算保留行局部中位数以上的大部分分数质量、同时把选择集中到高分尾。",
    "稀疏路径只对 kernel 支持的长、非因果 DiT 注意力调用启用：BF16 输入、head dim 128、至少 4096 token。前十去噪步用稠密；短段、token refiner、不支持的调用走稠密 fallback。H200/SM90 上，选定的 64×64 路由计划由 SGLang 的 CuTe block-sparse FlashAttention kernel 执行。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 6：SubBlock 逐行路由截断分数分布（0.50/0.75/0.80）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Demos 与致谢",
   "paras": [
    "demo 集为每选中 prompt 含四种模式：SGLang lossless、Cache-DiT conservative、SubBlock 0.75+Cache-DiT stride、SubBlock 0.80+Cache-DiT stride。文件名为 prompt/task/mode/duration 编码。四个模式对应：Prompt 1·T2VA·5s、Prompt 2·T2VA·10s、Prompt 3·FL2VA·5s（原 clip 见文末链接）。",
    "本基准是多个团队合作的结果，感谢所有参与者。",
    "**免责/备注**：2026-08-18 实测于 8× NVIDIA H200；复现细节与逐 prompt 原始数据在基准仓库。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "LMSYS 这篇把 SGLang Diffusion 在 8×H200 上加速 MiniMax-H3 视频生成的实测讲得清楚：**三加速可组合**，从不同方向降低视频扩散的两大成本——重复的 denoising loop 与超长序列注意力。无损路径（fused kernels）相对 Diffusers 约 2×（标题的 1.95×）；叠加两个有损加速（Cache-DiT 跨步复用 + SubBlock 稀疏注意力）后，平衡配置 SubBlock 0.75+stride 到 ~5×、最激进行最高 6.24×（代价 SSIM 降到 0.76–0.91）。",
  "机制上值得记：① **Cache-DiT** 对共享 DiT block stack（video+audio 打包）附 DBCache 上下文，靠比较边界块归一化残差决定中间块复用——Fn=1、Bn=0、4 warmup；② **SubBlock** 是训练-free 路由器——64-token 块分 4×16 子块（n_q=n_k=4）、log-sum-exp 评分保最高分 key 块，且注意 **sparsity 是被丢弃比例、非保留比例**（0.75 保约 25%）；③ **fused kernels** 把 AdaLN/gated residuals/SwiGLU/QK-RMSNorm+RoPE 融进单核、降内存流量与启动开销；④ trace 实证（49 步、37.78s→14.34s）。对做视频生成 serving/推理加速、或用 diffusion 的 lossless/lossy 权衡的人，这是「三类加速怎么组合、质量代价是多少」的实测参考。"
 ],
 "reference_url": "https://www.lmsys.org/blog/2026-08-27-minimax-h3-h200"
}
with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("✅ 写入 article_data.json")
