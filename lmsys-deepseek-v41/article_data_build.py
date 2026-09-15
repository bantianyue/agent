#!/usr/bin/env python3
"""article_data_build.py — lmsys-deepseek-v41
来源: https://www.lmsys.org/blog/2026-09-10-deepseek-v41
写完后: python write-article-data.py .  ->  python render-article.py .
"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "核心结论", "body": "模型发布当天，SGLang 与 Miles 跑通了 DeepSeek-V4.1 的推理与 RL 训练；整套优化的地基是压缩 KV 与检索选择在层间共享。"},
        {"key": "关键数据", "body": "Engram 表卸载到主机内存后 KV 缓存容量提升 36%；解码侧有界重放让 prefill 吞吐在 8x H200 上提升 1.56 倍、4x GB300 上提升 1.37 倍。"},
        {"key": "工程要点", "body": "有界重放是近似算法，AIME 2026 实测 pass@1 与全量 prefill 持平（各 453/480），能力边界与开关限制必须逐场景确认。"},
    ],

    "lead": [
        "DeepSeek-V4.1 发布当天，SGLang 与 Miles 就完成了 Day-0 支持：推理侧打通共享 KV、Engram 主机卸载与 SWA 有界重放，训练侧用 Miles 让 RL 训练和 rollout 共用一批 GPU。",
        "这套适配的难点不在加法，而在共享：压缩 KV、indexer keys 和检索候选要在层间流动，滑窗 KV 却必须逐层独立。有界重放引入了一个近似，换来的回报是缓存容量与 prefill 吞吐：KV 缓存容量提升 36%，8x H200 上 prefill 吞吐提升 1.56 倍。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "1. 架构总览",
            "paras": [
                "DeepSeek-V4.1 引入了若干会直接影响服务栈的架构选择。",
                "**低压缩率与滑窗注意力（SWA）。** 每层为其最近的 128 个位置维护一个 fp8 滑窗缓存，部分源层另外产出 fp4 压缩表示用于长程注意力。除前两层外，每个 query 同时关注本地窗口和最多 512 个由 indexer 选出的压缩位置。第 2 到 19 层使用成对压缩，因此 KV 源层必须在解码步之间跨步保留不完整的成对状态。",
                "压缩 KV 与检索选择在层间共享，详见第 2 节。",
                "**流形超连接（mHC）。** 每个子层通过依赖 token 的混合系数读写四条并行残差流。子层消费前驱产出的系数，下一次系数投影因此可以与当前的注意力或 FFN 计算重叠。",
                "**Engram 记忆。** 第 1 层与第 14 层从两张大型 fp8 表里按哈希后的 token n-gram 检索行，把选中的行门控后写进残差流。每个 step 只读取少量行，所以表的放置位置与查表开销比密集计算更要紧。",
            ],
        },
        {
            "type": "h2",
            "title": "2. 跨层共享与稀疏检索",
            "paras": [
                "**共享 KV 与 indexer keys。** 四个 KV 源层产出压缩 KV 和 indexer keys。消费层直接从最近的 KV 源读取，不必在每个消费层各自存储和生成。窗口 KV 仍然逐层独立。",
                "**共享候选的两级选择。** 第 20 层为每个 query 选出最多 2,048 个「八个位置一块」的块，并始终保留包含最新位置的那一块。它把这些候选发布给后续的 index 源层，同时从所有可达位置里选出自己的 top-512。后续 index 源层把自己的 top-512 限制在这些共享候选内。当所有可达位置都落在 16,384 的位置预算内时，候选过滤不会排除任何位置。",
                "**跨层选择复用。** 八个 index 源层用自己的 query 给 indexer keys 打分，每个 query 选出最多 512 个压缩位置。其余做压缩注意力的层直接复用最近一次选择，不再运行 indexer。",
            ],
            "fig_after": {
                "2": [
                    {"src": "fig01.png", "caption": "图1：各层角色与跨层共享，逐层压缩比、KV 源、候选源、index 源与 Engram 层一览"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "3. Engram 优化",
            "paras": [
                "Engram 是 DeepSeek-V4.1 的核心组件。它的两张 fp8 表共 189 GiB 权重，但每个解码步只读取少量行。SGLang 支持把这些表放在 GPU 或主机内存里。把表按四张 GPU 分片，每张 GPU 的 HBM 存四分之一，每次查表的结果就需要一次 all-reduce 汇总。",
            ],
        },
        {
            "type": "h3",
            "title": "3.1 主机内存布局",
            "paras": [
                "主机卸载把 Engram 表移出 GPU 内存，为 KV 缓存腾出容量。反量化、门控和 value 投影仍然留在 GPU 上。SGLang 支持两种主机布局，通信开销不同。",
                "在 host-sharded 布局里，每个 TP rank 在主机内存持有一个分片，查表仍然要走 all-reduce。在 shared host 布局里，所有 TP rank 访问同一份完整的主机内存副本，每个 rank 各自收集需要的行，从而省掉查表的 all-reduce。",
                "对大型表的随机访问可能受地址转换限制，用大页支撑可以降低这部分开销。在被评测的 GB300 容器里，host-sharded 表使用支持大页的匿名映射，shared 映射则不支持。因此自动布局选择选了 host sharding：保留一次 all-reduce，换取更快的主机查表。最佳放置取决于 CPU 与 GPU 之间的互联、大页可用性和具体负载。",
            ],
        },
        {
            "type": "h3",
            "title": "3.2 性能评估",
            "paras": [
                "在 4x GB300（TP4/EP4）上的成对测试里，主机卸载把 KV 缓存容量提升了 36%，解码吞吐和 TTFT 相当。这些运行使用带大页支撑的 host-sharded 表，并保留了查表 all-reduce。28 个贪心探针的补全结果与基线全部一致。",
                "要把 Engram 表放进主机内存，设置 SGLANG_ENABLE_DSV41_ENGRAM_HOST_TABLE=1。",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig02.png", "caption": "图2：TP4 下 Engram 表的放置方式与查表通信路径，GPU 分片与主机分片保留 all-reduce，共享主机布局取消它"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "4. SWA 有界重放",
            "paras": [
                "滑窗 KV 是逐层独立的。为前缀复用把它保留下来会占用缓存容量，而全序列 prefill 算出的窗口状态在后续解码里不会再被直接访问。模型的部署说明提出了有界重放，用来降低这两部分存储与计算成本。",
            ],
        },
        {
            "type": "h3",
            "title": "4.1 编码器侧有界重放",
            "paras": [
                "标准的 prefix reuse 需要缓存的压缩 KV、indexer keys，以及一个有效的滑窗检查点。编码器侧有界重放取消了检查点这一要求：前缀缓存保留压缩 KV 与 indexer keys，每个活跃请求维护一个 128 位置的窗口。",
                "命中缓存时，SGLang 重算缓存前缀的最后 128 个 token 来重建窗口 KV，缓存的压缩 KV 与 indexer keys 保持不变。这相当于用有界重算换取更低的缓存存储，让前缀复用不再依赖匹配位置上存在窗口检查点。",
            ],
        },
        {
            "type": "h3",
            "title": "4.2 解码器侧只算尾部",
            "paras": [
                "第 20 层是最后一个压缩 KV 源。第 21 到 39 层复用它的压缩 KV 与 indexer keys，同时计算自己的窗口 KV。对每个 prefill chunk，SGLang 对所有 token 执行第 0 到 20 层，而第 21 到 39 层只处理每个请求最后最多 128 个 token。",
                "第 0 到 20 层保留全上下文计算。在靠后的层里，本地注意力被限制在保留的尾部，因为该边界之前的窗口 KV 并没有被计算。",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig03.png", "caption": "图3：编码器侧前缀尾部重建与解码器侧只算尾部的 prefill 切分示意"},
                ],
            },
        },
        {
            "type": "h3",
            "title": "4.3 正确性边界与结果",
            "paras": [
                "两种模式都在重建边界处截断本地注意力，所以即使缓存的压缩 KV 不变，重算出的隐状态也可能与全量 prefill 不同。有界重放是一种近似，质量必须靠实测评估。",
                "在每批八个 8K token prompt 的成对测试里，解码器侧重放把 prefill 吞吐在 8x H200 上提升 1.56 倍、在 4x GB300 上提升 1.37 倍。在 4x GB300 上，成对的 AIME 2026 评测测得开启与关闭重放的 pass@1 相同，各自 453/480 个正确样本。",
                "两种模式都是可选项（--enable-encoder-swa-bounded-replay、--enable-decoder-swa-bounded-replay），并且可以组合使用。编码器重放不支持投机解码；解码器只算尾部不支持 input logprobs 与完整的 prompt 隐状态捕获。",
            ],
        },
        {
            "type": "h2",
            "title": "5. 内核与执行优化",
            "paras": [
                "mHC 执行与数值一致性：前驱 pre-mix 让下一个子层的混合系数可以同当前的注意力或 FFN 一起算出来。SGLang 让这部分工作重叠，并把混合统计的归约与 Sinkhorn 迭代融合在一起。归约采用与 batch size 无关的固定顺序，使每个 token 的混合系数在不同 batch 组合下保持一致。对小 batch，HC=4 的 post-mix 会沿隐藏维度切块，暴露出更多并行度。",
                "FP4 索引与 TP 布局：indexer 打分直接从 FP4 缓存读取。indexer heads 在各 TP rank 上复制，因为把这种 MQA 形状的操作分片并不能减少 key 带宽，反而需要一次规模随上下文长度增长的打分 all-reduce。",
                "在保持量化语义前提下的融合：indexer 把 RoPE、FP4 量化、打包或缓存写入合并进融合内核。融合必须保留原始计算的中间舍入与缩放，删掉一次中间写内存并不等于可以删掉它的数值影响。这样做减少了内核启动次数与中间内存流量，同时保持量化序列不变。",
                "低压缩率：压缩器投影使用 BF16 检查点权重，累加与输出使用 FP32。ratio-2 的解码池化被融合进一个内核，把每一对完成的位置合并起来。压缩与索引在输入就绪后也能与注意力准备重叠，在注意力消费它们的输出之前汇合。",
                "单 token 投影与 Engram 融合：分组输出投影对单 token 输入使用专门的 BF16 矩阵向量内核，因为通用矩阵乘法路径在这种情形下 GPU 利用率很低。融合后的 Engram 门控减少了 FP32 临时存储，n-gram 哈希在一个内核里算完。这些优化的目标，正是每个解码步都会重复出现的小投影与稀疏内存操作。",
            ],
        },
        {
            "type": "h2",
            "title": "6. Miles 中的强化学习",
            "paras": [
                "Miles 为 DeepSeek-V4.1 提供了 Megatron-Core 插件，并用 SGLang 做 rollout。训练后端实现了模型的共享注意力状态、mHC 与 Engram 记忆。一个核心目标是最小化同一批响应下 trainer 与 rollout 的 log-probability 差异。",
                "并行与共享状态：后端支持 DP、TP、SP、EP、PP 与 CP。TP 和 SP 切分注意力投影与压缩器分组。流水线边界需要搬运全部四条 mHC 残差流、前驱混合系数，以及下游消费者仍然需要的注意力状态。这些状态也让重算的层可以在本地恢复输入。上下文并行让 query 保持本地，同时跨 rank 收集窗口 KV、压缩 KV 与 indexer keys，以实现全局稀疏检索。",
                "量化感知训练：训练前向复现了服务引擎对压缩隐变量、indexer query 与 key 的 FP4 舍入，以及窗口缓存的 FP8 舍入。直通梯度让这些离散操作可以参与优化。窗口缓存的前向值使用引擎的分页缓存内核，梯度则由一个可微模拟来承载。稀疏注意力与索引复用 DeepSeek-V4 插件的 TileLang 内核，RoPE 与伪量化遵循服务侧公式。",
                "路由重放：Rollout Routing Replay 把采样得到的专家分配喂给 trainer 的 MoE 层，避免路由打平时选中不同的专家路径。indexer top-k 选择重算而不是存储重放：一旦它的量化输入对齐，重放并没有带来可测的一致性收益。这样就不必为每个 rollout token 保留逐层选择结果。",
                "数值一致性：压缩器门控、归一化统计、mHC 混合、Engram 门控与注意力汇累积都使用 FP32，并在操作边界做类型转换。压缩 KV 投影的梯度 all-reduce 同样使用 FP32。确定性的归约与矩阵乘法设置让重复前向可复现，有助于把执行波动与持续存在的 trainer-rollout 差异区分开。",
                "共置训练与 rollout：训练与 rollout 在 16 张 GPU 上交替进行。优化器动量流式写入节点本地 NVMe，rollout 引擎恢复之前先把 trainer 状态换出。每个训练步之后，更新过的 BF16 权重按桶传输。冻结的 FP8 Engram 表使用主机内存支撑，不参与权重同步。后端通过自己的 model bridge 直接加载 Hugging Face 检查点。",
            ],
        },
        {
            "type": "h3",
            "title": "6.1 已验证的训练",
            "paras": [
                "图 4 展示了一次 DAPO 运行的第 0 到 80 步：在 16 张 GB300（TP4、EP16、每步 128 个样本）上，用 DAPO-Math-17K 数据集、2K token 响应上限。前五个步的平均奖励是 0.51，最后五个步是 0.78。在绘制的区间里，trainer 与 rollout 之间的逐 token KL 落在 0.0012 到 0.0017，平均 log-probability 绝对差落在 0.017 到 0.025 nats。",
                "在这次运行中，测得的差异始终很小，也没有持续增长。这些测量并没有分离出差异的成因，也不构成数值等价性的证明。这次运行完成了 120 步以上，没有出现失败。",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig04.png", "caption": "图4：DAPO 训练的原始奖励与 trainer 对比 rollout 的策略差异，覆盖第 0 到 80 步"},
                ],
            },
        },
    ],

    "conclusion": [
        "**把新模型做成 Day-0 支持，拼的不是把架构硬塞进推理引擎，而是把「共享」当成一等公民。** DeepSeek-V4.1 的压缩 KV、indexer keys 和检索候选全部在层间共享：四个 KV 源层供全模型读取，第 20 层发布候选块，八个 index 源层负责打分，其余层直接复用结果。共享越彻底，单层要维护的状态越少，后面所有优化才有空间。",
        "三处取舍值得记住：Engram 表卸载到主机内存，用一次 all-reduce 换取 KV 缓存容量增加 36%；SWA 有界重放用有界重算换缓存与算力，prefill 吞吐最高提升 1.56 倍；训练侧用量化感知前向加路由重放，把 trainer 与 rollout 的差异压到 0.02 nats 量级。有界重放本质是近似，上线前必须逐场景验证，不能只看一个 benchmark 打平。",
    ],

    "reference_url": "https://www.lmsys.org/blog/2026-09-10-deepseek-v41",
    "title": "SGLang 与 Miles 首发支持 DeepSeek-V4.1：KV 缓存容量多 36%，prefill 吞吐快 1.56 倍",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
