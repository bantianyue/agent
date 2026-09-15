/* 传送门统一样式（add-portal.py动态注入时引用此class） */
.portal-title { font-size:12px; color:#888; }
.portal-links { font-size:12px; color:#888; }
.portal-links a { color:#888; text-decoration:none; }

要点速览

-核心机制：在函数执行之前，用__torch_dispatch__ 把前向和后向一起追踪进一张联合图，再用partition_fn切回两张独立图，编译器第一次能跨前向后向的边界做优化。-两种切分策略：default_partition把中间张量全保存下来，后向直接读；min_cut_rematerialization_partition把存与重算写成最大流/最小割问题，只保留输入，后向重算中间值。-省下来的是什么：逐点算子链上前后向都是访存受限，默认切分让每个中间张量被写一次、读一次；min-cut用几乎免费的多余浮点运算换掉这次写和读。

torch.fx和TorchDynamo解决的是同一件事：把Python代码变成一张图。但这两种追踪都只覆盖前向传播，训练里真正耗时的那一半，编译器一直看不到。
后向图原本由autograd引擎在前向跑完的那一刻动态搭出来，编译器插不上手，前向与后向之间那条边界也就无从优化。AOTAutograd补上了这一半：函数执行之前，前向和后向已经一起被追踪进同一张FX图。
从一个最小的aot_function例子入手，逐张读前向图和后向图，再看联合图怎么建起来、怎么被切回去，以及min-cut重算为什么能用几乎免费的计算换掉真实的访存。

后向传播：编译器看不到的另一半
前两篇里，torch.fx用符号追踪把Python代码变成图，TorchDynamo在字节码层面捕获图。但两者抓到的都只有前向传播。后向传播怎么办？
在torch.compile这套生态出现之前，用户可以用torch.fx追踪捕获前向图，后向却仍由autograd引擎动态生成，编译器只能看到前向那一半。前向和后向两张计算图因此无法合并成一张，跨这条边界的优化也就无从谈起。
AOTAutograd解决的正是这件事：它在执行之前把前向和后向一起追踪出来，编译器于是可以把整张图当成一个整体来做优化。
aot_function：最小能跑的例子
先从functorch.compile里最简单的aot_function入手。定义一个把两个张量相乘的函数，外面套一个只负责打印图的编译器：
import&nbsp;torchfrom&nbsp;functorch.compile&nbsp;import&nbsp;aot_function,&nbsp;make_boxed_funcdef&nbsp;fn(a,&nbsp;b):&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;a&nbsp;*&nbsp;bdef&nbsp;compiler_fn(fx_module,&nbsp;_):&nbsp;&nbsp;&nbsp;&nbsp;print(fx_module.code)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;make_boxed_func(fx_module.forward)a,&nbsp;b&nbsp;=&nbsp;[torch.randn(2,&nbsp;4,&nbsp;requires_grad=True,&nbsp;device=&quot;cuda&quot;)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;for&nbsp;_&nbsp;in&nbsp;range(2)]aot_fn&nbsp;=&nbsp;aot_function(fn,&nbsp;fw_compiler=compiler_fn,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;bw_compiler=compiler_fn)res&nbsp;=&nbsp;aot_fn(a,&nbsp;b)loss&nbsp;=&nbsp;res.sum()loss.backward()
运行后会打印两张图，一张前向、一张后向，我们逐张读。前向长这样：
def&nbsp;forward(self,&nbsp;primals_1,&nbsp;primals_2):&nbsp;&nbsp;&nbsp;&nbsp;mul&nbsp;=&nbsp;torch.ops.aten.mul.Tensor(primals_1,&nbsp;primals_2)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;(mul,&nbsp;primals_1,&nbsp;primals_2)
primal是什么？primal是函数的原始输入，按autograd的术语，就是你施加运算的那些张量。这里primals_1 = a，primals_2 = b。
前向返回(mul, primals_1, primals_2)，为什么要返回三个值？第一个是真正的输出（a * b），另外两个张量是为后向保存下来的。
再看后向图：
def&nbsp;forward(self,&nbsp;primals_1,&nbsp;primals_2,&nbsp;tangents_1):&nbsp;&nbsp;&nbsp;&nbsp;mul_1&nbsp;=&nbsp;torch.ops.aten.mul.Tensor(tangents_1,&nbsp;primals_1)&nbsp;&nbsp;&nbsp;&nbsp;mul_2&nbsp;=&nbsp;torch.ops.aten.mul.Tensor(tangents_1,&nbsp;primals_2)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;(mul_2,&nbsp;mul_1)
前两个参数primals_1, primals_2是前向传下来的已保存张量，tangents就是后向传播里算出来的传入梯度。
后向返回(mul_2, mul_1)，梯度顺序与前向的原始输入(a, b) 一致。正是这个顺序约定，让autograd知道哪个梯度属于哪个参数。
为什么叫AOT：把后向提前到执行之前
正常情况下，PyTorch的autograd在前向传播过程中动态构建后向图，后向图要等前向结束才算最终确定。这种做法很灵活，代价是执行之前你永远看不到完整图。
AOTAutograd换了做法：它在函数真正执行之前，就把前向和后向传播都以提前（Ahead-of-Time）的方式追踪好，两张计算图提前交到你手上。
整体流程是这样几步：
1&nbsp;AOT Dispatch追踪前向和后向，生成一张联合图（joint graph），本质是一张同时包含前向与后向Aten/Prim算子的FX图。
2&nbsp;Partition用partition_fn把联合图切成独立的前向图和后向图。
3&nbsp;Optional decomposition把高层算子拆成粒度更小的算子。
4&nbsp;两张图分别编译，最后整合进一个torch.autograd.Function。
torch dispatcher：算子是怎么被路由的
PyTorch有一个dispatcher，你可以把它理解成路由器。每次调用像a * b这样的算子，dispatcher都会根据输入张量的属性决定跑哪个kernel：是CUDA张量就跑CUDA kernel，需要梯度就用autograd包一层。一个算子通常要穿过多个分发层，才到达最终kernel。

图1：dispatcher像路由器，一次算子调用要穿过多个分发层才到达最终kernel
__torch_dispatch__ 是一个在最终kernel执行之前触发的钩子。它让你拿到原始ATen算子和它的输入，于是可以在算子层面拦截、检查或改写行为。
make_fx：借dispatcher拿到底层算子
torch.fx里有个make_fx，它和普通的symbolic_trace不同，是通过__torch_dispatch__ 实现的，因此能访问底层ATen算子。
看下面的例子。
import&nbsp;torchfrom&nbsp;torch.fx.experimental.proxy_tensor&nbsp;import&nbsp;make_fxdef&nbsp;f(x,&nbsp;y):&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;x&nbsp;+&nbsp;yx&nbsp;=&nbsp;torch.randn(8)y&nbsp;=&nbsp;torch.randn(8)g&nbsp;=&nbsp;make_fx(f)(x,&nbsp;y)print(g.code)
make_fx经由dispatcher追踪，捕获到的是底层ATen算子torch.ops.aten.add.Tensor。
def&nbsp;forward(self,&nbsp;x_1,&nbsp;y_1):&nbsp;&nbsp;&nbsp;&nbsp;add&nbsp;=&nbsp;torch.ops.aten.add.Tensor(x_1,&nbsp;y_1)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;add
符号追踪则是另一套，抽象层级高得多。
from&nbsp;torch.fx&nbsp;import&nbsp;symbolic_traceh&nbsp;=&nbsp;symbolic_trace(f)print(h.code)
def&nbsp;forward(self,&nbsp;x,&nbsp;y):&nbsp;&nbsp;&nbsp;&nbsp;add&nbsp;=&nbsp;x&nbsp;+&nbsp;y&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;add
dispatcher为什么重要到这里就清楚了。接下来看联合图是怎么建起来的。
联合图：把前向和后向装进同一张图
把前向和后向放进同一张FX图，价值在于能跨整条边界做优化，而不是把前向和后向分开看。
思路写成伪代码是这样：
def&nbsp;joint_forward_backward(*inputs):&nbsp;&nbsp;&nbsp;&nbsp;outputs&nbsp;=&nbsp;forward_fn(*inputs)&nbsp;&nbsp;&nbsp;&nbsp;grads&nbsp;=&nbsp;torch.autograd.grad(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;outputs,&nbsp;inputs,&nbsp;grad_outputs=...&nbsp;&nbsp;&nbsp;&nbsp;)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;outputs,&nbsp;grads
追踪过程中，每个算子都会被__torch_dispatch__ 拦截，对每个算子，AOTAutograd依次做四件事：
1&nbsp;从张量上取回FX proxy。
2&nbsp;用ATen算子作为target，在FX图里创建一个call_function节点。
3&nbsp;用真实张量把算子跑一遍。
4&nbsp;把执行结果张量绑定回proxy。
这个过程一直重复，直到前向和后向里的算子全部被追踪完，一张完整的联合图就出来了。
切分联合图：两种内置策略
拿到联合图之后，要把它切回独立的前向图和后向图。AOTAutograd的partition_fn负责这件事，它内置了两种策略，用一个具体例子来对比：
def&nbsp;fn(a,&nbsp;b,&nbsp;c,&nbsp;d):&nbsp;&nbsp;&nbsp;&nbsp;x&nbsp;=&nbsp;a&nbsp;+&nbsp;b&nbsp;+&nbsp;c&nbsp;+&nbsp;d&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;x.cos().cos()
default_partition：中间结果全留下
这是默认行为，也是第一个例子里那种做法：从输入到前向输出，途经所有算子的输出都保留下来，后向需要的张量同样作为前向输出返回，中间结果一个不丢。
def&nbsp;forward(self,&nbsp;primals_1,&nbsp;primals_2,&nbsp;primals_3,&nbsp;primals_4):&nbsp;&nbsp;&nbsp;&nbsp;add&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.add.Tensor(primals_1,&nbsp;primals_2)&nbsp;&nbsp;&nbsp;&nbsp;add_1&nbsp;=&nbsp;torch.ops.aten.add.Tensor(add,&nbsp;primals_3)&nbsp;&nbsp;&nbsp;&nbsp;add_2&nbsp;=&nbsp;torch.ops.aten.add.Tensor(add_1,&nbsp;primals_4)&nbsp;&nbsp;&nbsp;&nbsp;cos&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.cos.default(add_2)&nbsp;&nbsp;&nbsp;&nbsp;cos_1&nbsp;=&nbsp;torch.ops.aten.cos.default(cos)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;(cos_1,&nbsp;add_2,&nbsp;cos)&nbsp;&nbsp;&nbsp;&nbsp;#&nbsp;saves&nbsp;add_2&nbsp;and&nbsp;cos&nbsp;for&nbsp;backward
后向就把这些保存下来的张量当作输入收下来：
def&nbsp;forward(self,&nbsp;add_2,&nbsp;cos,&nbsp;tangents_1):&nbsp;&nbsp;&nbsp;&nbsp;sin&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.sin.default(cos)&nbsp;&nbsp;&nbsp;&nbsp;neg&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.neg.default(sin)&nbsp;&nbsp;&nbsp;&nbsp;mul&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.mul.Tensor(tangents_1,&nbsp;neg)&nbsp;&nbsp;&nbsp;&nbsp;sin_1&nbsp;=&nbsp;torch.ops.aten.sin.default(add_2)&nbsp;&nbsp;&nbsp;&nbsp;neg_1&nbsp;=&nbsp;torch.ops.aten.neg.default(sin_1)&nbsp;&nbsp;&nbsp;&nbsp;mul_1&nbsp;=&nbsp;torch.ops.aten.mul.Tensor(mul,&nbsp;neg_1)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;(mul_1,&nbsp;mul_1,&nbsp;mul_1,&nbsp;mul_1)
背景：逐点算子其实卡在访存上
这一段背景是为了说清下一项技术为什么有效。
在GPU上，一个算子耗掉的时间大头不是算术，而是内存的读写。对逐点算子（add、mul、cos、sin、relu等）尤其如此，它们对每个元素几乎不做多少计算。
所以把多个逐点算子融合起来，可能一点忙都帮不上，因为瓶颈在访存，不在浮点运算量。
放到训练里看，如果你的图是一条逐点算子链，前向和后向都是逐点算子，运行时间正比于读写的数据量。默认切分把每个中间张量都保存下来，等于把访存成本付了两遍：前向写一次做保存，后向读一次做加载。

图2：默认切分下中间张量在前向写一次、后向读一次，访存成本被付了两遍
那如果只保存输入、中间结果在后向里重算呢？这会带来两件事：
1&nbsp;前向和后向之间需要保存的张量变少。
2&nbsp;访存减少，因为既不用写中间结果去保存，也不用读回来加载。

图3：只保存输入、后向重算中间值，保存与加载两侧的访存都降了下来
重算本身几乎不花钱，因为这些逐点算子本来就被访存卡住，多出来的浮点运算会藏在内存延迟背后。这正是activation checkpointing（激活重计算）能成立的原因，AOTAutograd用min-cut建模把它一般化了。
min_cut_rematerialization_partition：存还是重算
既然不必保存所有中间张量，那怎么决定哪些保存、哪些重算？AOTAutograd把这件事写成最大流/最小割（max-flow/min-cut）问题，算法细节可以另外去读。
把同一段代码换成min-cut切分策略：
from&nbsp;functorch.compile&nbsp;import&nbsp;min_cut_rematerialization_partitionaot_fn&nbsp;=&nbsp;aot_function(fn,&nbsp;fw_compiler=compiler_fn,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;bw_compiler=compiler_fn,&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;partition_fn=min_cut_rematerialization_partition)
看前向图，cos不再被保存了：
def&nbsp;forward(self,&nbsp;primals_1,&nbsp;primals_2,&nbsp;primals_3,&nbsp;primals_4):&nbsp;&nbsp;&nbsp;&nbsp;add&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.add.Tensor(primals_1,&nbsp;primals_2)&nbsp;&nbsp;&nbsp;&nbsp;add_1&nbsp;=&nbsp;torch.ops.aten.add.Tensor(add,&nbsp;primals_3)&nbsp;&nbsp;&nbsp;&nbsp;add_2&nbsp;=&nbsp;torch.ops.aten.add.Tensor(add_1,&nbsp;primals_4)&nbsp;&nbsp;&nbsp;&nbsp;cos&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.cos.default(add_2)&nbsp;&nbsp;&nbsp;&nbsp;cos_1&nbsp;=&nbsp;torch.ops.aten.cos.default(cos)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;(cos_1,&nbsp;add_2)&nbsp;&nbsp;&nbsp;&nbsp;#&nbsp;only&nbsp;saves&nbsp;add_2,&nbsp;NOT&nbsp;cos
后向图里，cos是从add_2重算出来的，而不是读保存下来的值。
def&nbsp;forward(self,&nbsp;add_2,&nbsp;tangents_1):&nbsp;&nbsp;&nbsp;&nbsp;cos&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.cos.default(add_2)&nbsp;&nbsp;#&nbsp;recomputed!&nbsp;&nbsp;&nbsp;&nbsp;sin&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.sin.default(cos)&nbsp;&nbsp;&nbsp;&nbsp;neg&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.neg.default(sin)&nbsp;&nbsp;&nbsp;&nbsp;mul&nbsp;&nbsp;&nbsp;=&nbsp;torch.ops.aten.mul.Tensor(tangents_1,&nbsp;neg)&nbsp;&nbsp;&nbsp;&nbsp;sin_1&nbsp;=&nbsp;torch.ops.aten.sin.default(add_2)&nbsp;&nbsp;&nbsp;&nbsp;neg_1&nbsp;=&nbsp;torch.ops.aten.neg.default(sin_1)&nbsp;&nbsp;&nbsp;&nbsp;mul_1&nbsp;=&nbsp;torch.ops.aten.mul.Tensor(mul,&nbsp;neg_1)&nbsp;&nbsp;&nbsp;&nbsp;return&nbsp;(mul_1,&nbsp;mul_1,&nbsp;mul_1,&nbsp;mul_1)
整条栈还差最后一块
到这里，前向图、后向图和联合图都齐了，整条栈还差最后一块拼图：TorchInductor，它负责把捕获到的图降级编译成高效的Triton代码。

结语

AOTAutograd真正的贡献不是让后向跑得更快，而是让后向变成编译器看得见的代码：前向和后向在执行之前就被追踪进同一张FX图，跨边界优化才第一次成为可能。① 联合图是整条思路的地基。每个算子被__torch_dispatch__ 拦下，依次取FX proxy、建call_function节点、用真实张量执行、把结果绑回proxy，前向和后向因此落在同一张图里，而不是各自独立。② 切分方式决定内存账本。default_partition把中间张量全保存，前向写一次、后向读一次，逐点算子链上的访存要付两遍；min_cut_rematerialization_partition用最大流/最小割划出存与重算的边界，只保留输入、后向重算中间值，本质上是activation checkpointing的一般化。③ 重算划得来的前提，是算子本身已经受限在访存上。多出来的浮点运算藏在内存延迟背后近乎免费，省下的那次写和读却是实打实的开销，这让min-cut的选择变成纯粹的收益。想亲手验证这套机制，最短路径是用aot_function配一个只打印fx_module.code的编译器：前向多返回了哪些张量、后向把它们当作什么收下，读几张图就能看清编译器的内存账本是怎么记的。这也是理解torch.compile内核比啃后端代码更快的入口。

【传送门】

Torch Profiler在Trace里分析性能瓶颈: 剖析SGLang LLM推理
Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能
vLLM+Mooncake: 把agentic前缀复用从1.7%拉到92.2%
把KVCache变成可训练记忆：Context Tuning让LLM免权重微调
MLP就是Hebbian记忆: 无需训练，往Transformer块注入事实知识的构造方法
Kimi K3技术详解之KDA: 线性注意力如何精准编辑被压缩的记忆
Kimi K3技术解析之LatentMoE: 隐藏维度压缩至潜空间，通信与带宽开销同比例骤降
Kimi K3技术解析之AttnRes: 打破Transformer沿用十年的残差各层等权的假设
AI芯片架构全景: 从NVIDIA到Groq的六条设计路线
在NVFP4上超越cuBLAS: 从零手写+Claude极限优化Blackwell GEMM
KVCache缝合术: 突破前缀匹配天花板,首Token快14倍 多文档快2~4倍
TokenSpeed-Kernel：把推理内核做成一等公民
阿里Sparse Attention on CXL替代RDMA做KV Cache解耦 推理2.1×吞吐, 9.7×TTFT
英伟达Kernel Agent: 编译器与算子调优Agent的协同设计
Kimi K3技术报告-后训练Infra: 三阶段RL,MoonEP3,五千万沙箱,KDA感知缓存
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'

参考：https://jino-rohit.github.io/blogs/14_aot_autograd.html