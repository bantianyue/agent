<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>Agent的价值不在于自动写代码，而在于将工程经验编码为可执行的Skill</strong>：LMSYS团队围绕SGLang推理框架构建了约15个agent skill，覆盖CUDA crash调试、LLM基准测试、容量规划、trace分类、diffusion模型添加、生产事件处理等全链路开发场景<br><br>
- <strong>双步Profile分析</strong>：先用llm-torch-profiler-analysis将全局profile转为三张固定表（kernel、overlap机会、融合模式），再用llm-pipeline-analysis将热点定位到具体前向传递、层类型和kernel流<br><br>
- <strong>Humanize/RLCR + SGLang SOTA Performance Loop</strong>：Claude Code执行实验与实现，Codex Review每轮审查证据和风险。Codex Goal提供更低成本的单人循环方案<br><br>
- <strong>KDA-Pilot内核优化方法论</strong>：将CUDA kernel优化拆解为10个独立任务，在固定生产行上获得1.11x-2.75x加速比，已有3个优化合入SGLang上游<br><br>
- <strong>六条实践铁律</strong>：包括定义任务边界、固定基准测试后再profile、按计算特性解读NCU、检查后端回退、同一ABI/编译标志、Review比以往更重要
</div>
</div>

---

SGLang的开发正在超越孤立的代码变更。同一个仓库现在覆盖了LLM服务、分布式运行时、GPU内核、扩散模型管线、模型特化执行路径和生产事件处理。过去，许多这些工作流依赖于单个开发者的记忆：如何启动某个模型、如何读取profile trace、调试CUDA crash时先加哪条日志、performance PR应该包含哪些基准测试。随着agent工具日趋成熟，这种经验可以被转化为可执行的SKILL.md文件、脚本、基准测试契约和review循环。

综合来看，这些努力指向同一个方向：agent的价值来自程序化的工程知识，包括可执行的步骤、可复现的实验和可审查的证据。

<strong style="font-size:17px;color:#1a6ba0;">1. TL;DR</strong>

围绕SGLang agent开发，当agent能够沿着定义良好的工作流持续前进时，它们最有用。基准测试、profiling、kernel API日志记录、添加diffusion管线、生产事件回放和SOTA循环都可以被编码为skill。

一个SGLang skill就是一个可执行的开发流程。在 `debug-cuda-crash`、`sglang-diffusion-benchmark-profile` 和 `llm-torch-profiler-analysis` 中，重要的内容是预检查、硬失败条件、产物契约、复现命令和结果格式。

Profile证据是性能工作的核心。SGLang profiler skill生成固定的kernel表、overlap机会表和融合模式表。KDA-Pilot将其扩展为同ABI的基线/候选对比、真实工作负载、正确性门槛、NCU证据和按shape分类的结果。

长周期优化正在向Loop Engineering演进。SGLang SOTA Performance Loop将「追逐SOTA」拆解为公平基准测试、差距判断、profiling、打补丁和重新验证。Humanize/RLCR加入外部审查环节，而Codex Goal可以用更低的编排开销运行同样的循环。

Review变得更加重要。Agent可以运行更多实验，但它们也会生成更多看似合理但仍需仔细审查的变更。开发者越来越多地负责定义问题、选择证据、设计工作流，以及判断结果是否准备好进入生产路径。

<strong style="font-size:17px;color:#1a6ba0;">2. 为什么SGLang适合Agent辅助开发</strong>

SGLang是一个面向LLM和多模态模型的高性能推理框架。随着模型家族和硬件路径的扩展，开发中反复出现一些问题，比如 `torch.compile` 兼容性、不同模型的特化路径、性能回归排查等。这些问题天然适合agent处理：启动服务、修复工作负载、收集trace、分类profile行、添加测试和记录实验结果都有清晰的输入输出，适合脚本化和重复执行。

开发者需要定义边界：相同的基准测试设置、相同的profile解读规则、相同的精度门槛，以及agent应停止改代码的条件。

<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
本文讨论的agent是一个受工程工作流约束的执行器。重复的SGLang开发流程可以捕获为skill，让agent处理重复执行、证据收集和状态追踪。开发者负责定义目标、评判证据以及审查变更是否应该合入真正的serving路径。
</div>
</div>

<strong style="font-size:17px;color:#1a6ba0;">3. 从Prompt工程到Skill：协议与示例</strong>

在SGLang框架中，一个有用的skill至少应回答以下五个问题：

<table style="text-align:left;border-collapse:collapse;width:100%;margin:12px 0;">
  <thead>
    <tr>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">问题</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">Skill应捕获的内容</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">何时使用</td>
      <td style="border:1px solid #ddd;padding:8px;">触发场景、支持的模型、支持的硬件、硬停条件</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">如何开始</td>
      <td style="border:1px solid #ddd;padding:8px;">预检查、环境变量、仓库状态、依赖检查、模型配置</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">如何验证</td>
      <td style="border:1px solid #ddd;padding:8px;">基准测试命令、profile命令、测试入口、精度门槛</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">如何决策</td>
      <td style="border:1px solid #ddd;padding:8px;">输出表、失败模式、优先级、风险类别、回退条件</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">如何交付</td>
      <td style="border:1px solid #ddd;padding:8px;">产物目录、结果schema、PR描述、复现命令、review要求</td>
    </tr>
  </tbody>
</table>

SGLang agent相关skill覆盖不同的层次。有些接近源码变更（如调试、测试、添加diffusion模型、基准测试和profile工作流），另一些面向跨框架基准测试、容量规划、计算模拟、生产事件分类、PR优化知识、SGLang人工风格review，以及更高层次的Humanize/RLCR工作流。

<strong style="font-size:16px;color:#1a6ba0;">3.1当前Skill栈</strong>

当前常用的SGLang agent相关skill分为以下层次：

<table style="text-align:left;border-collapse:collapse;width:100%;margin:12px 0;">
  <thead>
    <tr>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">层次</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">代表性Skill / 项目</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">解决的问题</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">CUDA crash</td>
      <td style="border:1px solid #ddd;padding:8px;">debug-cuda-crash</td>
      <td style="border:1px solid #ddd;padding:8px;">记录自定义op/kernel API边界的输入、异常和dump，将临时崩溃转化为可离线分析的样本</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">LLM基准测试</td>
      <td style="border:1px solid #ddd;padding:8px;">llm-serving-auto-benchmark</td>
      <td style="border:1px solid #ddd;padding:8px;">在SGLang和其他OpenAI兼容推理栈之间运行公平、有界、可恢复的服务基准测试搜索</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">容量规划</td>
      <td style="border:1px solid #ddd;padding:8px;">llm-serving-capacity-planner</td>
      <td style="border:1px solid #ddd;padding:8px;">解析启动日志，解释权重内存、KV cache预算、CUDA graph开销、请求容量和OOM压力</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Trace分类</td>
      <td style="border:1px solid #ddd;padding:8px;">llm-torch-profiler-analysis</td>
      <td style="border:1px solid #ddd;padding:8px;">生成固定的kernel、overlap机会、融合模式三张表，将kernel映射回Python源码；同一工作流也存在于AI-Infra中供跨框架使用</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">流水线/层分析</td>
      <td style="border:1px solid #ddd;padding:8px;">llm-pipeline-analysis</td>
      <td style="border:1px solid #ddd;padding:8px;">将torch profiler trace切片为前向传递、层和kernel流，定位稳定传递、瓶颈层类型和Perfetto时间范围</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">模型计算模拟</td>
      <td style="border:1px solid #ddd;padding:8px;">model-compute-simulation</td>
      <td style="border:1px solid #ddd;padding:8px;">为LLM构建算子级计算模板，估算tensor形状、FLOPs、MFU、kernel-to-op映射和并行化假设场景</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Diffusion基准/profile</td>
      <td style="border:1px solid #ddd;padding:8px;">sglang-diffusion-benchmark-profile</td>
      <td style="border:1px solid #ddd;padding:8px;">捕获去噪延迟、性能dump和torch profiler trace，同时检查执行是否真的使用了原生SGLang diffusion后端</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">添加diffusion模型</td>
      <td style="border:1px solid #ddd;padding:8px;">sglang-diffusion-add-model</td>
      <td style="border:1px solid #ddd;padding:8px;">从Diffusers/reference管线向SGLang pipeline/stage/model/config结构中添加新的diffusion模型</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Diffusion性能调优</td>
      <td style="border:1px solid #ddd;padding:8px;">sglang-diffusion-performance</td>
      <td style="border:1px solid #ddd;padding:8px;">选择torch.compile、预热、SP/CFG并行化、offload、注意力后端和量化等性能设置</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">生产事件分类</td>
      <td style="border:1px solid #ddd;padding:8px;">sglang-prod-incident-triage</td>
      <td style="border:1px solid #ddd;padding:8px;">收集live-server数据、保存失败请求、回放，然后路由到有针对性的crash/hang/profile工具</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">SGLang审查 / PR历史</td>
      <td style="border:1px solid #ddd;padding:8px;">sglang-humanize-review和model-pr-history-knowledge</td>
      <td style="border:1px solid #ddd;padding:8px;">对照真实维护者讨论模式审查SGLang patch，保持PR驱动的模型演化历史靠近变更的源码</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">SGLang SOTA性能循环 (Loop Engineering)</td>
      <td style="border:1px solid #ddd;padding:8px;">sglang-sota-humanize-loop</td>
      <td style="border:1px solid #ddd;padding:8px;">首先公平对比SGLang与目标开源推理框架，然后将差距判断、profiling、打补丁和重新验证放入Humanize/RLCR循环</td>
    </tr>
  </tbody>
</table>

这些条目将容易被遗漏的步骤转化为可执行的协议，使工作流可以运行、恢复和被审查。

<strong style="font-size:16px;color:#1a6ba0;">3.2近期优化与工作流示例</strong>

以下案例来自最近合并的SGLang PR。表格展示了完整的工程路径：基准测试、profiling、定位、代码变更、测试和重新验证。

<table style="text-align:left;border-collapse:collapse;width:100%;margin:12px 0;">
  <thead>
    <tr>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">案例</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">结果</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">关键点</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Router long-context tokenization去重，PR #28744</td>
      <td style="border:1px solid #ddd;padding:8px;">DeepSeek-V4-Flash上60k/125k token请求的idle TTFT下降约29%/41%；60k token负载下TTFT下降34%-49%</td>
      <td style="border:1px solid #ddd;padding:8px;">Agent处理了cache-aware routing、chat-encoder对齐、engine侧的input_ids回退和proxy body构造，避免了router和engine中的重复tokenization</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Qwen3-Next FlashInfer allreduce融合，PR #22664</td>
      <td style="border:1px solid #ddd;padding:8px;">H100 TP=4上吞吐从5.49 req/s提升到9.41 req/s（+71.4%）；平均TTFT从456.24ms降到167.54ms</td>
      <td style="border:1px solid #ddd;padding:8px;">Profile驱动的LLM集体通信优化：未融合的跨设备reduce主导了prefill，融合后的allreduce路径通过了MMLU/GSM8K精度检查</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Cohere2Moe NVFP4 fused-MoE路径，PR #27401</td>
      <td style="border:1px solid #ddd;padding:8px;">1x B300上chat吞吐 +26%，summarization +21%，超越另一开源推理框架 +4.1%/+6.8%</td>
      <td style="border:1px solid #ddd;padding:8px;">补全了路由语义，使现有的flashinfer_trtllm NVFP4 fused-MoE kernel能在真实模型路径中正确使用，通过GSM8K/MMLU检查</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Kimi Delta Attention CuteDSL prefill kernel on SM100，PR #27488</td>
      <td style="border:1px solid #ddd;padding:8px;">B200上Delta Attention prefill比Triton快1.08x-1.52x；GSM8K从0.915提升到0.920，新增了针对真实gate幅度的回归测试</td>
      <td style="border:1px solid #ddd;padding:8px;">这个kernel任务覆盖了模型的gate分布、数值溢出、host开销、真实模型精度和单元测试</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">Spectral Progressive Diffusion，PR #27524</td>
      <td style="border:1px solid #ddd;padding:8px;">FLUX.1/FLUX.2/Z-Image/Wan/Qwen-Image去噪加速分别达到1.63x/1.77x/2.07x/2.32x/1.6x</td>
      <td style="border:1px solid #ddd;padding:8px;">Diffusion端的系统优化：早期去噪在较低潜空间分辨率运行，然后GPU DCT上采样在高频细节重要时恢复全分辨率</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">LTX-2 VAE decode channels-last-3d，PR #27431</td>
      <td style="border:1px solid #ddd;padding:8px;">LTX-2 decode阶段从5.41s提升到3.84s（1.41x）；峰值保留内存从71.81 GiB降到62.12 GiB（节省约9.7 GiB）</td>
      <td style="border:1px solid #ddd;padding:8px;">Profile指向Conv3d和layout转换，修复在causal padding中保持内存格式，连接loader策略到单GPU LTX-2</td>
    </tr>
  </tbody>
</table>

在这些示例中，agent主要通过执行工作流来贡献：运行基准测试、读取profile、定位Python源码、更改代码、添加测试、重新验证和准备PR描述。没有skill，许多步骤依赖人工提醒。一旦编码为skill，工作流就变得很容易重复。

<strong style="font-size:17px;color:#1a6ba0;">4. Profiling、Review和Loop Engineering</strong>

SGLang性能工作中的常见错误是只看总运行时间，或者在Perfetto中随便看几分钟就凭直觉认为某些操作「应该被融合」。对agent来说这个风险更大，因为它容易把一个视觉上很热的kernel误认为真正的瓶颈。

实践中通常同时使用两个profiler skill。`llm-torch-profiler-analysis` 处理第一层trace分类，将全局profile转化为三个固定表：
- Kernel Table：哪个阶段、哪个kernel占多少GPU时间，映射到哪行Python源码
- Overlap Opportunity Table：是否有overlap机会
- Fuse Pattern Table：是否有可参考的现有融合/重叠路径

如果SGLang落后于另一推理框架，profiler表应在任何代码变更开始前解释这个差距。

下一步是 `llm-pipeline-analysis`。知道了全局热点后，还需要知道它们属于哪个前向传递、层类型和kernel流。这个skill读取Chrome trace JSON和模型的 `config.json`，用layer-boundary anchor kernel将trace分割为前向传递和层，然后生成多张分析表：
- 前向传递摘要
- 每层时间线
- 层聚类统计
- 压缩比
- 计算流表

Profile分析因此成为两步过程：第一步避免凭直觉选方向，第二步避免只盯着一个全局热kernel而忽略模型结构中层类型的差异。

<strong style="font-size:16px;color:#1a6ba0;">4.1 Humanize/RLCR：在循环中加入外部审查</strong>

Humanize解决长运行任务中的状态和审查问题。一个高风险的SGLang性能任务通常不会在一次实现中完成：它可能经历多轮基准测试、profiling、打补丁、回退、改变方向和重新验证。Humanize将这个流程分为两个阶段：`humanize-gen-plan` 生成 `plan.md`，然后 `humanize-rlcr` 执行并审查每一轮。每一轮的prompt保存在 `.humanize/rlcr/<timestamp>/round-<N>-prompt.md`。

这个机制为SGLang SOTA Performance Loop提供了执行和审查基础。Claude Code运行基准测试、读取profile、修改SGLang代码和重新验证。Codex Review在每轮结束时检查证据、状态和风险。这对将成为PR、影响serving正确性或需要多天多轮实验的任务来说是好的选择。

实践中命令顺序应是明确的，这样agent不会直接跳入实现：

1. 在 `artifact_root/draft.md` 写下任务草稿
2. 运行 `humanize-gen-plan` 生成 `artifact_root/plan.md`
3. 从 `artifact_root/plan.md` 启动 `humanize-rlcr`
4. 所有决策、摘要和审查状态都保存在本地Humanize workspace中

<strong style="font-size:16px;color:#1a6ba0;">4.2 SGLang SOTA Performance Loop（Loop Engineering）</strong>

单个skill可以稳定一个任务。但经过十几轮实验后，另一个问题出现了：哪个候选项最好、哪些方向已经失败、之前的NCU报告说明了什么、基准测试是否仍然匹配基线、以及何时停止。这些状态不能仅存在于聊天上下文中。

SGLang SOTA Performance Loop是一个基于Humanize/RLCR构建的Loop Engineering工作流。在这里SOTA意味着在固定实验条件下的最佳可复现结果：相同的模型、硬件、GPU数量、精度、工作负载、SLA、框架commit和服务参数。问题很简单：SGLang能否在这些条件下达到当前最佳可复现结果？

一个完整的SGLang SOTA Performance Loop包含以下阶段（A full SGLang SOTA Performance Loop contains the following stages）：

![](img1.png)
<span style="font-size:12px;color:rgb(153,153,153);">Figure 1：SGLang SOTA Performance Loop。固定公平基准测试首先建立可复现的基线，后续的差距判断、profiling、流水线分析、打补丁和重新验证由Humanize/RLCR循环驱动。</span>

对于 `Qwen/Qwen3-Next-80B-A3B-Instruct-FP8` 在2x B200上这样的目标，循环之所以重要是因为基准测试结果、profile trace、失败的patch和中间结论都需要始终关联到同一组模型、硬件、工作负载和框架commit。如果这类任务被拆成许多独立的prompt，很容易忘记哪个命令产生了哪个结果，或者后面的profile是否还匹配原始的基线。一个有证据和review的循环能在多轮中保持条件一致。

<strong style="font-size:17px;color:#1a6ba0;">5. 基于KDA的CUDA Kernel优化</strong>

超越模型级优化，内核优化有更严峻的扩展问题。没有一个独立于硬件和工作负载的最佳kernel。同一算子可能在H100、H200、B200或B300上偏好不同的实现；不同模型架构暴露不同的tensor形状和布局约束；服务工作负载改变batch size、序列长度、精度格式、wrapper开销、同步行为和回退路径。在实践中，搜索空间是硬件、模型和工作负载定义的笛卡尔积。

这产生了组合优化负担。对每个候选kernel，开发者需要提取代表性生产行、构建同ABI的harness、运行A/B测量、跨shape bucket检查正确性、读取NCU指标、决定某个bucket是否值得专门优化，然后在真实SGLang路径中重新验证。对每个硬件/模型/工作负载组合手工做这件事是昂贵的。这也正是那种重复性、证据密集的工作流：只要人类定义不变量并审查最终路径：agent很擅长的。

但直接让agent写CUDA很容易导致benchmark reward hacking：更改基准测试、使用更轻量的wrapper、启用基线未用的fast math、只优化一种shape、破坏数值语义，或在真实SGLang路径中无收益。

KDA-Pilot的策略是将内核优化分离为独立的任务，让agent不能自由修改整个SGLang仓库。在这个框架下，对于每个候选kernel，开发者需要提取代表性生产行、构建同ABI的harness、运行A/B测量、跨shape bucket检查正确性、读取NCU指标、决定某个bucket是否值得专门优化，然后在真实SGLang路径中重新验证。对每个硬件/模型/工作负载组合手工做这件事是昂贵的。这也正是那种重复性、证据密集的工作流：只要人类定义不变量并审查最终路径：agent很擅长的。

公共KDA-Pilot B200 diffusion摘要当前列出10个被追踪的SGLang kernel任务。大多数行在KDA-Pilot ledger中有稳定的数值B200证据，在提取的生产行上wall-geomean加速比范围从1.1341x到2.7499x。`residual_gate_add` 行显示为1.11x，与已合入上游的LTX-2.3 B200结果一致。

截至2026年6月27日，三个KDA-Pilot衍生的优化已合入SGLang上游：PR #27392（Qwen-Image-2512的B200原生diffusion norm-scale-shift CUDA fast path）、PR #29281（Cosmos3 VAE causal Conv3D cat/pad copy路径）、PR #29361（LTX-2.3 residual-gate update路径）。

<table style="text-align:left;border-collapse:collapse;width:100%;margin:12px 0;">
  <thead>
    <tr>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">上游PR</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">目标路径</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">Kernel级证据</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">模型路径证据</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">#27392</td>
      <td style="border:1px solid #ddd;padding:8px;">Qwen-Image norm-scale-shift</td>
      <td style="border:1px solid #ddd;padding:8px;">目标kernel组profiler attribution提升1.279x</td>
      <td style="border:1px solid #ddd;padding:8px;">1x B200上5轮交错运行，全请求加速1.125x，去噪墙加速1.130x</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">#29281</td>
      <td style="border:1px solid #ddd;padding:8px;">Cosmos3 causal Conv3D cat/pad</td>
      <td style="border:1px solid #ddd;padding:8px;">B200加权kernel组从10.621ms降至5.240ms（2.03x）</td>
      <td style="border:1px solid #ddd;padding:8px;">启用torch.compile后Cosmos3-Nano T2V中位E2E时间从181.521ms降至177.687ms（1.021x）</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">#29361</td>
      <td style="border:1px solid #ddd;padding:8px;">LTX-2.3 residual-gate update</td>
      <td style="border:1px solid #ddd;padding:8px;">大B200 LTX-2.3行比现有Triton路径提升1.108x-1.130x，相邻diffusion行最高达2.587x</td>
      <td style="border:1px solid #ddd;padding:8px;">LTX-2.3 HQ T2V，E2E时间从46644.08ms降至45198.37ms（1.032x）</td>
    </tr>
  </tbody>
</table>

关键结论不是每个独立内核的胜利都能成为大的端到端胜利。而是同样的KDA-Pilot证据包：固定生产行、正确性门槛、同ABI比较、profiler attribution和真实模型检查：可以将内核任务从孤立基准测试推进到可审查的SGLang serving路径。

![](img2.png)
<span style="font-size:12px;color:rgb(153,153,153);">Figure 2：KDA-Pilot B200 diffusion kernel加速比汇总。大多数行报告KDA-Pilot wall-geomean加速比；wall时间包含Python分发、wrapper开销、kernel launch和同步开销，比纯kernel device时间更接近真实调用路径。</span>

<table style="text-align:left;border-collapse:collapse;width:100%;margin:12px 0;">
  <thead>
    <tr>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">内核任务</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">B200证据</th>
      <th style="border:1px solid #ddd;padding:8px;font-weight:bold;">主要优化方向</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">qknorm_rope</td>
      <td style="border:1px solid #ddd;padding:8px;">1.1341x</td>
      <td style="border:1px solid #ddd;padding:8px;">共享RoPE staging、Q/K复用、大行快速路径</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">norm_infer</td>
      <td style="border:1px solid #ddd;padding:8px;">1.3523x</td>
      <td style="border:1px solid #ddd;padding:8px;">Warp-row RMS、tiled persistent RMS、8B/16B vector路径</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">rotary_embedding</td>
      <td style="border:1px solid #ddd;padding:8px;">1.4912x</td>
      <td style="border:1px solid #ddd;padding:8px;">128-bit向量I/O、cos/sin hoisting、LTX2 block匹配</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">cutedsl_norm_tanh_mul_add</td>
      <td style="border:1px solid #ddd;padding:8px;">1.4953x</td>
      <td style="border:1px solid #ddd;padding:8px;">Row-invariant数学hoisting、launch-bounds调优、exact tanh</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">cutedsl_norm_scale_shift</td>
      <td style="border:1px solid #ddd;padding:8px;">1.3201x</td>
      <td style="border:1px solid #ddd;padding:8px;">Operand-class分派、16B/32B向量、two-pass variance</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">fuse_scale_shift</td>
      <td style="border:1px solid #ddd;padding:8px;">2.7499x</td>
      <td style="border:1px solid #ddd;padding:8px;">rowgrid/flatvec/exact-C多路径、cache hint、one-pass归约</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">group_norm_silu</td>
      <td style="border:1px solid #ddd;padding:8px;">2.3118x</td>
      <td style="border:1px solid #ddd;padding:8px;">Split-group stats、channels-last直接路径、大行回退</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">attention_concat_copy</td>
      <td style="border:1px solid #ddd;padding:8px;">1.30x</td>
      <td style="border:1px solid #ddd;padding:8px;">Single-launch区域拷贝、pitched 16B block gather、严格layout/device拒绝</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">causal_conv3d_cat_pad</td>
      <td style="border:1px solid #ddd;padding:8px;">2.06x</td>
      <td style="border:1px solid #ddd;padding:8px;">Flat chunking、16B向量化store、stride-aware回退、bitwise-exact gate</td>
    </tr>
    <tr>
      <td style="border:1px solid #ddd;padding:8px;">residual_gate_add</td>
      <td style="border:1px solid #ddd;padding:8px;">1.11x</td>
      <td style="border:1px solid #ddd;padding:8px;">One-pass CUDA融合、pinned-GPU正确性、SGLang PR #29361 B200 Triton-row重新基准</td>
    </tr>
  </tbody>
</table>

图表和任务表应以实验性视角阅读：它们报告的是kernel任务在提取的生产行上的加速比，不是全模型端到端收益。但它们仍然有用。一旦baseline、工作负载、正确性、profiling和review都被固定，agent可以在真实框架kernel上产生可审查的增量改进。

<strong style="font-size:17px;color:#1a6ba0;">6. 实践规则</strong>

<strong>启动agent之前先定义任务边界。</strong>
「Optimize SGLang」太宽泛。「让SGLang在 `Qwen/Qwen3-Next-80B-A3B-Instruct-FP8` 的2x B200上，在固定 `1000->1000` 和 `8000->1000` 工作负载下匹配另一开源推理框架」才是可执行的目标。

<strong>Fix the benchmark before reading profiles.</strong>
如果工作负载在结果已知后可以改变，agent可能意外地优化了一个更容易的问题。SOTA loop和KDA-Pilot都在打补丁之前固定了工作负载。

<strong>Interpret NCU results according to the kernel's compute characteristics.</strong>
对于内存密集型kernel，关注DRAM/L2吞吐量、load/store效率和memory pipe利用率。对于计算密集型GEMM/attention kernel，关注Tensor Core利用率、SM busy、eligible warps和主要stall原因。对于小延迟密集型kernel，检查launch数量、每kernel时长、同步点和可能的融合机会。单张trace截图不够，下一个代码变更应由具体指标支持。

<strong>Check backend and fallback gates before trusting a profile.</strong>
如果一个LLM运行悄悄切换了attention后端、禁用了CUDA graph、或者走了与基准测试不同的wrapper路径，这个trace就不再描述目标serving路径。diffusion同理：如果日志显示回退到diffusers后端，这个trace不能用作原生SGLang diffusion的证据。这些硬停条件应存在于skill中。

<strong>Kernel optimization must use the same ABI, wrapper, and compile flags.</strong>
候选内核不应悄悄走更轻的路径，`--use_fast_math` 不应只在一侧启用。

<strong>Review matters more than before.</strong>
Agent可以创建更多PR，也可以制造更多看似合理的错误。对SGLang这样的高性能系统的审查需要检查shape、dtype、分布式执行、CUDA graph行为、回退行为、精度、serving API、指标和基准测试设置。

Agent时代的SGLang开发不会将开发者排除在系统之外。更现实的变化是将开发者经验编写进工作流，将重复性执行交给agent，将判断、设计和审查留给人。节省的时间可以投入到更难的性能问题、模型路径和生产稳定性，或回投到改进agent工作流本身。对一个开源推理框架来说，这种基础设施值得持续投资。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这篇博客最吸引人的地方不是他们写了多少skill，而是他们把「工程知识程序化」这件事本身当作一种值得持续投资的基础设施。这跟把prompt写进Slack频道里的做法有本质区别：前者是经验分享，后者是经验封装。<br><br>
值得注意的一点是，博客反复强调agent不会取代开发者，而是会加速「重复执行→证据收集→人的判断」这个循环。但从KDA-Pilot的10个kernel任务中已有3个合入上游来看，agent的有效产出正在从「帮助审查」转向「直接贡献代码」。这中间的边界怎么划：哪些优化交给agent跑、哪些必须人亲自写：可能是未来一年每个高性能系统团队都要面对的决策。<br><br>
另外，六条实践规则中，检查后端回退和固定基准测试这两条其实指向同一个问题：agent很容易收集到错误的数据，然后基于错误数据做出表面合理的决策。这套方法论对任何尝试用agent做系统优化的团队都有参考价值。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/qcIFzXsBalSGpca5fzJKxg" target="_blank" data-linktype="2">Claude Code动态Workflow Vs. SubAgent Vs. Skill</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/aiJs5CC8Gb6qa_xDRNEjTA" target="_blank" data-linktype="2">Dynamic Subagents：用代码编排Agents，告别逐轮工具调用</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/mFuUJ79DRodIK6shVWOgpw" target="_blank" data-linktype="2">OpenAI GPT-5.6: 安全之外新增Prompt Cache断点+两种推理模式; 放弃版本号</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/xP1cEoO_plRpWItxhqeQnQ" target="_blank" data-linktype="2">Agent Harness Engineering：为什么Agent可靠性的天花板不是模型，而是基础</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/o6pnSWW01pahFQelJSbSPA" target="_blank" data-linktype="2">华为「韬定律」全解析：从 τ 常数到4GHz麒麟，一张时间表看清未来十年芯片路线</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/PLNx54PxO1A0oYc47hz99g" target="_blank" data-linktype="2">Anthropic三连：Claude Opus 4.8-更聪明+诚实；CC动态工作流+算力控制</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/Pdjz39WG9SS6IpWWAJ6pPw" target="_blank" data-linktype="2">Claude Opus 4.8击败Opus 4.7、GPT-5.5和Gemini 3.1 P</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/oDZJbvskv_ocNgPUH1DHVA" target="_blank" data-linktype="2">AI暗输出：为何AI价值在GDP统计中失效了</a></span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://www.lmsys.org/blog/2026-07-02-agent-assisted-sglang-development</span>
