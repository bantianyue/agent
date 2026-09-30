#!/usr/bin/env python3
"""article_data_build.py - Kimi K3 Optimization on GB300 Part I (LightSeek blog)"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "summary": [
        {"key": "场景", "body": "GB300单NVL72域TP8，长多轮SWE-Smith Agent负载，并发1到16"},
        {"key": "优化", "body": "EAGLE3投机解码、LatentMoE通信感知切分、Replay SSM、形状感知路由"},
        {"key": "结果", "body": "省7.7GiB参数显存，验证工作区从16.7GiB降到0.4GiB"},
    ],

    "lead": [
        "把 Kimi K3 跑在 GB300 上是个系统问题：KDA、Gated MLA、LatentMoE 和通信、持久状态搅在一起，长多轮 Agent 负载把孤立 decode 测不出的开销全暴露出来。LightSeek 这篇三部曲的第一部，讲单 NVL72 域 TP8 的优化：EAGLE3、通信感知切分、Replay SSM。下文拆解。",
    ],

    "sections": [
        {
            "type": "h2",
            "title": "端到端:长上下文Agent服务",
            "paras": [
                "服务曲线上每个点是一个实测并发。往右是每个用户生成更快，往上是每 GPU 聚合吞吐更高。对比的是 EAGLE3 与非投机执行，workload 与服务配置冻结一致。",
                "基准契约：GB300 GPU，8 卡跨两个 4 卡计算托盘但同属一个 NVL72 NVLink 域；注意力 TP8、MoE TP8；目标模型 nvidia/Kimi-K3-NVFP4；draft 模型 lightseekorg/kimi-k3-eagle3-mla，BF16 未量化；MLA 后端 TokenSpeed MLA；KDA 后端 CuTe DSL prefill 加 fused Triton decode/verify；MoE 后端 FlashInfer TensorRT-LLM；KV cache FP8；workload 是冻结的多轮 SWE-Smith trace；上下文从约 50K input token 起，每轮加约 800 token，最多约 68K；生成 10 到 15 轮，每轮最多 500 输出 token；并发 1、2、4、8、16；EAGLE3 验证 3 个 draft 步、4 位置目标窗口。",
                "8 个 TP rank 跨两个托盘但不出 NVL72 域，这组实验没有跨机架网络跳。SWE-Smith trace 模拟 Agent 编程会话的形状：长 prompt、重复工具调用 trace、多轮不断延长同一对话。每轮复用大段历史，追加工具输出，再要一段相对短的回复。",
                "指标是每 GPU 每分钟 token 数 TPM/GPU，和每用户每秒生成 token 数 TPS/user，由 TPOT 换算。TPS/user 不含首 token 时间。两个指标一起看，加并发时系统吞吐与单用户体验怎么变。",
                "对比范围声明：所有点用同一 trace 集、同一目标模型、同一服务配置，意图是 EAGLE3 对非投机的配对比较；别家系统的结果要先对齐 workload 与指标定义才可比。",
                "图 1 横轴 TPS/user、纵轴 TPM/GPU，标签标出每点的实测并发。EAGLE3 把整条曲线往外推：低并发和高吞吐区都受益。在 50 TPS/user 的参考生成速度下，对 EAGLE3 并发 8 和 16 两点线性插值，约 459K TPM/GPU，这是曲线上的插值点，不是独立测量。",
            ],
            "table": {
                "head": ["组件", "配置"],
                "rows": [
                    ["GPU", "NVIDIA GB300 GPU"],
                    ["拓扑", "8 卡跨两个 4 卡计算托盘，同属一个 NVL72 NVLink 域"],
                    ["并行", "注意力 TP8，MoE TP8"],
                    ["目标模型", "nvidia/Kimi-K3-NVFP4"],
                    ["Draft 模型", "lightseekorg/kimi-k3-eagle3-mla"],
                    ["Draft 精度", "BF16，未量化"],
                    ["MLA 后端", "TokenSpeed MLA"],
                    ["KDA 后端", "CuTe DSL prefill；fused Triton decode/verify"],
                    ["MoE 后端", "FlashInfer TensorRT-LLM"],
                    ["KV cache 类型", "FP8"],
                    ["负载", "冻结的多轮 SWE-Smith trace"],
                    ["上下文增长", "约 50K input token 起；每轮约 800 token；最多约 68K"],
                    ["生成", "10 到 15 轮；每轮最多 500 输出 token"],
                    ["并发", "1、2、4、8、16"],
                    ["EAGLE3 验证", "3 个 draft 步；4 位置目标窗口"],
                ],
            },
            "fig_after": {
                "5": [{"src": "fig01.png", "caption": "图1:多轮 SWE-Smith trace 上的聚合吞吐对每用户生成速度：EAGLE3 把曲线往外推"}],
            },
        },
        {
            "type": "h2",
            "title": "LatentMoE通信感知切分",
            "paras": [
                "profile 拆出三类反复出现的开销：LatentMoE 里复制投影与通信感知切分的权衡，KDA 的临时状态存储，以及主模型算子周围的小 M 执行。这些开销在 93 个 decoder 层里反复出现，包括 69 个 KDA 层、24 个 MLA 层、92 个 MoE 块。多 token 验证让某些形状与状态生命周期约束更显眼，但下面讲的是 K3 目标路径，不是投机解码算法本身。",
                "最初实现把两个路由隐投影都复制：每 TP rank 存并算完整的 hidden 到隐 down 投影，以及专家之后完整的隐到 hidden up 投影。省了显式拼装投影分片，但权重存储和投影计算都翻了 8 倍。理想是两个投影都切，但 MoE 块两侧的通信权衡不同：切 down 投影要新增拼装本地隐分片；切 up 投影反而能重构专家后的通信路径，把路由与共享专家的规约、本地投影分片、最终 hidden 组装合成一步。目标是 down 路径的拼装代价尽量小，up 路径的切分同时降复制计算和专家后尾巴的通信。",
                "路由 down 投影：每 MoE 块先把 7168 维 hidden 投到 3584 维路由隐空间。复制形态下每 rank 存完整 [3584, 7168] BF16 权重、算全部输出列。列切分把输出轴按 TP8 分：rank r 存并算 [448, 7168] 块，覆盖隐列 448r 到 448r+447，再拼回完整路由隐。",
                "拼装路径按 M 选：M≤8 用静态 M 的 SIMT kernel，算完本地块直接经 NVLink SHARP 多播虚地址发布；8<M≤1280 用 tensor core kernel 写进同一多播地址的跨步视图，省掉单独发布 kernel；两种都用 Lamport 协议 gather，在池化的双槽 mailbox 里等齐 8 rank 的分片再拼。超过 mailbox 上限，每 rank 写普通内存，最后一维 all-gather 拼。",
                "切路由 down 投影，每 rank 权重从 49.0 MiB 降到 6.1 MiB 每 MoE 块，92 个块在每 GPU 省约 3.9 GiB。延迟也不只小形状受益：M=4 整操作 14.9 降到 12.8μs；M=8192 从 225.1 降到 138.9μs，含 all-gather。M=1280 到 1281 的跳变是 mailbox 拼装切到 GEMM 加 all-gather，大 M 点测的是投影可扩展性，超出本 workload 的 decode 与验证区间。",
                "路由 up 投影：最初实现把路由和共享专家的部分和分别规约，再在每 rank 算完整复制 up 投影。切分路径每 rank 只算 hidden_size/TP 个输出元素。关键是块注入：每 rank 把自己的投影块和前缀张量的对应切片，加进共享专家部分和的匹配列。块互不相交，一次共享 all-reduce 既求和又拼装，省掉单独的路由 all-gather。GB300 上这条路径基于 TensorRT-LLM 的多节点 NVLink all-reduce 设计，经 FlashInfer 承接，一 shot 和两 shot 的 Lamport 协议用 NVLink 多播内存做小 TP 规约，TokenSpeed 加 K3 专用 epilogue 让规约后的相邻计算保持融合。小 M 时融合尾巴改走 reduce-scatter 共享分支，在投影 epilogue 里加本地共享分片，多播发布合并块再做 Lamport gather，同时加上前缀张量。这部分集成有 NVIDIA DevTech 的技术指导与优化支持。",
                "down 和 up 投影权重一样大，各省约 3.9 GiB/GPU，两处合计相对复制布局省约 7.7 GiB/GPU。从路由与共享专家产出本地部分和算起，完整尾巴 M=4 从 32.34 降到 18.28μs，扣掉空事件开销 1.77 倍，用原始事件间隔算是 1.69 倍；M=8192 从 915.77 降到 656.22μs，1.40 倍。M=256 处过渡形态比对照慢 19.4%，对照侧 M=2049 的跳变是它从 MNNVL 回退到 NCCL。这些是局部组合对比，不是孤立 finalize 融合收益，更不是端到端加速。",
            ],
            "fig_after": {
                "3": [{"src": "fig02.png", "caption": "图2:路由 down 投影的列切分与跨 8 个 TP rank 的隐拼装"}],
                "4": [{"src": "fig03.png", "caption": "图3:路由 down 投影延迟：复制路径对切分路径"}],
                "5": [{"src": "fig04.png", "caption": "图4:路由 up 投影切分与专家后尾巴融合：一次共享 all-reduce 又规约又拼装"}],
                "6": [{"src": "fig05.png", "caption": "图5:路由 up 投影与融合尾巴延迟对复制对照"}],
            },
        },
        {
            "type": "h2",
            "title": "Replay SSM:KDA验证状态",
            "paras": [
                "每个 token 在每 KDA 层推进卷积与循环状态。多 token 验证下，接受长度要等整个候选窗口评完才知道，每位置都快照完整状态，内存随 batch 和验证宽度涨。Replay SSM 只留已提交状态做锚，记重建要的小投影与门输入；采样返回接受长度后，一个 batched kernel 重放接受前缀加目标采样 token。",
                "TP8 的 K3 上，快照一行每请求每 KDA 层 795 KiB：27 KiB BF16 卷积状态加 768 KiB FP32 循环矩阵。batch 64 时，存锚加 4 个验证位置、69 个 KDA 层，要 16.7 GiB/GPU。Replay 只要 0.4 GiB/GPU，省 16.4 GiB/GPU，即 97.8%，45 倍，用 fused verify 和 replay kernel 没观测到延迟增加。",
                "内存换算：这里 cache 几何下，投影切分的 7.7 GiB 参数缩减和 Replay SSM 的 16.4 GiB 验证工作区缩减，按每逻辑 token 14.1 KiB/GPU，分别约等于 0.6M 和 1.2M 个目标加 draft 的 FP8 cache token。这不是分配器峰值测量，也不保证理论容量能同时分配出来。",
            ],
            "table": {
                "head": ["KDA 验证工作区，max_num_seqs=64", "每 GPU"],
                "rows": [
                    ["逐位置状态快照", "16.7 GiB"],
                    ["Replay SSM 工作区", "0.4 GiB"],
                    ["省下内存", "16.4 GiB (97.8%)"],
                    ["等价 FP8 cache 容量", "约 1.2M token"],
                ],
            },
        },
        {
            "type": "h2",
            "title": "Kernel融合与形状感知路由",
            "paras": [
                "通信与状态优化之外，剩下的 decode 与验证开销不再被单个大算子主导，而是一堆短投影、中间交接、路由步骤、元数据准备，围着 4 位置验证窗口转。单个都很小，但在模型里反复出现，decode 与验证的低 token 数下就显眼了。",
                "形状感知投影路由：没有一种 GEMV 或 GEMM 实现通吃所有投影形状。按 (M,N,K) 区域在 Triton row-per-CTA GEMV、CuTe DSL skinny GEMM、FlashInfer TGV、torch.mm 里选。图 6 覆盖 NVFP4 目标的未量化共享专家投影和选定的 BF16 EAGLE3 draft 投影，目标 FP8 注意力投影不在比较里。基线全用 torch.mm，路由决策按冷 L2 测量，更接近服务行为；选定的瘦形状在指针允许时再加 256-bit load。",
                "KDA 融合：多 token 验证在卷积与循环更新周围引入一串小操作。短卷积与循环能融则融，门准备按形状在切分与融合间选，跨步切片直接从合并输入投影里吃，不 repack 成连续中间量。目标是砍掉循环核心周围的 launch 与内存搬运，不动 KDA 计算本身。",
                "MLA decode 与验证融合：MLA 路径上注意力之前的几处 decode 交接可以压掉。FP8 KV cache 下，优化路径在同一 launch 里构造 FP8 query 并写隐 KV cache，中间物化省了。这些融合针对小 decode 与验证形状，大 prefill 形状继续用现有 kernel。",
                "AttnRes 与投机元数据：现有 fused AttnRes 路径扩展到更小的多 token 验证形状。模型算子之外，低 M 下显眼的元数据链也压掉：分页位置与页表准备，加 KDA replay 元数据准备。专用 launch 按步或按 cache 组跑，不再按层跑。",
                "局部消融：MLA query 加 cache 写，M=4，6.43 降到 4.39μs；AttnRes 输出 RMSNorm，M=4 加 7 个历史块，10.48 降到 8.20μs；写槽准备，1 请求 4 位置窗口，30.49 降到 4.30μs；KDA 已提交状态元数据，1 请求 4 位置窗口，21.35 降到 4.40μs。这些路径都有形状门限，门限外运行时保留参考实现。计时是单 GB300 GPU 上 NVFP4 兼容的 TP8 per-rank 形状、合成输入、冷 L2 准备、CUDA Graph 回放加图内计时的局部消融，两次独立运行，不是端到端收益的加总估计。",
            ],
            "table": {
                "head": ["路径", "测量形状", "基线→优化", "比较边界"],
                "rows": [
                    ["MLA query 与 cache 写", "M=4", "6.43 → 4.39μs", "合并的 query/cache 写阶段"],
                    ["AttnRes 输出 RMSNorm", "M=4，7 个历史块", "10.48 → 8.20μs", "全混合 epilogue，非上提部分和路径"],
                    ["写槽准备", "1 请求，4 位置窗口", "30.49 → 4.30μs", "完整元数据链"],
                    ["KDA 已提交状态元数据", "1 请求，4 位置窗口", "21.35 → 4.40μs", "完整元数据链"],
                ],
            },
            "fig_after": {
                "1": [{"src": "fig06.png", "caption": "图6:形状感知投影路由相对 torch.mm：按 (M,N,K) 在四种实现里选最优"}],
            },
        },
        {
            "type": "h2",
            "title": "边界与下一步",
            "paras": [
                "Part I 说明 K3 在 TP8 上的优化是系统级协同设计。受控服务负载下，EAGLE3 改善聚合吞吐对每用户生成速度的曲线；目标路径里，LatentMoE 投影切分拿回约 7.7 GiB/GPU 参数存储，Replay SSM 把验证工作区从 16.7 GiB/GPU 压到 0.4 GiB/GPU；局部消融指出通信感知拼装与形状专用融合砍掉剩下的算子与元数据开销。这些结果边界各不相同，不能加总成一个端到端加速比。",
                "专家并行：EP 同时改变 MoE 路由与通信，值得单独的吞吐与尾延迟研究。",
                "P/D 分离：长 Agent prompt 让 prefill 放置与 KV 传输重要，但这里故意排除。",
                "单 NVLink 域之外的通信：跨机架多一跳网络，可能偏好不同的 collective 或投影策略。",
                "其他投机路径：这里没评，另有一篇博客专门对比投机解码算法与 draft 配置。",
                "Part II 讲专家并行执行，覆盖 WideEP 与 prefill-decode 分离；Part III 回到端到端视角，用企业部署案例讲分布式调度、多级缓存，以及长多轮 Agent 负载生产运行的经验。",
            ],
        },
        {
            "type": "h2",
            "title": "服务启动配置",
            "paras": [
                "代表性服务启动配置如下。复现端到端结果还需要冻结的 SWE-Smith trace 与客户端并发调度，原文未附带。",
                "__CODE__bash::tokenspeed serve nvidia/Kimi-K3-NVFP4 \\\n  --served-model-name kimi-k3 \\\n  --attn-tp-size 8 \\\n  --moe-tp-size 8 \\\n  --mm-encoder-tp-mode data \\\n  --max-num-seqs 64 \\\n  --gpu-memory-utilization 0.92 \\\n  --trust-remote-code \\\n  --attention-backend tokenspeed_mla \\\n  --kda-backend cutedsl_kda \\\n  --moe-backend flashinfer_trtllm \\\n  --kv-cache-dtype fp8 \\\n  --speculative-algorithm EAGLE3 \\\n  --speculative-draft-model-path lightseekorg/kimi-k3-eagle3-mla \\\n  --speculative-num-steps 3 \\\n  --drafter-attention-backend tokenspeed_mla",
            ],
        },
    ],

    "conclusion": [
        "① EAGLE3 在 1 到 16 并发的全区间把吞吐对生成速度的曲线往外推，50 TPS/user 下插值约 459K TPM/GPU。② LatentMoE 两投影通信感知切分省 7.7 GiB/GPU 参数显存，专家后尾巴延迟 M=4 下 1.77 倍。③ Replay SSM 把 KDA 验证工作区从 16.7 GiB/GPU 压到 0.4 GiB/GPU，省 97.8%。",
        "系统优化没有银弹，只有把每一处的 10μs 都算清楚。Part II 见专家并行。",
    ],

    "reference_url": "https://lightseek.org/blog/kimi-k3-optimization-gb300-part-i.html",
    "title": "Kimi K3在GB300上的系统优化:TP8篇",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
