#!/usr/bin/env python3
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "KernelZero:双模型协同进化，7B 写 GPU 内核超过 Claude-4.5",
    "reference_url": "https://arxiv.org/html/2609.33074v1",
    "summary": [
        {"key": "核心观点", "body": "Proposer 出题、Coder 做题，两个模型交替优化形成自动课程，持续产出与 Coder 当前能力对齐的训练数据。"},
        {"key": "关键数据", "body": "7B 的 KernelZero 在 CUDA 上超过 Claude-4.5-Sonnet，Triton 上超过 DeepSeek-V4-Pro。"},
        {"key": "方法创新", "body": "CA-GRPO 先保正确率再优化性能，Keck 执行验证服务器给每个候选内核真实跑分。"},
    ],
    "lead": [
        "用大模型写 GPU 内核有两个老大难：**高质量训练数据稀缺**，而且数据还得跟模型当前能力对上号；**正确性和性能天然打架**，优化速度容易把正确性搞崩。",
        "KernelZero 的解法是养两个模型：**Proposer 负责出题**，生成 Torch 算子组合；**Coder 负责做题**，把题目翻译成 CUDA 或 Triton 内核。两者交替训练，互相抬轿子。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "出题人与做题人：两个模型一起进化",
            "paras": [
                "框架很直白：Proposer 输入一组 Torch API，生成可运行的 Torch 模块；Coder 把模块翻译成底层内核。**两个模型各有各的奖励函数**，r_P 奖励出题质量，r_C 奖励做题质量，交替用 GRPO 优化，另一个固定不动。",
                "关键在“出题”的方向：Proposer 不随机出题，而是**瞄着 Coder 当前的短板出**。Coder 哪类算子写不好，Proposer 就多生成这类模块，形成自动课程。这种 targeted 的训练方式比大水漫灌高效得多。",
                "交替优化带来稳定协同进化：Proposer 把题目分布推向 Coder 的能力边界，Coder 在新题目上练出更强的内核生成能力，反过来又逼 Proposer 出更难的题。**循环一旦转起来，能力就持续往上走**。",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig01.png", "caption": "图1：Proposer 与 Coder 分工。Proposer 生成 Torch 模块（出题），Coder 生成 GPU 内核（做题），分别用难度奖励 R_P 与加速比奖励 R_C 优化。"},
                ],
                "2": [
                    {"src": "fig02.png", "caption": "图2：KernelZero 完整框架。左侧 RL 训练循环交替优化两个模型；中间模块提议经 API 组合与合法性校验；右侧从 API 文档与真实模块中采样，保证题目真实多样。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "Proposer：专挑 Coder 的软肋出题",
            "paras": [
                "好题目有三个标准：**真实、多样、卡在能力边界上**。为保真实，Proposer 先从真实 Torch 模块里统计 API 共现分布，再按这个分布采样 API 组合，避免编出没人写的怪异组合。",
                "采样之后还有两道关：**合法性校验**保证模块能跑起来；**前沿奖励**鼓励生成 Coder 当前做不好的题目。难度不是拍脑袋定的，而是用 Coder 的实际表现标出来的。",
                "这套机制解决的是数据与能力错位：静态数据集要么太简单（学不到东西），要么太难（直接训崩）。**动态出题让每批数据都落在“跳一跳能够到”的区间**，训练效率自然高。",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig06.png", "caption": "图6：Torch API 共现统计与采样。左下热力图展示真实模块中 API 的共现频率，采样偏向真实高频组合；Coder 做不出的模块会被回收为新的难题。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "Coder：先做对，再做快",
            "paras": [
                "Coder 的目标是把 Torch 模块翻译成又快又对的内核。**正确性和性能的矛盾用 CA-GRPO 解**：正确率没达标之前，奖励只看对不对；正确率稳定之后，才开始奖励加速比。两步走，避免为了快把对搞丢。",
                "强化学习之前先做冷启动蒸馏，把四条编译器级别的优化原则灌进去：**分块**（tiling）把数据切到片上内存、**融合**、**向量化访存**、**规约优化**。这些是专家写高性能内核的通用套路，先内化再强化。",
                "奖励信号来自真实执行，不是模型自评。每个候选内核都要编译、运行、测速，**跑分是唯一的裁判**，杜绝纸上谈兵的“看起来快”。",
            ],
            "fig_after": {},
        },
        {
            "type": "h2",
            "title": "Keck：给每个内核真实跑分",
            "paras": [
                "Keck 是配套的执行验证服务器：左边收进来一批 Torch+CUDA 样本，中间调度 CPU 编译、GPU 运行，右边输出三样东西：**评估信息、性能剖析、奖励分数**。",
                "流程是四连问：**能编译吗？能跑吗？结果对吗？加速比多少？** 任何一关不过，样本就带着失败信息回去。这种细粒度反馈让 Coder 知道到底错在哪，而不是只拿到一个 0 分。",
                "规模化是关键：训练中要评估海量候选内核，Keck 把“一次采样多 GPU 并行”做成标准动作，**每个 GPU 跑一个样本**，吞吐量撑得起 RL 训练的消耗。",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig05.png", "caption": "图5：Keck 执行验证服务器。样本经 CPU 编译、GPU 运行四道检查（编译/运行/正确/加速比），输出评估信息、性能剖析与奖励。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "训练动态：两个模型互相抬轿子",
            "paras": [
                "训练曲线印证了协同进化的设想：Proposer 训练过程中，**题目有效性、Coder 正确率、奖励三条线一起往上走**，说明出的题越来越有质量，Coder 也越来越接得住。",
                "Coder 侧分 Level 1 和 Level 2 看，pass@1 稳步爬升，KernelZero 线（深色）始终压着 CUDA、Triton、Frozen Proposer 几条基线。**Proposer 持续更新比冻结版本强**，证明动态出题不是摆设。",
                "有意思的是 Fast_1@1 那条线：Coder 越到后期，生成的内核不仅对得多，而且快的比例也在涨。**先保正确再追性能的 CA-GRPO 策略在曲线上看得很清楚**。",
            ],
            "fig_after": {
                "2": [
                    {"src": "fig03.png", "caption": "图3：KernelZero 训练动态。左：Proposer 训练中题目有效性、Coder 正确率与奖励同步上升；中右：Coder 在 Level 1/2 的 pass@1 与 Fast_1@1 持续领先基线。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "结果：7B 参数，超过大模型",
            "paras": [
                "KernelBench 上的数字很硬：CUDA Level 1/2 的 pass@1 为 **75.8%/69.6%**，pass@10 达到 **100%/97%**；Triton 为 **77.2%/72.5%**，pass@10 达 **99%/98%**。7B 参数的模型，**CUDA 超过 Claude-4.5-Sonnet，Triton 超过 DeepSeek-V4-Pro**。",
                "加速比上 Triton 优势明显：Level 1 的 fast_1@1 达 43.9，CUDA 只有 17.6。原因在于 Triton 的 tile 级抽象让分块融合更容易表达，**生成的 CUDA 内核不调用外部高性能库**，全靠自己写，难度天然更高。",
                "跟专用基线比也不虚：Level 1 fast_2@1 为 7.2，超过 cudaLLM-8B；Level 2 在更严格的 fast_2 标准下同样领先。**正确率高、速度快、参数小**，三者兼得是这套方法最值钱的地方。",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig04.png", "caption": "图4：KernelBench 上的 Fast@k 结果。KernelZero（最右）在四个组合（Level 1/2 × Triton/CUDA）上全面领先，Triton 的加速比优势尤为明显。"},
                ],
            },
        },
    ],
    "conclusion": [
        "KernelZero 证明了一件事：**写内核这种硬任务，数据策略比堆参数更重要**。动态出题让 7B 模型吃到了“定制口粮”，效果超过大几十倍参数的通用大模型。",
        "CA-GRPO 的“先对后快”也值得借鉴：**把正确率做成门槛而不是加权项**，优化目标就不会为了速度牺牲正确性。这种分阶段优化的思路，放到其他代码生成任务上同样成立。",
    ],
}
json.dump(DATA, open(_article_dir + "/article_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("article_data.json 已写入")
