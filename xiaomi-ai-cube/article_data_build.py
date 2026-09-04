# -*- coding: utf-8 -*-
"""Xiaomi AI Cube 编译 build（俄语源→中文, 1图, 格式规范）。"""
import json

DATA = {
  "title": "小米 AI Cube：三颗 XRing 芯片的本地 AI 计算机，能跑 120B 参数模型",
  "lead": [
    "2026 年 8 月中旬，小米半导体部门的非公开展示细节流出：一款名为 Xiaomi AI Cube 的工程原型机。它不是又一台用 Intel/AMD 移动处理器做的迷你主机，而是一台为特定任务打造的紧凑工作站——本地运行最多 120B 参数的开源神经网络，无需连云、也不依赖 Nvidia 显卡。这是目前已知关于该设备的一切。"
  ],
  "summary": [
    {"key":"三芯片架构","body":"异构 chiplet：O3（ARM v9.2 系统控制器，10 核，200 TOPS NPU）+ O100（6nm 矩阵加速器，1.22TB/s，解 TTFT 延迟）+ D100（3nm 计算 + 统一内存 160GB，源自小米电汽车自动驾驶芯片）。"},
    {"key":"性能","body":"3B-14B 模型（Q8/FP16）85-100 token/s@35W；70B（Q4）25-28 token/s；110-120B MoE 10-14 token/s@150W。整机峰值 150W，Type-C PD 200W。"},
    {"key":"软件与状态","body":"Linux + HyperOS AI Server + XRing Core 运行时（CUDA 实时转译）；支持 vLLM/llama.cpp/Ollama/PyTorch。工程样品，未定价，估组装成本约 1200-1500$——若卖 ≤2000$ 成 Mac Studio 直接对手。"}
  ],
  "sections": [
    {"type":"h2","title":"外观、结构与散热","paras":[
      "AI Cube 是一个边长约 16 厘米的立方体，外壳由整块航空铝在 CNC 机床铣削而成，而非冲压塑料。作者认为放弃塑料是为散热——金属外壳本身充当巨大的散热器。侧面和背面用激光开了超过 3.3 万个变径贯穿微孔。",
      "内部装有一块加大面积的均热板（vapor chamber），盖住整个硅片堆和内存芯片。唯一的风扇是一颗动压轴承的径向涡轮。",
      "整机峰值发热 150W（最大负载）；后台助手模式或跑轻量模型时功耗降到 30-40W。电源通过单根 Type-C（Power Delivery 协议）从外置 200W GaN 适配器供电。"
    ],"fig_after":{"0":[{"src":"fig01.png","caption":"图 1：Xiaomi AI Cube——16cm 铝立方，CNC 铣削，3.3 万微孔散热，本地跑最大 120B 参数模型。"}]}},
    {"type":"h2","title":"硬件平台：三芯片 XRing 组装","paras":[
      "整机逻辑不建立在单一芯片上，而是异构 XRing 芯片组（chiplets）组装。三颗处理器焊在同一块硅基板上，通过高速芯片间互连相连。",
      "**XRing O3——系统控制器**：ARM v9.2 通用逻辑芯片，内置 10 个计算核心（2 超大核+4 性能核+4 能效核）、自研 G2-Ultra NX 16 核集显、以及 200 TOPS（INT8/FP8）的基础 NPU。操作系统、驱动、存储和网络栈都跑在 O3 上。",
      "**XRing O100——矩阵加速器**：专为矩阵运算和 transformer 层快速解码（token 生成阶段）而生的 6nm 专用芯片，3D 布局。带 1.22TB/s 条带宽的专用高速缓冲——正是这一单元消除了 Time-to-First-Token 延迟。",
      "**XRing D100——计算器 + 内存银行**：3nm 芯片，20 个高密度内核，最初为小米电动车自动驾驶设计。集成四通道统一内存控制器，支持最多 160GB 的 LPDDR5X/LPDDR6 阵列，CPU 和 NPU 可直接访问。"
    ],"fig_after":{}},
    {"type":"h2","title":"接口与外设","paras":[
      "AI Cube 既能当带显示器的独立工作站，也能当局域网里的无头服务器（headless）。后面板接口：",
      "**两个 USB4/Thunderbolt**（40 Gbit/s，支持 DisplayPort 2.1 视频输出）；**两个 10 Gbit/s 以太网口**（快速搬运数据集、可把多个立方体组集群）；**一个 HDMI 2.1**（4K/120Hz）；**无线 Wi-Fi 7 + 蓝牙 5.4**。"
    ],"fig_after":{}},
    {"type":"h2","title":"真实模型的性能","paras":[
      "据 8 月 18 日闭门演示数据，工程师在原型上跑了 3B 到 120B 参数范围的模型。生成速度实测如下：",
      "**3B-14B 模型**（Llama 3.2、Qwen 2.5），Q8 或 FP16 量化，只用 O3+O100 组合。生成速度超过 85-100 token/s，功耗约 35W。",
      "**70B 模型**（Llama 3.3 70B、DeepSeek V3 Lite），Q4_K_M 4-bit 量化后约 42GB，动用 D100 芯片内存阵列。靠着加速器 1.22TB/s 带宽，生成速度维持在 25-28 token/s——比人舒适阅读速度（5-8 token/s）还快。",
      "**110B-120B 模型**及稀疏专家（MoE）架构，连同 32k-64k token 的工作上下文，整个塞进 D100 的 160GB 内存池。生成速度 10-14 token/s，最大功耗 150W。"
    ],"fig_after":{}},
    {"type":"h2","title":"软件栈","paras":[
      "设备跑定制版 Linux 发行版 + HyperOS AI Server 层。为兼容全球软件，小米工程师开发了 XRing Core 运行时，把 CUDA 算子实时转译成 O100 和 D100 硬件单元的指令。开箱即支持 vLLM、llama.cpp、Ollama 的 fork 及 PyTorch 框架。",
      "访问机器有三种方式：Web 界面、本地 OpenAI 兼容 API 端点、或直接 SSH 终端连接。"
    ],"fig_after":{}},
    {"type":"h2","title":"状态、价格与时间表","paras":[
      "目前 Xiaomi AI Cube 是**可运行的工程样品（Engineering Sample）**。公司尚未公布零售价和上架时间。据中国行业分析师估算，在当前环境下装配一台带 160GB 高速内存 + 3nm D100 芯片的机器，成本约 1200-1500 美元。",
      "如果量产版能压到 2000 美元以内上市，桌面 AI 工作站市场将迎来 Mac Studio 的直接竞争者——一台能用普通灯泡功耗跑动服务器级权重的机器。",
      "作者表示：期待发布，非常好奇最终价格是多少。"
    ],"fig_after":{}}
  ],
  "conclusion": [
    "这篇 Habr 汇总把小米 AI Cube 的核心信息讲全了：**一台为「本地跑大模型」而生的三芯片工作站**——XRing O3(O)+O100（矩阵加速器）+D100（计算+统一内存），16cm 铝立方、整体耗电仅 150W 峰值，就能跑 120B 参数模型（MoE），不依赖云和 Nvidia。",
    "关键亮点：140B 档 Q4 也有 25-28 token/s（比人阅读快）、120B MoE 带 32-64k 上下文能塞进 160GB 统一内存、CUDA 经 XRing Core 实时转译所以 vLLM/llama.cpp/Ollama 开箱即用。仍是工程样品、未定价，但若量产版压到 2000$ 以内、配合 Mac Studio 同级的本地 120B 推理，对桌面 AI 工作站市场是重磅——尤其对想本地跑大模型、不愿被云/Nvidia 绑定的用户。"
  ],
  "reference_url": "https://habr.com/ru/articles/1073828/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")