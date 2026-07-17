要点速览

- 975B MoE首发：TML开源Inkling：975B总参数、41B激活参数，全/滑动窗口注意力交替。- 双厂FP4原生：NVFP4跑NVIDIA B200/B300，MXFP4（AMD Quark量化）跑AMD MI350X/MI355X。- 扁平KV缓存：单一分页池配异构视图，统一分配单元却不强制统一页大小，省显存不碎片。- 统一kernel API：一套API横跨NVIDIA/AMD，复用模型逻辑，只在关键处做专门优化。- MTP提速2.3×：B200上MTP(8 draft steps) 达354.6 tok/s/用户，比关MTP提升2.33×。

Thinking Machines Lab（TML）发布开源MoE模型Inkling，总参数975B、每token激活41B。TokenSpeed与TML合作，在首发日就为其提供跨NVIDIA/AMD的推理支持。本文梳理其架构、原生FP4检查点，以及支撑跨平台推理的引擎与kernel工作。

核心亮点
面向AMD的原生MXFP4权重：用AMD Quark生成并发布Inkling MXFP4检查点，提供NVFP4的AMD原生替代方案。

面向复杂注意力的扁平KV缓存架构：为全注意力、滑动窗口注意力与卷积状态设计异构视图的扁平缓存布局，分配与调度统一且不浪费显存。
借助TokenSpeed Kernel统一多芯片开发：一个kernel API横跨NVIDIA与AMD，复用模型逻辑、只在关键处专门优化。
面向NVIDIA的更快CuteDSL解码kernel：专为解码写的注意力kernel，比prefill路径更高效映射短查询、长KV负载。
面向AMD的高性能Gluon注意力：用persistent prefill与split-K decode设计，在AMD GPU上实现强劲性能。
原生FP4量化的模型
Inkling是基于transformer的MoE模型，交替使用全注意力与滑动窗口注意力。模型共66层、256个路由专家，每token激活6个路由专家与2个共享专家，总参数达9750亿。其基准测试成绩与其他开源模型相当。

参考检查点使用BF16，NVFP4量化版本在NVIDIA GPU上运行。为支持AMD GPU，团队用AMD Quark将模型量化为面向MI350X/MI355X的MXFP4，检查点发布于lightseekorg/Inkling-MXFP4。评测中NVFP4与MXFP4检查点在质量上接近BF16基线，同时实现更高服务性能。

借助原生Kernel加速推理
TokenSpeed的模块化架构将模型层、调度器与kernel子系统在清晰边界后分离。启用Inkling因此是一个系统性过程：编写与加速器无关的模型逻辑、复用现有调度器、用统一kernel API从同一套模型集成拉起NVIDIA与AMD支持。在此共同基线之上，再加入针对每种加速器架构定制的推理引擎技术与原生kernel。

面向异构状态的扁平缓存布局
Inkling推理携带三种持久状态：全注意力层不断增长的KV状态、滑动窗口层有界的KV状态，以及卷积的窗口状态。为每个状态维护独立内存池会碎片化缓存并使调度复杂化；而单一池子配统一页形状又会把较小条目填充到最大页体积造成浪费。

TokenSpeed改用单一扁平分页池配合异构视图。类似原则也见于vLLM中的Jenga（分离物理内存分配与逻辑内存组织）。Inkling的66层构成11个重复单元，每单元含5个滑动窗口层与1个全注意力层，连同6个KV卷积与6个隐状态卷积，每个单元映射到一个slab。一个block ID在所有11个slab中选相同大小的固定槽位；因各状态每token占用不同，该槽位可容纳256个全注意力KV、128个滑动窗口KV或KV侧卷积状态、或16个隐状态卷积状态。这保持了分配单元统一，又不必强制逻辑页大小统一。
缓存管理层次中，一个协调器把每个请求分发给各缓存组，每组维护自己的按请求BlockTable。表项持有指向共享块池的引用计数BlockRef，page ID k直接映射到物理slab第k行。组管理器控制匹配与淘汰策略，但内存所有权集中，使释放页能安全、立即跨组复用。物理布局与管理层次一起，在单一共享分配器与单一调度模型之上提供异构缓存视图。
面向NVIDIA GPU的CuteDSL注意力
注意力占据Inkling计算的很大一部分，但prefill与decode形态截然不同。prefill时Q序列很长，FlashAttention风格kernel有足够并行度沿Q长度分块，因此复用TML的FlashAttention-4（FA4）路径（由Colfax Research开发）。
decode时查询通常只有一两个token，KV缓存却可能很长；偏好prefill的kernel围绕大Q分块组织，许多计算通道未被充分利用。专用decode kernel改为在长KV序列上流式处理，把小的查询/预测维度更高效地打包进每个CTA分块，提升了短查询decode的GPU利用率。
为支持softmax前施加的相对偏置，FA4 prefill路径用独立ShearingBias预处理kernel（开销可在多查询行摊薄）；decode时查询维度足够小，可直接在在线softmax循环内计算相对索引。

面向AMD GPU的Gluon注意力
对AMD GPU，团队扩展了TokenSpeed现有的Gluon注意力kernel以覆盖Inkling的prefill与decode负载：prefill用persistent循环，decode用split-K。由于与NVIDIA后端一同实现统一kernel API，模型代码保持加速器无关，而AMD路径能以最小集成工作量使用专门的高性能kernel。
端到端性能预览
在多轮agentic工作负载上（50K+ token上下文、每对话10–15轮、缓存命中率约90%），TokenSpeed在4张NVIDIA B200上以NVFP4运行Inkling：并发1时每用户317 tokens/s，其中MTP（多token预测，3个draft步）每轮迭代推进约3.3个token。关闭MTP时，并发1维持每用户152 tokens/s（每迭代6.6 ms），并发4维持每用户122 tokens/s，此时系统吞吐量达40K tokens/s。
batch size 1时，3/1/4、5/1/6、8/1/9三种MTP配置（对应3、5、8个draft步）分别带来每用户317.5、342.5、354.6 tokens/s；相比关闭MTP的152.4 tokens/s，decode吞吐提升2.08×、2.25×、2.33×。
MXFP4检查点也让AMD上的agentic服务切实可行：让975B模型在4张MI355X上运行，同时保留足够缓存支撑50K+ token上下文与多轮对话。由于TokenSpeed将模型逻辑与调度同kernel分离，AMD可复用与NVIDIA相同的MTP路径而无需改动模型层。早期MI355X运行中，batch size 1–4范围内MTP将每用户decode速度从2.4x提升至1.5x。

结语

Inkling的发布验证了「一个模型、双厂原生FP4、统一kernel API」的跨平台推理路线：NVIDIA走CuteDSL专用decode kernel，AMD走Gluon persistent/split-K，底层却共享同一套模型逻辑与调度。性能上，MTP是这次最大的杠杆：B200上8 draft steps把decode吞吐顶到354.6 tok/s/用户，比关MTP提升2.33×；MXFP4则把975B模型塞进4张MI355X跑长上下文agentic负载。这些仍是早期数字（对照组仅152.4 tok/s），团队仍在持续压榨调度、缓存与厂商原生kernel，后续还有不小的提升空间。

参考：https://lightseek.org/blog/tokenspeed-inkling.html