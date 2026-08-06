#!/usr/bin/env python3
"""article_data_build.py — Piper: A Programmable Distributed Training System"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

# 与 write-article-data.py 一致的代码块样式
CODE_STYLE = (
    'style="background:#f5f5f5;padding:12px 16px;border-radius:4px;overflow-x:auto;'
    'font-family:Consolas,Monaco,\'Courier New\',monospace;font-size:13px;'
    'line-height:1.5;margin:1em 4px;border-left:4px solid #e0e0e0;"'
)

CODE1 = """python examples/test_harness.py \
  --test-file examples/test_qwen.py \
  --base-schedule examples/base-schedules/pp2_dp2_ep2_custom_order.json \
  --schedule custom --ranks 2 --mbs 4 --viz"""

CODE2 = """PP_TAG = 'PP'
EP_TAG = 'EP'

class AnnotatedMoE(MoE):
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        ...
        # 包裹专家计算
        return piper.annotate(EP_TAG)(x)"""

CODE3 = """[
  {"op": "place", "filter": {"PP": 0}, "devices": [0, 2], "stream": "pp_stream"},
  {"op": "place", "filter": {"PP": 1}, "devices": [1, 3], "stream": "pp_stream"},
]"""

CODE4 = """[
  {"op": "replicate", "filter": {"PP": 0}, "devices": [0, 2], "reduce_stream": "dp_stream"},
  {"op": "replicate", "filter": {"PP": 1}, "devices": [1, 3], "reduce_stream": "dp_stream"},
]"""

CODE5 = """[
  {"op": "shard", "filter": {"PP": 0, "EP": "*"}, "devices": [0, 2], "stream": "ep_stream"},
  {"op": "shard", "filter": {"PP": 1, "EP": "*"}, "devices": [1, 3], "stream": "ep_stream"},
]"""

CODE6 = """{"op": "split", "filter": {}, "dim_name": "MB", "num_microbatches": 2}"""

CODE7 = """[
  {"op": "order", "filters": [
    [{"PP": 0, "MB": 0, "PASS": "F"}],
    [{"PP": 0, "MB": 1, "PASS": "F"}],
    [{"PP": 0, "MB": 0, "PASS": "B"}],
    ...
  ]},
]"""

CODE8 = """python examples/test_harness.py \
  --test-file examples/test_qwen.py \
  --base-schedule examples/base-schedules/pp4_dp2_ep2_v_placement.json \
  --schedule dualpipev --ranks 2 --mbs 4"""

DATA = {
    "summary": [
        {"key": "核心观点", "body": "Piper 将模型放置与 GPU 调度从模型代码和运行时中解耦，让用户可编程地表达分布式训练策略。"},
        {"key": "双抽象", "body": "用轻量模型标注 + 一条调度指令语言，表达、可视化、剖析并运行高性能训练调度。"},
        {"key": "关键结果", "body": "DualPipeV 调度下 Qwen3 1B/9B 吞吐比 1F1B 提升 13%/10%，且支持 PP x ZeRO 组合。"},
    ],

    "lead": [
        "新的分布式训练策略和优化不应要求新的分布式运行时。大型训练作业越来越多地组合流水线、数据、专家并行与 ZeRO 式分片等策略，产生了当前框架无法干净表达的放置与 GPU 调度选择。",
        "今天，研究者和工程师要么构建定制化的一次性系统（性能好但难以扩展），要么使用通用框架（易用但控制力有限）。Piper 是一种用户可控的 PyTorch 分布式训练系统，把模型放置和 GPU 调度从模型代码与运行时实现中解耦。借助轻量级模型标注和一个小型调度语言，用户就能表达、可视化、剖析并运行诸如 DualPipe 式流水线与专家并行重叠这类高性能训练调度。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "组合的并行维度带来复杂的通信模式",
            "paras": [
                "大模型训练通常组合多个并行维度：**数据并行（DP）** 复制模型状态，在每个副本上运行不同数据，并通过集合通信同步梯度。**流水线并行（PP）** 把层切分为阶段，用点对点通信在阶段间传递激活和梯度，数据批次被拆成微批次以保持流水线繁忙。**专家并行（EP）** 切分混合专家（MoE）层中的专家，并通过集合通信在专家子集间路由 token。**张量并行（TP）** 切分单个张量算子（如矩阵乘法），用集合通信拼装部分结果。**ZeRO 式分片** 跨 DP 秩削减冗余的优化器、梯度和参数状态，通过分片模型状态并引入额外的集合通信来收集和同步分片。",
                "组合并行策略并非「一刀切」，正确选择取决于模型架构、内存约束和网络拓扑。Figure 1 展示了一个 MoE 模型：跨层使用流水线并行，层内使用数据/专家并行。",
            ],
            "fig_after": {
                "1": [{"src": "fig01.jpg", "caption": "Figure 1：一个用于混合专家模型的 PP x EP x DP 放置。流水线并行把层分布在阶段间、专家并行切分专家 MLP、数据并行复制注意力等非专家组件。"}],
            },
        },
        {
            "type": "h2",
            "title": "调度张量算子到每张 GPU 上很难",
            "paras": [
                "组合多个维度会产生复杂的通信模式和较高的通信开销。对 Figure 1 的放置，单次训练步需要协调向前向后流经模型的 PP 微批次、关键路径上的 EP token 路由、以及 DP 梯度同步。因此最大化训练吞吐需要仔细调度每张 GPU 上的张量算子，以隐藏通信延迟、避免气泡（GPU 空闲时间）。",
            ],
            "fig_after": {
            },
        },
        {
            "type": "h3",
            "title": "MoE 训练与 DualPipe 调度",
            "paras": [
                "MoE 训练特别能说明对 GPU 调度细粒度控制的需求：EP 在专家计算周围引入了关键路径上的全互联（A2A）集合通信。DeepSeek-V3 报告在他们设置中，仅 token 路由就产生了约 1:1 的计算-通信比（专家分布在慢速机间链路上）。为隐藏该延迟，他们引入了 DualPipe 调度，将专家计算与来自不同流水线并行微批次的集合通信重叠。Figure 2 展示了一种 DualPipe 调度变体，并用高亮标出重叠的前向-后向微批次对。",
                "当 DP 与 EP 组合、在反向传播中加入集合全规约（AR）通信时，调度算子到 GPU 上并不简单。Figure 3 展示了不同的 GPU 调度选择，其中流代表 GPU 上的并行度。最佳选择取决于内核运行时间、派发顺序和关键路径依赖。",
                "把 A2A 和 AR 放在不同的流上（a）可让它们并发执行，但存在争抢网络带宽的风险；放在同一流上（b）通过串行化集合通信避免网络干扰，但可能延迟通信；把 AR 拆成更细粒度单元（c）可减少干扰（参数分桶是常见策略），但很难预测对训练吞吐的整体影响，因为拆分可能降低通信效率。",
            ],
            "fig_after": {
                "0": [{"src": "fig02.jpg", "caption": "Figure 2：2 路 PP、4 个微批次的 DualPipeV 调度。数字是微批次 ID，加粗单元是重叠的前向-后向微批次对。"}],
                "1": [{"src": "fig03.jpg", "caption": "Figure 3：在重叠微批次对中，DP all-reduce 和 EP all-to-all 的流调度选择。最佳选择取决于内核运行时间、派发顺序和关键路径依赖。"}],
            },
        },
        {
            "type": "h3",
            "title": "现有框架的限制",
            "paras": [
                "Megatron、DeepSpeed、TorchTitan 等现有通用训练框架不暴露底层调度选择。例如 TorchTitan 把不同并行维度隔离实现，并在不同流上急切派发不同维度的通信算子，实践中只支持选项（a）。因此试验（b）或（c）这类选择往往需要侵入式运行时改动——因为当前框架缺乏一个灵活调度跨 GPU 和 GPU 内的通信/计算算子的中央抽象。",
                "Piper 的关键思想是把模型放置和调度选择从模型实现与运行时中解耦，建立抽象来暴露对设备间模型放置、流水线调度以及设备内调度的控制。",
            ],
        },
        {
            "type": "h2",
            "title": "Piper 一览",
            "paras": [
                "Piper 有两个用户输入：一是**带标注的 PyTorch 模型**——标准模型代码，附轻量标签以标记可调度区域（如流水线阶段和 MoE 专家）；二是一段**调度指令程序**——告诉 Piper 编译器如何对可调度区域进行切分、复制、排序和重叠。",
                "Piper 编译器用 TorchDynamo 追踪模型，提取标注区域作为可调度模型组件，并在分布式训练中间表示（IR）上以图重写方式应用调度指令。该 IR 是一个全局训练 DAG，显式编码计算、通信、数据依赖、时序依赖、设备放置和逻辑流分配。",
                "Piper 运行时随后把这个全局 DAG 分解为每个设备的执行计划，并在 Ray worker 上运行。每个 worker 管理局部 CUDA 流、通信器、模型状态缓冲和中间张量。",
            ],
            "fig_after": {
                "2": [{"src": "fig04.jpg", "caption": "Figure 4：Piper 架构。用户提供带标注的模型和调度；Piper 将其编译成全局训练 DAG，并用分布式运行时执行每个 worker 的子 DAG。"}],
            },
        },
        {
            "type": "h2",
            "title": "用 DualPipe 式调度在 Piper 中训练高性能 MoE",
            "paras": [
                "下面以 PP x DP x EP 放置加上协调的 DualPipe 式训练调度，走一遍在 Piper 中分布一个 MoE 模型的示例。按仓库安装说明准备后，可在仓库根目录用如下命令运行示例：",
                f'<pre {CODE_STYLE}><code>{CODE1}</code></pre>',
            ],
        },
        {
            "type": "h3",
            "title": "标注一个 Qwen3 MoE 模型",
            "paras": [
                "Piper 标注用于标识用户调度中要引用的模型区域。对 PP x EP x DP 放置，我们使用两个标签：`PP` 标识流水线阶段，`EP` 标识 MoE 层内的专家 MLP。专家标注出现在 AnnotatedMoE 模块内。",
                f'<pre {CODE_STYLE}><code>{CODE2}</code></pre>',
                "这段代码用 `piper.annotate(EP_TAG)` 包裹专家计算，创建一个命名区域，调度可通过按 EP 标签过滤来匹配该区域。例如过滤器 `{'EP': 0}` 匹配模型中第一个 EP 区域，`{'EP': *}` 匹配所有 EP 区域，`{'EP': -}` 匹配所有非 EP 区域。",
                "流水线标注出现在 AnnotatedQwen3TransformerBlock 模块内，把 transformer 层划分为 num_stages 个连续区间，每段用 `piper.annotate(PP_TAG)` 包裹。因此同一份模型代码可用不同 PP 度追踪，Piper 会按数据流顺序自动分配阶段索引；每个标注区域成为一个可调度的流水线块。",
                "这些标注是 torch.fx 追踪期间附加的元数据：Piper 借助 TorchDynamo 提取带标注的 PyTorch 算子图作为 fx.Graph，编译器再把图按标注区域分解为子图——这些是系统中最小的可调度单元。接下来我们看用户调度程序如何指示编译器切分、复制和重叠这些标注区域以构建高性能训练计划。",
            ],
        },
        {
            "type": "h3",
            "title": "调度 DualPipe 式 PP x DP x EP 模型放置",
            "paras": [
                "第二个用户输入是由指令组成的调度，指令告诉编译器如何切分、复制和重叠标注区域；每条指令内部编码一次对 IR 表示的 DAG 重写。下面是从小示例调度中抽取的指令片段，我们直接解析 JSON 来解释接口，实际中这些指令可由调度构建器生成。",
                "首先用 `place` 指令设置流水线阶段：数据并行度为 2 时，阶段 0 运行在设备 0 和 2，阶段 1 运行在设备 1 和 3。",
                f'<pre {CODE_STYLE}><code>{CODE3}</code></pre>',
                "当编译器看到跨设备数据依赖（如前向中阶段 0→1、反向中阶段 1→0）时，会向 IR DAG 加入点对点 send/recv 通信节点，并关联到逻辑流 pp_stream。逻辑流即 GPU 流：一个按序执行操作的工作队列。Piper 用逻辑流标识「彼此应串行、但在依赖和硬件资源允许时可能与其他逻辑流上的操作重叠」的类操作。",
            ],
        },
        {
            "type": "h3",
            "title": "replicate 与 shard 指令",
            "paras": [
                "其次用 `replicate` 指令告诉 Piper 同步每个流水线阶段两个副本之间的梯度：Piper 在反向传播后加入集合通信节点来同步复制区域的梯度，并把它们关联到逻辑流 dp_stream。",
                f'<pre {CODE_STYLE}><code>{CODE4}</code></pre>',
                "`replicate` 有几个可选参数：`bucket_size` 通过把参数装进 bucket_size-MB 的分组来控制通信粒度——更小的桶可能暴露更多重叠或减少干扰，但也可能降低通信效率。`shard_grads` 对复制区域施加 ZeRO-1 梯度分片。`shard_params` 施加 ZeRO-2 参数分片，这要求在前向/反向算前收集参数分片。`gather_stream` 允许指定用于参数分片相关收集集合通信的独立流，从而更细粒度地控制哪些集合通信被重叠或串行化。",
                "再次用 `shard` 指令把每阶段内的 MoE 专家区域切分到该阶段的设备上，并在独立的流上路由专家通信：过滤器 `{'PP': 0, 'EP': '*'}` 匹配流水线阶段 0 内所有带专家标注的块，Piper 为这些区域加入集合通信并关联到逻辑流 ep_stream。",
                f'<pre {CODE_STYLE}><code>{CODE5}</code></pre>',
                "逻辑流是用户控制哪些类通信算子可重叠、哪些必须串行化的方式：用户不手动协调 CUDA 流，Piper 把逻辑流映射到物理流，仅在数据或时序依赖要求时插入同步。通过通信分桶和流分配，用户可以试验 Figure 3 中那样的多种底层调度策略。",
                "至此我们看到了 place、replicate、shard 指令如何描述计算和通信发生在哪里。对 DualPipe 式调度，还需要描述微批次数据如何流经流水线、以及它们如何重叠。",
            ],
        },
        {
            "type": "h3",
            "title": "调度 DualPipe 式流水线调度",
            "paras": [
                "Piper 用 `split` 和 `order` 指令暴露对流水线调度的控制。首先用 `split` 把每个训练步拆成独立调度的微批次：空过滤器匹配整个训练 DAG，Piper 将匹配的 DAG 复制 num_microbatches 次，并把副本标记为 MB=0、MB=1 等等。",
                f'<pre {CODE_STYLE}><code>{CODE6}</code></pre>',
                "`order` 加入时序依赖。Piper 提供 PASS 标签，支持 F（forward 前向）、B（backward 反向）、BI（backward for inputs 输入反向）、BW（backward for weights 权重反向）来指代训练 DAG 的不同部分——输入反向 vs 权重反向实现了 ZeroBubble 式反向分解。",
                f'<pre {CODE_STYLE}><code>{CODE7}</code></pre>',
                "关键的双 Pipe 式构造是嵌套过滤器的出现：它告诉 Piper 可以交织多个子图以启用设备内重叠。例如阶段 1 的 order 指令中第二个过滤器元素表示微批次 1 前向和微批次 0 反向可以交织。",
                "这给了用户对调度结构的控制，同时把机械的交织决策留给系统：用户说明哪些子 DAG 可以重叠，Piper 决定如何在该可重叠区域内交织通信和计算。这由一个编译器 pass 实现，它为每个逻辑流决定一个全序：Piper 在各流上对计算和通信算子排序，以促进重叠、避免气泡。",
            ],
        },
        {
            "type": "h3",
            "title": "可视化调度",
            "paras": [
                "Piper 提供多种可视化分布式训练调度的工具。第一种是排序指令的时间表示，类似于典型流水线调度可视化，可帮助从高层识别意外的流水线气泡（白框）。示例中的简单流水线调度输出如下可视化：",
            ],
            "fig_after": {
                "0": [{"src": "fig05.png", "caption": "Figure 5：2 路 PP、2 个微批次、带重叠前向-后向微批次对的简单流水线调度。"}],
            },
        },
        {
            "type": "h3",
            "title": "DAG IR 可视化",
            "paras": [
                "第二种工具是 DAG IR 可视化。应用调度指令并为每个逻辑流解析全序后，Piper 生成每张 GPU 局部训练 DAG 的可视化，帮助识别算子将如何在 GPU 上重叠。",
            ],
            "fig_after": {
                "0": [{"src": "fig06.png", "caption": "Figure 6：重叠前向-后向微批次对的 DAG IR 片段。"}],
            },
        },
        {
            "type": "h3",
            "title": "解析 DAG IR 可视化",
            "paras": [
                "这是我们示例中 PP rank 1（GPU 1 和 3）训练 DAG 的片段，展示微批次 0 反向与微批次 1 前向重叠。数据依赖用实线表示，时序依赖用虚线表示。",
                "拓扑序（由 topo=x 标识）决定运行时派发顺序。Piper 用时序依赖约束每个逻辑流的全序来强制重叠（例如 ep_stream 的通信都有唯一拓扑索引，dp_stream 同理）。运行时的调度启发式通过「SEND > 其他节点 > RECV」的优先级排序，跨流消解模糊的拓扑排序，以避免点对点通信干扰。",
                "最后一种可视化工具是自定义 PyTorch profiler 支持，把每个 SPMD 组内所有 PP 秩的 profile 合并，并标注与每个 IR 节点关联的 GPU 内核。Figure 7 展示了示例中 PP rank 1 重叠前向-后向微批次的 profiler 轨迹：EP 流上的 all-to-all 内核和 DP 流上的 all-reduce 内核都与计算完全重叠。",
            ],
            "fig_after": {
                "2": [{"src": "fig07.jpg", "caption": "Figure 7：重叠前向-后向微批次对的 Profile。EP 和 DP 集合通信被完全隐藏。"}],
            },
        },
        {
            "type": "h3",
            "title": "用调度构建器生成指令",
            "paras": [
                "实际上我们不期望用户手写完整 JSON 调度——对于高 PP 度和多微批次的复杂流水线调度，JSON 会很冗长。我们设想用户编写调度构建器：接受一些参数（如带模型放置指令的基础调度、PP 度、微批次数量），输出带完整 order 指令的 JSON。",
                "调度构建器是输出 Piper 小型指令语言的普通 Python 函数。我们为 1F1B、interleaved 1F1B、ZeroBubble 和 DualPipeV 流水线调度提供了构建器。我们希望研究者实现新的调度构建器来尝试新的设备内外并行策略；流水线调度可视化器将帮助可视化调试。Piper 也有安全护栏，要求 order 指令尊重模型的数据流和设备放置。",
                "走一遍 DualPipeV 构建器的高层逻辑：n_ranks 是物理 PP 秩数，n_mbs 是微批次数量。对每个物理秩，构建器分配两个虚拟阶段，编码 V 型放置（每个秩从模型前端拥有一个阶段、从后端拥有一个阶段）。构建器把时间表示为一组槽位，每个槽位在调度允许重叠时可放两个操作；它遍历 DualPipeV 阶段：前向预热、填充第二个虚拟阶段、主重叠前向/反向对、冷却反向、拆分权重反向清理。返回前，`_order_directive_from_slots` 把槽位数组降到 JSON order 格式。",
            ],
        },
        {
            "type": "h3",
            "title": "运行走查示例",
            "paras": [
                "仓库中有一个更完整的 DualPipe 式调度示例。从 Piper 仓库根目录运行：",
                f'<pre {CODE_STYLE}><code>{CODE8}</code></pre>',
                "该命令从 V 放置基础调度出发，为 2 个流水线秩和 4 个微批次生成 DualPipeV order 指令，在该调度上运行 Qwen 模型，并把生成的调度、调度可视化、DAG 可视化、吞吐/内存统计写入 out/<timestamp>/。要收集 profiler 轨迹，追加 `--pytorch-profiler --pytorch-profiler-iters 3`。",
            ],
        },
        {
            "type": "h2",
            "title": "评估亮点",
            "paras": [
                "我们把 Piper 与 Megatron、DeepSpeed、TorchTitan 对比，回答三个评估问题：① Piper 在常用支持的策略上是否与现有系统表现相当？② 在策略灵活性和性能上，Piper 提供哪些优势？③ Piper 的可扩展性如何？下面重点展示覆盖问题 ② 的几个结果，完整评估见论文。",
            ],
        },
        {
            "type": "h3",
            "title": "PP x EP 与 DualPipeV",
            "paras": [
                "我们评估基线系统与 Piper 对 DualPipe 式调度的支持。TorchTitan 是唯一支持全互联重叠的基线。在 Qwen3 1B 上，Piper-DualPipeV 相比 Piper-1F1B 吞吐提升 13%，而同样设置下 TorchTitan-DualPipeV 相比其 1F1B 仅提升 3%。通过简短的源码探查，我们把 TorchTitan 较小的提升归因于前向/反向微批次派发线程之间的意外串行化。",
            ],
            "fig_after": {
                "0": [{"src": "fig08.jpg", "caption": "Figure 8：各种流水线调度下 Qwen3 1B 和 Qwen3 9B 的 PP x EP 吞吐。"}],
            },
        },
        {
            "type": "h3",
            "title": "PP x ZeRO",
            "paras": [
                "在 Qwen3 9B 上，TorchTitan 在所评估配置中内存溢出；Piper-DualPipeV 相比 Piper 的 interleaved 1F1B 调度吞吐提升 10%，相比 Megatron 的 interleaved 1F1B 提升 6%。Megatron 不支持 DualPipeV，其 interleaved 调度是最接近的基线。除了重叠 EP 通信，我们还计划通过集成 Megatron 的优化内核进一步提升性能。",
                "我们评估基线系统与 Piper 对流水线并行组合 ZeRO 分片策略的支持。回顾 ZeRO 内存优化——逐级的模型状态分片：ZeRO-1 分片优化器状态，ZeRO-2 额外分片梯度，ZeRO-3 额外分片参数。ZeRO 级别越高内存节省越好，但通信开销也越大，因为模型状态必须在正确时点物化和分片。",
                "Megatron、DeepSpeed、TorchTitan 都没有完全支持流水线并行组合 ZeRO-2/3。TorchTitan 提供有限支持：我们发现在所有微批次之间模型状态没有被重新分片，因此内存节省远小于预期。Figure 9 展示了 Piper 通过正确编码 ZeRO-2/3 分片语义，支持大得多的批次规模。",
            ],
            "fig_after": {
                "2": [{"src": "fig09.jpg", "caption": "Figure 9：Qwen3 9B 上 PP x ZeRO-2 和 PP x ZeRO-3 的峰值内存。"}],
            },
        },
    ],

    "conclusion": [
        "Piper 建立在一个简单前提之上：新的分布式训练策略不应要求新的分布式运行时。通过把模型放置和 GPU 调度从模型代码、运行时实现中分离，Piper 提供了一种简洁方式来表达原本需要侵入式框架改动的调度。",
        "对正在设计新流水线调度、探索如何重叠通信、或尝试组合当前框架无法干净支持的并行维度的人，Piper 提供表达、可视化、剖析和快速迭代的路径。我们期待 Piper 的调度接口也能成为未来自动化与智能调度方法的有用目标。",
    ],

    "reference_url": "https://syfi.cs.washington.edu/blog/2026-06-05-piper/",
    "title": "Piper：一种可编程的分布式训练系统",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
