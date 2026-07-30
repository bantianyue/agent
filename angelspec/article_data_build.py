#!/usr/bin/env python3
"""
article_data_build.py — AngelSpec: Towards Real-World High Performance Inference with Speculative Decoding
=====================================================================================================
"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "AngelSpec：腾讯面向真实世界的投机解码框架——MTP+DFly+D-cut 三管齐下",
    "summary": [
        {"key": "核心洞察", "body": "不存在通用的最优草稿器——不同工作负载适配不同结构。MTP 适合高熵对话，DFly 适合代码/数学等结构化场景"},
        {"key": "DFly 架构创新", "body": "混合目标条件化骨架 + 前驱条件化自回归头，将平均接受长度提升约 30%，Hy3-A21B 上 MAL 达 5.32"},
        {"key": "D-cut 自适应预算", "body": "将验证视为共享批次级资源，动态选择保留深度；在 64 并发下将吞吐提升至 AR 的 1.44 倍"},
    ],
    "lead": [
        "投机解码可以加速大模型推理而无需改变目标分布，但没有任何单一结构在所有工作负载上表现最佳。腾讯发布的 AngelSpec 从训练、架构、推理三个层面解决了这个异构性问题：**MTP（多 token 预测）为高熵对话提供轻量稳定提案；DFly（块扩散）为代码/数学场景扩展候选序列；D-cut 自适应验证预算在运行时动态分配批次级资源。** 在 Hy3-A21B 上，DFly 平均接受长度提高约 30%，在所有测试并发下实现最高平均吞吐；D-cut 进一步将验证受限场景的吞吐提升至自回归基线的 1.44 倍。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "共享参数多深度 MTP：轻量级自回归前端",
            "paras": [
                "原始 Hy3 模型只使用单个 MTP 层，没有循环自条件展开。自回归解码时，第一个预测位置基于真实前文，但后续位置收敛于近似。AngelSpec 使用共享参数多深度 MTP：所有 D 个预测层共享参数，但每个深度 k 由其独立的移位未来 token 目标监督。训练时块自回归展开 D 步。预测形成短的线性草稿块，目标模型在一次前向中完成验证。",
                "关键改进是 Training-Time Test (TTT)：在目标模型自身生成的 rollout 混合上继续训练 MTP 草稿器，将平均接受率从 52.8% 提升至 66.4%（+13.6 百分点），MAL 从 2.58 提升至 2.99。深度 D=3 时在 Hy3 上实现 1.73× 速度提升。",
            ],
        },
        {
            "type": "h2",
            "title": "DFly：规模化且自回归感知的并行草稿架构",
            "paras": [
                "并行草稿器在一次骨干前向中生成所有候选 token，草稿延迟几乎与块长度无关。DFlash 为代表的方案将多个目标层的隐藏状态投影到共享上下文再注入每层。但共享目标上下文限制了层特化，且预测位置缺乏显式自回归依赖。",
                "**DFly 从三个方面改进 DFlash：** 第一，混合目标条件化骨架，结合 DFlash 的显式投影与 DFlare 的层特定目标视图，使每层既接收共享上下文又关注匹配深度的目标层特征。第二，两个自回归头——低秩马尔可夫转移头和隐藏校正头——在并行骨干后引入前驱信息。第三，接受感知目标，将分布匹配与各位置对期望接受长度的贡献对齐。",
                "**结果：** Qwen3-8B 上平均 MAL 达 5.41（vs DSpark 5.32、DFlash 4.57、MTP 3.24）。Hy3-A21B 上 MAL 平均 5.32，相比 MTP 提升 59.7%、相比 DFlash 提升 29.8%。",
            ],
        },
        {
            "type": "h2",
            "title": "D-cut：自适应验证预算分配",
            "paras": [
                "草稿质量的提升和实际吞吐之间存在张力：更长的草稿可以增加提交 token 数，但目标模型必须评估每一个保留位置，可能拖慢每步时间。D-cut 将目标模型验证视为共享批次级资源：先估算每个请求不同保留深度的预期收益，再结合预分析的运行时间成本选择操作点。",
                "D-cut 使用草稿器的 token 级置信度估计前缀存活概率：位置 k 有用当且仅当所有前置位置存活。然后通过组合收益与运行时成本选择预算比 ρ（共享验证位置数 / 总请求数）。核心实现保证 D-cut 不亏钱——当修剪不利时保留完整块。",
                "**生产环境结果：** 在 Hunyuan 实际流量 (Hy3-295B-A21B, 8×H20, TP=8) 上，DFly 在 48 并发后饱和（860 tok/s），而 D-cut 继续将额外并发转化为吞吐，在 56 并发达 981 tok/s，64 并发达 976 tok/s。**相同 per-user 延迟下，吞吐提升 14%。** 更关键的是 D-cut 保持了接受长度（2.50 vs 2.46，仅减少 1.5%），说明丢弃的主要是目标模型本身会拒绝的低质量位置。",
            ],
        },
        {
            "type": "h2",
            "title": "AngelSpec 训练框架",
            "paras": [
                "所有草稿器基于 TorchSpec 训练，解耦了推理引擎与训练：目标模型在 vLLM 中运行，隐藏状态通过 Mooncake-backed RDMA 存储流式传输到分布式训练 worker。训练支持 MTP（含 TTT 拟合）和 DFlash 家族：每层通过可学习的融合权重组合目标层特征，融合权重初始化为距离先验（匹配深度）。自回归头通过相同组件接口附加。",
                "框架包含评估服务器，定期针对最新 checkpoint 运行真正的投机解码并报告部署侧指标（MAL、逐位置接受率）。提供两种部署模式：轻量模式（每次评估启动新 vLLM 实例，适合单节点）和持久模式（目标模型常驻，每次只重载草稿权重）。",
            ],
        },
    ],
    "conclusion": [
        "AngelSpec 的核心贡献不在于某一个单独的数字，而在于**正视了『一个方案通吃所有』的不可能性**。MTP 适合高熵对话，DFly 适合结构化场景，D-cut 在高并发下提供额外收益——三者在 AngelSpec 框架内形成完备的推理加速方案栈。",
        "**技术层面最具价值的贡献是 D-cut 中『验证作为批次级共享资源』的视角转换。** 传统的自适应方法在请求局部做决策（保持/丢弃），忽略了批次竞争对共享目标模型容量的影响。D-cut 的全局预算视角显著增加了有用并发范围，这对大规模生产部署是实实在在的收益。",
        "**独立观点：** D-cut 的置信度前缀乘积估计（∏c_i 作为位置存活概率）是一个不错的启发式，但真正的上限在于顺序验证的本质——你必须先验证位置 1 才能知道位置 2 是否有用。如果未来有跳步验证或近似验证机制，D-cut 的框架可以自然扩展。此外，框架层面将推理引擎与训练解耦（Mooncake RDMA 流式隐藏状态）的建设性价值可能大于任何单一算法改进。",
    ],
    "reference_url": "https://arxiv.org/abs/2607.25852",
    "figs": [
        {"src": "fig01.png", "caption": "AngelSpec 概览：三个轨道覆盖不同工作负载的投机解码需求。"},
        {"src": "x1.png", "caption": "Figure 1: 共享参数多深度 MTP 训练与 TTT。"},
        {"src": "x3.png", "caption": "Table 3: DFly 在 Qwen3-8B 和 Hy3-A21B 上的主结果，数学/代码/闲聊平均 MAL。"},
        {"src": "x2.png", "caption": "Figure 2: DFly 混合目标条件化骨架架构。"},
        {"src": "fig02.png", "caption": "Figure 4 (a-b): Hy3-DFlash/DFly 延迟分解。"},
        {"src": "x4.png", "caption": "Figure 6: AngelSpec 整体概览。"},
    ],
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入: {len(DATA['sections'])} sections, {sum(len(s.get('paras',[])) for s in DATA['sections'])} paras")