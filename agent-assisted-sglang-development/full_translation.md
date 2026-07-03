# Agent-Assisted SGLang Development: An Initial Exploration

LMSYS 博客 · 2026-07-02

SGLang 开发越来越超越孤立的代码变更。同一个仓库现在覆盖了 LLM 服务、分布式运行时、GPU 内核、扩散模型管线、模型特定执行路径和生产事件处理。过去，许多这些工作流依赖于单个开发者的记忆：如何启动某个模型、如何读取 profile trace、调试 CUDA crash 时先加哪条日志、performance PR 应该包含哪些基准测试。

随着 agent 工具日趋成熟，这种经验可以被转化为可执行的 `SKILL.md` 文件、脚本、基准测试契约和 review 循环。

**SKILL.md**：围绕 SGLang agent 开发，已经涌现出一组适用于 LLM 和 diffusion 工作的 skill。`.claude/skills` 目录包含了这些技能文件。综合来看，这些努力指向同一个方向：agent 的价值来自程序化的工程知识，包括可执行的步骤、可复现的实验和可审查的证据。

## 1. TL;DR

`debug-cuda-crash`、`sglang-diffusion-benchmark-profile`、`llm-torch-profiler-analysis` 是常用 skill 的代表。

## 2. Why SGLang Is a Good Fit for Agent-Assisted Development

SGLang 是一个面向 LLM 和多模态模型的高性能推理框架。随着模型家族和硬件路径的扩展，开发中反复出现一些问题：`torch.compile` 兼容性、不同模型的特化路径、性能回归排查等。

这些问题天然适合 agent 处理。启动服务、修复工作负载、收集 trace、分类 profile 行、添加测试和记录实验结果都有清晰的输入输出，适合脚本化和重复执行。开发者需要定义边界：相同的基准测试设置、相同的 profile 解读规则、相同的精度门槛，以及 agent 应停止改代码的条件。

本文讨论的 agent 是一个受工程工作流约束的执行器。重复的 SGLang 开发流程可以捕获为 skill，让 agent 处理重复执行、证据收集和状态追踪。开发者负责定义目标、评判证据以及审查变更是否应该合入真正的 serving 路径。

## 3. From Prompt Engineering to SKILL: Protocols and Examples

在 SGLang 框架中，一个有用的 skill 至少应回答以下问题：

| 问题 | skill 应捕获的内容 |
|------|-------------------|
| 何时使用 | 触发场景、支持的模型、支持的硬件、硬停条件 |
| 如何开始 | 预检查、环境变量、仓库状态、依赖检查、模型配置 |
| 如何验证 | 基准测试命令、profile 命令、测试入口、精度门槛 |
| 如何决策 | 输出表、失败模式、优先级、风险类别、回退条件 |
| 如何交付 | 产物目录、结果 schema、PR 描述、复现命令、review 要求 |

SGLang agent 相关 skill 覆盖不同的层次。有些接近源码变更（如调试、测试、添加 diffusion 模型、基准测试和 profile 工作流），另一些面向跨框架基准测试、容量规划、计算模拟、生产事件分类、PR 优化知识库、SGLang 人工风格 review，以及更高层次的 Humanize/RLCR 工作流。

### 3.1 Current Skill Stack

当前常用的 SGLang agent 相关 skill 分为以下几组：

| 层次 | 代表性 skill / 项目 | 解决的问题 |
|------|--------------------|----------|
| CUDA crash | debug-cuda-crash | 记录自定义 op/kernel API 边界的输入、异常和 dump，将临时崩溃转化为可离线分析的样本 |
| LLM 基准测试 | llm-serving-auto-benchmark | 在 SGLang 和其他 OpenAI 兼容推理栈之间运行公平、有界、可恢复的服务基准测试搜索 |
| 容量规划 | llm-serving-capacity-planner | 解析 SGLang 和其他推理框架的启动日志，解释权重内存、KV cache 预算、CUDA graph 开销、请求容量和 OOM 压力 |
| Trace 分类 | llm-torch-profiler-analysis | 生成固定的 kernel、overlap 机会、融合模式表，将 kernel 映射回 Python 源码 |
| 流水线/层分析 | llm-pipeline-analysis | 将 torch profiler trace 切片为前向传递、层和 kernel 流，定位稳定传递、瓶颈层类型和 Perfetto 时间范围 |
| 模型计算模拟 | model-compute-simulation | 为 LLM 构建算子级计算模板，估算 tensor 形状、FLOPs、MFU、kernel-to-op 映射和并行化假设场景 |
| Diffusion 基准/profile | sglang-diffusion-benchmark-profile | 捕获去噪延迟、性能 dump 和 torch profiler trace，同时检查执行是否真的使用了原生 SGLang diffusion 后端 |
| 添加 diffusion 模型 | sglang-diffusion-add-model | 从 Diffusers/reference 管线向 SGLang pipeline/stage/model/config 结构中添加新的 diffusion 模型 |
| Diffusion 性能调优 | sglang-diffusion-performance | 选择性能设置如 torch.compile、预热、SP/CFG 并行化、offload、注意力后端和量化 |
| 生产事件分类 | sglang-prod-incident-triage | 收集 live-server 数据、保存失败请求、回放，然后路由到有针对性的 crash/hang/profile 工具 |
| SGLang 审查/PR 历史 | sglang-humanize-review 和 model-pr-history-knowledge | 对照真实维护者讨论模式审查 SGLang patch，并保持 PR 驱动的模型演化历史靠近变更的源码 |
| SGLang SOTA 性能循环 | sglang-sota-humanize-loop | 首先公平对比 SGLang 与目标开源推理框架，然后将差距决策、profiling、打补丁和重新验证放入 Humanize/RLCR 循环 |

这些条目将容易被遗漏的步骤转化为可执行的协议，使工作流可以运行、恢复和被审查。

### 3.2 Recent Optimization and Workflow Examples

以下案例来自最近合并的 SGLang PR。表格展示了完整的工程路径：基准测试、profiling、定位、代码变更、测试和重新验证。

| 案例 | 结果 | 关键点 |
|------|------|--------|
| Router long-context tokenization 去重，PR #28744 | DeepSeek-V4-Flash 上 60k/125k token 请求的 idle TTFT 下降 ~29%/41%；60k token 负载下 TTFT 下降 34%-49% | Agent 处理了 cache-aware routing、chat-encoder 对齐、engine 侧的 input_ids 回退和 proxy body 构造，避免 router 和 engine 中的重复 tokenization |
| Qwen3-Next FlashInfer allreduce 融合，PR #22664 | H100 TP=4 上吞吐从 5.49 req/s 提升到 9.41 req/s (+71.4%)；平均 TTFT 从 456.24ms 降到 167.54ms | Profile 驱动的 LLM 集体通信优化：未融合的跨设备 reduce 主导了 prefill，融合后的 allreduce 路径通过了 MMLU/GSM8K 精度检查 |
| Cohere2Moe NVFP4 fused-MoE 路径，PR #27401 | 1x B300 上 chat 吞吐 +26%，summarization +21%，超越另一开源推理框架 +4.1%/+6.8% | 补全了路由语义，使现有的 flashinfer_trtllm NVFP4 fused-MoE kernel 能够在真实模型路径中正确使用，通过 GSM8K/MMLU 检查 |
| Kimi Delta Attention CuteDSL prefill kernel on SM100，PR #27488 | B200 上 Delta Attention prefill 比 Triton 快 1.08x-1.52x；GSM8K 从 0.915 提升到 0.920 | Kernel 任务必须覆盖模型的 gate 分布、数值溢出、host 开销、真实模型精度和单元测试 |
| Spectral Progressive Diffusion，PR #27524 | FLUX.1/FLUX.2/Z-Image/Wan/Qwen-Image 去噪加速分别为 1.63x/1.77x/2.07x/2.32x/1.6x | Diffusion 端系统优化：早期去噪在较低潜空间分辨率运行，然后 GPU DCT 上采样在高频细节重要时恢复全分辨率 |
| LTX-2 VAE decode channels-last-3d，PR #27431 | LTX-2 decode 阶段从 5.41s 提升到 3.84s（1.41x）；峰值内存从 71.81 GiB 降到 62.12 GiB | Profile 指向 Conv3d 和 layout 转换，修复在 causal padding 中保持内存格式，连接 loader 策略到单 GPU LTX-2 |

在以上示例中，agent 主要通过执行工作流来贡献：运行基准测试、读取 profile、定位 Python 源码、更改代码、添加测试、重新验证和准备 PR 描述。没有 skill，许多步骤依赖人工提醒。一旦编码为 skill，工作流就变得很容易重复。

## 4. Profiling, Review, and Loop Engineering

SGLang 性能工作中的常见错误是只看总运行时间，或者在 Perfetto 中随便看几分钟就凭直觉认为某些操作「应该被融合」。对 agent 来说风险更大，因为它容易把一个视觉上很热的 kernel 误认为真正的瓶颈。

实践中通常同时使用两个 profiler skill。`llm-torch-profiler-analysis` 处理第一层 trace 分类，将全局 profile 转化为三个固定表：Kernel Table、Overlap Opportunity Table 和 Fuse Pattern Table。这些表回答第一组问题：哪个阶段和哪个 kernel 占用了多少 GPU 时间、它们映射到哪行 Python 源码、是否有可参考的现有融合/重叠路径。

下一步是 `llm-pipeline-analysis`。知道全局热点后，还需要知道它们属于哪个前向传递、层类型和 kernel 流。这个 skill 读取 Chrome trace JSON 和模型 config.json，用 layer-boundary anchor kernel 将 trace 分割为前向传递和层，然后生成前向传递摘要、每层时间线、层聚类统计、压缩比和计算流表等分析产出。

Profile 分析因此成为两步过程：先 `llm-torch-profiler-analysis` 识别全局冲突，然后 `llm-pipeline-analysis` 将问题定位到稳态前向传递、代表层和具体 kernel 流。

### 4.1 Humanize/RLCR: Adding External Review to the Loop

Humanize 解决长运行任务中的状态和审查问题。一个高风险的 SGLang 性能任务通常不会在一次实现中完成。它可能经历多轮基准测试、profiling、打补丁、回退、改变方向和重新验证。Humanize 将这个流程分为两个阶段：`humanize-gen-plan` 生成 plan.md，然后 `humanize-rlcr` 执行并审查每一轮。`.humanize/rlcr/<timestamp>/round-<N>-prompt.md` 记录每一轮的 prompt。

这个机制为 SGLang SOTA Performance Loop 提供了执行和审查基础。Claude Code 运行基准测试、读取 profile、修改 SGLang 代码和重新验证。Codex Review 在每轮结束时检查证据、状态和风险。

实践中命令顺序应是明确的，这样 agent 不会直接跳入实现：
1. 在 artifact_root/draft.md 下写任务草稿
2. 运行 humanize-gen-plan 生成 artifact_root/plan.md
3. 从 artifact_root/plan.md 启动 humanize-rlcr
4. 所有决策、摘要和审查状态都保存在本地 Humanize workspace 中

### 4.2 SGLang SOTA Performance Loop (Loop Engineering)

单个 skill 可以稳定一个任务。但经过十几轮实验后，另一个问题出现了：哪个候选项最好、哪些方向已经失败、之前的 NCU 报告说明了什么、基准测试是否仍然匹配基线、以及何时停止。这些状态不能仅存在于聊天上下文中。

SGLang SOTA Performance Loop 是一个基于 Humanize/RLCR 构建的 Loop Engineering 工作流。在这里 SOTA 意味着在固定实验条件下的最佳可复现结果：相同的模型、硬件、GPU 数量、精度、工作负载、SLA、框架 commit 和服务参数。问题是 SGLang 是否能在这些条件下达到当前最佳可复现结果。

完整的 SGLang SOTA Performance Loop 包含以下阶段：固定公平基准测试 → 差距决策 → profiling → 流水线分析 → 打补丁 → 重新验证。

对于 `Qwen/Qwen3-Next-80B-A3B-Instruct-FP8` 在 2x B200 上这样的目标，循环之所以重要是因为基准测试结果、profile trace、失败的 patch 和中间结论都需要始终关联到同一组模型、硬件、工作负载和框架 commit。

### 4.3 Codex Goal: A Lower-Cost Loop Implementation

SGLang SOTA Performance Loop 使用双角色设置：Claude Code 执行基准测试、profiling、补丁和重新验证，Codex Review 在每轮结束时检查。这对正式的 PR 工作是合适的，但每轮消耗一个执行模型和一个审查模型，增加成本和等待时间。

Codex Goal 提供另一种实现。一旦将"公平基准测试 → 差距决策 → profile → patch → revalidate → artifact ledger"写入持久化的 Goal，单个 Codex Goal 可以执行执行、自我检查和重新验证，无需双角色设置。

两者的区别：

| 维度 | Humanize/RLCR SOTA Loop | Codex Goal |
|------|------------------------|------------|
| 执行 | Claude Code 负责实现和实验；Codex Review 每轮审查 | 一个 Codex Goal 连续执行、自检和重新验证 |
| 状态位置 | Plan/prompt/summary/review 结果在 `.humanize/rlcr/...` | 当前 Goal 线程 + manifest/evidence 在 artifact_root |
| 审查方法 | 停止钩子 + Codex Review + git/state/schema 检查 | Goal 级自检 + artifact 契约 + 人工抽查 |
| 成本 | 双模型角色参与，每轮成本更高 | 一个 Goal 承担执行和检查，降低成本 |
| 主要风险 | 循环设置更复杂，每轮等待时间更长 | Goal drift 或过早完成（除非硬停条件明确） |

## 5. KDA-Based CUDA Kernel Optimization for SGLang Systems

超越 LLM 和 diffusion 的模型级优化，内核优化有更严峻的扩展问题。没有一个独立于硬件和工作负载的最佳 kernel。同一算子可能在 H100、H200、B200 或 B300 上偏好不同的实现；不同模型架构暴露不同的 tensor 形状和布局约束；服务工作负载改变 batch size、序列长度、精度格式、wrapper 开销、同步行为和回退路径。在实践中，搜索空间是硬件、模型和工作负载定义的笛卡尔积。

这产生了组合优化负担。对每个候选 kernel，开发者需要提取代表性生产行、构建同 ABI 的 harness、运行 A/B 测量、跨 shape bucket 检查正确性、读取 NCU 指标、决定某个 bucket 是否值得专门优化，然后在真实 SGLang 路径中重新验证。对每个硬件/模型/工作负载组合手工做这件事是昂贵的。这也正是那种重复性、证据密集的工作流——只要人类定义不变量并审查最终路径——agent 很擅长的。

但直接让 agent 写 CUDA 很容易导致基准测试奖励黑客（benchmark reward hacking）：更改基准测试、使用更轻量的 wrapper、启用基线未用的 fast math、只优化一种 shape、破坏数值语义，或在真实 SGLang 路径中无收益。

KDA-Pilot 将内核优化分离为独立的任务，因此 agent 不会自由修改整个 SGLang 仓库。

公共 KDA-Pilot B200 diffusion 摘要当前列出 10 个被追踪的 SGLang kernel 任务。大多数行在 KDA-Pilot ledger 中有稳定的数值 B200 证据，在提取的生产行上 wall-geomean 加速比范围从 1.1341x 到 2.7499x。截至 2026 年 6 月 27 日，三个 KDA-Pilot 衍生的优化已合入 SGLang 上游。

每个内核任务的加速比和优化方向：

| 内核任务 | B200 证据 | 主要优化方向 |
|---------|----------|------------|
| qknorm_rope | 1.1341x | 共享 RoPE staging、Q/K 复用、大行快速路径 |
| norm_infer | 1.3523x | Warp-row RMS、tiled persistent RMS、8B/16B vector 路径 |
| rotary_embedding | 1.4912x | 128-bit 向量 I/O、cos/sin hoisting、LTX2 block 匹配 |
| cutedsl_norm_tanh_mul_add | 1.4953x | Row-invariant 数学 hoisting、launch-bounds 调优、exact tanh |
| cutedsl_norm_scale_shift | 1.3201x | Operand-class 分派、16B/32B 向量、two-pass variance |
| fuse_scale_shift | 2.7499x | rowgrid/flatvec/exact-C 路径、cache hint、one-pass 归约 |
| group_norm_silu | 2.3118x | Split-group stats、channels-last 直接路径、大行回退 |
| attention_concat_copy | 1.30x | Single-launch 区域拷贝、pitched 16B block gather、严格 layout/device 拒绝 |
| causal_conv3d_cat_pad | 2.06x | Flat chunking、16B 向量化 store、stride-aware 回退、bitwise-exact gate |
| residual_gate_add | 1.11x | One-pass CUDA 融合、pinned-GPU 正确性、SGLang PR #29361 B200 Triton-row 重新基准 |

关键结论不是每个独立内核的胜利都能成为大的端到端胜利，而是同样的 KDA-Pilot 证据包——固定生产行、正确性门槛、同 ABI 比较、profiler attribution 和真实模型检查——可以将内核任务从孤立基准测试推进到可审查的 SGLang serving 路径。

## 6. Practice Rules

**在启动 agent 之前定义任务边界。**
"优化 SGLang"太宽泛。"让 SGLang 在 `Qwen/Qwen3-Next-80B-A3B-Instruct-FP8` 的 2x B200 上在固定 `1000->1000` 和 `8000->1000` 工作负载下匹配另一开源推理框架"才是可执行的目标。

**在读取 profile 之前固定基准测试。**
如果工作负载在结果已知后可以改变，agent 可能意外地优化了一个更容易的问题。SOTA loop 和 KDA-Pilot 都在打补丁之前固定了工作负载。

**根据 kernel 的计算特性解释 NCU 结果。**
对于内存密集型 kernel，关注 DRAM/L2 吞吐量、load/store 效率和 memory pipe 利用率。对于计算密集型 GEMM/attention kernel，关注 Tensor Core 利用率、SM busy、eligible warps 和主要 stall 原因。对于小延迟密集型 kernel，检查 launch 数量、每 kernel 时长、同步点和可能的融合机会。单张 trace 截图不够；下一个代码变更应由具体指标支持。

**在信任 profile 之前检查后端和回退条件。**
如果 LLM 运行悄悄切换了 attention 后端、禁用了 CUDA graph、或走了与基准测试不同的 wrapper 路径，trace 就不再描述目标 serving 路径。diffusion 同理：如果日志显示回退到 diffusers 后端，该 trace 不能用作原生 SGLang diffusion 的证据。这些硬停条件应存在于 skill 中。

**内核优化必须使用相同的 ABI、wrapper 和编译标志。**
特别是，候选内核不应悄悄走更轻的路径，`--use_fast_math` 不应只在一侧启用。

**Review 比以往更重要。**
Agent 可以创建更多 PR，也可以制造更多看似合理的错误。对 SGLang 这样的高性能系统的审查需要检查 shape、dtype、分布式执行、CUDA graph 行为、回退行为、精度、serving API、指标和基准测试设置。

Agent 时代的 SGLang 开发不会将开发者排除在系统之外。更现实的变化是将开发者经验编写进工作流，将重复性执行交给 agent，将判断、设计和审查留给人。节省的时间可以投入到更难的性能问题、模型路径和生产稳定性，或回投到改进 agent 工作流本身。对一个开源推理框架来说，这种基础设施值得持续投资。
