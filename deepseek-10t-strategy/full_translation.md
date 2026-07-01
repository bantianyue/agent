# DeepSeek 的 10 万亿美元大棋局

作者：@bookwormengr (GDP)
发布时间：2026年5月22日

## 开篇

DeepSeek 如何赚钱，且赚大钱？他们没有像 GLM、MoonShot、MiniMax 那样推出有竞争力的 coding plan。他们没有多模态模型、语音模型、视频模型。至今他们没有构建 harness（最近才开始招聘 harness 方向的人）。DeepSeek 还承诺长期开源，乐于分享秘方。这是疯狂吗？是纯粹烧钱吗？准备投 100 亿美元的投资人是在往水里扔钱吗？

不——恰恰相反。

本文梳理 DeepSeek 至今所做的一切，提出他们似乎正在遵循的宏大战略。DeepSeek CEO 梁文锋的眼光放在更大的目标上——他们可能达到 1 万亿美元估值，同时帮助创造一个 10 万亿美元的产业。

## DeepSeek 的英雄之旅

DeepSeek 一直逆风而行，不追求渐进式改进和短期应用变现。他们在别人构建密集模型时走 MoE 路线；从第一性原理出发发明 GRPO 替代 PPO；发现 RLVR 是提升推理能力的关键策略；通过 MTP 实现投机解码；优化 Zero Bubble 管线提高 GPU 利用率；发布 Expert Load Balancer 让 MoE 部署更经济；发明 MLA/DSA/CSA/HCA 减少 KV Cache 需求；发明 Engram 用记忆换计算；发明 mHC 实现大模型稳定训练。

在英雄之旅的故事结构中，英雄从不事先决定旅程的方向——一路学习，发现使命，克服一切困难完成它。DeepSeek 也因此赢得了全球追随者与尊重。

DeepSeek 在这条路上的终极目的地已清晰：不是卖 coding plan，而是赋能一个 10 万亿美元的中国 AI 硬件生态，并为自己实现 1 万亿美元估值。在此过程中，他们也将帮助西方硬件生态的新入局者。

## KV Cache 计算

用 DeepSeek V4 Pro 的 KV Cache 节省与 GLM、Qwen 对比。1M 上下文：

- DeepSeek V4：仅需 5.48GB HBM
- GLM5：需要 60GB HBM
- Qwen3-235B-A22B：需要 89GB HBM

注意：DeepSeek 是 1.6T 参数模型，GLM5 约 700B 参数（已使用 MLA 和 DSA），Qwen3 约 235B 参数（使用 GQA）。

DeepSeek 在缓解内存压力方面做出了基础性贡献。如果这项创新被广泛采用，长时程 Agent 将变得非常经济，解锁下一波应用场景。

## 疯狂背后的方法

极小的 KV Cache（不牺牲质量）是 DeepSeek 能以极低价格提供长时缓存的原因——不到 Sonnet 4.6 cache hit 价格的 3%，且保持数小时。长时程任务的少量缓存可以卸载到 SSD 并成本高效地重新加载，降低了对中国 AI 硬件产业最紧缺、最难制造的 HBM 的需求。

## KV Cache 压缩的直接受益者

大规模供应 SSD 的是谁？YMTC（长江存储）正在崛起为 3D NAND 巨头。NAND 让 DeepSeek 避免重新计算 KV，而 DeepSeek 又为 NAND 和 SSD 创造了巨大市场——不仅是 YMTC 的，还包括所有人的。

## 不止是 NAND 和 SSD

LPDDR 内存有可能成为存放权重的地方，按需流式传输到 HBM，减少对 HBM 的需求压力。SGLang 团队发表了相关研究。DeepSeek 没有特别为此做什么——但他们的 MoE 架构（大量专家 + 4-bit 权重）让这个方案易于实现。

中国谁做 LPDDR？CXMT（长鑫存储）。速度仅落后 0.5 代，密度落后 1 代，差距不大。

## 善用记忆也能减轻 GPU/ASIC 压力

LPDDR 可以存放大量的 Engram。DeepSeek 的 Engram 论文中，将经典 N-gram 嵌入现代化为 O(1) 哈希查找，创建了称为条件记忆的互补稀疏轴。这是一种经典的内存-计算置换——每次查找的代价（LPDDR 查找 vs Transformer 层前向传播）使得大尺度下置换极为有利。

中国的 GPU 和 ASIC 因缺乏 EUV 光刻机，晶体管密度永远落后西方，封装技术也有差距。因此这种置换非常值得，尤其是有充足 NAND 和 LPDDR 可用的情况下。

## DeepSeek 的长期棋局

从所有这些创新来看，DeepSeek 的游戏不是几亿美元的短期利润——他们在打一场耐心的 10 万亿美元棋局，以赋能替代性硬件生态。

七大创新：

1. **MoE 和 MLA（DeepSeek V2，2024年5月）**：MoE 用少 40-50% 的计算训练智能模型。MLA 将 KV Cache 减少 90%，使 SSD 卸载高效。

2. **DSA（DeepSeek V3.2 Exp）**：减少长上下文场景的计算，缓解 HBM 带宽压力。处理时间随上下文增长保持平稳。

3. **mHC（2025年12月）**：宏观架构创新，用多平行信息高速公路替代标准残差连接，通过双随机约束保证深度信号稳定。27B 参数下：BBH +7.2 分，DROP +3.2，GSM8K +2.8，MMLU +1.4。训练开销仅 6.7%。

4. **CSA、HSA（DeepSeek V4，2026年4月）**：KV 需求再降 90%，同时大幅减少 FLOPs。

5. **Engram（2026年Q1）**：用 LPDDR 记忆换计算。

6. **计算通信重叠**：Dual Path 等创新。DeepSeek 甚至为硬件厂商提供 ASIC 设计建议。

7. **TileLang**：一次编写 kernel，多平台运行，帮助中国硬件厂商间接突破 CUDA 护城河。

## 大规模 RL 和 RSI

更多硬件选项 + 计算需求降低 = DeepSeek 可以承担更宏大的训练项目。RL 后训练需要生成大量轨迹（数万亿 tokens）。训练 1M 上下文的模型也需要同样长的轨迹。更多硬件还将实现自动化研究（RSI），即 AI 自行设计和执行实验。

## DeepSeek 今天做的，是行业明天做的

DeepSeek 的 MoE、MLA、DSA 已被全球和中国 AI 实验室采纳。ZAI（GLM 系列）使用 MLA 和 DSA。Kimi（Moonshot）已采用 MLA。作为回馈，DeepSeek 使用 Moonshot 首次大规模使用的 Muon 优化器。

注：MoE 由 Google 在 2017 年发明（Noam Shazeer），DeepSeek 以大规模应用和自创技巧著称。Muon 优化器由 Keller Jordan 在 2024 年末创建，Moonshot 团队首次大规模使用。

## 如何赚钱？

OpenAI 以低价获得 AMD 和 Cerebras 股票的认股权证，基于消费里程碑兑现。AMD 公告称："AMD 向 OpenAI 发行了最多 1.6 亿股 AMD 普通股的认股权证，根据特定里程碑完成情况分期兑现。"

预计 DeepSeek 将与多家中国存储、ASIC、CPU 和网络设备厂商签署类似协议，紧密合作使他们的硬件栈适用于领先 AI 工作负载。

西方 AI 相关股票的合计估值远超 10 万亿美元。这种通过股权奖励的合作方式，让 DeepSeek 能帮助在中国建立同样庞大的产业，同时为自己攫取 1 万亿美元的份额。
