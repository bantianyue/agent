# -*- coding: utf-8 -*-
"""Tenstorrent QuietBox 400tps 标准模板 build"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
tr=json.load(open(os.path.join(_article_dir,"_trans.json"),encoding="utf-8"))

DATA = {
  "title": "⚡ 1.2万美元的 Tenstorrent QuietBox 跑出 400 token/s：桌面级 SRAM 推理的极限（8B MoE）",
  "summary": [
    {"key":"结果","body":"Marco-Nano-Instruct（8B MoE、6亿激活）在 1.2万美元 QuietBox (Blackhole) 桌面主机上全自回归解码推到 397.7 token/s（trace 重放 402.6）。"},
    {"key":"方法","body":"核心差异是 SRAM 驻留：把关键循环/注意力状态放进 720MB 片上 SRAM，冷权重从 GDDR6 流式加载，而非架构全靠 HBM。"},
    {"key":"对比","body":"最快全 DRAM 端到端 ~260 token/s，优化后 +53%；为 Tenstorrent Galaxy 32 芯片扩展提供 desk-scale 证明。"},
  ],
  "lead": [
    "我们拿 **Marco-Nano-Instruct**（80 亿参数混合专家模型，每 token 激活约 6 亿参数），把它的完整自回归解码流水线，在一台**1.2 万美元的 Tenstorrent QuietBox（Blackhole）** 上推到了 **397.7 token/s**。",
    "这个数字的意义不止于贵不贵：它不是投机解码、没有草稿模型、不跳层，token 完整穿过全部 28 层。SRAM 是额外的杠杆——把每个 token 都要取的关键数据留在芯片旁边。",
  ],
  "sections": [
    {"type":"h2","title":"720MB 片上 SRAM，预览 Galaxy 时代","paras":[
      "实验主角是 Marco-Nano-Instruct，一个 8B MoE（混合专家）模型，每 token 激活约 6 亿参数。优化后自回归解码流水线在桌边 QuietBox 上跑到 **397.7 token/s**。",
    ],"fig_after":{0:[{"src":"fig01.png","caption":"图1：吞吐 trace——397.7 token/s 的关键路径"}]}},
    {"type":"h3","title":"越过 400：trace 与全 DRAM 基线","paras":[
      "trace 本身已越过 400：不交付最终 token 日志重放时到 **402.6 token/s**；项目记录中最强的全 DRAM 端到端约 **260 token/s**。",
      "「这是 batch one」：无投机解码、无草稿模型、无跳层、每用户数字里没有隐藏第二流——token 穿过全部 28 层、最终归一化，端到端一气呵成。",
      "用的优化族与高性能 NVIDIA 代码相同：**kernel 融合、异步预取与双缓冲、精细分片的数据流、设备端状态、trace 图**。SRAM 是额外杠杆——与其每个 token 都去拉关键数据，不如把它摆在消费它的 Tensix 核心旁。",
    ]},
    {"type":"h2","title":"Tenstorrent 构建了什么","paras":[
      "大多数做 AI 的人都认识 NVIDIA，但很少有人知道 Tenstorrent 处理器内部构造，值得从硬件说起。",
      "**Blackhole 是 Tensix 核心网格，由两套片上网络连接**。每个 Tensix 核心组合了：基于 tile 的矩阵引擎、向量引擎、可编程 RISC-V 核心（负责计算与数据搬运）、本地 SRAM、硬件管理的环形缓冲流控。",
      "两个用户可编程的数据搬运内核可发起异步读写、寻址 SRAM/DRAM 存储体、通过信号量协调，并在计算内核工作的同时搬运数据。",
    ],"fig_after":{0:[{"src":"fig02.png","caption":"图2：Blackhole / TT-Metalium（Hot Chips 2024）"}]}},
    {"type":"h3","title":"「独立 AI 计算机」","paras":[
      "Hot Chips 2024 的 Blackhole 和 TT-Metalium 演示把芯片描述为「独立 AI 计算机」。这是个有用的说法——**Blackhole 不只是等待主机供料的矩阵引擎**：计算、数据移动、本地存储、DRAM 控制、网络都是机器中可编程的部分。",
    ],"fig_after":{0:[{"src":"fig03.png","caption":"图3：Blackhole 芯片架构（Tensix 网格 + 片上网络）"}]}},
    {"type":"p","title":"","paras":[
      "当前的 Blackhole p150 产品暴露 **120 个 Tensix 核心、180MB SRAM、32GB GDDR6（512 GB/s）**、Block FP8 下 664 TFLOPS，还有 4 个 800G 以太网口支持 Blackhole 直连。",
      "所有这些均为本地拥有，并可通过 Tenstorrent 的开源软件栈完全编程。",
    ]},
    {"type":"h2","title":"为什么 LLM 解码通常是内存问题","paras":[
      "运行 LLM 有两个不同阶段。**预填充**处理输入提示，许多 token 一起评估；**解码**逐一生成答案 token，每个新 token 依赖之前所有 token（自回归）——解码步是高度内存受限的。",
    ]},
    {"type":"h2","title":"内存赌注","paras":[
      "现代 AI 处理器大部分时间在搬运张量而非做乘法。算术单元速度提升快于外部内存供给速度。**NVIDIA 通过 HBM 解决**：先进封装 + 庞大规模支撑的供应链；**Tenstorrent 则押注 SRAM 驻留**。",
    ],"fig_after":{0:[{"src":"fig04.png","caption":"图4：内存赌注——HBM 中心 vs SRAM 驻留"}]}},
    {"type":"p","title":"","paras":[
      "这些是完整 Blackhole 设计的架构级汇总数据，不是承诺每个内核都能看到 94 TB/s。SRAM 带宽随参与核心数与数据移动模式扩展。",
    ]},
    {"type":"h2","title":"缩小的 Galaxy 实验","paras":[
      "Marco Nano 提供了合适的实验形态：**真实 28 层 MoE、每层 232 个专家、每 token 选八个**，涉及注意力、增长的 KV 缓存、路由、专家执行、张量并行集合通信与自回归反馈——与更大规模 MoE 必须做的工作类别相同。",
      "总参数量 80 亿，但每 token 仅激活约 6 亿参数。这让在四颗芯片上复现内存策略成为可能：**把关键循环注意力与解码状态保留在 SRAM，同时从 GDDR6 流式加载选定专家权重**。",
      "确实使用了 Blackhole 原生低精度格式：对选定注意力与语言（token embedding/logit）部分用低精度。",
    ]},
    {"type":"h2","title":"实际带来的改变","paras":[
      "记录中最强的全 DRAM 端到端路径约 260 token/s；**在围绕持久 SRAM 数据优化流水线后，实际路径到 397.7 token/s，吞吐提升约 53%**。原始 trace 重放（不含最终 token 日志交付）到 402.6。",
    ],"fig_after":{0:[{"src":"fig05.gif","caption":"图5：演示回放——约 400 token/s 实时解码"}]}},
    {"type":"p","title":"","paras":[
      "以约 400 token/s 进行的演示回放。Iceland 副本经过精心挑选以让流可见——这是速度可视化，而非模型质量样本。",
    ],"fig_after":{0:[{"src":"fig06.png","caption":"图6：解码效果对比"}]}},
    {"type":"p","title":"","paras":[
      "这改变了模型的使用感受：长答案几乎即时返回。编程 Agent（智能体）可以检查、提议、测试、修订，而无需在循环里花大部分时间等推理；评估可即时、交互式进行。",
    ]},
    {"type":"h2","title":"为何 SRAM 超越带宽本身","paras":[
      "区别在**暂存（staging）与驻留（residency）**。每个加速器都会暂存数据——NVIDIA 开发者用异步拷贝、TMA、双缓冲、kernel 重叠把数据搬上搬下；Tenstorrent 的这个实验把关键数据**驻留**在 SRAM 里，让重复出现的循环数据不再每 token 往返外部内存。",
    ]},
    {"type":"h2","title":"从四芯片到 32 芯片","paras":[
      "QuietBox 是这套架构的桌面级版本；Galaxy 是扩展性论证变得有趣的地方——Galaxy Blackhole 在 6U 系统中连接多块处理单元。",
    ],"fig_after":{0:[{"src":"fig07.png","caption":"图7：从 QuietBox（桌面）到 Galaxy（机架）"}]}},
    {"type":"p","title":"","paras":[
      "从 QuietBox 到 Galaxy，**价格约涨 9.2 倍**：处理器数 8 倍、SRAM 约 8.6 倍、DRAM 容量 7.5 倍以上。",
    ]},
    {"type":"h2","title":"NVIDIA 对比","paras":[
      "NVIDIA 和 Tenstorrent 下的是不同的赌注。NVIDIA 围绕 **HBM、NVLink 与深度成熟的专有软件生态**构建了异常强大但以 HBM 为中心的系统；Tenstorrent 反向扩展：**加芯片、加 SRAM、加内存**，直至关键路径塞进分布式 SRAM。",
    ]},
    {"type":"h2","title":"每美元性能，也是每美元自由","paras":[
      "AI 基础设施讨论常把经济性简化为每百万 token 成本——这对服务业务有用，但对用模型构建的人来说不完整。**快速自有推理同时带来几方面的自由**：全栈可观察、数据不出门、迭代闭环更快。",
    ]},
    {"type":"h2","title":"下一规模","paras":[
      "QuietBox 实验回答了小版本问题：**循环工作集可驻留 Blackhole SRAM，选定冷权重从 GDDR6 流式加载，全 token 流水线在小型 MoE 上接近每秒 400 token**。Galaxy 让我们探讨大规模版本。",
      "基础模型共享工作集中多少能驻留 32 芯片？上下文增长时 KV 如何分布？专家预取在哪与注意力重叠？不牺牲每用户延迟下多少批处理提升 tile 利用率？多 Galaxy 互联时哪些张量该移动？",
    ]},
  ],
  "conclusion": [
    "这个实验最有力的点在于「放大器效应」：Marco Nano 虽小，却包含了与大规模 MoE 完全相同的工作类别（注意力、路由、专家、集合通信、自回归）。把关键路径压进 720MB 片上 SRAM，就能在 1.2 万美元的一台主机上换回 400 token/s 的完整推理。",
    "它把 Tenstorrent 与 NVIDIA 的路线分野摆得很清楚：一个以 HBM 流动性为中心，一个以 SRAM 驻留为主导。当 Galaxy 把 SRAM 从 720MB 推到几十 GB、扩展到 32 芯片时，这个 desk-scale 的 400 token/s 就成为「可规模化」的底层证明。",
  ],
  "reference_url": "https://medium.com/&#64;arnis.us/400-tokens-per-second-on-a-12-000-tenstorrent-quietbox-425aaf55bbeb",
}

out_path = os.path.join(_article_dir, "article_data.json")
os.makedirs(_article_dir, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
toti=sum(len(s['paras']) for s in DATA['sections'])
figs=sum(len(v) for s in DATA['sections'] for v in s.get('fig_after',{}).values() if isinstance(v,list))
print(f"✅ {len(DATA['sections'])} sections, {toti} paras, {figs} 图")
