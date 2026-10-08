#!/usr/bin/env python3
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
    "title": "CoMoE:把主机内存变成路由中心，RTX 5090 跑 MoE 接近 A800",
    "reference_url": "https://arxiv.org/html/2610.09424v1",
    "summary": [
        {"key": "核心观点", "body": "把主机内存从被动中转提升为主动路由中心，dispatch 写一次、combine 按 token 聚合，干掉冗余传输与全局同步。"},
        {"key": "关键数据", "body": "RTX 5090 上吞吐最高提升 1.46 倍，硬件成本仅为 A800 的 23.4%，性能接近后者。"},
        {"key": "方法创新", "body": "host-backed token multicast 与细粒度分解 combine，把 All-to-All 拆成单边读写。"},
    ],
    "lead": [
        "MoE 推理离不开专家并行，token 在 GPU 之间疯狂搬运。数据中心靠 NVLink 这种高速互联硬扛，**消费级 GPU 只有可怜的 PCIe 带宽，还不支持 P2P**，通信直接成为瓶颈。",
        "CoMoE 的思路很妙：**与其抱怨互联 topology 差，不如把主机内存扶正**，让它从被动的中转缓冲区变成主动的路由中心，从根本上减少通信量、消灭同步等待。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "消费级 GPU 跑 MoE：通信是命门",
            "paras": [
                "数据中心 GPU 之间有 NVLink 全互联，消费级卡之间只能走 PCIe switch，经 CPU 和主机内存中转。**带宽差一个数量级，还没有 P2P**，MoE 那种动辄把 token 发往 3 到 5 个 GPU 的路由模式，在这种 topology 上直接窒息。",
                "专家并行里每个 token 要发给 top-k 个专家，专家散落在不同 GPU 上。实测显示，E=64、k=4 的配置下，**平均每个 token 要扇出到 3.38 个 GPU**。传统做法把 dispatch 建模成 All-to-All 集合通信，语义上就错了：All-to-All 假设每个消息都独一无二，而这里是同一个 token 发多份。",
                "动机很直接：消费级 GPU 算力不差、价格只有零头，**如果能把通信短板补上，MoE 推理就能走进个人与本地隐私部署**。CoMoE 要回答的就是这个问题。",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig01.png", "caption": "图1：数据中心 GPU 与消费级 GPU 的互联对比。左侧 NVLink 全互联，右侧只能经 PCIe switch 和主机内存中转，无 P2P，带宽受限。"},
                ],
                "1": [
                    {"src": "fig02.png", "caption": "图2：专家并行中的 token 路由示例。一个 token 被发往多个专家所在的 GPU，传统 All-to-All 把同一份数据重复传输多次。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "Dispatch：同一个 token 只写一次",
            "paras": [
                "先算一笔账：按 All-to-All 语义，源 GPU 要把同一个 token 给每个目标 GPU 各发一份，**出口流量随目标数线性膨胀**。E=128、k=8 时平均扇出 5.34，意味着一份数据要发 5 遍，纯属浪费。",
                "CoMoE 的解法是 host-backed token multicast：**源 GPU 把 token 往主机内存写一次**，各目标 GPU 自己来取。写一次、读多次，冗余传输直接清零。主机内存从“中转站”升级成“分发中心”，语义从点对点变成一对多组播。",
                "这招能成立，恰恰是因为消费级 topology 的“劣势”：反正所有跨卡流量都要过主机内存，**不如把必经之路变成主动设计**，而不是被动承受。",
                "实测的 dispatch 开销印证了判断：token 到 GPU 的平均扇出随模型规模增长，**冗余传输占 dispatch 总流量的大头**。组播化之后，这部分开销几乎归零，剩下的就是必要的有效载荷。",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig04.png", "caption": "图4：两种 dispatch 方案对比。(a) 传统 All-to-All 把同一 token 向每个目标各发一份；(b) CoMoE 经主机组播只写一次，各 GPU 按需读取。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "Combine：拆掉全局同步",
            "paras": [
                "Combine 阶段的传统做法更值得推翻：同步 All-to-All 要求所有 GPU 到齐才往下走，**一个 straggler 拖住全局**，而且规约计算要等所有数据到齐才能开始，白白浪费重叠机会。",
                "CoMoE 指出一个关键事实：重建某个 token 只需要它自己的专家输出到齐，**跟别的 token、别的 GPU 的进度毫无关系**。MoE combine 的最小同步单元是 token，不是整个 batch。全局同步从一开始就是过度设计。",
                "于是把 All-to-All 拆成单边读写：发送方把专家输出**单边写**进主机 staging buffer，接收方按 token 粒度**单边读**回来做规约。发送和接收彻底解耦，**快的 GPU 不用等慢的**，通信和计算还能重叠起来。",
                "实现上用 fused transfer kernel 把传输和规约融进一个 kernel：接收侧把 token 块读进来直接做 reduce，发送侧写 buffer 不阻塞。流水线式的规约让 combine 延迟进一步被隐藏。",
            ],
            "fig_after": {
                "1": [
                    {"src": "fig05.png", "caption": "图5：传统 All-to-All 与 CoMoE combine 对比。左侧全局同步等 straggler，右侧按 token 粒度经主机 buffer 解耦，发送接收互不阻塞。"},
                ],
                "2": [
                    {"src": "fig06.png", "caption": "图6：combine 阶段的 fused transfer kernel。发送方单边写主机 buffer，接收方单边读回并做 token 级规约，通信与计算重叠。"},
                ],
                "3": [
                    {"src": "fig07.png", "caption": "图7：流水线规约。token T0/T1/T2/T4 的专家输出陆续到达即陆续规约，不必等整个 batch 到齐。"},
                ],
            },
        },
        {
            "type": "h2",
            "title": "结果：5090 接近 A800",
            "paras": [
                "延迟先看：不同请求率下，**TTFT 平均降 18.8%，TPOT 平均降 26.9%**。负载越轻，通信占比越高，优化效果越明显；重载下排队延迟占主导，提升收窄，符合预期。",
                "吞吐量更直观：Qwen3-30B-A3B 从 3914 涨到 5506（**1.41 倍**），GPT-OSS-20B 从 4991 涨到 7304（**1.46 倍**）。**RTX 5090 上的 CoMoE 直接对标 A800 基线**，把消费级和数据中心的性能鸿沟填上了一大截。",
                "性价比是杀手锏：**硬件成本只有 A800 的 23.4%**，性能却接近。这意味着个人工作站、私有化部署也能跑大 MoE 模型，不用再为 NVLink 交税。",
                "GPT-OSS 上提升最大（TPOT 降 29.9%），因为它的 hidden dim 更大（2880 vs 2048），路由时搬运的 hidden state 更多，**通信优化的收益自然更大**。这也反证了瓶颈确实在通信不在计算。",
            ],
            "fig_after": {
                "0": [
                    {"src": "fig03.png", "caption": "图3：TTFT 与 TPOT 随负载的变化。CoMoE（深色线）在各请求率下全面低于基线，轻载下优势最大。"},
                ],
                "1": [
                    {"src": "fig08.png", "caption": "图8：各模型吞吐量对比。CoMoE 在 RTX 5090 上把四个 MoE 模型的吞吐全部抬升，最高达基线的 1.46 倍。"},
                ],
            },
        },
    ],
    "conclusion": [
        "CoMoE 最大的启发是**把硬件的“劣势”变成设计的支点**：既然消费级 GPU 的跨卡流量必经主机内存，那就让主机内存成为路由中心，而不是被动的中转站。",
        "dispatch 写一次、combine 按 token 解耦，这两招都不依赖特殊硬件，**思路可以搬到任何带宽受限的互联上**。MoE 推理平民化的路，这篇算是铺了一段实的。",
    ],
}
json.dump(DATA, open(_article_dir + "/article_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("article_data.json 已写入")
