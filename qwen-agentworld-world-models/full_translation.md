# 完整翻译 — Qwen-AgentWorld

来源1：Qwen Blog https://qwen.ai/blog?id=qwen-agentworld
来源2：arXiv:2606.24597 https://arxiv.org/html/2606.24597v1

## 第一部分：产品介绍

Qwen 发布 Qwen-AgentWorld，首个原生语言世界模型，从 CPT 阶段就将环境模拟作为训练目标。覆盖七个域：MCP、Search、Terminal、SWE、Web、OS、Android。三个 GUI 域的观察用 accessibility tree 和 UI 层级标记，不是像素帧。

两个规格：35B-A3B (MoE) 和 397B-A17B。397B 版在 AgentWorldBench 以 58.71 超过 GPT-5.4 (58.25) 和 Claude Opus 4.8。35B 版三阶段训练后从 47.73 涨到 56.39，超过 Claude Sonnet 4.6 (56.04)。

三阶段训练：CPT 用 1,000 万+ 真实轨迹 + 专业域语料（工业控制、网络安全、法律、医疗、金融、时事）做持续预训练。逐轮信息论损失掩码根据四个统计量（Overlap、Novelty、Jaccard、长度比）识别真正携带环境信息的轮次，排除机械行为轮次的梯度。SFT 通过 `<think>` 块激活显式推理，256K 窗口 + 拒绝采样。RL 用 GSPO + 混合奖励（Rubric 法官 + 规则验证器）精炼。

AgentWorldBench 从五个前沿模型（GPT-5.4、Claude Opus 4.6 等）在九个已有基准上的真实交互构建，每样本有 ground-truth observation 配对，五维开放 Rubric 评分：格式、事实性、一致性、真实感、质量。

三种涌现推理模式：(1) 自我修正——"Wait!" 中断，129 轮中 1,347 次；(2) 信息泄露预防——持参考答案的 Search 域，不相关查询不泄露答案；(3) 多步因果推理——预测 curl 管道失败需六步因果链。

## 第二部分：技术架构

LWM 训练指三个阶段（CPT/SFT/RL）训练世界模型本身。Sim RL 用世界模型做环境模拟器训练策略 Agent；Real RL 用真实环境。

轨迹 (trajectory) = 多轮 (action, observation) 对。Agent 轨迹包含内部思考 + 动作选择 + 环境观察。环境轨迹从 Agent 轨迹剥离推理后得到。

统一环境轨迹 schema：system_prompt = task_description ⊕ action_space ⊕ initial_state ⊕ demonstrations ⊕ simulation_instruction。turn_t = (action_t, observation_t)。系统提示五组件：任务描述定义模拟目标，动作空间枚举工具，初始状态（可选）指定环境起始配置，演示为 few-shot 示例，模拟指令指定可控条件。

LWM 公式：ô_{t+1}=f_θ(c, o_≤t, a_≤t)。无状态环境（Search）隐式携带状态；有状态环境（Terminal、OS）维护显式内部状态。

数据来源：(1) 专用基础设施（容器沙箱、MCP 服务器、Android/Web/OS 模拟器）自动合成任务；(2) 公开轨迹，经多 Agent 清理流水线（获取、去噪、分割、语义对齐、评分）；(3) 内部 Agent 轨迹。三阶段数据池不重叠。SFT+RL 共 7,094+92,308 条轨迹。

数据处理：轨迹扩展为轮级预测样本（任意轮次 t 可作预测目标）。过滤：去重试循环（保留状态链）、去无变化轮次（GUI 域）。系统提示模板用 AutoResearch：12 轮并行 × 10 轮迭代优化，从 30 行简约版到 1,100 行规范版。

CPT 训练：标准 next-token prediction，多轮轨迹框架化为世界建模任务。信息论损失掩码分类：retrieval 100%保留、expansion 100%、action 100%、transform 50%、boilerplate 10%、echo 5%、other 100%。

SFT：CPT 后知识已掌握但仅隐式应用。SFT 显式激活下一状态预测推理。256K 上下文。拒绝采样 10,250→7,094 条（69.2% 保留率）。

RL：GSPO 训练，混合奖励（Rubric LLM 法官 + 规则验证器）。

## 第三部分：两种范式

**范式 I：解耦模拟 (Sim RL)**。策略 Agent 与世界模型分开。Qwen-AgentWorld 模拟 4,000 个零样本 OpenClaw 环境，Claw-Eval +4.3，QwenClawBench +7.1。用 Qwen3.6-Plus 做模拟器几乎无提升——模型质量是瓶颈。

可控模拟：无控制指令的 Sim RL 无效果（Tool Decathlon 从 32.4 到 31.5）。加可控扰动后 Tool Decathlon +3.7，MCPMark +12.3。可控性不是锦上添花，是 Sim RL 起效的前提。

Sim RL 超 Real RL：WideSearch F1 50.3% vs 45.6%。行为差异：Sim RL 增加 web_extractor 调用（2.5→4.0），Real RL 减少（2.5→1.5），因模拟器摘要刻意隐藏详情。

虚构世界也行：1,000 个全虚构环境的 Sim RL 泛化到真实搜索任务。

**范式 II：统一 Agent 基础模型**。同一模型既选动作又预测环境状态。LWM 训练将下一状态预测内化为元推理能力。

单轮 LWM RL（无工具调用）迁移到多轮带工具 Agentic 任务，跨七个基准五个域，不做任何额外微调。OOD 域增益最大：Claw-Eval +11.3，QwenClawBench +9.7，BFCL v4 +9.0。下一状态预测作为元推理模式可跨任务格式和域泛化。
