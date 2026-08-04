#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.getcwd())

DATA = {
    "title": "LongCat Sparse Attention：驯服闪电——用流感知 + 跨层 + 分层的索引器给稀疏注意力提速",
    "summary": [
        {
            "key": "问题",
            "body": "DeepSeek 稀疏注意力 DSA 的 Lightning Indexer 有 O(L²) 打分开销 + 索引输出非连续导致硬件访问低效两大部署瓶颈"
        },
        {
            "key": "三策略",
            "body": "流感知索引（SI）合并 HBM 访问、跨层索引（CLI）把索引次数从 L 降到 L/N、分层索引（HI）用 coarse-to-fine 缩小候选集"
        },
        {
            "key": "结果",
            "body": "69B→560B 规模与全注意力持平；支持 100 万 token 原生训练，支撑 LongCat-2.0（1.6T-A48B）"
        }
    ],
    "lead": [
        "DeepSeek 稀疏注意力（DSA）凭借其 Lightning Indexer（闪电索引器）实现了高效的长上下文建模。**但实际部署仍受两个系统级瓶颈制约**：一是索引器昂贵的 O(L²) 打分开销，二是其输出导致的低硬件效率、非连续的内存访问模式。",
        "为此，论文提出 **LongCat Sparse Attention（LSA）**——一个硬件-算法协同设计的框架，由三个互补且正交的策略构成：**流感知索引**（把分散的 KV 条目选择性转成硬件对齐的连续布局，实现合并的 HBM 访问）、**跨层索引**（复用单层的索引结果以摊销索引开销，配合跨层蒸馏）、以及**分层索引**（coarse-to-fine 打分，逐步缩小每个查询的候选集，从而大幅降低索引计算）。"
    ],
    "sections": [
        {
            "type": "h2",
            "title": "背景：DSA 的闪电索引器为何卡在部署",
            "paras": [
                "DSA 用 Lightning Indexer 为每个查询挑出少量重要 token，以稀疏注意力的方式让长上下文建模变得高效。**但索引器本身有两种代价**：打分要扫全序列（O(L²)），且选出的 KV 在内存里是分散、不连续的。",
                "**瓶颈一：非合并的内存访问。** token 级稀疏选择迫使每次内存事务只读回一个不连续的 KV 向量，严重拉低高带宽内存（HBM）利用率。理想合并下，AI 加速器单核可维持约 50 条在途 cacheline（每条 512B）；而 DSA 的非连续访问几乎无法利用这一点。",
                "**瓶颈二：打分开销随上下文膨胀。** 上下文越长，索引器要做的打分越多。这两大系统级瓶颈，正是 LSA 用三个**彼此正交、可自然叠加**的模块去解决的靶点。"
            ],
            "fig_after": {
                "1": [
                    {
                        "src": "fig00.png",
                        "caption": "Figure 1: 提出的 LongCat Sparse Attention（LSA）架构，核心是流感知的分层跨层索引器（此处省略 sink tokens）。"
                    }
                ]
            }
        },
        {
            "type": "h2",
            "title": "策略一：流感知索引（SI）——把分散 KV 排成连续布局",
            "paras": [
                "StreamingLLM 发现一个关键规律：**少量首部 token（sink tokens）充当了注意力汇聚点，对稳定长上下文性能至关重要**；同时存在少数的「流式头」（streaming heads），它们的注意力行为与其他头不同。",
                "LSA 的流感知索引利用这一点：**对 sink tokens 和流式头部，总是给予高优先级、把它们的 KV 整理进硬件对齐的连续布局**；其余候选再按稀疏打分挑选。",
                "这样做的效果是**把原来「东一个西一个」的非连续 KV 访问，变成硬件亲和的合并访问（coalesced access）**——一次内存事务读回多个连续元素，显著提升 HBM 利用率，这正是解决非合并访问瓶颈的直接手段。"
            ],
            "fig_after": {
                "1": [
                    {
                        "src": "fig01.png",
                        "caption": "Figure 2: 全注意力 LongCat-Flash-Lite（69B-A3B）模型上的注意力质量分布，该模型含 14 个带两个串行注意力层的 shortcut MoE 块。"
                    }
                ]
            }
        },
        {
            "type": "h2",
            "title": "策略二：跨层索引（CLI）——一层算，多层共享",
            "paras": [
                "论文的分析发现：**相邻层挑选出的 Top-K token 有很高的重叠度**（Figure 3）——也就是说，逐层各自跑一遍索引器，很大程度是在重复劳动。",
                "跨层索引据此把连续层划分成 CLI 组（组大小 N）：**只有组内第一层真正执行索引器，后续 N-1 层直接复用第一层产出的索引集**。索引器调用的总次数从 L 层降为 L/N 层，索引开销被直接摊销掉。",
                "但「朴素复用索引集」不做训练适配时会掉性能，所以论文引入**跨层蒸馏（cross-layer distillation）**：让被复用的那些层学会适应共享的索引，从而在不损失效果的前提下拿到减半甚至更省的索引计算。"
            ],
            "fig_after": {
                "2": [
                    {
                        "src": "fig02.png",
                        "caption": "Figure 3: 全注意力 LongCat-Flash-Lite（69B-A3B）上的跨层 Top-K 索引分析。每层从全注意力矩阵里独立挑选自己的 Top-K token。"
                    }
                ]
            }
        },
        {
            "type": "h2",
            "title": "策略三：分层索引（HI）——coarse-to-fine 先粗后细",
            "paras": [
                "与其对所有候选都做昂贵的精打分，LSA 用**两阶段 coarse-to-fine 打分**：便宜的粗阶段先召回一小批候选子序列，把昂贵的精打分限制在缩小后的候选集上。",
                "**阶段一（块级粗过滤）**：把序列切成大小为 P 的连续页，先做粗选择挑出 Top-M 页；对每页再切成 B token 的子块，预计算每块的粗评分，快速排除明显不相关的区域。",
                "**阶段二（细粒度精打分）**：只在粗阶段留下的候选子集上做完整、高精度的打分。**这样索引计算的规模大幅缩小**，直接缓解 DSA 的 O(L²) 打分开销，且粗选的高质量保证精打分几乎不丢召回。"
            ]
        },
        {
            "type": "h2",
            "title": "实验：从 69B 到 560B，全程追平全注意力",
            "paras": [
                "规模从 **69B-A3B 一直到 560B-A27B** 的广泛实验显示：**LSA 在通用与长上下文基准上都持续达到与全注意力持平（on par）的性能**，同时换来大幅的推理/训练加速（如降低 TTFT 与 TPOT，Figure 5；单层注意力训练延迟也更低，Figure 4/10）。",
                "三个消融（Figure 6/7/8）分别验证了每个模块的独立贡献：流感知索引、跨层索引、分层索引各自的收益都能被隔离出来，且 MTP（多 token 预测）指标保持稳定，说明稀疏改造没损害预测质量。",
                "**LSA 支持最长 100 万 token 的原生长上下文训练**，并支撑了 LongCat-2.0（1.6T-A48B）的开发；论文同时开源了整合 LSA 的 LongCat-Flash-Lite-Sparse（69B-A3B）及更新后的长上下文训练语料。",
                "总体而言，LSA 证明了稀疏注意力可以不必牺牲性能——只要把「索引」本身做得又快又硬件友好。对想要普及长上下文、又受制于 DSA 系统开销的团队来说，这套三管齐下的方案提供了即插即用的优化思路。"
            ],
            "fig_after": {
                "0": [
                    {
                        "src": "fig03.png",
                        "caption": "Figure 4: 不同上下文长度下 LSA 与 DSA 的单注意力层训练延迟。柱形报告前向、反向与总延迟（含内核执行）。"
                    }
                ],
                "1": [
                    {
                        "src": "fig04.png",
                        "caption": "Figure 5: LSA 与 DSA 基线在端到端推理上的延迟对比：prefill 的首 token 时间（TTFT，对数刻度）与 decode 的每输出 token 时间（TPOT）。"
                    }
                ],
                "2": [
                    {
                        "src": "fig05.png",
                        "caption": "Figure 6: 流感知索引（SI）消融。“X% fixed”= 将预算 K 的 X% 分配给固定窗口与 sink tokens。(a) 相对 MLA 的训练损失差距。"
                    }
                ],
                "3": [
                    {
                        "src": "fig06.png",
                        "caption": "Figure 7: 跨层索引（CLI）消融（base 模型）。(a) 相对 MLA 的训练损失差距。(b) 长上下文验证损失。(c) Needle-in-a-haystack 检索。"
                    },
                    {
                        "src": "fig07.png",
                        "caption": "Figure 8: 所有 3 步 MTP 的指标变化（DSA + CLI − MLA）。准确率与损失的差异在整个训练中紧贴零，确认稀疏改造未损害预测质量。"
                    },
                    {
                        "src": "fig08.png",
                        "caption": "Figure 9: 上下文长度扩展消融。(a) 128K 阶段的损失差距（LSA − MLA）。(b) 512K 阶段的损失差距。(c) SFT 损失差距。"
                    }
                ]
            }
        }
    ],
    "conclusion": [
        "LongCat Sparse Attention 的洞察很务实：DSA 的闪电索引器让稀疏注意力在算法上成立，但**真正落地难在系统层**——打分贵、访问散。LSA 不否定稀疏注意力，而是把索引本身重新设计成又快又硬件友好的组件。",
        "流感知索引处理了「访问散」，把 sink 与流式头的 KV 排成连续布局；跨层索引处理了「重复劳动」，一层算、多层共享，配合蒸馏不掉点；分层索引处理了「打分贵」，coarse-to-fine 先把候选集砍小再做精打分。三者正交可叠加，换来从 69B 到 560B 全程追平全注意力、并支撑 100 万 token 原生训练与 1.6T 参数 LongCat-2.0 的成绩。"
    ],
    "reference_url": "https://arxiv.org/html/2608.01662v1"
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path}")
