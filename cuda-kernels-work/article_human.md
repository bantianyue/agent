/* 传送门统一样式（add-portal.py动态注入时引用此class；真身在内联style，class仅兜底） */
.portal-title { font-size:12px; color:#1a6ba0; font-weight:bold; }
.portal-links { font-size:12px; color:#0F4C81; }
.portal-links a { color:#0F4C81; text-decoration:none; }

要点速览

- 核心思想：Kernel 按单线程写一次，GPU 让数千线程并行执行同一份代码，各自处理不同数据- 分工机制：线程、线程块、网格三级组织，i=块号×每块线程数+块内线程号定位各自任务- 性能要点：warp 以 32 线程为单位执行同一指令，分支发散与主机设备间拷贝是主要性能陷阱

AI 模型每一次推理，背后都是成千上万个 CUDA Kernel 在 GPU 上并行执行。Kernel 究竟是什么，线程如何分工，GPU 内部又发生了什么，下文从零讲清。

为什么需要GPU?
CPU 是计算机的大脑，擅长一个接一个地处理任务。主流 CPU 只有 4、8 或 16 个核心，一个核心一次只能做一件事。
GPU 是另一种芯片，最初为屏幕绘图而生。画一幅图要计算数百万像素的颜色，每个像素可独立计算，无需等待其他像素。GPU 因此内置数千个小核心，同时开工，这种工作方式叫并行。
假设要给 10000 个土豆削皮：CPU 像一位大厨，技艺精湛但一次只能削一个；GPU 像 5000 名帮手，每人慢一些，但 5000 人同时动手。削 10000 个土豆，帮手阵营轻松获胜。
AI 训练与推理就是数以百万计的小乘加运算，彼此大多不相关，正是典型的削土豆式任务，GPU 派上用场。
但有个关键问题：GPU 自己决定不了做什么。必须有人写程序，指挥数千个小核心各自干什么，这就是 CUDA 登场的背景。
什么是CUDA?
CUDA(Compute Unified Device Architecture) 是 NVIDIA 打造的平台，NVIDIA 生产了 AI 用的绝大多数 GPU，CUDA 让人能写出跑在 GPU 上的程序。
简单说，CUDA 让人用 C、C++、Python 这类常规语言写代码，同时跑在数千个 GPU 核心上。
CUDA 之前，想把 GPU 用于图形之外的事，得把数据伪装成图片来骗过 GPU，非常痛苦。CUDA 终结了这种折磨：直接告诉 GPU，这里是数据，这里是任务，并行执行。
怎么告诉 GPU 做什么？答案是写 Kernel。
什么是CUDA Kernel?
CUDA Kernel 是跑在 GPU 上的函数，被大量线程同时执行。
拆开看：函数是一段完成一件工作的代码；线程是执行代码的一个工人。用厨房打比方，线程就是一名帮手。
于是 CUDA Kernel 等于函数加上跑在 GPU 上再加上被数千线程同时执行。
最重要的思想只有一句：Kernel 只写一次，按单线程写，GPU 把同一份 Kernel 并行跑数千遍，每个线程跑一遍。
回到厨房：不用给 5000 名帮手写 5000 份不同的指令，只写一份，拿起土豆削皮，5000 人同时照做，区别只是每人拿的土豆不同。
CUDA Kernel 正是如此：一份指令，数千工人，每人处理不同数据。
线程,线程块与网格
数千个线程需要组织，否则一团乱。CUDA 用三级结构组织线程。
线程：单个工人，把 Kernel 代码跑一遍。
线程块：一组线程，比如 256 个线程组成一个块。同块线程可以互相交流，共享一小块内存。
网格：一组线程块，一次 Kernel 启动的所有块构成一个网格。网格等于多个块，块等于多个线程。
厨房版：线程是一名帮手；线程块是围在一张桌子旁的一队帮手，同桌之间递东西方便；网格是摆满桌子的整个厨房。
启动 Kernel 时告诉 CUDA 两件事：要多少个块，每块多少线程，CUDA 随即创建全部线程，在每个线程上跑一遍 Kernel。
注意：一个块的线程数有限制，通常 1024，这就是需要多个块的原因。块的数量没有实际限制，一次启动可跑数百万线程。
主机与设备
写代码前先认识两个词，CUDA 里无处不在。
主机：CPU 及其内存，即内存条，计算机的主内存。
设备：GPU 及其自带内存，即显存，插在显卡上的内存。
主机与设备内存相互独立。为便于理解，假设 CPU 读不到显存，GPU 也读不到内存。想让 GPU 处理数据，必须先把数据从主机拷到设备；做完再把结果从设备拷回主机。
于是 CUDA 程序永远走六步：
第 1 步：在主机上准备好数据。
第 2 步：在设备上分配内存，分配即预留放数据的空间。
第 3 步：把数据从主机拷到设备。
第 4 步：在设备上启动 Kernel。
第 5 步：把结果从设备拷回主机。
第 6 步：释放设备内存，把预留的空间还回去。
厨房版：大厨的土豆在储藏室，帮手在另一个房间干活，大厨得先把土豆搬过去，削完再把削好的搬回来。搬运要花时间，后面会看到这为什么重要。
第一个CUDA Kernel
学东西最好的办法是看例子。假设有两个各 100 万个数的列表 a 和 b，要逐位相加存进第三个列表 c，即每个位置 i 都有 c[i] = a[i] + b[i]。
CPU写法
先看不用 CUDA 的 CPU 写法：
void&nbsp;add(int&nbsp;n,&nbsp;float&nbsp;*a,&nbsp;float&nbsp;*b,&nbsp;float&nbsp;*c)&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;for&nbsp;(int&nbsp;i&nbsp;=&nbsp;0;&nbsp;i&nbsp;&lt;&nbsp;n;&nbsp;i++)&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;c[i]&nbsp;=&nbsp;a[i]&nbsp;+&nbsp;b[i];&nbsp;&nbsp;&nbsp;&nbsp;}}
函数 add 里，void 表示不返回东西，float 表示带小数点的数，float *a 表示这样一串数。循环从 0 跑到 n-1，每步加一对数。100 万个数，循环跑 100 万次，一个接一个。一位大厨，一次一个土豆。
CUDA Kernel写法
同样的事写成 CUDA Kernel：
__global__&nbsp;void&nbsp;add(int&nbsp;n,&nbsp;float&nbsp;*a,&nbsp;float&nbsp;*b,&nbsp;float&nbsp;*c)&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;int&nbsp;i&nbsp;=&nbsp;blockIdx.x&nbsp;*&nbsp;blockDim.x&nbsp;+&nbsp;threadIdx.x;&nbsp;&nbsp;&nbsp;&nbsp;if&nbsp;(i&nbsp;&lt;&nbsp;n)&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;c[i]&nbsp;=&nbsp;a[i]&nbsp;+&nbsp;b[i];&nbsp;&nbsp;&nbsp;&nbsp;}}
`__global__` 是特殊关键字，告诉 CUDA 这是个 Kernel，从主机调用，在设备上运行。
循环消失了。每个线程只处理一个 i。GPU 把这个函数并行跑 100 万遍，每个线程跑一遍，各管一个位置。
`int i = blockIdx.x * blockDim.x + threadIdx.x;` 是每个线程算出自己负责哪个 i 的办法，下一节细讲。
`if (i 
整个 Kernel 就这么几行，一次干完 100 万次循环迭代的活。
启动Kernel
再看怎么从主机启动这个 Kernel：
int&nbsp;n&nbsp;=&nbsp;1000000;int&nbsp;threadsPerBlock&nbsp;=&nbsp;256;int&nbsp;blocks&nbsp;=&nbsp;(n&nbsp;+&nbsp;threadsPerBlock&nbsp;-&nbsp;1)&nbsp;/&nbsp;threadsPerBlock;add&lt;&lt;&lt;blocks,&nbsp;threadsPerBlock&gt;&gt;&gt;(n,&nbsp;d_a,&nbsp;d_b,&nbsp;d_c);
`threadsPerBlock = 256` 表示每块 256 个线程。
`blocks = (n + threadsPerBlock - 1) / threadsPerBlock` 算出覆盖 100 万个数需要多少块，这是个向上取整的小技巧。100 万个数、每块 256 线程，算出 3907 个块。3907 乘 256 等于 1000192 个线程，比 100 万多一点，这就是 Kernel 里需要 `if (i 
`>>` 是启动 Kernel 的特殊语法，三重尖括号告诉 CUDA：用这么多块、每块这么多线程跑这个函数。
`d_a`、`d_b`、`d_c` 是数据在设备内存中的地址，告诉 Kernel 数据在 GPU 的哪里。`d_` 前缀是命名惯例，表示 device，调用 Kernel 前数据已经拷过去了。
完整六步流程
把前面讲的内存步骤串起来看完整流程：
//&nbsp;Step&nbsp;1:&nbsp;a,&nbsp;b,&nbsp;and&nbsp;c&nbsp;are&nbsp;already&nbsp;prepared&nbsp;on&nbsp;the&nbsp;host//&nbsp;Step&nbsp;2:&nbsp;Allocate&nbsp;memory&nbsp;on&nbsp;the&nbsp;devicefloat&nbsp;*d_a,&nbsp;*d_b,&nbsp;*d_c;cudaMalloc(&amp;d_a,&nbsp;n&nbsp;*&nbsp;sizeof(float));cudaMalloc(&amp;d_b,&nbsp;n&nbsp;*&nbsp;sizeof(float));cudaMalloc(&amp;d_c,&nbsp;n&nbsp;*&nbsp;sizeof(float));//&nbsp;Step&nbsp;3:&nbsp;Copy&nbsp;data&nbsp;from&nbsp;host&nbsp;to&nbsp;devicecudaMemcpy(d_a,&nbsp;a,&nbsp;n&nbsp;*&nbsp;sizeof(float),&nbsp;cudaMemcpyHostToDevice);cudaMemcpy(d_b,&nbsp;b,&nbsp;n&nbsp;*&nbsp;sizeof(float),&nbsp;cudaMemcpyHostToDevice);//&nbsp;Step&nbsp;4:&nbsp;Launch&nbsp;the&nbsp;kerneladd&lt;&lt;&lt;blocks,&nbsp;threadsPerBlock&gt;&gt;&gt;(n,&nbsp;d_a,&nbsp;d_b,&nbsp;d_c);//&nbsp;Step&nbsp;5:&nbsp;Copy&nbsp;result&nbsp;from&nbsp;device&nbsp;to&nbsp;hostcudaMemcpy(c,&nbsp;d_c,&nbsp;n&nbsp;*&nbsp;sizeof(float),&nbsp;cudaMemcpyDeviceToHost);//&nbsp;Step&nbsp;6:&nbsp;Free&nbsp;the&nbsp;device&nbsp;memorycudaFree(d_a);cudaFree(d_b);cudaFree(d_c);
`cudaMalloc` 在 GPU 内存里预留空间，告诉 GPU 把这么多空间留给数据。
`cudaMemcpy` 在主机与设备之间拷数据，最后一个参数定方向：`cudaMemcpyHostToDevice` 或 `cudaMemcpyDeviceToHost`。
启动 Kernel 那行和前面一样。
`cudaFree` 用完释放 GPU 内存。
跑起来完全没问题：100 万次加法由 GPU 并行完成。
注意：CUDA 代码存成 `.cu` 文件，用 NVIDIA 的专用工具 `nvcc` 编译，同时懂主机的常规 C++ 代码和设备的 Kernel 代码。
线程如何找到自己的任务
现在理解 Kernel 里最重要的一行：
int&nbsp;i&nbsp;=&nbsp;blockIdx.x&nbsp;*&nbsp;blockDim.x&nbsp;+&nbsp;threadIdx.x;
每个线程跑的代码一模一样，每个线程怎么知道自己加哪个数？答案是 CUDA 给每个线程发了几个内置变量，标出自己的位置，索引即从 0 开始的位置号。
`threadIdx.x` 是线程在块内的编号。块有 256 个线程时，这个值从 0 到 255。
`blockIdx.x` 是块在网格内的编号。有 3907 个块时，这个值从 0 到 3906。
`blockDim.x` 是每块的线程数，这里是 256。
全局索引 i 的算法：`i = 块号 × 每块线程数 + 块内线程号`
举例：块 0 的线程 0，`i = 0 × 256 + 0 = 0`；块 0 的线程 5，`i = 0 × 256 + 5 = 5`；块 1 的线程 0，`i = 1 × 256 + 0 = 256`；块 2 的线程 10，`i = 2 × 256 + 10 = 522`。
每个线程拿到唯一的 i，没有两个线程拿到同一个 i。同一份代码跑在数千线程上，就这样处理了不同的数据。
最后回一次厨房：每名帮手有桌号 `blockIdx` 和座位号 `threadIdx`，每张桌子 256 个座位 `blockDim`。于是 2 号桌 10 号座位的帮手知道自己该拿 522 号土豆，不用问任何人，算一下就行。
注意：到处用 `.x` 是因为 CUDA 允许线程和块按一维排成直线、二维排成纸面网格、三维排成立方体。简单列表一维就够，图像或矩阵用二维更自然，还会用到 `.y`，思想不变。
Kernel运行时GPU内部发生了什么
学会了写和启动 Kernel，再看 GPU 拿到 Kernel 后到底做了什么。
GPU 由许多流式多处理器组成，简称 SM。SM 是 GPU 内部的一个大工作单元，包含许多小核心，一块现代 GPU 可有 100 多个 SM。
启动带 3907 个块的 Kernel 时，CUDA 不会同时跑完所有块，而是把块分给各个 SM。每个 SM 接几个块，做完再接下一批，直到全部做完。
SM 内部线程也不是一个一个跑。SM 把线程按 32 个一组打包，这个包叫 warp。warp 里的 32 个线程在同一时刻执行同一条指令。CUDA 快的秘诀在此：一条指令只取一次，同时作用于 32 个线程。
厨房版：厨房分成许多区，每个区一次处理几张桌子；每张桌子旁的帮手按 32 人排成行，桌长喊一声削，整行 32 人一起动手。
但有个陷阱：warp 的 32 个线程必须执行同一条指令，Kernel 里如果有 `if`，一部分线程走一条路、一部分走另一条路，warp 得把两条路先后各跑一遍，这叫分支发散，会拖慢速度。好的 CUDA Kernel 尽量让线程做同样的事。
注意：`if (i 
CUDA中的内存
前面已知主机与设备内存分离，再看设备内存内部，因为性能大头在这里。
GPU 有三种主要内存：
全局内存：GPU 的大内存，即显存，比如 24GB 或 80GB，所有线程可读写，`d_a`、`d_b`、`d_c` 就住这里。大而慢，因为离核心远。
共享内存：每块 SM 内部的一小块极速内存，只供同块线程使用，像每张桌子上的白板，同桌帮手都能看见能写。
寄存器：最快的内存，每个线程独享，变量 `i` 就住在寄存器里，像每名帮手手里的记事本。
全局内存比共享内存慢约 100 倍。CUDA 编程的常用技巧：先把一块数据从全局内存搬进共享内存，让块内线程反复用共享内存算很多遍，最后把结果写回全局内存。
简单加法例子里每个数只用一次，共享内存帮不上忙。但矩阵乘法这种大表格相乘、同一批数被反复用的场景，这招效果巨大。
CUDA Kernel对AI的意义
AI 模型比如 LLM，是由叫权重的海量数字组成的集合。给一个输入，模型把输入和权重相乘、求和、套几个简单数学函数，在很多层里重复。AI 模型内部几乎全是矩阵乘法，即大表格的乘加运算。
几百万个数的矩阵乘法是完美的削土豆问题：每个输出数可独立计算。于是为矩阵乘法写一个 CUDA Kernel，用几百万个线程启动。
用 PyTorch 这类搭 AI 模型的流行工具写 `torch.matmul(a, b)` 时，自己一行 CUDA 也没写。但幕后 PyTorch 调的是 NVIDIA 写好的高度优化 CUDA Kernel，来自 cuBLAS 这类现成数学 Kernel 库。做的正是今天学的东西，只是快得多，技巧也多得多。
LLM 每生成一个词，GPU 上就有成千上万个 CUDA Kernel 一个接一个地启动。模型里的每一步，无论大的矩阵乘法还是小的数学函数，都是一个 CUDA Kernel。没有 GPU 和 CUDA，无法想象现代 AI。
CUDA Kernel擅长与不擅长的场景
CUDA Kernel 擅长的场景：同一操作作用于大量数据，如矩阵乘法、图像处理、科学仿真；不同数据的计算互不依赖；工作量足够大，省下的时间超过主机与设备之间拷数据的时间。
CUDA Kernel 失效或帮不上忙的场景：任务太小，把 10 个数拷到 GPU 再拷回来，比 CPU 直接加还慢，为 10 个土豆把人搬去另一个房间不值；工作串行，第 2 步要等第 1 步的结果，第 3 步要等第 2 步，数千线程帮不上忙，一次只能一个线程干；线程老走不同分支，重度分支造成 warp 发散，GPU 最后只能一件事一件事做；数据大到装不进显存，得来回搬数据，拷贝变成瓶颈。
把 CPU 和 GPU 的区别列成表更直观：

CPUGPU

核心少而强，4 到 64 个成千上万个小核心
擅长一个接一个地做任务擅长同时对大量数据做同一任务
擅长逻辑、决策与运行操作系统擅长大列表与大表格的数学运算、图形与 AI
数据已在内存中，无需拷贝数据必须在主机与设备之间来回拷贝

总结
GPU 有数千个小核心同时工作，为对大量数据做同一操作而生。
CUDA 是 NVIDIA 让程序跑上 GPU 的平台。
CUDA Kernel 是跑在 GPU 上的函数，被数千线程并行执行。
Kernel 只写一次，按单线程写，GPU 跑数千遍，每个线程用 `blockIdx`、`blockDim`、`threadIdx` 找到自己的数据。
线程组成块，块组成网格。
主机与设备内存分离，所以流程永远是分配、拷贝、启动、拷回、释放。
GPU 内部块跑在 SM 上，线程按 32 个一组的 warp 跑。
全局内存大而慢，共享内存小而快，寄存器最快。
AI 模型里的几乎每个操作，幕后都是一个 CUDA Kernel。
常见问题
初学者常问的几个问题，集中回答。
用PyTorch还需要自己写CUDA代码吗?
不需要。写 `torch.matmul(a, b)` 时自己不写 CUDA，幕后 PyTorch 调的是 NVIDIA 写好的高度优化 CUDA Kernel，来自 cuBLAS 这类现成数学 Kernel 库。
CUDA Kernel为什么需要if (i 
因为经常多启动几个线程。块数向上取整，100 万个数、每块 256 线程会得到 3907 个块共 1000192 个线程，`if (i 
一个CUDA块最多能有多少线程?
通常最多 1024 个线程，这就是一次启动要用多个块的原因。块数没有实际限制，一次 Kernel 启动可跑数百万线程。
什么是warp发散?
warp 里 32 个线程在 `if` 处走了不同分支时发生。warp 的 32 个线程必须执行同一条指令，warp 得把两条路先后各跑一遍，拖慢速度。好的 CUDA Kernel 尽量让线程做同样的事。
CUDA代码怎么编译?
CUDA 代码存成 `.cu` 文件，用 NVIDIA 的专用工具 `nvcc` 编译，同时懂主机的常规 C++ 代码和设备的 Kernel 代码。

结语

① Kernel 是 GPU 的执行单元：写一次、跑数千遍的函数，是 AI 算力的最小调度单位。② 线程分工靠三级索引：线程、线程块、网格加全局索引公式，让每个线程自定位。③ 性能来自内存与执行模型：warp 同指令执行、共享内存提速、主机设备拷贝是主要开销。下次看到 PyTorch 一行 matmul 跑出惊人速度，可以想起幕后是成千上万个 Kernel 在 SM 上以 warp 为单位整齐划一地推进。理解这套机制，是看懂 GPU 优化、推理加速乃至一切 AI Infra 文章的起点。

【传送门】

Kimi K3技术报告-后训练Infra: 三阶段 RL,MoonEP3,五千万沙箱,KDA感知缓存
Kimi K3技术详解之KDA: 线性注意力如何精准编辑被压缩的记忆
在NVFP4上超越cuBLAS: 从零手写+Claude极限优化Blackwell GEMM
Kimi K3技术解析之LatentMoE: 隐藏维度压缩至潜空间，通信与带宽开销同比例骤降
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'
AI芯片架构全景: 从NVIDIA到 Groq的六条设计路线
小米MiMo罗福莉:8卡GPU让1T参数模型跑出1000 TPS , FP4+DFlash+TileRT全解读
Torch Profiler在Trace里分析性能瓶颈: 剖析SGLang LLM推理

参考：https://outcomeschool.com/blog/how-do-cuda-kernels-work