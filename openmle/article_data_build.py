#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

DATA = {
    "title": "OpenMLE：杨军林创业首作震撼开源——训练可自我改进的机器学习 Agent，MLE-Bench 超越 GPT-5.5+Codex",
    "summary": [
        {"key": "核心系统", "body": "OpenMLE 是开源全栈 RSI 系统：5758个可执行环境 Gym + 执行反馈训练 ERL + 经验引导长程搜索 Evo，闭环 AI 训练 AI"},
        {"key": "元进化 Agent", "body": "用 OpenMLE 训练出 Frontis-MA1 35B（元进化 Agent gen1），Draft/Improve/Debug/Crossover 四原子算子既是训练对象也是搜索引擎"},
        {"key": "关键结果", "body": "MLE-Bench Lite Medal Average 39.39%→71.21% 超越 GPT-5.5+Codex 3.03pp；NatureBench Lite 匹配 GPT-5.4，证明能力跨域迁移"},
    ],
    "lead": [
        "AI 能力的增长不再只由人类工程师推动——AI 系统正越来越会写代码、跑实验、搜设计、帮助构建下一代 AI，这被称为 **AI for AI (AI4AI)**，其终极目标是递归自我改进（RSI）：每个改进后的系统进一步提升生产其继任者的过程。**杨军林新公司推出的 OpenMLE，把机器学习工程（MLE）作为这一方向的第一个可执行测试床，打通了「可验证环境 → 执行反馈训练 → 推理时进化搜索」的完整闭环。** 在 MLE-Bench Lite 上，用 OpenMLE 训练出的 Frontis-MA1 35B 将 Medal Average 从 39.39% 提升到 71.21%，超越 GPT-5.5 + Codex，并让 AI 在真实科研任务 NatureBench 上迁移能力。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "为什么 MLE 是 AI4AI 的最佳测试床",
            "paras": [
                "机器学习工程（MLE）是 AI4AI 最直接的落地形式：Agent 必须为真实世界任务构建机器学习方案，并通过执行反馈迭代改进。一个轨迹往往从可运行的 pipeline 开始，经过反复实验推进到与人类或前沿模型方案竞争的解。**每次迭代都消耗时间与算力，结果可能几十分钟或几小时后才到来——这让 MLE 成为研究 Agent 如何在延迟、噪音、异构反馈下改进 AI 系统的具体而严苛的测试床。**",
                "现有工作沿三条互补但重叠的线推进：一是基于结构化或进化搜索的推理时 harness；二是构建可执行任务与环境；三是用执行反馈对 MLE Agent 进行后训练。**但没有一个公开系统真正打通全部三环**——直到 OpenMLE 将其统一在「环境构建 + Agent 后训练 + 进化 harness」一个验证过的工作流中。",
                "OpenMLE 训练并部署的模型被称为 **元进化 Agent（meta-evolution agent）**：被训练的模型同时是 OpenMLE 栈的产物和引擎，进化 harness 用它做搜索的变化引擎，形成「改进者本身被训练」的元进化闭环。核心模型 Frontis-MA1 35B（Meta-evolution Agent，第1代）在此命名。",
            ],
            "fig_after": {
                "1": [{
                    "src": "fig22.png",
                    "caption": "定位：左图在 AI4AI 框架内，MLE 是任务域，OpenMLE 栈训练并部署 Frontis-MA1，其既是产品也是引擎，仅在第三方基准上评测；右图是从进化到递归自我改进的机制阶梯，元进化环（橙色）把本工作放在「改进者本身被训练」这一层。"
                }]
            }
        },
        {
            "type": "h2",
            "title": "OpenMLE-Gym：5758 个可执行环境",
            "paras": [
                "AI 训练 AI 需要 Agent 通过可执行实验构建和改进 AI 系统，因此需要大规模、多样、高质量、覆盖数据检查/准备/建模/预测/评估的完整任务包。**但现有基准在开放性、可执行多样性或覆盖度上受限，异构文件与评估协议又难以规模化。** 静态任务集不足以支撑后训练或搜索——Agent 生成的程序必须在受控资源下执行，产生可靠、信息丰富的反馈。",
                "每个 OpenMLE-Gym 任务由五要素定义的环境实例构成：**状态**（任务说明/公共数据/隐藏评估器/资源预算/当前工作区）、**动作**（Agent 提交的 MLE 程序及执行需求）、**转移**（沙箱执行：物化工作区、跑程序、产出有效提交时调用评估器）、**观测**（执行状态/分数/日志/错误类型/产物/运行时元数据）、**奖励**（评估器返回的可验证任务分数）。",
                "环境通过**三条来源路径**构建，占据质量-规模曲线上互补的位置：**人工精选锚点**（从现有论文和基准手工挑选，置信度最高但规模受限）、**Kaggle 数据集**（大幅拓宽覆盖，用 MLE-Smith 流程加工并做包级质控）、**Kaggle 竞赛**（人类撰写的任务说明/评估指标/提交流程提供更强锚定，用 Meta Kaggle 目录规模化收集）。所有来源统一成共享的可执行任务包：原始资产放 raw/、Agent 可见描述/训练数据/测试输入放 data/public/、隐藏答案隔离放 data/private/、任务专用 metric.py 验证预测文件并返回标量反馈。",
                "任务经过**五维度语义质量过滤**（任务有效性/数据充分性/原始数据使用/任务复杂度/数据质量）筛选退化样本、数据泄漏、标注错误，只保留严格的 recommended 判定。**最终 5758 个质量门控任务**：156 人工精选锚点 + 3362 Kaggle 数据集 + 2240 Kaggle 竞赛，覆盖表格/文本/时间序列/图像等多种模态，11% 多模态，分类和回归占 87%。",
                "沙箱执行后端：集中调度器接收 API 请求、记录任务、追踪 worker 可用性、按资源需求分发到 CPU/GPU Docker worker。每个 worker 物化隔离任务工作区、挂载任务数据和评估器、执行候选程序、把日志/提交/产物写回共享存储。**返回六种反馈模式**：成功完成/运行时错误/缺代码/缺提交/评分失败/超时，让 Agent 能区分「执行无效」和「任务表现弱」。",
            ],
            "fig_after": {
                "1": [{
                    "src": "fig27.png",
                    "caption": "OpenMLE-Gym 任务构建与可执行格式：左为来源层级，中为从 Meta Kaggle 目录到质量门控包的过滤，右为公共任务输入、私有答案与可执行工具。"
                }]
            }
        },
        {
            "type": "h2",
            "title": "OpenMLE-ERL：执行反馈强化可复用进化算子",
            "paras": [
                "进化式 AutoResearch 用有限搜索预算内找到的最佳可执行程序作为评判标准。控制器可能调用 Draft/Debug/Improve/Crossover 成百上千次，所以模型必须学会的不仅是单次生成方案，而是随搜索展开**反复修复、精炼、重组程序**。后训练因此要同时扩大可达到的强程序集合，并改进推理 harness 组合的各变换算子。",
                "**核心设计原则是把模型学到的局部能力与推理时的搜索算法分离**——不训练完整轨迹，而是训练一组可复用的程序变换算子（Draft/Improve/Debug/Crossover）。这避免稀疏的控制器监督，让同一组算子能在共享沙箱协议下被不同进化搜索流程组合。",
                "**执行锚定的监督微调（SFT）**按任务逐题执行采样程序，保留有效且有分数样本，直到达标额度或用尽执行预算——容易任务提前结束，把更多尝试配给稀少成功任务，把验证算力导向仍能挖出监督的地方。**双路径收集**：并行路径独立采样执行完整 Draft 方案（17245 全响应样例），进化路径对已执行程序应用 Improve/Debug/Crossover（9014 轨迹步样例），合计 26259 例 SFT 语料。",
                "**执行锚定的强化学习（RL）**要解决异构分数可比性问题：不同任务可能优化准确率或 log loss，即使对齐方向原始分数范围也不可比。OpenMLE 先用固定任务边界定义有界基奖励，再根据每任务历史 on-policy 分数前沿推导**自适应上界**重映射，保留当前候选所在区域的分辨率。随后用**熵优势**浓聚上尾学习信号——让接近顶部的候选获得不成比例的正反馈，而非等量强化所有不失败的方案。",
                "**异步 rollout 移除掉队者**：MLE RL 主导时延来自执行候选程序而非 token 粒度验证，运行时跨任务差异大。同步批次中完成的组要等最慢的沙箱任务返回。OpenMLE 让生成-执行组独立启动，训练器从队列消费每个完成的组，解耦策略更新与名义批次中最长任务。",
                "**选择有信息量的状态训练算子**：RL 不只选任务和算子，还要选算子作用其上的程序状态。OpenMLE 用三项目适应度采样父程序——父程序奖励强度（利用）、子奖励方差（定位训练信号未消解区域）、访问冷却（防止单一最优垄断预算）。",
            ],
            "fig_after": {
                "1": [{
                    "src": "fig24.png",
                    "caption": "OpenMLE-Gym 执行后端架构：Agent 请求派发到 CPU/GPU Docker worker，worker 执行候选程序、挂载任务数据与评估器、把日志/产物写回共享存储。"
                }],
                "3": [{
                    "src": "fig16.png",
                    "caption": "从已执行 rollout 中学习：并行路径保留达标 Draft 方案；进化路径在反复 Debug 后出现有效端点时回溯非 debug 算子并用 LLM 保留修复轨迹中的有用步骤，两路径构成 26259 例 SFT 语料。RL 用父奖励、子奖励方差、访问冷却选父程序，top-1/top-K 自适应边界并配熵优势放大上尾信号。"
                }],
                "5": [{
                    "src": "fig23.png",
                    "caption": "Frontis-MA1 35B 的 RL 训练曲线。"
                }]
            }
        },
        {
            "type": "h2",
            "title": "OpenMLE-Evo：经验引导的长程搜索",
            "paras": [
                "测试时扩展（test-time scaling）在 AI4AI 中变成测试时学习——搜索必须把执行结果转化为可复用证据，改变它接下来探索什么。**不是生成更多候选，而是提出、执行、从经验学习、适应未来扩展的长程闭环。** 经验驱动的进化依赖两个耦合的科学问题：该扩展哪个节点（超越贪心分数最大化）？记忆如何构建，让算子收到可行动证据而非不断膨胀的轨迹？",
                "**结构化经验积累**：每个候选经沙箱评估后生成节点级「经验卡」，确定性提取来源/性能/执行结果/资源占用；所有节点卡片聚合成任务级「经验板」，维护方法族统计、族内最优候选、欠探索方向、重复失败、分数趋势、父图。卡片+板防止节点级信号在扩展搜索空间里丢失。",
                "**经验引导的父选择**：原 AIRA-Evo 几乎全靠归一化 fitness 派生父采样概率，倾向集中扩展已强节点。OpenMLE-Evo 把经验卡的确定性元数据转为三因子：归一化验证分数 s̄、相对最强父的正向改进 Δ̃、方法族新颖性 ν，组合成经验引导效用并按 softmax 采样下一父节点。**同时保留高质量解、分配预算给有实质进步或引入欠探索方向的候选。**",
                "**操作触发的记忆合成**：原 AIRA-Evo 默认对每个评估节点急切调用 LLM 总结历史，浪费在从不被选中的节点上。OpenMLE-Evo 分离确定性存储与 LLM 合成——沙箱评估后保留经验卡和板，延迟丰富自然语言记忆直到 Improve/Crossover/Debug 调用选定了相关节点，只对被选父节点及其检索的祖先/兄弟/错误尝试调用记忆模型并缓存。",
                "**算子条件上下文构建**：选定父节点后构建小而算子特定的上下文，而非追加完整自由格式历史。Improve 拼接节点确定性经验记录、近期祖先垂直轨迹、共享至少一个父节点的兄弟水平集（按三因子效用排序只留最有信息量的）；Crossover 对双父分别应用并加方法族互补线索；Debug 检索同错误签名的先前尝试。上下文还指定剩余搜索预算/步数/每次执行上限，让决策在实际计算约束下可行。",
            ],
            "fig_after": {
                "1": [{
                    "src": "fig25.png",
                    "caption": "搜索效率与上下文长度对比（原 AIRA-Evo 灰 vs OpenMLE-Evo 青，66 匹配任务-运行）：Panel A 资源指标归一化到原 AIRA-Evo=100，Panel B 验证轨迹生产力（new-best 更新/百万 token），Panel C 串行化用户提示长度对数轴。"
                }]
            }
        },
        {
            "type": "h2",
            "title": "实验结果：训练与搜索增益叠加",
            "paras": [
                "在官方 22 任务 MLE-Bench Lite 上，每任务固定 12 GPU-小时（单张 RTX 4090，12GB）预算——远小于 MLE-Bench 绝大多数报告的沙箱算力。报告三个聚合指标：**有效提交率**（22 任务中出有效提交的比例）、**奖牌平均**（获任何 Kaggle 奖牌的任务比例）、**人类排名**（超越的人类榜参与者比例）。",
                "**训练与搜索的增益叠加**：相同 OpenMLE-Evo harness 下，执行锚定后训练把 Frontis-MA1 35B 相对其 Qwen3.6 骨架的 Medal Average 提升 21.22 个百分点；伙伴模型 30B 在 Qwen3 上复现 18.18 个百分点。叠加 OpenMLE-Evo-Max（蒸馏跨任务先验 + 异步多 GPU 并行搜索）进一步达到 71.21%，**超越 GPT-5.5 + Codex 3.03 个百分点**，证明训练与搜索提供互补提升。",
                "**Harness 层面**：固定模型下对比，OpenMLE-Evo 一致把相同模型转成比 Claude Code / Codex 等通用编码 Agent harness 更强的 MLE 系统。对 Frontis-MA1 35B，相对原 AIRA-Evo，Medal Average 从 53.03% 提升。",
                "**长程自我改进**：OpenMLE-Evo 持续改进远超第一个可执行解——后段 Improve 和 Crossover 操作把积累经验变成决定性性能增益，说明经验引导长程搜索把额外测试算力转化为持续进步而非冗余采样。leaf 分类任务上后段操作贡献验证增益的 85%，最终验证 Human Rank 0.7713、保留集 0.9455 获 Bronze；mlsp-2013 音频上 Improve+Crossover 占验证改进的 91.9%，验证 0.7284、保留集 0.8889 获 Silver。",
                "**方案上限**：训练和 Evo-Max 不仅增加奖牌覆盖率，更把成功方案推向 Gold——35B 模型相对于外部系统超越 Claude Opus 4.8 + Claude Code、Gemini 3.5 Flash + Gemini CLI，并匹配 Kimi K3 的 Gold 率。",
            ],
            "fig_after": {
                "1": [{
                    "src": "fig19.png",
                    "caption": "共同 OpenMLE-Evo harness 下的模型性能（MLE-Bench Lite）：实柱为标准 OpenMLE-Evo 结果，斜纹帽显示 Frontis-MA1 35B、GLM-5.2、MiniMax M3 加 Evo-Max 的额外增益。"
                }],
                "3": [{
                    "src": "fig26.png",
                    "caption": "Gold/Silver/Bronze 分解对比与代表通用 Agent harness：柱长报告每奖牌层评估结果占比，标签为最终 Medal Rate。"
                }]
            }
        },
        {
            "type": "h2",
            "title": "跨模态元能力与 NatureBench 迁移",
            "paras": [
                "把 22 个 MLE-Bench Lite 任务分成图像/文本/表格/音频/多模态五组后，Frontis-MA1 35B 相对 Qwen3.6 在五组全部提升平均 Human Rank，且从不降低组级 Medal Rate；14 个新增奖牌分布到每组的每个模态（+2/+4/+1/+4/+3），证明聚合增益不靠单一模态解释。",
                "**NatureBench 验证域外迁移**：NatureBench（90 个容器化任务，来自六个科学领域的 Nature 期刊论文）隐藏测试真值与论文方法，用方向归一化相对差距比较异构科学指标。固定 NatureBench 适配器，Frontis-MA1 35B 相对 Qwen3.6 在 All S（Surpass-SOTA）提高 10 个百分点（3/10 vs 2/10）、All M（Match-SOTA）提高 20 点（7/10 vs 5/10）；固定基模型，OpenMLE-Evo 适配器相对原 AIRA-Evo 在 All S 提高 10 点（2/10 vs 1/10）、All M 提高 30 点（5/10 vs 2/10）。**组合系统匹配 GPT-5.4、GLM-5.1、MiniMax-M3 的 3/10 All S 和 7/10 All M，超越 DeepSeek-V4-Pro、Claude Opus 4.6**。",
            ],
            "fig_after": {
                "1": [{
                    "src": "fig20.png",
                    "caption": "MLE-Bench Lite 子集按模态分层结果：Base 为 Qwen3.6-35B-A3B，Frontis 为 Frontis-MA1 35B，均用 OpenMLE-Evo 评估。宽轮廓柱为 Medal Rate，窄填充柱为平均 Human Rank。"
                }]
            }
        },
    ],
    "conclusion": [
        "OpenMLE 的价值不在某个单一算法，而在把「AI 训练 AI」从口号变成可复现的工程闭环——可验证环境（Gym）、执行反馈训练（ERL）、经验引导搜索（Evo）三者不是孤立的组件，而是通过 Draft/Improve/Debug/Crossover 四个算子被同一套接口串起来，让训练阶段监督的变换和搜索阶段组合的变换是同一件事。这种「被训练的模型就是进化引擎」的设计，正是走向递归自我改进的关键一步。",
        "训练与搜索在 12 GPU-小时的小算力预算下仍分别贡献 20+ 个百分点的增益并叠加到 71%，说明执行锚定后训练（而非单纯扩大模型或推理算力）才是 MLE Agent 能力跃迁的主因；跨模态的 Medal 分布与 NatureBench 的迁移证据则说明学到的不是某个数据集上的过拟合技巧，而是可泛化的「构建并改进 ML 方案」的元能力。开源训练/评测代码与沙箱，也给了整个社区一个研究元进化的公共底座。",
    ],
    "reference_url": "https://arxiv.org/abs/2607.28568",
    "title": "OpenMLE：杨军林创业首作震撼开源——训练可自我改进的机器学习 Agent，MLE-Bench 超越 GPT-5.5+Codex",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
