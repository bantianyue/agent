<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>原生世界模型</strong>：Qwen-AgentWorld是首个从CPT阶段就将环境模拟作为训练目标的语言世界模型，一次覆盖MCP、Search、Terminal、SWE、Web、OS、Android七个域<br><br>
- <strong>三阶段训练流水线</strong>：CPT注入环境知识（含专业域语料）→ SFT通过 `<think>` 块激活显式推理 → RL用混合奖励精炼，逐轮信息论损失掩码让模型只从真正的环境信息中学习<br><br>
- <strong>模拟RL反超真实环境</strong>：作为独立模拟器，可控Sim RL的训练效果超过与实时搜索引擎对练的Real RL（WideSearch F1 50.3% vs 45.6%），4,000个零样本OpenClaw环境也能直接模拟<br><br>
- <strong>世界模型warm-up = 新的预训练范式</strong>：单轮LWM RL warm-up（无工具调用）迁移到多轮Agentic任务，在完全OOD的Claw-Eval上+11.3、BFCL v4上+9.0
</div>
</div>

Qwen团队今天发布了一个东西，他们训练了一个**专门模拟Agent环境的语言模型**。

不是教Agent怎么用工具，是教模型预测"Agent执行某个动作后，环境会返回什么"。前者让Agent变强，后者让Agent能在模拟器里练手，而且练出来的效果竟然比在真实环境里练还好。

**Qwen-AgentWorld** 是个原生语言世界模型，覆盖了MCP、Search、Terminal、SWE、Web、OS、Android七个交互域。三个GUI域（Web、OS、Android）的观察不是像素帧，而是accessibility tree和UI层级标记，纯文本就能模拟视觉环境。

![](blog_teaser.png)
<span style="font-size:12px;color:rgb(153,153,153);">Qwen-AgentWorld的总体框架：上图为七域统一语言世界模型，下图为两种应用范式（解耦模拟器 & 统一Agent基础模型）。</span>

模型有两个规格：35B-A3B (MoE)和397B-A17B。397B版在AgentWorldBench上以58.71分超过GPT-5.4 (58.25)和Claude Opus 4.8。35B版在三阶段训练后从47.73涨到56.39，超过了Claude Sonnet 4.6 (56.04)。

**为什么会这样？** 我们先聊一下训练方法。

**CPT注入，SFT激活，RL精炼**

三个阶段的设计逻辑如下：

**Stage 1 CPT** 用超过1,000万条真实环境交互轨迹做持续预训练，同时混入专业域语料（工业控制、网络安全、法律、医疗、金融、时事）。模型不只是看（action, observation）对，他们设计了一个**逐轮信息论损失掩码**：根据四个统计量（Overlap、Novelty、Jaccard、长度比）把每轮对话分成七类。像API echo这种"动作=响应"的轮次只保留5%的梯度，真正携带环境信息（如 `read_file` → 文件内容）的轮次100%保留。

背后的直觉是：模型不应该在"参数敲进去、回显参数出来"这种机械行为上浪费学习信号。

**Stage 2 SFT** 在CPT基础上显式教会模型通过 `<think>...</think>` 块进行下一状态预测推理。用256K上下文窗口+拒绝采样（3条rollout中选最好的）整理出7,094条高质量思考轨迹。

**Stage 3 RL** 用GSPO +混合奖励（Rubric法官+规则验证器）精炼输出质量。

![](blog_pipeline.png)
<span style="font-size:12px;color:rgb(153,153,153);">三阶段训练流水线：CPT注入→SFT激活→RL精炼。</span>

**AgentWorldBench：五维Rubric，ground-truth锚定**

为了评估世界模型质量，团队从GPT-5.4、Claude Opus 4.6等五个前沿模型在Tool Decathlon、Terminal-Bench、OSWorld-Verified等九个已有基准上的真实交互中构建了AgentWorldBench。每一条评估样本都配有真实环境执行的ground-truth observation，用开放Rubric从格式、事实性、一致性、真实感、质量五个维度评分。

![](blog_bench_results.png)
<span style="font-size:12px;color:rgb(153,153,153);">AgentWorldBench结果：Qwen-AgentWorld-397B-A17B以58.71分超过GPT-5.4（58.25）和Claude Opus 4.8。优势在Terminal和SWE上最显著。</span>

**那训练世界模型到底有什么用？**

团队提出了两种应用范式。

**范式一：作为独立环境模拟器（Sim RL）**

世界模型和策略Agent是两个分开的模型。训练时世界模型扮演环境：Agent执行动作，世界模型预测下一轮观察，Agent从这些模拟rollout中学习。

三个发现：

1. **零样本泛化到未见环境**。用一个从未在训练中出现过的开源平台OpenClaw（覆盖排程、编码、邮件处理、浏览器自动化等任务），模拟4,000个环境做Sim RL，Claw-Eval +4.3，QwenClawBench +7.1。作为对比，用Qwen3.6-Plus做模拟器几乎没有提升，**世界模型的质量是Sim RL的瓶颈**。

2. **可控模拟是必需的不是可选的**。不加控制指令的Sim RL完全没有效果（Tool Decathlon从32.4降到31.5），因为模拟器缺乏足够grounding来产生可信响应。一旦加入可控扰动（间歇性API错误、分页响应、不完整中间结果），Tool Decathlon +3.7，MCPMark +12.3。可控性是Sim RL在这类域中起效的前提条件。

3. **Sim RL超过Real RL**。在WideSearch上直接对比：可控Sim RL在step 60时F1达50.3%，而用实时搜索引擎训练的Real RL只有45.6%。行为差异也值得单独看看：Sim RL训练的Agent大幅增加了 `web_extractor` 调用（2.5 → 4.0），而Real RL反而减少（2.5 → 1.5）。原因在于模拟器的摘要刻意隐藏了详情，Agent学会了必须提取完整页面才能拼出答案。

![](blog_rl_comparison.png)
<span style="font-size:12px;color:rgb(153,153,153);">Sim RL vs Real RL训练曲线：可控Sim RL达到或略超Real RL（实时搜索引擎）的效果。</span>

**范式二：统一Agent基础模型**

这次Agent和世界模型是同一个模型。LWM训练将下一状态预测内化为模型的元级推理能力：模型在行动前先在心里模拟环境响应。

效果不错：在Qwen3.5-35B-A3B-SFT上跑单轮LWM RL（没有工具调用、纯文本生成），然后直接拿到多轮、带工具调用的Agentic任务上评估，不做任何额外微调。

| 基准 | Base | +LWM RL | Δ |
|---|---|---|---|
| Terminal-Bench 2.0 | 33.3 | 39.6 | +6.3 |
| SWE-Bench Verified | 64.5 | 67.9 | +3.4 |
| SWE-Bench Pro | 42.2 | 47.4 | +5.2 |
| WideSearch (F1 Item) | 33.4 | 46.2 | +12.8 |
| Claw-Eval **OOD** | 53.6 | 64.9 | **+11.3** |
| QwenClawBench **OOD** | 39.8 | 49.4 | **+9.7** |
| BFCL v4 **OOD** | 62.3 | 71.3 | **+9.0** |

效果在完全out-of-distribution（OOD）的域上最显著。LWM训练时模型根本没接触过OpenClaw和BFCL，但"在行动前预测环境状态"这个元能力被学会了，并且迁移到了这些域。

**世界模型在思考什么**

团队分析了129条LWM推理轨迹，发现了三种涌现模式：

1. **审慎的自我修正**。模型会在思考过程中突然用"Wait!"打断自己，修正之前的预测。129轮里统计到1,347次中断（每轮10.4次），涉及事实错误、认知边界确认（"我实际上不能执行 `np.random.seed(42)`"），甚至视角转换。

2. **信息泄露预防**。在Search域，世界模型持有一个参考答案，Agent正在找它。当Agent的查询不相关时，模型会确保摘要不意外暴露答案：这是世界模型的心智理论能力。

3. **多步因果推理**。预测 `curl -s localhost:3000 | python3 -m json.tool` 的输出需要链条：Node.js没装 → 服务器没启动 → 3000端口无监听 → curl静默失败 → 空管道 → json.tool抛出JSONDecodeError。六个步骤，每一步都需要对系统的因果理解，不是模板化生成。

![](blog_reasoning.png)
<span style="font-size:12px;color:rgb(153,153,153);">LWM推理模式：自我修正、信息泄露预防、多步因果推理。</span>

**再聊几句为什么世界模型有意义**

团队在论文中强调了一个论点：**世界模型不是为了替代真实环境或省钱，而是从另一个维度推Agent能力边界。**

真实环境训练再好也有天花板。工具调用的非确定性响应、不可逆操作、需要专用基础设施的部署环境，这些场景要么不可复现，要么没法规模化。世界模型提供了三个真实环境做不到的事：

1. **可伸缩性**。不需要维护4,000个容器沙箱就能模拟4,000个环境。
2. **可控性**。可以制造在真实环境中极其罕见的边界条件（间歇性错误、分页数据、不完整响应），有针对性地暴露Agent弱点。
3. **内化预测能力**。教会Agent在行动前先做"心智模拟"，这是一种元能力的迁移，跟教模型"先思考再写代码"类似，但面向的是未来的环境状态，不是过去的反思。

第三个能力在Unified范式下产生了跨域的、无需微调的迁移效果，这类似给预训练模型加了一个"预测层"，不是加参数，是加了一种思维模式。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
过去的Agent研究几乎全在拼策略（Policy），世界模型（World Model）是缺的那一块。Qwen-AgentWorld展示了语言世界模型能做到什么：它从CPT阶段就把"模拟环境"作为训练目标，不是事后在ChatGPT上套一层壳。<br><br>
比超越GPT-5.4更有看点的是Sim RL > Real RL这个反直觉的结果。如果你的模拟器足够好，在模拟器里练出来的Agent能比用真实环境练的更好，因为模拟器可以制造真实环境给不了的压力。这对Agent训练的工业化有直接价值。<br><br>
Unified范式的warm-up效应可能被低估了。单轮LWM RL（无工具调用）迁移到多轮带工具任务，且在OOD域上效果最好，说明下一状态预测是一种比反思更根本的"元推理"能力。如果这个结论在更大规模的模型上成立，LWM warm-up有希望成为Agent预训练的标准组件。
</div>
</div>

---

<span style="font-size:12px;color:#888888;">参考：

https://qwen.ai/blog?id=qwen-agentworld
https://arxiv.org/html/2606.24597v1</span>
