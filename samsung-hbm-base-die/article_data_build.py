# -*- coding: utf-8 -*-
"""Samsung HBM base die 编译 build"""
import json

DATA = {
 "title": "三星在 Hot Chips 2026 展示「演进的 HBM 基片」：从被动中介层走向协处理器",
 "lead": [
  "Hot Chips 2026 上，三星带来《Evolving HBM Base Die》演讲，讲述如何把高带宽内存的基片（base die/B-die）从被动中介层变成强大得多的角色。ServeTheHome 现场报道全文。",
  "核心轨迹：用先进逻辑工艺武装基片，Phase 1 回收 XPU 面积（PHY 缩小、内存控制器下移）、Phase 2 扩展功能（RAS/传感器、外接内存、处理单元卸载）、Phase 3 迈向真正的 3D 垂直集成（zHBM，移除 2.5D 中介层）。"
 ],
 "summary": [
  {
   "key": "背景与趋势",
   "body": "HBM 分 DRAM 核心堆叠（C-die）和基片（B-die，含 PHY+TSV）。带宽/容量从 HBM1（~1GB/1TB/s）涨到 HBM5（60GB+/6TB/s）；限速在 TSV 密度、I/O 数和 PHY 速度。B-die 从 HBM4 起转 4nm 先进逻辑。"
  },
  {
   "key": "三阶段路线",
   "body": "Phase1 回收 XPU 面积：PHY→D2D 接口缩小、Heat Path Block 散热（峰温降 >35%）、内存控制器下移 B-die、SRAM 修复方案。Phase2 扩展功能：SoC 级 RAS/传感器/自测、外接内存、处理单元卸载、aHBM 2.5D。Phase3 3D 集成：zHBM 去中介层、WoW 混合键合、省 ~100W。"
  },
  {
   "key": "判断",
   "body": "基片正从被动中介层变协处理器——把内存控制器、处理单元搬进 HBM 给加速器厂商新家。系统架构师应密切关注未来 HBM 世代。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "背景：新汉基底片的角色与演进",
   "paras": [
    "HBM 把工作分给堆叠在上方的 DRAM 核心 die 和下方的 base die。三星把堆叠的存储层叫 C-die，base die（或 B-die）承载 PHY 和穿透硅通孔（TSV），形成到计算 die 的通信通道。4、8、12 或 16 个 C-die 堆叠落在 base die 上。",
    "HBM 带宽和容量自第一代起稳步攀升。三星历史数据：从最初 HBM 的约 1GB 容量、1TB/s 带宽，到 HBM5 世代突破 60GB 和 6TB/s。持续上升的带宽（而非纯容量）不断迫使 base die 发生根本变化。",
    "几个限制制约 HBM 带宽增长。三星指出 C-die 堆叠和 base die 上的穿透硅通孔数量和间距，以及 B-die 内嵌 PHY 的 I/O 数量和速度。TSV 和 DQ 数对比间距和面积跨世代变化，显示压力在哪里累积。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 1：三星 HBM——C-die 堆叠落在承载 PHY+TSV 的 base die（B-die）上。"
     }
    ],
    "1": [
     {
      "src": "fig04.png",
      "caption": "图 2：三星 HBM 发展史——从 HBM 约 1GB/1TB/s 到 HBM5 突破 60GB/6TB/s。"
     }
    ],
    "2": [
     {
      "src": "fig05.png",
      "caption": "图 3：限制带宽缩放的关键因素——TSV/DQ 数 vs 间距/面积。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "工艺演进：B-die 转向先进逻辑",
   "paras": [
    "C-die 的工艺技术留在 DRAM 类节点，但 base die 开始迁移。三星趋势表显示 B-die 从较旧的逻辑工艺转向、HBM4 起用 4nm，缩小与 XPU SoC 的差距。即便能效提升，MPGA 功耗仍在升，这正是三星说从 HBM4 起 B-die 里先进逻辑变得必需的原因。",
    "三星把 D1c DRAM 工艺和逻辑 4nm 用到 HBM4，主要目标是降功耗。active area 最小化也重要，这项工作标志着真正的 DRAM 与先进逻辑集成之始。跨工艺节点轨迹显示，逻辑节点推进时 TSV 到 PHY 的中继器功耗和延迟都在下降。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig06.png",
      "caption": "图 4：三星工艺节点趋势——B-die 从 HBM4 起转 4nm。"
     }
    ],
    "1": [
     {
      "src": "fig07.png",
      "caption": "图 5：用先进逻辑工艺的好处——TSV-PHY 中继器功耗与延迟随节点下降。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "标准 vs 定制 HBM（sHBM/cHBM）",
   "paras": [
    "标准 HBM（sHBM，三星称）把 B-die 限制在基本的数据和测试路径功能。定制 HBM（cHBM）则用先进逻辑工艺构建更 SoC 化的 base die，同时仍共享标准 C-die 堆叠。此前业界连非内存厂商（如 Marvell）都展示过定制 HBM。",
    "传统缩放正撞物理极限。节点缩小放缓、单片 die 接近光罩极限、多 chiplet 中介层碰尺寸极限。三星的答案是用已经在跑先进逻辑的 base die，把一些功能从 XPU 卸载到 B-die。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig08.png",
      "caption": "图 6：走向定制 HBM（cHBM）——概念与动机。"
     }
    ],
    "1": [
     {
      "src": "fig09.png",
      "caption": "图 7：Phase 1——xPU 面积回收：把功能卸载到 B-die。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Phase 1：回收 XPU 面积",
   "paras": [
    "当代标准 HBM 上，PHY 是 base die 上最大的块。三星用建在先进逻辑上的 die-to-die 接口替换传统 HBM PHY，缩小占用 footprint、也缩短通道提升能效。腾出的硅变成 XPU 面积扩展的空间——floorplan 对比可见。",
    "从 HBM2 到 sHBM4，PHY footprint 和通道深度持续扩张以喂更高带宽。先进逻辑显著削减 HBM4 到 HBM5 的 PHY 和 D2D 面积，把更多功率包进更小的 PHY 区域。更短通道降低每 bit 能，但把更多功率塞进更小 PHY 提高功率密度、制造热热点。",
    "热压力有专门解决。三星提出 Heat Path Block（HPB），基于 cHBM4 设计经验构建。PHY 覆盖率超过 50% 时，峰值温度降超 35%——sHBM4E 到 sHBM5 I/O 速度翻倍、功率密度从 0.5 升到超 2.0 W/mm²，三星正需要这个。",
    "base die 一旦有空间，三星开始把 XPU 逻辑搬上去。首要目标就是内存控制器。把 MC 移到 B-die 回收宝贵的 XPU 硅，三星称热影响可控，传统 HBM 内存控制器已积极移植进 cHBM。",
    "把 SRAM 放 base die 也提升可靠性。三星基于 SRAM 的 cell 修复方案用未用的 B-die 空间、以细粒度解码并重定向失败 cell 地址、跨通道共享修复容量。相比依赖 C-die 有限备用资源的传统修复，此方案在 B-die 提供更大更灵活的修复资源。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig10.png",
      "caption": "图 8：Phase 1——PHY 面积缩减：D2D 接口替换传统 HBM PHY。"
     }
    ],
    "1": [
     {
      "src": "fig11.png",
      "caption": "图 9：Phase 1——跨世代面积缩减：先进逻辑削减 PHY/D2D 面积。"
     }
    ],
    "2": [
     {
      "src": "fig12.png",
      "caption": "图 10：Phase 1——热挑战与 Heat Path Block 方案（峰温降 >35%）。"
     }
    ],
    "3": [
     {
      "src": "fig13.png",
      "caption": "图 11：Phase 1——内存控制器卸载到 B-die 回收 XPU 硅。"
     }
    ],
    "4": [
     {
      "src": "fig14.png",
      "caption": "图 12：Phase 1——近 MC：基于 SRAM 的 cell 修复方案。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Phase 2：扩展功能集",
   "paras": [
    "Phase 1 在桌上留了大量硅。因为整体 HBM footprint 主要由 C-die 堆叠界定、sHBM 的 base die 大多是被动布线，即使内存控制器移走后三星仍看到空间。那片未利用的 B-die 区域成为 Phase 2 扩展功能集的基础。",
    "定制 HBM 把 SoC 级 RAS 带进 base die——标准 HBM 所缺乏的。三星集成热、电压、工艺、老化传感器做实时遥测，加上片上自测方案（on-die ATE 和 pattern generators）提高测试覆盖和良率。这种传感器+自测部署正是区分 cHBM 与 sHBM 的所在。",
    "容量需求增长得和带宽一样快。三星指出上下文窗口每年扩张约 30 倍，驱动大量 KV cache 内存需求，并称长期记忆存储/检索是下一代 AI 模型的关键瓶颈。这指向下一代 AI SoC 需要更高容量、而不只是更高带宽。",
    "加容量的一条路径是从 base die 直接挂外部内存。三星用 B-die 的外侧岸线（outer shoreline）通过 die 上集成的专用 PHY 和控制器连接外部内存——比传统 PCIe 扩展更高带宽更低延迟。",
    "三星还看到把计算卸载到 B-die 的空间。base die 里的处理单元（PE）可承担 XPU SoC 的部分工作，削减 die-to-die 带宽需求、降低功耗和热开销。有限硅面积和这些 PE 带来的更高热密度是关键挑战。",
    "把处理单元集成进 base die、三星更进一步走向 2.5D 系统。先进 HBM（aHBM）把 XPU 计算卸载到那些 PE，最小化跨中介层的数据移动。三星称由此实现的能效收益是系统级突破。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig15.png",
      "caption": "图 13：Phase 2——B-die 额外功能（RAS/传感器/自测）。"
     }
    ],
    "1": [
     {
      "src": "fig16.png",
      "caption": "图 14：Phase 2——RAS 与测试：传感器+自测区分 cHBM/sHBM。"
     }
    ],
    "2": [
     {
      "src": "fig17.png",
      "caption": "图 15：Phase 2——容量需求：上下文窗口年增 30×、KV cache 需求巨大。"
     }
    ],
    "3": [
     {
      "src": "fig18.png",
      "caption": "图 16：Phase 2——内存扩展：外部内存直接挂 B-die 外侧岸线。"
     }
    ],
    "4": [
     {
      "src": "fig19.png",
      "caption": "图 17：Phase 2——处理单元卸载：PE 卸掉 XPU 部分工作。"
     }
    ],
    "5": [
     {
      "src": "fig20.png",
      "caption": "图 18：Phase 2——2.5D 集成与 aHBM：最小化跨中介层数据移动。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Phase 3：真正的 3D 集成 —— zHBM",
   "paras": [
    "Phase 3 完全超出中介层。三星认为行业正转向紧耦合的 AI 内存，在严格功耗限制内最大化每秒 token 数是推理的挑战。zHBM 是答案——XPU 与 C-die 堆叠的真正 3D 垂直集成，移除 2.5D 中介层。",
    "zHBM 改变 HBM 的物理叙事。分布式 I/O 缩短数据在堆叠内部走的距离，真正 3D 结构消除传统 2D 接口（如 HBM PHY 或 D2D）。三星用这种安排瞄准超低功耗。",
    "功耗是 zHBM 的头号优势。移除 SERDES 和数据对齐开销戏剧性削减 I/O 功耗，三星的系统级预估显示这转化为算力和热余量。一个例子：SiP 里四个 zHBM 堆叠、配 1200W GPU，显著提升带宽同时节省约 100W。",
    "交付 zHBM 靠两大技术支柱。Wafer-on-wafer 键合和混合铜键合实现超高 I/O 密度，三星强调统一的 SoC 和 DRAM 设计验证流对 co-architecture 至关重要。该图展示 WoW 键合流程和协同开发 DRAM C-die 与 XPU 的一体化设计流程。",
    "三星以框架收尾：把先进逻辑用到 base die 解锁架构灵活性——Phase 1 卸载并优化、Phase 2 扩展功能、Phase 3 以 zHBM 收敛到真正 3D 集成。这条从回收 XPU 面积到消除中介层的三阶段路径，就是三星认为推动 HBM base-die 设计向前的东西。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig21.png",
      "caption": "图 19：Phase 3——3D 集成：zHBM 移除 2.5D 中介层。"
     }
    ],
    "1": [
     {
      "src": "fig22.png",
      "caption": "图 20：zHBM 概念——分布式 I/O、去除 PHY/D2D。"
     }
    ],
    "2": [
     {
      "src": "fig23.png",
      "caption": "图 21：zHBM 优势——I/O 功耗大降、省约 100W。"
     }
    ],
    "3": [
     {
      "src": "fig24.png",
      "caption": "图 22：zHBM 关键技术——WoW 键合 + 混合铜键合 + 统一设计流。"
     }
    ],
    "4": [
     {
      "src": "fig25.png",
      "caption": "图 23：三星总结——三阶段路线（回收面积→扩展功能→3D 集成）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "结语",
   "paras": [
    "这些图合起来展示三星如何处理演进的 HBM base die。",
    "**ServeTheHome 看法**：这个 base die 正变成协处理器而非被动中介层，改变了 AI 系统里内存和逻辑设计的位置。把内存控制器、最终还有处理单元搬进 HBM，给加速器厂商提供了部分硅的新家。zHBM 无论多远，都指引行业走向把计算直接堆在 DRAM 上、移除中介层。系统架构师应密切关注下一批 HBM 世代的此转变。一场精彩的 Hot Chips 2026 演讲。"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "这篇 Hot Chips 2026 三星演讲把 HBM 基片的演变讲清楚：**基片从被动中介层变成协处理器**。三阶段——Phase 1 把先进逻辑用上基片、回收 XPU 面积（PHY→D2D 接口缩小、Heat Path Block 峰温降 >35%、内存控制器下移 B-die、SRAM cell 修复）；Phase 2 扩展功能（SoC 级 RAS/传感器/自测、外侧岸线挂外部内存、处理单元卸载、aHBM 2.5D）；Phase 3 走向 zHBM 真正 3D 集成、移除中介层、WoW 混合键合、省约 100W。",
  "本质：给加速器厂商提供新家（内存控制器、处理单元搬进 HBM）、上下文年增 30× 驱动容量需求、zHBM 把计算直接堆 DRAM 上。对做 AI 硬件/加速器/系统架构的人，这是理解内存与逻辑设计边界如何重画的重要信号——基片化是下一个大方向。"
 ],
 "reference_url": "https://www.servethehome.com/samsung-evolving-hbm-base-die-at-hot-chips-2026/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")