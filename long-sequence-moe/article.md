<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>告别 Docker 环境</strong>：Dockerless 是一个无需仓库级运行环境的智能体验证器，通过主动探索代码库来评判补丁正确性，彻底绕开为每个仓库搭 Docker 的痛点<br><br>
- <strong>AUC 超越最强开源方案 14.3 点</strong>：在验证器的评测集上达到 81.0 AUC，超越现有最强开源验证器 DeepSWE Verifier 14.3 个点，也优于 GPT-5.4 等闭源模型<br><br>
- <strong>无环境 post-training 匹敌有环境方案</strong>：用 Dockerless 同时做 SFT 数据筛选和 RL 奖励信号，SWE-bench Verified 达 62.0%，仅比用真实测试执行的版本低 0.4 点
</div>
</div>

---

## 当 Docker 成为瓶颈

程序验证器在训练编码 Agent 中扮演着核心角色——无论是筛选高质量轨迹用于监督微调（SFT），还是为强化学习（RL）提供奖励信号，验证器决定了 Agent 的 rollout 是否成功解决了 Issue。

目前，验证的金标准是执行测试：在每个仓库的 Docker 环境里运行单元测试。听起来简单，但实际工程成本极其沉重——为每个仓库定制 Docker 镜像、解析依赖、识别相关测试、编写执行脚本和结果解析器。即便最先进的自动化流水线，也只能覆盖有限比例的仓库。更根本的问题是：大量真实世界的代码库，尤其是私有、企业或遗留仓库，根本没有可复现的环境或完整的测试套件。

最近的研究尝试从共享基础镜像执行 Agent rollout 来降低成本，但验证器仍然是一个瓶颈。现有无环境验证器只靠表面信息（文本 diff 相似度、LLM 一次性评分）来打分，从不检查代码库本身。对于复杂的软件工程任务，这种浅层方法远远不够——判断一个补丁是否真正修复了 Issue，需要深入的仓库上下文。

## Dockerless：主动探索代码库的验证器

Dockerless 的核心思路很简单：与其匹配文本 diff，不如像人类开发者一样主动去代码库里找证据。它使用一个两阶段的架构：

**第一阶段——问题生成与探索。** 给定 Issue 描述和参考补丁（golden patch），模型先生成 2-4 个验证性问题。这些问题涵盖四个维度：
- **Location（位置）**：修复应该在仓库的哪个位置生效
- **Behavior（行为）**：补丁后的代码应该做什么
- **Test Evidence（测试证据）**：哪些测试或断言能确认正确性
- **Edge Cases（边界情况）**：仓库的其他部分会不会被破坏

针对每个问题，Dockerless 派发一个子 Agent，通过只读 shell 工具（find、grep、rg）探索代码库，返回有证据支持的答案。多个子 Agent 并行运行。

**第二阶段——判决。** 所有子 Agent 返回答案后，Dockerless 聚合收集到的证据，输出一个二值判决 token（0=不解决 Issue，1=正确解决）。推理时将两个判决 token 的 logits 通过 softmax 转换为连续分数，作为评分。

![](x2.png)
<span style="font-size:12px;color:rgb(153,153,153);">Dockerless 架构图：先根据 Issue 和参考补丁生成验证问题，并行派发子 Agent 探索代码库收集证据，最后聚合证据输出判决分数</span>

## 训练：拒绝采样 + 单一骨干共享

Dockerless 的训练使用拒绝采样（rejection sampling）。数据来源于 SWE-Gym 和 Multi-SWE-RL 的 3,700 个 Issue，每个训练样本包含（Issue、参考补丁、候选补丁、真实标签）。

用教师模型生成完整的"问题-答案-判决"轨迹，只保留那些预测判决与真实执行结果一致的样本。正负样本比上限设为 4:1 以缓解类别不平衡。然后在整个输出序列上用标准 next-token cross-entropy 训练。

关键设计：**单一骨干模型共享所有阶段**——问题生成、子 Agent 探索和最终判决使用同一个 Qwen3.5-9B 模型联合训练。不需要为每个阶段部署不同的模型。

![](x3.png)
<span style="font-size:12px;color:rgb(153,153,153);">Dockerless 训练流水线：教师模型生成问题-答案-判决轨迹，与执行标签匹配的保留用于微调</span>

## 无环境 Post-Training

Dockerless 的最终目标是实现一个完全不依赖仓库级环境的 post-training 流水线：

**无环境 RFT。** 在最小 Linux 镜像中收集大量 rollout（16K），用 Dockerless 给每个 rollout 的最终补丁打分，保留 top 4K 用于 SFT 微调。这替代了传统的"通过仓库级测试才保留"模式。

**无环境 RL。** 在 SFT 模型基础上，用 Dockerless 作为奖励模型跑 GRPO。每次对同一个补丁执行 M=2 次独立的 Dockerless 评估并取平均，提升奖励稳定性。全程不涉及任何仓库级测试执行。

![](x4.png)
<span style="font-size:12px;color:rgb(153,153,153);">无环境 post-training 流水线：(A) 环境自由的 RFT——Dockerless 筛选 top-K rollout；(B) 环境自由的 RL——Dockerless 提供奖励信号</span>

## 实验结果

### 验证器评估：全面领先

在平衡验证器评测集上，Dockerless 在 SWE-bench Verified 分片达到 **81.0 AUC**，在 Multi-SWE-bench Flash 分片达到 **72.1 AUC**。

| 模型 | Verified AUC | Multi-SWE AUC |
|------|-------------|---------------|
| DeepSeek-V3.2 | 69.4 | 58.5 |
| Kimi-K2.5 | 70.7 | 63.9 |
| GLM-5 | 73.2 | 62.5 |
| GPT-5.4 | 75.9 | 59.5 |
| SWE-Gym Verifier | 61.0 | 53.7 |
| R2E-Gym Verifier | 64.3 | 55.1 |
| OpenHands Critic | 48.6 | 52.2 |
| DeepSWE Verifier | 66.7 | 62.9 |
| **Dockerless** | **81.0** | **72.1** |

相比最强开源验证器（DeepSWE Verifier），Dockerless 在 Verified 上提升 **14.3 点**，在 Multi-SWE 上提升 **9.2 点**。即使对阵最强前沿 LLM 做零样本判决（GLM-5 的 73.2），也领先 **5.1 和 8.2 点**。

### 端到端结果：无环境匹敌有环境

完全无环境的 post-training 流水线产出的 Dockerless-RL-9B 达到：

| 基准 | Dockerless-RL-9B | Qwen3.5-9B 基线 | 提升 |
|------|-----------------|----------------|------|
| SWE-bench Verified | **62.0%** | 59.6% | +2.4 |
| SWE-bench Multilingual | **50.0%** | 41.3% | +8.7 |
| SWE-bench Pro | **35.2%** | 32.3% | +2.9 |

与使用真实测试执行奖励的 Test-Execution RL（62.4/51.3/35.7）相比，Dockerless 的差距仅为 **0.4/1.3/0.5 点**——几乎完全追平。这是首个证明无环境 post-training 可以匹敌有环境基准的工作。

### 验证问题数量的影响

Dockerless 在 K=4 时达到 AUC 峰值 81.0。超过 4 个问题后性能不再提高（K=6 时 79.6，K=8 时 80.3），说明额外问题往往引入冗余或噪声证据。因此推理时生成 2-4 个问题，在准确率和每次调用的探索成本之间取得平衡。

![](x5.png)
<span style="font-size:12px;color:rgb(153,153,153);">验证问题数量 K 对 AUC 的影响：K=4 达到峰值，之后不再提升</span>

### 延迟：Agent rollout 才是瓶颈

Dockerless 因为要执行多步仓库探索再做奖励评估，比直接打分慢。但在 RL 场景下，Agent rollout 平均耗时 **2308 秒**，而奖励评估仅增加 **41-180 秒**（只占总时间的 **7.2%**）。端到端延迟分布在三种奖励源下几乎完全重叠——瓶颈是 rollout 本身，不是验证器。

### 案例研究

一个 matplotlib offsetText 颜色的 Issue——候选补丁用内联条件风格重写了修复，与参考补丁的辅助变量风格完全不同。文本相似度只给 0.468，DeepSWE Verifier 只给 0.035。但 Dockerless 通过子 Agent 探索确认：修复确实应用到了 XAxis 和 YAxis 的初始化路径，inherit 语义被保持——给出 **0.996** 分，与真实执行结果一致。

## 相关工作

Dockerless 的独特之处在于将 Agent 本身放在了验证位置：不是训练一个从固定 prompt 打分的分类器，而是让验证器主动去代码库中寻找证据。这与之前所有 SWE 验证器（SWE-Gym Verifier、DeepSWE Verifier、R2E-Gym Verifier 等）形成本质区别——它们没有一个会调用工具或检查仓库。

## 结语

Dockerless 提供了一个清晰的信号：**验证这件事，可以不依赖执行环境。** 在编码 Agent 的训练流程中，搭建 Docker 环境一直是最麻烦的环节之一。Dockerless 用"智能体主动探索代码库"替代了"跑测试"，在验证器自身性能上大幅领先现有方案，同时让整体 post-training 效果几乎无损。

更值得关注的是它的设计思路——把验证器本身也做成了一个 Agent，让它像人一样去代码里找证据。这可能是一个比"提升验证器准确率"更根本的视角转换：不再问"这个补丁能不能通过测试"，而是问"我们能不能找到证据说明这个补丁是对的"。对于大量没有测试覆盖的真实仓库来说，后一个问题显然更有实际意义。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
Dockerless 最大的意义不只是更高的 AUC 或更低的工程成本，而是它打开了"无环境 post-training"这个方向——在那些没有测试套件、没有可复现环境的真实仓库长尾上，仍然有路可走。Agent 化的验证器，可能是编码 Agent 从"比赛级"走向"工业级"的关键一块拼图。
</div>
</div>

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/html/2606.28436v1</span>
