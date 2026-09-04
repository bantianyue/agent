# -*- coding: utf-8 -*-
"""HBM5 SI 编译 build"""
import json, os, sys

DATA = {
 "title": "HBM5 高速互连深度解析：信号完整性与协同设计挑战",
 "lead": [
  "当大量注意力集中在当前的 HBM4 短缺时，这篇帖子聚焦于扩展 HBM5 性能的实际技术挑战。",
  "本文将基于 SK Hynix 和 KAIST 的 ECTC 2026 论文，讨论 HBM5 中以下**信号完整性**和**协同设计**挑战：HBM1 到 HBM5 的信号完整性趋势；短高速互连的抖动（jitter）组件树和关键抖动源描述（Echo、SSC/SSN、PSIJ）；SK Hynix 如何量化高速 HBM5 数据线中的传输线效应（传输线基础、RC 与 LC 主导两个工作区域）；以及 KAIST 面向 Chiplet（UCIe）GPU-HBM 互连的 PSIJ 的 SI/PI 协同分析框架。",
  "这篇文章深受 ECTC session 11「Signal Integrity Design for High-Speed Interfaces」影响，也基于我亲临 DesignCon 2026 的经历。这会是偏**进阶**的深度解析，但**扎根于基础**。我以基线 EE 概念起步，构建理解多层 SI/PI 协同设计复杂性的框架。",
  "注意我不是信号完整性专家。但我带着 **RF/Microwave** 视角沉浸进 DesignCon 2026 的 SI 世界，用来分析高速信号完整性效应。读这些论文时很清楚：内存和 SI 工程师与 RF 人不说同一种语言，但他们从自己的视角描述同样的效应。",
  "我个人的看法是，在越来越快的数据速率下，**RF/Microwave 和信号完整性领域之间会有知识收敛**。我旨在弥合这个理解鸿沟。"
 ],
 "summary": [
  {
   "key": "核心背景",
   "body": "HBM5 每 DQ 数据率达 20-30 Gbps，进入有损传输线区域——之前 HBM 世代（<10Gbps、~6mm interposer）无显著传输线效应。无法用端接电阻（1000+ I/O 会导致高热耗和静态功耗），需 RF/Microwave 视角分析。"
  },
  {
   "key": "抖动三源",
   "body": "高速非端接并行线的确定性抖动三源：Echo jitter（阻抗失配反射，存储记忆+过冲）、Bounded Uncorrelated（串扰，海量组合但界于最坏情况）、Periodic（SSN 同步开关噪声，周期性重复）。PSIJ 尤其难建模，是 power-noise 导致的时序退化。"
  },
  {
   "key": "SK Hynix 方案",
   "body": "HBM 互连通道电阻高（1-10 欧姆 vs 特性阻抗），无法用标准微波技术（50 欧姆标准化不适用）。选 Ron=14 欧姆、特性阻抗 34 欧姆，平衡版图面积和 slew rate，源端反射系数 -0.41。把工作模式分 RC 主导和 LC 主导两区域定义自己的 SI 评价准则。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "SK Hynix：高速 HBM 路线图",
   "paras": [
    "高带宽内存（HBM）是 AI 训练工作负载的关键组件，存储 AI 计算涉及的一切：模型权重、梯度、优化器状态和激活。HBM 用 TSV 垂直连接多个 DRAM die，在给定 footprint 内最大化内存密度。这些 DRAM die 尽可能靠近 GPU，以最大化数据吞吐、克服**冯诺依曼瓶颈**。",
    "在这个 ECTC 2026 展示的 SK Hynix 路线图中，有几条 HBM 世代的性能缩放趋势：",
    "HBM1 到 HBM4，每 DQ 数据率从 1Gb/s 线性增到 11.7Gb/s；沿这些世代，信号 rise time 和 unit interval（UI）与每 DQ 总数据率成反比缩放。",
    "HBM3E 到 HBM4 之间，总带宽阶跃式跳升 2.5×，主要由**每 cube I/O 从 1024 翻倍到 2048** 驱动。",
    "为跟上 AI 工作负载需求，HBM5 期望用 Chip-on-Wafer-on-Substrate（CoWoS-L 和 CoWoS-R）等最先进 interposer 技术达到**每 DQ 20-30 Gbps**。",
    "在这些数据率下，HBM 在信号完整性、电源完整性和热领域遇到协同设计挑战。在 ECTC 上，我在三篇论文中注意到三个高层次趋势。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：2.5D 封装中使用的 HBM。来源：J. Lau, ECTC2026。"
     },
     {
      "src": "fig02.png",
      "caption": "图 2：HBM Gen1 到 Gen5 缩放中的 SI 特性。来源：T. Bae et al., ECTC2026。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "挑战一：传输线效应抖动",
   "paras": [
    "SK Hynix 指出，对于数据率低于每 DQ 10 Gbps、约 6mm 长 interposer 互连的先前 HBM 世代，未观察到显著传输线效应。",
    "然而在 30Gbps 速率下，先进封装互连技术表现出明显的**有损传输线特性**，必须加以考虑。",
    "通常传输线用等效阻抗端接以避免反射。然而**端接电阻无法合理用于** HBM 中 1000+ 个 I/O，因为这会导致**高热惩罚和静态功耗**。这带来后续将讨论的额外信号完整性挑战。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "挑战二：从「宽而慢」到 UCIe",
   "paras": [
    "另一个挑战是 **I/O 的边缘密度限制**。I/O 引脚数量翻倍导致硅上物理层（PHY）footprint 过大。I/O 数量从根本上受金属 pitch、层数和用于控制串扰的 ground rail 面积约束。",
    "为扩展 I/O 数量，KAIST 正在研究从宽而慢的 I/O 走向 Universal Chiplet Express（UCIe）标准中更高速 SerDes lane 的性能影响。",
    "KAIST 指出，基于 UCIe 的 chiplet GPU-HBM 中利用八个 D2D 模块，每个模块含 64 个 Tx 和 Rx、各 32Gb/s。共 512 个 Tx 和 Rx 为读和写方向支持 2 TB/s。",
    "用更快、更紧凑的 PHY，更多 I/O 能装进 HBM shoreline，提高数据吞吐。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 3：HBM4 传统与 G2D 模块的 shoreline 示意。来源：H. Suh, ECTC2026。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "挑战三：3D 堆栈的 PDN",
   "paras": [
    "另一个协同设计挑战是 HBM 堆栈中的 TSV 如何影响**热特性**。",
    "该论文评估不同 TSV 配置的**热和 IR drop 特性**。这里看到每个组件如何建模为网格结构中的单元阵列，带等效 RLC 电路模型。",
    "虽然我认为这篇论文对有效协同设计很重要，尤其对建模 PSIJ 的 PDN，但我暂时把分析留在这篇帖子之外，聚焦前两篇论文的信号完整性挑战。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 4：所用 TSV 和电源网格结构示意。来源：J. Yoon et al., ECTC2026。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "高速低电压并行线的关键抖动源",
   "paras": [
    "抖动是高速信号完整性的关键约束，必须尽可能考虑和最小化。",
    "高速数据发送到 HBM 及从 HBM 发出时，每个 bit 在称为「Unit Interval」（UI）或 bit-period 的给定时隙内接收。抖动和 slew rate 约束把接收数据的有效 aperture「窗口」减小。全篇中所有 aperture 结果都归一化到 UI=1。",
    "这个来自 Mike Peng Li 博士 DesignCon 2026 tutorial 的全面抖动树展示了许多不同抖动源。",
    "抖动分为两大统计类别：确定性和随机抖动。",
    "在确定性抖动下，有三个与高速、海量并行、非端接线相关的初级抖动类："
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 5：HBM 的眼图测量，显示 aperture 和抖动。来源：T. Bae et al., ECTC2026。"
     },
     {
      "src": "fig06.png",
      "caption": "图 6：抖动组件树，显示抖动的统计效应及其物理机制。来源：M. Li, DesignCon 2026。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Echo Jitter",
   "paras": [
    "由阻抗失配和反射引起的抖动。",
    "当信号沿线传播并遇到阻抗失配时，部分信号前后反射，导致存储的「记忆」和过冲，影响未来 bit 测量。这会导致 ISI。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Bounded Uncorrelated Jitter 与 Periodic Jitter",
   "paras": [
    "**Bounded Uncorrelated Jitter**：有界但与信号不相关的抖动。包括跨海量并行线的**串扰**，有大量可能的串扰交互组合，但整体抖动影响「有界」在最坏情况。",
    "**Periodic Jitter**：时序变化在特定频率随时间周期性重复的抖动。包括每个开关周期发生的**同步开关噪声（SSN）**。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "PSIJ：电源引起的抖动",
   "paras": [
    "在数据率提高时特别成问题的一个抖动源是**power-supply induced jitter（PSIJ）**——电路内部一种 power-noise 引起的时序退化形式。它难以建模，因为它结合了来自几个源的抖动。",
    "电路的 rise/fall 时间和传播延迟取决于 PDN 给 FET 电容充电的速度。门开关时产生**同步开关电流（SSC）**，穿过 PDN 在线路上引起**同步开关噪声（SSN）**。PDN 上的噪声会影响电容充电电流，引入**时序不确定性**。",
    "随着在同一 PDN 上堆叠和塞入更多 HBM、PDN 线路变得更嘈杂，PSIJ 变得更成问题。数据率提高、数千个 I/O 驱动器同步开关、低电源电压下，**PSIJ 的边际增加会侵蚀抖动预算并导致信号故障**。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig07.png",
      "caption": "图 7：PSIJ 从 VRM 耦合的电源噪声显现的高层示意。来源：H. An et al., ECTC2026。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "SK Hynix 如何纳入高速 HBM 数据线的传输线效应",
   "paras": [
    "现在讨论 SK Hynix 面临的传输线效应带来的高速 SI 挑战。我从 RF 视角宽泛介绍传输效应，作为它关联 SI 的细微差别，然后直接进入 SK Hynix 的分析。",
    "**从 Lumped 到 Distributed 抽象**：大多数电路分析（如 V = IR）最初以「lumped」抽象教授，其中组件值被 lumped 或简化成由电阻、电容和电感组成的器件。Lumped 抽象构成大多数传统电路分析的基础，如 nodal、mesh 等。",
    "lumped 抽象的重点是，频率足够低时，lumped 组件之间物理连接的传播特性可合理忽略。频率低时，由于整条线上**分布**的电容几乎瞬时充电，信号电平在所有线长上几乎相同。",
    "然而高频下，信号必须物理传播过线从 A 到 B，所以互连的物理特性重要。这被称为「distributed」抽象，其中**电磁波传播**特性沿线（**传输线**）起作用。图中可看到高频波发送下线时，电压在不同时间点上升。",
    "决定用 lumped 还是 distributed 元素建模的 RF 经验法则：**线长约为信号波长的 10% 时，传输线效应开始起作用**。对约 6mm、er=4 的互连，对应 2.5 GHz 频率。显然 HBM 数据率正在进入这个区域。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig08.png",
      "caption": "图 8：长度占波长可观百分比的传输线上的瞬时电压。来源：T. Bae, ECTC 2026。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "反射系数与阻抗失配",
   "paras": [
    "传输线理论中，波沿特性阻抗 Zo 的线发送时，端接处需要相等阻抗让信号「匹配」，否则波会向后反射。**反射系数**量化该效应。",
    "阻抗不匹配时反射系数非 0。根据失配程度，一部分到达负载的波**沿时间延迟 Td 前后反射，随时间衰减**。",
    "对开路或高阻抗电路，Z_L 无穷、反射系数为 1。这意味着对高频 RF 信号，所有传播信号都被发回，因为没有地方端接。这表现为图 8 中的「阶梯」函数。",
    "从源 POV，看向线的有效阻抗取决于**源和端接之间的线长**。Smith chart 上的阻抗可按波长的整数倍旋转，找到「看向」线的等效阻抗。一个特例（面试常问）是 λ/4 线把开路阻抗「变换」成看向线的短路。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig09.png",
      "caption": "图 9：传输线的信号特性——信号发出、到达开路端、按 Td 延迟反射回源、遇到 Ron=14 欧姆与 Zo=35 欧姆的失配再反射回去降低电压。来源：T. Bae, ECTC 2026。"
     },
     {
      "src": "fig10.png",
      "caption": "图 10：Smith chart 显示四分之一波长线的阻抗变换。（注意 Smith chart 分析对高速数字信号不总是有效，但构建直觉有用）"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "RF 技术应用于 SI 的注意事项",
   "paras": [
    "虽然 RF 有高度发达的宽带分析技术如 Smith chart，但应用于信号完整性时有几个注意事项：",
    "数据是数字数据，理想上是带 rise/fall 时间和奇模谐波的方波，而非宽带正弦波。信号在源端变高时，其值保持高在固定电平直到下一个周期。",
    "**互连电阻相当高（1 到 10 多欧姆），相比特性阻抗。**在大多数有足够板空间的有损 RF 传输线中，电阻通常不会这么高。HBM 电阻高唯一原因是海量并行所需的微小线宽。",
    "RF 理论中特性阻抗常标准化为 50 欧姆、源阻抗匹配。然而把源阻抗匹配到 HBM 互连阻抗不实际，因为改变 Ron 能解决一个问题但制造其他问题：",
    "增大 Ron 做阻抗匹配会把发射电压砍半、更慢给线充电、降低 slew rate；减小 Ron 需要大宽度晶体管，可能侵蚀边缘密度。",
    "因此 SK Hynix 为特性阻抗 34 欧姆选择 **Ron 14 欧姆**，平衡**版图面积**和 **slew rate** 的权衡。这导致源端反射系数 -0.41。",
    "简言之，对每 DQ 30Gb/s 的 HBM5，SK Hynix 面对**高通道电阻**和**传输线效应**的棘手组合，无法用标准微波技术轻松分析，因此必须为高速信号完整性定义自己的评价准则。这些准则涉及把操作模式分为两个不同区域：**RC 主导**和 **LC 主导**。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇文章是 HBM5 信号完整性的深度科普（作者 Chad 带 RF/Microwave 视角），核心价值在「**RF 语言与 SI 语言正在收敛**」的洞察：HBM5 的 20-30 Gbps/DQ 数据率进入有损传输线区域，但 HBM 互连的高通道电阻（1-10 欧姆）和非端接（1000+ I/O 无法用端接电阻）让标准微波技术（50 欧姆匹配）失效。",
  "几个扎实的工程点：**抖动三源**（Echo 反射、BUJ 串扰、Periodic/SSN）+ PSIJ（电源噪声→时序退化，难建模）；**lumped→distributed 分界**（线长≈10% 波长，对 6mm interposer 是 2.5GHz）；SK Hynix 的 **Ron=14Ω/Zo=34Ω** 权衡（平衡版图面积与 slew rate，反射系数 -0.41）、RC/LC 双区域评价准则。",
  "注意：**原文为付费墙文章**（Silicon Co-Design Paid），本文基于免费区主体内容；付费区的 DOE 实验结果、KAIST SI/PI 协同分析框架和 BONUS「The Brain」3D HBM 状态未包含。"
 ],
 "reference_url": "https://www.siliconcodesign.com/p/a-comprehensive-deep-dive-into-high"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")