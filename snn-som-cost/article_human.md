<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>核心做法</strong>：CTA-pipelining把跨GPU的数据依赖kernel拆到CTA粒度做空间流水线，消费者CTA一拿到生产者产出的数据块就立刻启动，无需等整层算完。<br><br>
- <strong>关键收益</strong>：相比micro-batching延迟最高降31.8%，相比张量并行（TP）最高降29.6%，且能作为正交维度与TP组合进一步压低延迟。<br><br>
- <strong>侵入极小</strong>：只在kernel首尾注入prologue/epilogue代码片段，不改核心实现，可对接CUTLASS等现有库直接在8卡H200/B200上跑。
</div>
</div>

---

## 问题：TP给延迟优化设了天花板

多GPU部署LLM推理，通用基线就是流水线并行（PP）和张量并行（TP）。PP在层间切分只为提吞吐，TP在算子层面空间切分能同时降延迟。但TP每两层就要一次All-Reduce集合通信来消解数据依赖，这给单batch延迟优化画了一道硬天花板。

这些方案都不是冲着单batch延迟去的。CTA-pipelining补的正是这块：用细粒度空间流水线，把跨GPU的依赖kernel并发跑起来。

## CTA-pipelining：在CTA粒度上跨GPU流水线依赖kernel

CTA（协作线程阵列）是GPU最细的执行粒度。老做法是等生产者kernel整段跑完，才轮到消费者；CTA-pipelining不这么干：生产者每吐出一个输出块，对应的消费者CTA马上启动去接。依赖的kernel摊到多GPU上，几乎同时点火、同时收工，只有消费者尾部最后一轮略晚半拍。

![](fig01.png)
<span style="font-size:12px;color:rgb(153,153,153);">图1：双GPU下CTA-pipelining的整体执行架构（含依赖数组、记分牌、跨设备工作队列三类组件）</span>

## 协议核心：依赖数组、记分牌、跨设备队列

支撑这套控制流的是三个数据结构，统称依赖结构：

- **依赖数组**：以生产者CTA ID为索引，标明它影响哪些消费者CTA，存在生产者设备内存。
- **记分牌**：原子计数器数组，每个消费者CTA一个条目，初始化为前置生产者数；归零即表示"我就绪了"，也存生产者侧。
- **跨设备工作队列**：环形缓冲区作就绪信号。放在消费者设备内存以压低关键路径延迟，生产者用CUDA异步写"发射后不管"，消费者单线程忙轮询。

注入的逻辑极轻：生产者CTA把输出经NVLink直写消费者输入内存后，发系统级内存屏障，再原子递减记分牌；计数器归零就把就绪的消费者CTA ID推入队列。消费者侧prologue单线程轮询队列、广播取值，CTA把自己重映射成该ID，跑标准未改动的kernel负载。核心kernel一字不动，只加了首尾片段。

图3给出多层GEMM的流水线示意，第一层输出被第二层直接消费。

![](fig04.png)
<span style="font-size:12px;color:rgb(153,153,153);">图3：多层GEMM的CTA-pipelining执行流程（每层即一个流水线阶段）</span>

## 开销实测：warp特化kernel里几乎为零

开销评测在8卡H200（经典SM90 kernel）和8卡B200（SM100 warp特化持久kernel）上进行，GEMM尺寸16384×8192。

- 经典kernel：每CTA epilogue约6μs，跨设备可见需120μs，消费者prologue取队列约1.5μs，且逐轮累积。
- warp特化持久kernel：利用微流水线中其他warp的等待空闲，把协议操作塞进去。跨设备写可见仅5μs，prologue 1.5μs、广播0.5μs均被隐藏。开销只在流水线初始爬升时可见一次。

实测两个连续GEMM基线各自1080μs；套上CTA-pipelining后，生产者1090μs、消费者1165μs（含可见开销与末轮流水线延迟）。没动原kernel的寄存器分配和共享内存，不引发溢出。

## 对比micro-batching：最高降31.8%

负载为多层GEMM（模拟MLP层，省去激活），权重固定8192×8192，每GPU一层、GPU数即层数；基线用cuBLAS+CUDA Graph，并扫描最优chunk尺寸保证公平。

![](fig06.png)
<span style="font-size:12px;color:rgb(153,153,153);">图4：不同GPU数与chunk尺寸下，CTA-pipelining相对micro-batching的延迟降低（R-MB）</span>

结果：对比扫描中最优chunk，CTA-pipelining在2/4/8 GPU下分别降31.8%/30.0%/23.4%。micro-batching的根本矛盾是chunk尺寸两难：chunk太大会拉长流水线头尾、降低并行度；太小则单kernel效率崩、启动气泡多。CTA-pipelining在CTA级重叠，又不显式切chunk，保住原生kernel效率，直接化解这个两难。极小输入（序列长1024、kernel仅百微秒级）时协议开销会凸显，但此时micro-batching也到极限。

## 对比TP：最高降29.6%，且能与TP正交组合

![](fig07.png)
<span style="font-size:12px;color:rgb(153,153,153);">图5：不同输入序列长度下，CTA-pipelining相对TP的延迟降低（R-TP）</span>

纯CTA-pipelining在2/4/8 GPU上相对TP降29.0%/46.2%/59.0%，主要因为完全绕开了All-Reduce。但有的负载kernel不够多、凑不出足够流水线阶段，这时把它和TP组合：硬件切成2-GPU组，组内用CTA-pipelining跑本地两层GEMM，最终All-Reduce的world size减半。

![](fig10.png)
<span style="font-size:12px;color:rgb(153,153,153);">图7(a)：CTA-pipelining+TP组合的总延迟（线）与计算/通信拆分（柱）</span>

![](fig12.png)
<span style="font-size:12px;color:rgb(153,153,153);">图7(c)：高TP度下纯TP因通信主导反而变慢，组合方案继续降延迟</span>

组合方案最实在的账是：All-Reduce的world size砍半、通信时间直接掉下来；同时不必上那么高的TP度，矩阵维度保得更大，计算效率也跟着沾光（个别尺寸被流水线爬升延迟吃回去一部分）。两者正交，能直接叠。

## 讨论：中心化NVLink拓扑限制重叠

CTA-pipelining依赖NVLink营造的"共享内存错觉"。但8卡B200经NVSwitch中心化交换，每GPU并发进出带宽被这颗星型交换机卡住。生产者直写消费者内存会长期占住同一物理链路，消费者想和第三方通信做计算-通信重叠时只能跟它抢带宽。论文提到更分散的NVLink拓扑（如GB200 NVL72多Switch）能化解：一栈CTA-pipelining kernel塞进单一Switch下，二次通信走另一Switch，重叠才真正可行。

<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
这套工作的价值不在某个新kernel，而在把"跨GPU依赖kernel的细粒度空间流水线"做成了一个对现有库几乎零侵入的软件协议：只加prologue/epilogue就能让CUTLASS kernel跨设备并发跑。<br><br>
它和TP不是替代关系而是正交维度，给部署多GPU LLM推理多了一根延迟杠杆，尤其适合能端到端纯CTA-pipelining执行的负载。<br><br>
真正的瓶颈已经不在软件而在互连拓扑：中心化NVLink让"共享内存错觉"在物理上撑不住，后续收益要看更分散的交换机拓扑和硬件级kernel间信令支持。
</div>
</div>


---

<span style="font-size:14px;color:#888888;font-family:'Courier New',monospace;">【传送门】<br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OqtF6ZaWQNu3o-VAWLfqbg" target="_blank" data-linktype="2">榨干GPU性能：流水线解码消除GPU气泡，推理吞吐提升35%</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/TrDau7cG1M7kwsLQNwOpzA" target="_blank" data-linktype="2">揭秘最快的GLM-5.2推理优化技术：如何将吞吐推到280 TPS</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/HnGKVp45C-GApBJ-LleP6g" target="_blank" data-linktype="2">小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/Ww55Gc65e32oFDEXw24VRA" target="_blank" data-linktype="2">A4Q：大神用Claude一天给Blackwell写出原生4-bit Attention Kernel，花费$5.34</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/nVqW9acA7NN1zeALDwRAsw" target="_blank" data-linktype="2">Google新论文RubricEM: 评分标准引导的深度研究Agent训练框架</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/OoHu1yeuh1gzgCfEiPvDuQ" target="_blank" data-linktype="2">RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/g2sTEQwPjDcmas42qU49nw" target="_blank" data-linktype="2">Anthropic用J透镜打开LLM意识黑箱J-Space,揭秘干预LLM思维的新训练技术</a><br>
<a class="normal_text_link mp_article_text_link" href="https://mp.weixin.qq.com/s/FTsibdpbEjvoPWtxGqgxkQ" target="_blank" data-linktype="2">小米MiMo罗福莉后训练新范式MOPD: 多教师同策略蒸馏，多领域无损集成</a><br>
</span>

---

<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：https://arxiv.org/html/2607.07862v1</span>
