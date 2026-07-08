<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>外卖公司造出万亿参数大模型</strong>：美团 LongCat Lab（原"光年之外"团队）发布了 LongCat 2.0，一个 1.6T 参数的模型，完全在华为国产 910C 芯片上训练，Terminal Bench 2 达到 70.8%<br><br>
- <strong>华为 CloudMatrix 384 正面挑战 NVL72</strong>：384 个 NPU 的单扩展域（vs NVL72 的 72 个 GPU），BF16 计算量接近翻倍，内存容量超 3.6 倍——代价是功耗高出 4.1 倍<br><br>
- <strong>UB-Mesh 统一互联取代 NVLink + PCIe 混合栈</strong>：华为开源的内存语义互联协议，支持 384 NPU + 192 CPU 的 P2P 全互联，节点间带宽退化低于 3%<br><br>
- <strong>N+1 备用 NPU + 自动愈合架构</strong>：每机架一个备用 NPU，路由系统支持快速故障恢复，让大量低性能组件也能可靠训练
</div>
</div>

---

**美团 LongCat Lab 发布 LongCat 2.0，一个完全在华为 Ascend 910C 芯片上训练的 1.6 万亿参数模型**——这一消息在 AI 社区引发了不小的震动。但比模型本身更值得关注的，是这件事折射出的两个深层次故事：一个外卖巨头为什么要自建前沿 AI 实验室？华为又如何用一套"低配硬件的并行集群"做出了比肩 Nvidia 旗舰系统的算力？

先说美团。想象一下把 Uber Eats、DoorDash、Yelp、Groupon、TripAdvisor 全部塞进一个 App，那就是美团的日常——中国最大的生活方式超级应用。用户在同一界面里订外卖、骑共享单车、买电影票、订酒店、抢美发团购券。而超级应用的超能力来自 AI：用户只需告诉原生助手"小美"预算和位置，AI 就能在 7 亿实时商家库存和 13 亿用户评论中完成交叉检索，自主完成决策。

**AI 对美团不是可选项，是生存必需品。** 在阿里巴巴、京东、字节跳动等超级应用对手环伺的战场，谁先让 AI 帮用户自动驾驶日常生活，谁就能拿走每年数百亿的增量收入。美团的逻辑与 Meta 完全一致——LLM 层太重要了，必须自己掌握。

LongCat Lab 的诞生本身就是一个充满戏剧性的故事。2023 年初，ChatGPT 发布后不久，美团联合创始人王慧文自掏腰包 5000 万美元创立"光年之外"，立志打造"中国的 OpenAI"，吸引了包括 CEO 王兴在内的多位美团元老投资。他开启了中国 AI 实验室追逐 OpenAI、Anthropic 的浪潮（DeepSeek、Moonshot、Z AI 均在此列）。可惜压力太大，到 2023 年 6 月王慧文因心理健康问题退出，美团出手收购了这家实验室。

**今天回头看，那笔收购是一笔超值的投资。** 团队虽然不完全一样，但王慧文奠定的基础催生了 LongCat 2.0——一个 1.6T 参数、60%+ 基准测试成绩的模型，而且是完全在中国国产芯片上训练出来的。这在训练大模型越来越难的今天，本身就是一次宣言。

<span style="font-size:12px;color:rgb(153,153,153);">美团 LongCat 从 Nvidia NVL72 "跳"向华为 CloudMatrix 384</span>

LongCat 2.0 最大的亮点不是参数规模——DeepSeek V4 Pro 也是 1.6T，Moonshot 据说也有 1T 参数模型。真正的新意在于：**这是第一个公开已知完全在华为 Ascend 910C 上训练的模型，只用了 5 万颗 ASIC。**

据 SemiAnalysis 的分析，华为存够了 160 万颗 910C 芯片的零部件。5 万颗就能训出一个 1.6T 模型，160 万颗意味着什么不言而喻。而且中芯国际还在基于 7nm 节点为华为持续供货——逻辑芯片不是瓶颈。

但华为 Ascend 910C 的纸面参数其实不算亮眼：128GB HBRAM、3.2TB/s 带宽。对比 Nvidia B200 的 192GB HBM/8TB/s 带宽、B300 更是到了 288GB/22TB/s。单芯片完全不在一个级别。

**华为的破局之道，不在单芯片，在集群体系结构。**

Nvidia NVL72 用 72 个 GPU 组成一个单扩展域——任何 GPU 都可以直接访问其他 GPU 的 HBM，铜缆背板连接，低延迟高带宽。这是一台"巨型 GPU"。

华为 CloudMatrix 384 的思路完全不同：**用 384 个 NPU 组成一个单扩展域。** 每个 Ascend 910C 单芯片确实降级，但把 384 颗拼在一起，总 BF16 算力达到 300 PFLOPs——几乎是 GB200 NVL72 的两倍！聚合内存容量超 3.6 倍，内存带宽超 2.1 倍。

**代价也是巨大的：功耗是 NVL72 的 4.1 倍。** 每 FLOP 功耗差 2.5 倍，每 TB/s 内存带宽功耗差 1.9 倍。但对中国来说，电力是国内供应链，光通信和网络设备也是——这是一笔可控的成本。

支撑这套系统的核心是 **UB-Mesh**——华为开源的统一互联协议。它被设计用来取代目前数据中心中 PCIe、NVLink、TCP/IP 的"混合"方案，统一为内存语义（load/store/atomic）的互联结构。在 CloudMatrix 384 中，384 个 NPU 和 192 个鲲鹏 CPU 通过 UB 交换机全互连，节点间带宽退化低于 3%，延迟增加不到 1 微秒。

**更值得关注的是内存池化。** CloudMatrix 384 把所有 192 个 CPU 的 DRAM 聚合为一个共享高性能内存池，384 个 NPU 中的任何一个都可以通过 UB 网络以统一带宽和延迟访问。这彻底改变了一个关键瓶颈：传统架构中 KV 缓存必须路由到持有它的节点，否则远程访问太慢。在 CloudMatrix 中，任何 NPU 都可以从共享池直接拉取数据，请求调度完全与数据位置解耦。

好处是三重：消除了传统架构中 DRAM 利用率低下的孤岛问题；简化了调度（不需要缓存感知路由）；显著提高了突发工作负载下的缓存命中率。**这几乎是每个做 KV 缓存优化的人梦寐以求的能力——Nvidia 生态系统中还需要通过 SGLang HiCache + Mooncake 等软件层实现，华为已经在硬件层面内置了。**

另一个巧妙的设计是 **N+1 容错**：每个机架有一个备用 NPU。当 NPU 故障时自动激活恢复训练。路由系统还支持链路故障的快速自动愈合。这使得华为可以在系统中大量使用"低性能"组件而不牺牲可靠性——因为他们的系统组件数是 Nvidia 等效系统的数倍，故障是必然的，关键是如何从故障中恢复。

**LongCat 团队自己也做了一个同样精妙的设计。** 受 DeepSeek Engram 方法的启发（用 CPU 内存换取 ASIC 计算和 HBM），他们添加了一个 N-gram Embedding 模块，将嵌入空间扩展了约 100 倍。通过保存 n-gram token 组合来捕获更丰富的局部上下文，代价是多用了一些 CPU DRAM，但省下了更宝贵的 ASIC FLOPs 和 HBM 带宽。公平地说，LongCat 的论文《LongCat Flash》在 DeepSeek Engram 发布仅两周后就发表了，且关键设计有显著差异——很可能是独立发明。

<span style="font-size:12px;color:rgb(153,153,153);来源：SemiAnalysis CloudMatrix 384 分析</span>

这背后反映的是一个更宏大的趋势：**整个中国 AI 生态系统已经达到了"逃逸速度"。** DeepSeek 的 MLA、DSA、CSA、HCA 等技术被广泛采用——比如 CSA 和 HCA 将 KV 缓存的 HBM 需求减少 98%，DSpark 将解码阶段带宽需求减少 66%。长鑫存储正在突破 HBM3，长江存储提供了"足够好"的 NAND。从芯片到互联到内存到模型架构，所有关键环节都开始有了国产替代方案。

**一个外卖公司做出了一流的基础模型。** 如果 Uber 或 Doordash 不造模型，为什么美团要？答案是：中国有微信、支付宝、抖音、淘宝这样的超级应用——西方还没有见过这种东西。AI 让这些超级应用变得更强大，帮助用户自动驾驶日常生活。不能掌控 LLM 层的公司，在这个赛道上连参赛资格都没有。

而对于华为来说，他们正在证明一件事：**出口管制不是不可逾越的天花板。** 用更多芯片、更先进的互联、更聪明的架构设计，可以用"低配组件"做出"超配系统"。CloudMatrix 384 不是 Nvl72 的替代品——两者根本就是不同哲学下的产物。

---

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
华为 CloudMatrix 384 不等于 Nvl72，它不是"对标品"而是"替代方案"——用系统工程的思维，在单芯片性能被限制的条件下从集群层面找突破。这种思路本身就给整个行业提了一个问题：当电力不再是约束时，"更多但更弱"的方案是否比"更少但更强"更有工程优势？<br><br>
LongCat Lab 的出现也值得深思。当一家外卖公司都开始训练 1.6T 参数的模型，说明 AI 竞争已经从"技术赛道"变成了"生存赛道"——不上船，就会出局。下一个"意想不到的选手"会是谁？高德？货拉拉？还是携程？<br><br>
最后，华为把 UB-Mesh 开源这件事值得单独提一笔。内存语义互联如果成为行业标准，整个数据中心的网络架构都将重新洗牌。这不是一个"国产平替"的故事——这是一场互联革命的前奏。
</div>
</div>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://x.com/bookwormengr/status/2072421710692028900</span>
