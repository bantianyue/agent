# -*- coding: utf-8 -*-
import os,json
D=os.path.dirname(os.path.abspath(__file__))
S=[]
def h2(t): o={"type":"h2","title":t,"paras":[]};S.append(o);return o
def t(o,*p): o["paras"]+=list(p)

s=h2("一上来,先承认 kernel 这个词被双重占用了")
t(s,"操作系统里的 kernel,是给软件程序与物理硬件之间提供 API 的内核程序。GPU 编程里的 kernel,是一个要并行跑在几千个线程上的函数。两条 N 里讲的往往是后一种:有人说自己 wrote a kernel、或某模型因为 custom kernels 跑得快,指的都是给 GPU 写自定义内核。")
s=h2("kernel 到底是什么")
t(s,"kernel 是一个在 GPU 上运行的函数,GPU 把同一个函数同时跑在成千上万个线程上,每个线程领一个 thread ID 以分辨自己与自己的管辖范围。作者给了个两数组相加的例子:没有循环,a[]、b[]、out[] 都在共享内存里,数千线程分摊到不同的 GPU 核心。核心思想就是:每个线程认领自己的那份共享内存,加载、算一点、写回。")
t(s,"原文里这个例子的示意图在 X 客户端内渲染,这类插图本平台取不到,故行文展开其机制。")
s=h2("一个 kernel 是怎么被调起来的")
t(s,"除非你写自定义 kernel,否则不会直接调它。torch.matmul(a,b) 被编译成这样的链路:PyTorch 见两数组在 GPU 上,选对应的 C++ matmul 函数;该函数再进 NVIDIA 自带预编译库(cuBLAS 管矩阵乘法、cuDNN 管常见神经网络 op),或进 PyTorch 自己写的 kernel;库再让 GPU 驱动去 launch 这个 kernel:代码与数据指针都备好,用这么多线程跑它。之后 CPU 把 launch 丢进队列,继续执行下一行 Python,GPU 按队列顺序处理。")
t(s,"所以跑一次模型,本质是 CPU 排一排 kernel launch、GPU 一条条消化;用 profiler 看 GPU 时间线,就是数百个小方框,每个都是一个 kernel。每次 launch 有几微秒固定开销,累积起来相当可观。")
s=h2("为什么要自己写: fusion 是最直观的理由")
t(s,"GPU 由又大又慢的高带宽内存 HBM 和又小又快的内存 SRAM 组成。HBM 与 SRAM 之间带宽约是每秒几个 TB,但核心做数学快得多,所以推理的大多数步骤里,核心总是在空等数据送达。")
t(s,"看 stock(sic)PyTorch 模型:一次三连拍,乘一个常数、加一个常数、过个激活。这会是三个独立 kernel,每个都慢内存读入、算一点点、再写回慢内存。自定义 kernel 则一趟全做:读一次,乘、加、激活都在数字还在 SRAM 时完成,只写回一次。这就是人们说的融合(fused)kernel。")
t(s,"FlashAttention 是名例:标准 attention 把完整注意力矩阵写到 HBM,再读回做 softmax 并乘 V;FlashAttention 把一个 tile 在 SRAM 里就把 score、softmax、乘 V 算完、累积好再进下一块。搭 tile 做这件事其实相当难,要很巧的算法,但收益就是少读写慢内存。")
s=h2("但要清醒: custom kernel 在最性感,却排在最后")
t(s,"写 custom kernel 的确是改善首 token 延迟 TTFT、逐 token 延迟、吞吐最帅的道路,可大多数增益来自 kernel 之上那些不性感的层:batching(合并许多请求进一次前向)、量化(权重存 8/4 bit 而非 16,每 token 少读)、投机解码(小模型先猜几个 token、大模型一次验证)、编译器(让 ML compiler 先自动融合易做的 op)、以及前缀缓存、prefill/decode 分离、paged attention 等。")
t(s,"一个慢的推理系统慢在哪,多半是它跳过了上面这些标准招;写 custom kernel 工作量大,只有在它之上那层都已经足够快之后才值得动手。")
s=h2("从哪儿开始")
t(s,"NVIDIA 上先用 Triton:用 Python 写一块数据的逻辑,它替你生成 GPU 代码,能覆盖大部分需求;CUDA 是更下一层,给你完全的控制。这个空间还留了很多活,大多在 kernel 之上：更好的 batching、调度、整条推理栈上的内存管理;也大把在 kernel 旁边:Triton 只是众多 kernel DSL 之一,ThunderKittens、TileLang、CuTe、Mojo 都在控制力与易用性之间做各自的取舍。")
t(s,"作者还推荐一篇入门:Horace He 的 Making Deep Learning Go Brrrr From First Principles,即使你不打算写 kernel,也值得读。")
d={"title":"到底什么是 GPU kernel,以及为什么值得自己写",
 "reference_url":"https://x.com/liao_lucas/status/2097149853499588971",
 "summary":[
  {"key":"一句", "body":"kernel 在 GPU 里指并行跑在数千线程上的函数。跑一次模型=CPU 把一堆 kernel launch 排队、GPU 顺序执行,每次 launch 有数微秒开销。自己写 kernel 最有价值的点是把多个小 op 融合成一个、降低慢内存往返,如 FlashAttention。"},
  {"key":"一张顺序图","body":"别急着写 custom kernel:先做 batching、量化(8/4bit)、投机解码、交给编译器融合、前缀缓存等上层招,g与它来的收益多半在这;写 kernel 只在其上都够快之后值得。入口 NVIDIA 上 Triton→CUDA。"}
 ],
 "lead":["这段时间满屏都在聊推理与性能工程,每个人都似乎随口一句 kernel、custom kernels。这篇用不到两千字的篇幅说清三件事:GPU kernel 到底是个什么、它怎么被调起来、以及为什么(在别的手段之后)值得自己写一个。","原文示意图/例程属客户端渲染,平台侧取不到静态图,本稿以文字展开其机制,不臆造插图。"],
 "sections":S,
 "conclusion":["把视角放回推理栈:加速的杠杆从低到高排布,而 custom kernel 明明最被追捧,却几乎是最后才该拧的那颗。先把 batch、量化、投机解码、编译器跟常开源的 tricks 做完,再看还差什么,再决定要不要为那几个热点 op 亲手 fusion 一把。入口工具链也简单:NVIDIA 上 Triton 起步、CUDA 下沉。"]}
json.dump(d,open(os.path.join(D,'article_data.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
print('sections',len(S))
