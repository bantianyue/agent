# -*- coding: utf-8 -*-
"""Groq 3 LPX 编译 build"""
import json

DATA = {
 "title": "NVIDIA Groq 3 LPX：在长上下文下解锁超高交互速度",
 "lead": [
  "NVIDIA Groq 3 LPX 是 Vera Rubin 平台的交互式 AI 推理加速器。本文报告第三方基准 Artificial Analysis 在 Gemma 4 31B 上的 100K context 测试结果：**3431 token/秒**的世界级交互速度，且精度/质量无损失。",
  "背后是编译器确定性调度 + 细粒度计算通信重叠 + 预规划 chip-to-chip 网络，让小 batch（高交互必需）下也能做有效张量并行。与 Vera Rubin NVL72 配合，还能支撑 prefill-decode 分离、attention-FFN 分离、外部 draft 推测解码等多种共执行配置，扩展到万亿参数模型。"
 ],
 "summary": [
  {
   "key": "核心数字",
   "body": "第三方基准 Artificial Analysis：Gemma 4 31B 100K context 达 3431 token/s（最快公开端点 870）、10K 3382；开源 SPEED-Bench 编码任务中位 4767 token/s（P80 5520）。无精度/质量损失。"
  },
  {
   "key": "技术关键",
   "body": "编译器确定性调度消除实时仲裁：256 LPU/128GB SRAM/96 条 112Gbps C2C 链路全程预规划；320-byte 向量级细粒度计算-通信重叠。这让小 batch 高交互区张量并行仍有效。"
  },
  {
   "key": "共执行配置",
   "body": "与 Vera Rubin NVL72 配合三种：prefill-decode 分离、attention-FFN 分离、外部 draft 推测解码——各机柜干最擅长部分，推向万亿参数高交互 agentic。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "为什么长上下文 + 高交互重要",
   "paras": [
    "Agentic 会话的特征是多轮推理。每轮结束，agent 的输出被追加到持续增长、并喂进后续所有轮的上下文里。",
    "如图 1，尤其当会话超过几百轮，上下文可涨到几十万 token。这意味着任务后期 agent 必须反复处理到目前为止学到的一切。没有长上下文，agent 只能考虑先前相关上下文的一小部分。无论模型多快多聪明，有限上下文 = 有限 agentic 能力。最强 agent 不仅要快，还得在会话增长时保住长上下文。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：NVIDIA Groq 3 LPX 机柜——Vera Rubin 平台的交互式推理加速器。"
     }
    ],
    "1": [
     {
      "src": "fig02.png",
      "caption": "图 2：多轮 agentic 会话中每轮携带的上下文持续上升。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "超高交互 + 长上下文为何难",
   "paras": [
    "给单个用户在管理 100K 输入 token KV cache 的同时以 >3000 token/s 服务，是独特的系统挑战。推理里分治技术如张量并行（TP）能带来数量级加速——如果系统能高效管理所需的协调（集合操作）。但最高交互等级要求非常小的 batch，此时固定协调成本可能盖过 TP 节省的时间。",
    "TP 两部分：并行跨多芯片算，再合并结果。高交互推理要求的小 batch 下，让 TP 有效需要紧协调——很多小张量必须在计算单元间转移，每张精确在需要的时间地点到达。通信和合并结果的时间很容易等于甚至大于分布计算节省的时间。",
    "每次单独转移总时间两个分量：**first bit latency**（判定该用哪条链路、同步收发端、仲裁冲突的费用）+ **转移时间**（数据量除以带宽）。TP 的数量级加速要求把 first bit latency 压到绝对最低。在整个前向传播做到这点——对权重和长上下文 KV cache 都并行——需要同时为低延迟和长上下文设计的方案。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 2：任意系统两芯片/核心间数据传输时间方程。小 batch 推理瓶颈通常是 first bit latency（A），因为传输数据量 N 相对带宽 B 极小。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "怎么做：编译器调度 + 细粒度重叠",
   "paras": [
    "Groq 3 LPX 用编译器调度的负载规划服务超高交互长上下文，包括机架内 chip-to-chip（C2C）网络和把计算与处理器间通信大幅重叠。",
    "**紧调度的芯片间通信**：LPX 用确定性执行模型。编译器能看见每颗 LP30（256 个 LPU 之一）里的独立计算单元、这些芯片合计的 128GB SRAM、每芯片 96 条 112Gbps C2C 链路。能据此在负载开始前产出精确到时钟周期的调度方案，消除转移的实时仲裁——预先规划每块数据何时走每条 C2C 链路。",
    "预负载调度还带来转移方式的根本转变。很多系统每次转移多步（一方请求、另一方确认并定位、可能竞争资源）；编译器调度让 LPU 在数据就绪的时钟周期发出、到达的时钟周期消费，数据直接从发送者结果走 I/O 链路到接收者，无中间路由（连接静态由编译器决定）。链路是 LPU 两两之间的点对点，每颗 LPU 既是处理器也能当路由器。",
    "这套网络把 first bit latency 压到绝对最低。大 batch 时 first bit 被线上实际秒字节的时间掩盖；但对高交互帕累托区，把固定转移初始化时间最小化变得关键。",
    "**细粒度计算-通信重叠**：编译器还能把众多小 C2C 转移与计算在极细粒度重叠——在 320-byte 向量粒度调度计算和通信单元。利用矩阵乘法可表达为一系列点积，编译器能让单颗 LPU 算输出矩阵的 320 列、算完立即经 C2C 发走，不必等整个矩阵操作完成。这提升计算-通信重叠，尤其对小张量——细粒度 C2C 调度让计算以最小通信尾部完成。",
    "合起来，这些技术带来长上下文推理最算力密集的注意力操作的数量级加速。靠紧协调的芯片间计算通信调度，LPX 能在小 batch、高交互的帕累托区利用张量并行的分治优势。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.gif",
      "caption": "图 3：三颗 LPU 沿绿色编译器调度路线连续交换数据（无停顿无竞争）。"
     }
    ],
    "1": [
     {
      "src": "fig05.png",
      "caption": "图 4：LPU 预定路由——两步直达、少竞争，压降 first bit。"
     }
    ],
    "2": [
     {
      "src": "fig06.png",
      "caption": "图 5：单 token matmul 利用「矩阵乘法=一系列点积」，结果切片（320 列）就绪即发。"
     }
    ],
    "3": [
     {
      "src": "fig07.png",
      "caption": "图 6：LPX 细粒度 C2C 调度让计算以最小通信尾部完成。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "实测：100K 上下文第三方基准",
   "paras": [
    "Artificial Analysis 有标准基准套件测不同推理提供者在其模型上的服务速度（10K 和 100K 输入上下文）。用此套件测了 2026 年 4 月发布的 31B 稠密模型 Gemma 4 的 100K 基准。NVIDIA 在自己数据中心搭的 Groq 3 LPX 系统以 **3431 输出 token/s** 作答——而 Artificial Analysis 最快的公开端点约 870 token/s。",
    "10K context 测同样系统：**3382 token/s**（最快公开端点 1402）。LPU 确定性架构 + 高张量并行让延迟和输出 token/s 相对上下文长度变化极小。两基准 NVIDIA 配置均无精度或模型质量损失。",
    "作为编码特定补充测量，跑开源 SPEED-Bench（原始生成速度在 agentic 编码工作流里尤其重要）。同 Gemma 4：中位 **4767 输出 token/s**、P80 **5520**——20% 任务超 5500 token/s。",
    "对 agentic 编码任务（agent 可能读几百文件轻松超 100K context、再据此生成 5000 个推理+输出 token），这不只受益于上下文、也是根本改变体验的速度。**解码 5000 token 约 1.5 秒**，vs 100 token/s 要 50 秒（34×）——而当今最流行 agentic 工具实际更接近 60 token/s。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig08.png",
      "caption": "图 7：Gemma 4 100K 输入上下文的速度——LPX 3431 vs 最快公开端点 870 token/s。"
     }
    ],
    "1": [
     {
      "src": "fig09.png",
      "caption": "图 8：生成 5000 token 用时——100 token/s 约 50 秒 vs LPX 实测 1.5 秒（34×）。"
     }
    ],
    "2": [
     {
      "src": "fig10.png",
      "caption": "图 9：Gemma 4 10K 输入上下文——LPX 3382 vs 最快公开端点 1402 token/s。"
     }
    ],
    "3": [
     {
      "src": "fig11.png",
      "caption": "图 10：SPEED-Bench 编码任务实测速度——中位 4767、超 20% 任务 >5500 token/s。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "与 Vera Rubin NVL72 共执行",
   "paras": [
    "把 LPX 的低延迟确定性执行与 Vera Rubin NVL72 机柜配对，支持多种服务配置：",
    "**标准 prefill-decode 分离**：Vera Rubin NVL72 处理 prefill、每轮把 KV cache 交给 LPX；LPX 用它 + 存在 SRAM 的权重，执行整个 decode 步。",
    "**attention-FFN 分离**：Vera Rubin 算 attention 并把 KV cache 存 DRAM，LPX 执行 FFN 层——只有中间 token 每整个 attention 层一次跨机柜发送。",
    "**外部 draft 推测解码**：LPX 在 Vera Rubin 上的大目标模型前跑小 draft 模型，后者验证并提交 token、把被拒位置返回给下一 chunk。每机柜保各模型自己的 KV cache，只有 draft token 跨链路。",
    "这些都让每机柜聚焦它最擅长的负载部分。全协同设计下，LPX 把 Vera Rubin 平台推向新高交互低延迟。图 11 是把 GPT-OSS 缩放到 2 万亿参数、跑在 Vera Rubin NVL72 + Groq 3 LPX 的投影。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig12.png",
      "caption": "图 11：GPT-OSS-2T 用户 TPS 对比——LPX 扩展 Vera Rubin 平台支撑高交互 agentic。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "小结",
   "paras": [
    "Groq 3 LPX 的速度已被第三方基准测到，确证它在对 agentic 工作流重要的上下文长度上给出领先交互；NVIDIA 还在开源编码基准上测到更极端的性能。",
    "了解更多：Inside NVIDIA Groq 3 LPX: The Low-Latency Inference Accelerator for the NVIDIA Vera Rubin Platform。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇是 NVIDIA 首次公布 Groq 3 LPX 的第三方实测：**Artificial Analysis 在 Gemma 4 31B 的 100K context 基准上测到 3431 输出 token/s，是最快公开端点的近 4 倍（870）**；10K 也达 3382、开源 SPEED-Bench 编码任务中位 4767（P80 5520），且无精度损失。解码 5000 token 只要约 1.5 秒（vs 100 TPS 的 50 秒，34×）。",
  "技术本质：确定性编译器把 256 LPU、128GB SRAM、96×112Gbps C2C 链路全程预规划到时钟级，消除实时仲裁（压降 first bit latency）+ 320-byte 向量级细粒度计算-通信重叠，让高交互必需的小 batch 下张量并行仍有效。与 Vera Rubin NVL72 的三种共执行配置（prefill-decode/attention-FFN 分离、外部 draft 推测解码）把平台推向万亿参数 agentic。对做推理部署/长上下文 agentic 的人，这是「高交互 + 长上下文」系统的当前标杆。"
 ],
 "reference_url": "https://developer.nvidia.com/blog/how-nvidia-groq-3-lpx-unlocks-ultrafast-interactivity-at-long-context-on-nvidia-vera-rubin/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")