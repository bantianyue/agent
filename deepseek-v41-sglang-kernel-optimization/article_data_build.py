#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

TBL_ARCH = {
    "head": ["", "V4 Flash", "V4.1 Flash"],
    "rows": [
        ["主干", "284B", "552B，另有 196B Engram 记忆参数"],
        ["每 token 激活", "约 13B", "输入约 8B、输出约 16B"],
        ["结构", "43 个解码层", "20 层因果编码器 + 20 层解码器"],
        ["全局注意力", "CSA / HCA", "CSA2，KV 与索引跨层共享"],
        ["每 token 全局 KV", "3514 字节", "<strong>890 字节</strong>"],
    ],
}

TBL_DSPARK = {
    "head": ["配置", "BS=1 输出速度（tokens/s）", "实测接受长度"],
    "rows": [
        ["DSpark，优化前", "558.24", "5.505"],
        ["+ verify / MoE 融合与重叠", "718.75", "5.505"],
        ["+ 小块投影 / mHC 融合", "761.71", "5.505"],
        ["+ indexer 后处理 / Q RoPE / WO-A 量化", "802.38", "5.505"],
        ["+ C2 verify 压缩融合", "853.49", "5.520"],
        ["全部优化 + MoE 换 TP4 + padding", "<strong>873.63</strong>", "5.505"],
    ],
}

CODE1 = '''__CODE__bash::export MODEL_PATH=/path/to/DeepSeek-V4.1-Flash
export SGLANG_RAGGED_VERIFY_MODE=static
export SGLANG_SIMULATE_ACC_LEN=5.5
export SGLANG_SIMULATE_ACC_METHOD=match-expected
CUDA_VISIBLE_DEVICES=0,1,2,3 PYTHONPATH="$PWD/python" MAX_JOBS=16 \\
python -m sglang.launch_server \\
  --model-path "$MODEL_PATH" \\
  --served-model-name deepseek-ai/DeepSeek-V4.1-Flash \\
  --tp 4 --ep-size 1 --trust-remote-code \\
  --moe-a2a-backend none --moe-runner-backend flashinfer_mxfp4 \\
  --mem-fraction-static 0.80 --max-total-tokens 33554432 \\
  --chunked-prefill-size 4096 \\
  --cuda-graph-bs-decode 1 2 4 8 16 32 64 \\
  --max-running-requests 128 \\
  --speculative-algorithm DSPARK --speculative-dspark-block-size 5 \\
  --skip-server-warmup --reasoning-parser deepseek-v41 \\
  --random-seed 42 --decode-log-interval 10 \\
  --host 127.0.0.1 --port 30021'''

CODE2 = '''__CODE__bash::ASSET_URL=https://raw.githubusercontent.com/BBuf/how-to-optim-algorithm-in-cuda/master/large-language-model/sglang/assets/deepseek-v41-kernel-journey/random-dspark
curl -fL "$ASSET_URL/prompt.json" -o prompt.json
curl -fL "$ASSET_URL/benchmark.py" -o benchmark.py
python -m pip install requests
python benchmark.py bench --prompt prompt.json --max-tokens 1024 --out result --repeat 6'''

DATA = {
    "summary": [
        {"key": "结果", "body": "4×GB300、BS=1：plain decode 从首个可用构建的 35.2 提到 203.3 tokens/s；打开 DSpark 后进一步到 873.63 tokens/s"},
        {"key": "主要手段", "body": "MXFP8 GEMM 换掉慢路径、小算子融合（RoPE+FP4、C2 压缩、GEMV）、mHC 归约与统计重叠、MoE 从 EP4 换成 TP4+padding"},
        {"key": "KV cache", "body": "架构换成 20 层因果编码器 + 20 层解码器，每 token 全局 KV 从 3514 字节压到 890 字节，约为 V4 Flash 的四分之一"},
    ],
    "lead": [
        "SGLang 团队和 DeepSeek 一起完成了 DeepSeek-V4.1 Flash 的 day-0 支持与 kernel 优化。在 4 张 GB300 上、BS=1 的纯解码场景里，从第一个能跑通的构建 35 tokens/s 起步，一路调到 873.63 tokens/s。",
        "这篇文章记录了整个过程：架构层面 KV cache 是怎么压下来的、纯解码阶段做了哪些算子级优化，以及打开投机解码 DSpark 之后如何把 verify、MoE 和小批量投影逐个吃透。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "优化旅程：16 轮把 35.2 推到 873.6",
            "paras": [
                "整条优化路径可以按 16 轮看：第 1 轮是第一个能跑通的构建（35.2 tokens/s），第 2 轮换上 MXFP8 GEMM 到 117.8，第 3 轮把 RoPE 与 FP4 融合到 133.5，第 4 轮 mHC 按输入行分块到 141.1，第 5 轮归约与 Sinkhorn 融合到 146.5，第 6 轮跨层共享 scratch 到 148.4，第 7 轮 C2 pooling 融合到 152.1，第 8 轮 mHC 统计量重叠到 186.4，第 9 轮把快速路径默认打开到 186.6，第 10 轮 GEMV / norm / Engram gate 到 203.3。",
                "第 11 轮打开 DSpark 直接跳到 558.2；随后 verify / MoE 融合到 718.8，小块投影与 mHC 到 761.7，indexer 后处理与投影融合到 802.4，C2 verify 压缩融合到 853.5，最后把 MoE 从 EP4 换成 TP4 加 padding 到 873.6。第 1 到 10 轮是纯解码的累计测量；第 11 到 16 轮使用同样的随机 4k/1k 输入、模拟接受长度固定 5.5，取多次运行中位数。",
            ],
            "fig_after": {
                "1": [{"src": "fig01.png", "caption": "图 1：kernel 优化旅程。BS=1 下从 35.2 到 873.6 tokens/s 的 16 轮优化，第 11 轮起开启 DSpark（模拟接受长度 5.5）"}],
            },
        },
        {
            "type": "h2",
            "title": "架构变化与 KV cache 压缩",
            "paras": [
                "V4.1 Flash 的主干比 V4 Flash 更大，但每个输入 token 激活的参数更少，KV cache 也小得多。对服务来说关键的是下面这几行。",
                "因果编码器-解码器结构砍掉了 prefill 计算：20 个解码层从编码器的最终输出取全局 KV，所以长提示主要由前 20 层处理；解码器仍然需要局部窗口，它通过重放最后 128 个 token 来重建，这让主干的 prefill 工作量大约减半。但生成阶段是另一回事：每个生成的 token 仍然要走完所有 40 层。",
                "KV cache 的压缩来自共享、池化与 FP4 存储三件事。40 层里只有 4 层（第 2、8、14、20 层）产生全局 KV，其余层读取这些缓存，少数层会重算自己的索引。前三个缓存每两个 token 池化成一个条目，只有最后一个保持每个 token 一个条目；条目本身用 FP4 存储，主 KV 占 288 字节、indexer K 占 68 字节。折算到每个原始 token 上，大约只有 V4 Flash 的四分之一。由于局部窗口总能靠重放重建，需要持久化的状态更少，DeepSeek 给出的 SSD 缓存需求大约降到此前的八分之一。需要提醒的是，890 字节是逻辑大小，SGLang 里有些路径仍在使用 FlashMLA 兼容的缓存布局，实际分配的内存并不相同。",
                "架构里还有两个组件贯穿了后面的 kernel 工作：CSA2 用分层候选过滤收窄 indexer 的搜索范围，最后只有 top-512 的全局位置参与注意力；Engram 通过 n-gram 查找引入一种条件记忆。它们在模型里各司其职，也各自带来了新的索引、归一化与融合工作。",
            ],
            "table": TBL_ARCH,
            "fig_after": {
                "1": [{"src": "fig02.png", "caption": "图 2：编码器-解码器拆分与共享 KV cache。提示大多只经过前 20 层，生成仍然要走全部 40 层；每 token 全局 KV 从 3514 B 降到 890 B"}],
            },
        },
        {
            "type": "h2",
            "title": "纯解码阶段的 kernel 优化",
            "paras": [
                "先看纯解码是怎么从第一个可用构建的 35 tokens/s 走到 203 tokens/s 的。这一节的数字都是原始测量值。",
                "FP8 GEMM：35 到 118。部分稠密权重随模型以 FP8 发布，但它们的量化块与 scale 布局和后端期望的不一致，这些 GEMM 一开始走了更慢的回退路径。现在在加载权重时一次性重排 scale 布局，它们就能直接进入 Blackwell 的 MXFP8 GEMM。仅这一项就把 BS=1 从 35.2 提到 117.8 tokens/s。结论是：接入新模型时，先确认一个 GEMM 真正派发到了哪个 kernel，通常比调 tile 更有价值。",
                "小算子融合与 GEMV。逐 token 解码会跑一长串很短的 kernel；RoPE、FP4 量化、压缩器池化、RMSNorm 和缓存写入彼此直接衔接，把相邻算子融合起来，每次都能省下一次 kernel 启动和一趟内存往返。具体收益是：RoPE 加 FP4（旋转、量化、反量化合进一个 kernel）从 117.8 到 133.5；C2 压缩器（相邻 token 的归一化、池化与状态写入融合）从 148.4 到 152.1；WO-A、norm 与 Engram gate（单行投影用 GEMV，小规模的 norm 与 gate 用融合 kernel）从 186.6 到 203.3。",
                "此外，他们把每步的请求索引与 scratch 缓冲从「每层各自重建」改成跨层共享，省掉大量重复的转换与初始化，把 BS=1 从 146.5 提到 148.4 tokens/s。等这些快速路径验证通过后，就直接默认开启。",
                "mHC：归约融合与重叠。mHC 维护四条残差流而不是一条，对每个注意力与 MoE 子层都要为它们计算混合系数、再用 Sinkhorn 归一化。这些单独看都不贵，但它们要在每层的注意力和 MoE 里各跑一次，小批量下就会累加。先按输入行数选择 tile 尺寸，再把统计量归约与 Sinkhorn 融合，BS=1 依次从 133.5 到 141.1、再到 146.5 tokens/s。",
                "更大的收益来自 V4.1 单遍 mHC 的定义方式：pre-mix 使用上一个子层产出的系数，因此当前的注意力或 MoE 可以与本子层的统计量计算并行。团队把两者放在不同 stream 上跑，在 post-mix 处汇合。再配合压缩器与 indexer 的融合和重叠，BS=1 从约 152 提到 186 tokens/s。小批量下，融合后的 pre-mix 与 RMSNorm 会先完成，然后统计量才开始，这减少了短 kernel 之间的争用。",
            ],
            "fig_after": {
                "0": [{"src": "fig03.png", "caption": "图 3：单遍 mHC 中的重叠。pre-mix 使用上一个子层的系数，统计量计算与注意力 / MoE 并行，两条流在 post-mix 处汇合"}],
            },
        },
        {
            "type": "h2",
            "title": "DSpark 适配与优化",
            "paras": [
                "DSpark 随官方 checkpoint 一起发布，包含三个轻量草稿块：它们从主模型最后几层的隐状态出发，一次为多个位置产出 logits，用 Markov 头解决草稿 token 之间的依赖，然后把整块交给目标模型做批量验证。他们把块大小固定为 5，并用 5.5 的目标接受长度模拟接受行为；算上锚点，目标验证对单个请求最多要处理 6 行，而纯解码每个请求只处理 1 行，所以原来为 M=1 设计的快速路径需要为这种小批量重做。",
                "第一组优化落在 verify 与 MoE 上：把 mHC 的重叠接进 verify 与草稿、让 WO-A 投影直接写进下一阶段需要的布局；候选掩码把有效长度检查与候选处理融合，减少对大缓冲区的扫描。MoE 侧，路由器现在直接输出专家需要的布局，输入量化与路由重叠，专家加权归约、共享专家相加和 all-reduce 合成一步，减少中间写回。",
                "第二组是小批量投影与归一化：WO-A 用 split-K 让更多线程块并行工作，mHC 把四条残差流的混合与 RMSNorm 融合；草稿的多个 KV 投影改为复用 MXFP8 权重与 scale，而不是旧的 FP8 路径。",
                "第三组融合了更多 indexer 后处理与投影：top-k 之后的分数检查、非法位置过滤与 KV 页地址翻译合成一步，选中的候选块直接展开成 token 掩码；Q 的 RoPE 合并进注意力缓冲写入，WO-A 的 split-K 归约自己完成后续 MXFP8 量化，省掉一个中间张量。",
                "第四组针对第 2、8、14 层（从 0 开始编号）的 verify 期压缩：这三层原本要跑一串小算子去找上一个 token、处理掩码、再池化并写缓存。verify 的位置是连续的，所以一个请求内可以直接读上一行，只有第一行需要环形缓冲。他们把成对池化、RMSNorm、RoPE、量化与主 KV 写入融合成单个 kernel，然后把这份融合写入复用到 index-K。",
                "最后，MoE 从 EP4 换成 TP4 加 padding：按 TP4 切分后，专家中间维每张卡 576，加载时 padding 到 640 以适配 kernel。每张卡计算同一批专家的不同切片，因此专家负载不均时等待更少。在其余优化全部到位的情况下做同轮对比，EP4 是 854.64 tokens/s、TP4 是 873.63 tokens/s，提升 2.22%；从 trace 上看，各 rank 到达 finalize 的中位差距从 11.14 微秒降到 3.40 微秒。",
            ],
            "table": TBL_DSPARK,
            "fig_after": {
                "0": [{"src": "fig04.png", "caption": "图 4：DSpark 每步验证多个 token。进入 verify 的行数不等于请求批大小：1 个请求（BS=1）时 verify 最多处理 6 行"}],
            },
        },
        {
            "type": "h2",
            "title": "如何复现：随机 4k/1k，模拟接受长度固定 5.5",
            "paras": [
                "这一节复现的是图中 DSpark 的第 11 到 16 轮：4096 个随机输入 token、固定 1024 个输出 token，接受长度用模拟方式瞄准 5.5。服务器配置控制接受长度，所有版本使用同一份输入。",
                "使用 BBuf/sglang@835c3909 的代码与 revision dba1be0a 的官方 checkpoint，硬件是 4 张 GB300；环境为 PyTorch 2.13.0+cu130、FlashInfer 0.6.18、Triton 3.7.1、sglang-kernel 0.4.6.post1、sgl-deep-gemm 0.1.7 与 CUTLASS DSL 4.6.2。",
                "下面是 873.63 tokens/s 背后的 TP4 服务命令，在该 SGLang checkout 的根目录下运行。--tp 4 与 --ep-size 1 意味着注意力与 MoE 都用 TP4，这个版本在加载权重时施加 padding。",
                CODE1,
                "要复现 EP4 的对比，把 --ep-size 1 改成 --ep-size 4，其余保持不变。完整的 TP4 启动脚本见 launch-tp4.sh。",
                "输入用固定随机种子 42 生成：从模型词表中排除特殊 token，均匀抽取 4096 个 token id，直接输入、不走 chat 模板，所有配置复用同一份。",
                "在第二个终端里运行下面的基准脚本。",
                CODE2,
                "脚本使用 temperature=0 与 ignore_eos=True，并在每次运行后校验输入为 4096 token、输出为 1024 token。输入走 /generate；脚本在启动后调用 /freeze_gc，每次运行前清空缓存，并丢弃一次预热。每次服务启动测 6 次；小块投影、indexer 后处理与投影融合、C2 verify 和 TP4 这几组配置各自独立启动了两次，取 12 次运行的中位数。本轮的 EP4 / TP4 对比按 TP、EP、TP、EP 交替启动，保留全部测量，测吞吐时关闭 profiler。",
                "match-expected 每轮接受 5 或 6 个 token，所以期望接受长度是 5.5；有限轮数与最后一步的截断会让实测值略有偏差，表格保留实际值。接受是模拟出来的，因此生成文本不用于判断回答质量，模拟模式也会禁用图内的接受路径。吞吐按首个流式事件之后新增的 token 数除以首末事件之间的时间计算，不含完整 prefill；接受长度统计目标模型产出的 token，所以块大小为 5 时上限是 6。",
                "下表把 DSpark 关闭与开启并排放在一起，再加上 MoE 的 TP4 + padding 配置。所有条目使用同一份代码、同一份随机输入、同一输出长度与同一种计时方式，注意力全程 TP4；表头的 EP4 / TP4 指 MoE 的配置。DSpark 关闭时为 223.50 tokens/s，开启后 853.49，换成 TP4 + padding 后 873.63。",
            ],
        },
        {
            "type": "h2",
            "title": "相关链接与致谢",
            "paras": [
                "相关链接包括：LMSYS 博客的 day-0 支持文章（涵盖推理与 RL 训练）、SGLang 的 DeepSeek-V4.1 部署指南（启动配置、硬件支持与调优说明）、SGLang DeepSeek-V4.1 代码（dsv4.1 分支）、Miles 的 DeepSeek-V4.1 Flash 训练指南、Miles GitHub 仓库，以及 DeepSeek-V4.1 技术报告；kernel 实现可参考 C2 verify 压缩、indexer 后处理、Q RoPE / store 与 WO-A / MXFP8 的具体代码。",
                "致谢部分感谢 DeepSeek 团队开源 DeepSeek-V4.1，也感谢 SGLang 与 Miles 团队以及社区中参与模型支持、kernel、测试与评审的所有人；其中部分 kernel 使用 KDA 0.5 框架开发，作者也感谢 Humanize 与 Kernel Design Agents 提供的工具与工作流。",
            ],
        },
    ],
    "conclusion": [
        "**这条 35 到 873 的曲线里，最大的两次跳跃都来自「先搞清楚瓶颈在哪」。** 第一次是把错配到慢回退路径的 FP8 GEMM 换成 Blackwell 的 MXFP8 GEMM，一步就把 BS=1 从 35 提到 118；第二次是打开 DSpark，直接把 203 推到 558。中间那些融合与重叠（RoPE+FP4、C2 压缩、mHC 统计量重叠、跨层共享 scratch）则是一分一分地把剩余空间抠出来。",
        "更值得注意的是这些小批量专有优化：投机解码让单个请求在 verify 阶段变成最多 6 行，原来为 M=1 写的快速路径全部要重做；而 MoE 从 EP4 换成 TP4 + padding 只带来 2.22%，却把 rank 间到达 finalize 的中位差距从 11.14 微秒压到 3.40 微秒。小批量推理的优化重点不在算力，而在减少等待与短 kernel 之间的空转。",
    ],
    "reference_url": "https://www.sglang.io/blog/deepseek-v4.1-flash-kernel-optimization",
    "title": "DeepSeek-V4.1 Flash 在 SGLang 上的调优实录：从 35 到 873 tokens/s",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print("OK wrote", out_path, len(DATA.get("sections", [])), "sections")
