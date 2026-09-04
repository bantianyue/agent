# -*- coding: utf-8 -*-
"""Cerebras GPT-5.6 Sol 文章编译 build（Sarah Chieng / @MilksandMatcha）"""
import json

DATA = {
 "title": "Cerebras 如何在满速下服务 GPT-5.6 Sol：最高 750 tokens/秒",
 "lead": [
  "过去两年 AI 模型的能力大幅跃升——能更久推理、写出生产级代码、操作电脑、用浏览器，并在科学、金融、数学、物理、工程等领域产出专业工作。但体验的一部分始终没变：等待。",
  "OpenAI 正在预览跑在 Cerebras 上的 GPT-5.6 Sol 的新 Ultrafast 模式，最高 750 输出 token/秒。这个速度改变了我们使用 AI 的方式：现在能和 agent 保持在同一节奏、实时协作。本文（Cerebras DevX 负责人 Sarah Chieng 的 X 长文）讲清它怎么做到的。"
 ],
 "summary": [
  {
   "key": "核心：没改模型只换硬件",
   "body": "GPT-5.6 Sol on Cerebras 不是更小模型/蒸馏/低精度量化——同一架构、权重、精度、上下文配置和推理设置，完整保留 browser-use/computer-use/coding 能力。唯一差异是硬件：跑在 Cerebras WSE-3（世界最大 AI 芯片）上，替代 GPU。"
  },
  {
   "key": "为何快：绕过 GPU 内存墙",
   "body": "GPU 权重在片外 HBM、每步推理都要越过边界传进 compute——内存墙。WSE-3 用整片晶圆当芯片：44GB SRAM 直接分布在 90 万核旁，聚合带宽 21PB/s。Sol 跨多个 CS-3 按层分片，activation 在 wafer 间移动、权重留在原地。"
  },
  {
   "key": "结果：agent 工作流提速",
   "body": "GDP-Val 质量匹配样本上 5.6× 更快、Humanity's Last Exam 上 6.9× 更快；1 小时任务不到 9 分钟完成。开放模型端点亦达数千 tok/s（GPT OSS 120B 3000、Gemma4 31B 1850、GLM4.7 1000）。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "引言：等待是唯一没变的部分",
   "paras": [
    "过去两年 AI 模型能力大幅跃升：能更久推理、写生产级代码、操作电脑、用浏览器，并在科学、金融、数学、物理、工程产出专业工作。",
    "但体验的一部分始终没变：等待。",
    "OpenAI 正在预览跑在 Cerebras 上的 GPT-5.6 Sol 的新 Ultrafast 模式，最高 750 输出 token/秒。这个速度改变我们使用 AI 的方式：现在能留在工作流里，与 agent 实时协作。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "最关键：我们什么都没改",
   "paras": [
    "最重要的细节是我们没有改什么。",
    "Cerebras 上的 GPT-5.6 Sol 不是更小的模型、没有蒸馏、也没有量化到更低精度。它使用与标准 OpenAI 端点上 GPT-5.6 Sol **完全相同的模型架构、权重、精度、上下文配置和推理设置**。它完整保留了人们喜爱的 browser-use、computer-use、coding 能力。",
    "唯一差异是模型运行的硬件：不再是 GPU，我们在 Cerebras WSE-3 上服务 Sol-Ultrafast——世界上最大的 AI 芯片。",
    "用 Cerebras，GPT-5.6-Sol 重新定义了「速度到智能」的帕累托前沿（speed to intelligence Pareto frontier）。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "为什么前沿模型推理通常很慢",
   "paras": [
    "**Why frontier-model inference is usually slow**",
    "在传统 GPU 上，计算核心和存放模型权重的高带宽内存（HBM）在分离的芯片上。推理里每次计算，权重都必须反复越过那道边界到达计算核心。随着模型变大，推理更多受「系统能多快搬运这些权重」约束，而非算术本身。",
    "这就是 GPU 内存墙（GPU memory wall）。",
    "加 GPU 能提升吞吐，但不会自动让单个响应变快。把模型拆到多块芯片意味着每一层都以同步步骤收尾，每加一块芯片都让那步更贵、同时缩小它本想加速的计算。存在交叉点：互连开销压过收益，更多硬件反而让模型更慢。说白了：计算机花太多时间搬数据了。",
    "Cerebras 的构建正是为了解决这个内存搬运瓶颈：造一个足够大的处理器，让模型的活跃权重直接待在使用它们的计算核心旁。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 1：GPU 内存墙——权重跨 HBM/芯片边界搬运。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "如何加速：从整片硅晶圆开始",
   "paras": [
    "**How Cerebras accelerates models, starting with an entire silicon wafer**",
    "传统芯片从硅晶圆上切割下来。Cerebras 则直接把整片晶圆当作芯片。",
    "在传统 GPU 上，模型权重住在片外 HBM、每个 token 都必须越过边界进入 compute。WSE-3 则把 44GB SRAM 分布在整片晶圆上、直接放在其 900,000 个核心旁。这套内存合起来提供每秒 21 拍字节（21 PB/s）的聚合带宽，让每个核心都能快速访问它需要的权重。",
    "GPT-5.6 Sol 对单块加速器太大，所以 Cerebras 在层边界把它分区到多个 CS-3 系统上。每片晶圆在本地 SRAM 保留它分到的层。对每个 token，activation 从一片晶圆移到下一片，直到最终阶段输出结果。",
    "这用更简单的路径替代了传统 GPU 集群所需的细粒度分片和同步：权重贴近 compute、只有 activation 在阶段间移动。然后管线重复——最高每秒 750 次。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 2：WSE-3——整片晶圆即芯片，44GB SRAM 紧靠 90 万核。"
     }
    ],
    "1": [
     {
      "src": "fig04.png",
      "caption": "图 3：Sol 跨多个 CS-3 按层分区，activation 在 wafer 间流动。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "每秒 750 token 对你意味着什么",
   "paras": [
    "**What up to 750 tokens per second means for you**",
    "大多数人以为和 agent 协作就是给个输入、得到输出。但底层 agent 要好多步：读任务、推理结果、写代码、测试它的工作、决定下一步，在一个循环里工作直到准备好交出回合。",
    "复杂任务可能涉及多个模型请求和工具调用，延迟会随工作流累积。",
    "这意味着每 token 延迟不是一次性代价，而是你在每一步都要付、并且乘以完成任务所需步数的成本——而那些步数累积得很快。",
    "那个乘数是可测的，而且比你想的大。在一份质量匹配的 GDP-Val 任务样本（含法律、金融、工程交付物）上，GPT-5.6 Sol Ultrafast 比同一模型在标准端点**快 5.6× 完成同样的任务**。",
    "在 Humanity's Last Exam 的匹配问题（推理主导工作流）上，Sol Ultrafast **快 6.9× 完成成功工作**。照这个速度，一个 1 小时的任务不到 9 分钟就完成。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 4：每 token 延迟是每步都要付、且按步数放大的成本。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "对开发者",
   "paras": [
    "**For Developers**",
    "没有哪里比编码更能体现 Cerebras 的速度。开发者让 agent 连续工作几小时甚至几天很常见。无论跑循环还是长驻 agent，Sol on Cerebras 都是无与伦比的体验——前沿级智能以极速服务，让你比以往更快构建、测试、迭代想法。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "对知识工作者",
   "paras": [
    "**For Knowledge Workers**",
    "知识工作有更多人在回路。但它仍是一个循环——工作流很大部分是阅读和决策、评估输出、创建交付物，而人一直在等待。每秒最多 750 token 让迭代显著更快，同样时间里产出更多，无论是起草邮件、处理税务还是剪视频。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 5：750 tok/s 让知识工作者迭代更快。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "电脑使用与自动化",
   "paras": [
    "**Computer Use & Automation**",
    "agent 最受欢迎的新用例之一，是在你许可下、在你专注更重要任务时，让模型在后台使用你的机器或浏览器。这赋予你创建强大自动化、把你能描述的任务直接委派给 agent 的能力，而不接管你的机器。",
    "更快的推理对 computer-use 工作负载的好处：减少「观察界面 → 决定做什么 → 采取下一步行动」之间的延迟。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "开放模型：公共端点数千 tok/s",
   "paras": [
    "另外，Cerebras 在其公共端点上以每秒数千 token 服务领先的开放模型：",
    "**OpenAI GPT OSS 120B 在 3,000 tok/s**",
    "**Gemma 4 31B 在 1,850 tok/s**",
    "**Z.ai GLM 4.7 在 1,000 tok/s**",
    "对专用企业端点，Cerebras 还支持 Kimi K2.6、GLM 5.1、MiniMax M2.5、Qwen3 Coder 480B、Llama 4 Maverick、Mistral Large 3、DeepSeek V3.2，以及更多模型家族。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig07.png",
      "caption": "图 6：Cerebras 公共端点开放模型速度。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "附加来源与致谢",
   "paras": [
    "**Additional Sources**",
    "OpenAI: GPT-5.6 launch；Cerebras WSE-3 product page；Cerebras: Introducing Cerebras Inference；Cerebras: WSE-3 announcement；Cerebras: OpenAI partnership；Cerebras: Getting the most out of GPT-5.6 (Sol, Terra, Luna)；Cerebras GPT-5.6-Ultrafast Blog。",
    "图表由 Halley Chang 绘制。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "Sarah Chieng（Cerebras DevX 负责人）这篇 X 长文把「Cerebras 怎么让 GPT-5.6 Sol 跑到 750 tok/s」讲得极清楚：**核心是「什么都不改」**——同一模型架构/权重/精度/推理设置，唯一差异是硬件换成 WSE-3（整片晶圆当芯片：44GB SRAM 紧靠 90 万核、21PB/s 带宽），绕过 GPU 片外 HBM 的内存墙。",
  "机制值得记：GPU 权重要不断跨 HBM 边界搬进 compute（内存墙），加卡只会让同步步更贵；Cerebras 让权重贴近 compute、Sol 按层分片到多 CS-3、只有 activation 在 wafer 间流动。收益可测：GDP-Val 5.6×、Humanity's Last Exam 6.9× 更快、1 小时任务 <9 分钟。对关心推理速度/agent 延迟的人，这是「换硬件而非换模型」的教科书级案例。"
 ],
 "reference_url": "https://x.com/MilksandMatcha/status/2092664576404070562"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("✅ 写入 article_data.json")
