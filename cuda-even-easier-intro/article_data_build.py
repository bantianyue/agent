# -*- coding: utf-8 -*-
"""
article_data_build.py — cuda-even-easier-intro
源文: https://developer.nvidia.com/blog/even-easier-introduction-cuda/
代码块从 _code.json 逐字读取（源 HTML 的 <pre> 原文，未做任何改写）。
"""
import json
import os
import sys

_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
_code = json.load(open(os.path.join(_dir, "_code.json"), encoding="utf-8"))
assert len(_code) == 18, f"代码块数量应为 18, 实际 {len(_code)}"


def C(i, lang="cpp"):
    return "__CODE__" + lang + "::" + _code[i]


BULLET = ('<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">'
          '●</span>&nbsp;')


def NUM(n):
    return ('<span style="color:#0F4C81;font-weight:bold;">%d</span>&nbsp;' % n)


S = []


def h2(t):
    S.append({"type": "h2", "title": t, "paras": []})
    return S[-1]


def fig(sec, name, caption, idx=None):
    i = len(sec["paras"]) - 1 if idx is None else idx
    sec.setdefault("fig_after", {}).setdefault(str(i), []).append(
        {"src": name, "caption": caption})


# ── 1. 从一段 C++ 加法程序开始 ──────────────────────────────
sec = h2("从一段C++加法程序开始")
sec["paras"] += [
    "先看一段最简单的 C++ 程序：把两个各含一百万个元素的数组逐元素相加。",
    C(0),
    "把上面的代码存成 add.cpp，用 C++ 编译器编译。Linux 下用 g++，Windows 上可以用 MSVC，"
    "WSL 里同样可以用 g++。",
    C(1, "bash"),
    "然后运行：",
    C(2, "bash"),
    r"（在 Windows 上可以把可执行文件命名为 add.exe，用 .\add 运行。）",
    "输出显示求和没有任何误差，程序随即退出。接下来要把这段计算放到 GPU 的众多核心上并行执行，"
    "第一步其实很简单。",
    "先把 add 函数改造成 GPU 能运行的函数，在 CUDA 里称为 kernel。做法是给函数加上 __global__ "
    "修饰符，告诉 CUDA C++ 编译器：这个函数运行在 GPU 上，并且可以被 CPU 代码调用。",
    C(3),
    "这个 __global__ 函数就是 CUDA kernel，运行在 GPU 上。跑在 GPU 上的代码通常称为设备代码，"
    "跑在 CPU 上的称为主机代码。",
]

# ── 2. CUDA 的内存分配 ────────────────────────────────────
sec = h2("CUDA的内存分配")
sec["paras"] += [
    "要在 GPU 上计算，得先分配 GPU 能访问的内存。CUDA 的统一内存提供一块被系统中所有 GPU 与 "
    "CPU 共享的内存空间。调用 cudaMallocManaged() 就能在统一内存里分配数据，返回的指针在主机代码"
    "和设备代码里都能访问；释放时把指针交给 cudaFree() 即可。",
    "改动就是把代码里的 new 换成 cudaMallocManaged()，把 delete [] 换成 cudaFree。",
    C(4),
    "接下来要把 add() kernel 放到 GPU 上执行。CUDA kernel 的启动使用三尖括号语法 <<< >>>，"
    "加在 add 的调用里、参数列表之前。",
    C(5),
    "就这么简单。尖括号里的内容稍后展开，现在只需要知道这一行启动了一个 GPU 线程来运行 add()。",
    "还有一件事：kernel 启动不会阻塞发起调用的 CPU 线程，CPU 必须在读取结果前等 kernel 结束，"
    "所以在最终做误差检查之前要调用 cudaDeviceSynchronize()。",
    "完整代码如下：",
    C(6),
    "CUDA 源代码的文件扩展名是 .cu。把代码存成 add.cu，用 CUDA C++ 编译器 nvcc 编译。",
    C(7, "bash"),
    "这只是第一步。按现在的写法，kernel 只对一个线程是正确的，因为每个运行这个 kernel 的线程都会把整个数组"
    "算一遍；多个并行线程同时读写同一批位置，还会造成竞态。",
    "在 Windows 上要注意，把 Microsoft Visual Studio 项目配置属性里的平台设为 x64。",
]

# ── 3. 先测再改：用 profiler 看耗时 ────────────────────────
sec = h2("先测再改:用profiler看耗时")
sec["paras"] += [
    "想知道 kernel 跑多久，可以用 Nsight Systems 的命令行工具 nsys。直接敲 "
    "nsys profile -t cuda --stats=true ./add_cuda 也行，但输出啰嗦。这里只关心 kernel 的耗时，"
    "所以写了个包装脚本 nsys_easy，只输出需要的信息，同时避免 nsys 在源码目录里留下中间文件。"
    "脚本放在 GitHub 上，下载后放进 PATH 或当前目录即可。",
    "为适配网页宽度，下面的输出删掉了一部分统计项。",
    C(8, "text"),
    "这张 CUDA GPU 摘要表显示 add 只被调用了一次，在 NVIDIA T4 GPU 上耗时约 75ms。"
    "接下来用并行把它变快。",
]

# ── 4. 线程登场 ──────────────────────────────────────────
sec = h2("线程登场")
sec["paras"] += [
    "一个线程的 kernel 跑通了，怎么并行？关键在 <<<1, 1>>> 这个执行配置，用来说明这次启动要用"
    "多少个并行线程。配置有两个参数，先改第二个：一个线程块里的线程数。CUDA GPU 以 32 的倍数划分"
    "线程块，256 个线程是个合适的选择。",
    C(9),
    "只改这一处，计算会被每个线程重复做一遍，而不是分摊到并行线程上。要改对，得动 kernel。"
    "CUDA C++ 提供了让 kernel 获取当前线程下标的变量：threadIdx.x 是线程在自己块内的下标，"
    "blockDim.x 是块内线程数。把循环改成用并行线程按步长扫过数组：",
    C(10),
    "add 函数的变化很小：把 index 设为 0、stride 设为 1，与第一版语义完全一致。",
    "把文件存成 add_block.cu，再用 nsys_easy 编译运行。下文只给出输出里相关的那一行。",
    C(11, "text"),
    "提速很明显，从 75ms 降到 4ms。从 1 个线程变成 256 个线程，这个结果并不意外，继续往下压。",
]

# ── 5. 走出线程块 ────────────────────────────────────────
sec = h2("走出线程块")
sec["paras"] += [
    "CUDA GPU 的众多并行处理器被归入流多处理器，简称 SM。每个 SM 可以同时运行多个线程块，"
    "一个线程块只能待在一个 SM 上。",
    "以基于 Turing 架构的 NVIDIA T4 GPU 为例，40 个 SM、2560 个 CUDA 核心，每个 SM 最多"
    "支持 1024 个活跃线程。要用满这些线程，就得用多个线程块启动 kernel。",
    "执行配置的第一个参数是线程块的数量。这些并行线程块合在一起称为网格。",
    "要处理 N 个元素、每块 256 个线程，只需算出至少能提供 N 个线程的块数：用 N 除以块大小，"
    "注意 N 不是 blockSize 整数倍时要向上取整。",
    C(12),
]
fig(sec, "fig01.png", "图1: CUDA kernel 中网格、线程块与线程的下标索引方式（一维）。")
sec["paras"] += [
    "kernel 代码也要改成覆盖整个网格。CUDA 提供 gridDim.x，保存网格中的块数；blockIdx.x 保存"
    "当前线程块在网格中的下标。",
    "图1 展示了一维情况下用 blockDim.x、gridDim.x 和 threadIdx.x 为数组定位的方式。每个线程的下标"
    "由两部分相加：所在块在数组里的起始偏移，即块下标乘以块大小 blockIdx.x * blockDim.x，"
    "再加上线程在块内的下标 threadIdx.x。blockIdx.x * blockDim.x + threadIdx.x 是 CUDA 里惯用的写法。",
    C(13),
    "更新后的 kernel 还把 stride 设为网格中的线程总数，即 blockDim.x * gridDim.x。CUDA kernel 里"
    "这种循环通常叫网格步长循环。",
    "把文件存成 add_grid.cu，再用 nsys_easy 编译运行。",
    C(14, "text"),
    "结果有点意思：这次改动没有带来提速，甚至可能略慢。计算规模已经扩大到 40 倍，也就是全部 SM 的"
    "数量，总时间却没有下降，说明计算不是瓶颈。",
]

# ── 6. 统一内存的预取 ────────────────────────────────────
sec = h2("统一内存的预取")
sec["paras"] += [
    "瓶颈的线索藏在 profiler 的完整摘要表里：",
    C(15, "text"),
    "表里出现 64 次主机到设备（H2D）和 24 次设备到主机（D2H）的统一内存 memcpy，代码里却没有任何"
    "显式的 memcpy 调用。CUDA 的统一内存是虚拟内存：每个虚拟内存页可以驻留在系统中任意设备"
    "（GPU 或 CPU）的内存里，页按需迁移。程序先在 CPU 上用 for 循环初始化数组，再启动 kernel 让 "
    "GPU 读写数组；kernel 运行时这些页还在 CPU 上，于是产生大量缺页，硬件在缺页时把页迁移到 GPU "
    "内存。这就形成了内存瓶颈，也是没有提速的原因。",
    "迁移昂贵的原因是缺页逐次发生，GPU 线程要停下等待页迁移。既然知道 kernel 需要哪些内存，"
    "x 和 y 两个数组，就可以用预取让数据在 kernel 需要之前待在 GPU 上。方法是在启动 kernel 前调用 "
    "cudaMemPrefetchAsync()：",
    C(16),
    "再跑一遍 profiler，输出如下。kernel 现在只要不到 50 微秒。",
    C(17, "text"),
]

# ── 7. 数据汇总 ──────────────────────────────────────────
sec = h2("数据汇总")
sec["paras"] += [
    "一次性预取数组的所有页，比逐页缺页快得多。这个改动对所有版本的 add 程序都有效，三个版本都加上"
    "预取再跑一遍 profiler，得到下面这张汇总表。",
]
sec["table"] = {
    "head": ["版本", "耗时", "相对单线程加速", "带宽"],
    "rows": [
        ["单线程", "91,811,206 ns", "1x", "137 MB/s"],
        ["单块（256线程）", "2,049,034 ns", "45x", "6 GB/s"],
        ["多块", "47,520 ns",
         '<strong style="color:#1a7f5a;">1932x</strong>',
         '<strong style="color:#1a7f5a;">265 GB/s</strong>'],
    ],
}
sec["paras"] += [
    "数据进入内存之后，从单块到多块的提速与 GPU 的 SM 数量成正比，也就是 40 倍。",
    "GPU 上能拿到很高的带宽。add kernel 是典型的带宽受限负载，265 GB/s 已经超过 T4 峰值带宽 "
    "320GB/s 的 80%；而 GPU 同样擅长计算密集型任务，比如稠密矩阵线性代数、深度学习、"
    "图像与信号处理、物理仿真。",
]

# ── 8. 练习题 ────────────────────────────────────────────
sec = h2("练习题")
sec["paras"] += [
    "想继续练手，可以试试下面几项，也欢迎在评论区聊聊结果。",
    NUM(1) + "浏览 CUDA Toolkit 文档。还没装 CUDA 的话，先看 Quick Start Guide 和安装指南，"
    "再看 Programming Guide 与 Best Practices Guide；官方还提供了针对不同架构的调优指南。",
    NUM(2) + "在 kernel 里试试 printf()。打印部分或全部线程的 threadIdx.x 与 blockIdx.x，"
    "它们是按顺序打印的吗？为什么？",
    NUM(3) + "在 kernel 里打印 threadIdx.y、threadIdx.z 或 blockIdx.y，blockDim 与 gridDim 同理。"
    "它们为什么存在？怎么让它们取到 0 以外的值，对 dims 是 1 以外的值？",
]

# ── 9. 接下来往哪走 ──────────────────────────────────────
sec = h2("接下来往哪走")
sec["paras"] += [
    "想把 CUDA C++ 用到自己的计算里，可以从下面这批入门文章接着读：",
]
for _t in [
    "How to Implement Performance Metrics in CUDA C++",
    "How to Query Device Properties and Handle Errors in CUDA C++",
    "How to Optimize Data Transfers in CUDA C++",
    "How to Overlap Data Transfers in CUDA C++",
    "How to Access Global Memory Efficiently in CUDA C++",
    "Using Shared Memory in CUDA C++",
    "An Efficient Matrix Transpose in CUDA C++",
    "Finite Difference Methods in CUDA C++, Part 1",
    "Finite Difference Methods in CUDA C++, Part 2",
    "Accelerated Ray Tracing in One Weekend with CUDA",
]:
    sec["paras"].append(BULLET + _t)
sec["paras"] += [
    "还有一批与之对应的 CUDA Fortran 文章，从 An Easy Introduction to CUDA Fortran 开始。",
    "NVIDIA Developer Blog 上还有大量 CUDA C++ 与 GPU 计算相关的内容，可以慢慢翻。",
    "想看更多，NVIDIA DLI 提供多门深入的 CUDA 编程课程：",
    BULLET + "刚入门的话可以看 Getting Started with Accelerated Computing in Modern CUDA C++，"
    "其中提供专用 GPU 资源、更完整的编程环境、NVIDIA Nsight Systems 可视化 profiler、"
    "数十个交互练习、详细讲解、8 小时以上的材料，以及 DLI 能力证书。",
    BULLET + "Python 开发者可以看 Fundamentals of Accelerated Computing with CUDA Python。",
    BULLET + "更进阶的内容可以看 NVIDIA DLI 自主学习目录里的加速计算部分。",
]

DATA = {
    "summary": [
        {"key": "起步三步",
         "body": "给函数加 __global__ 修饰符、用 cudaMallocManaged 分配统一内存、"
                 "用 <<<1, 1>>> 启动 kernel，一段 C++ 加法程序就搬到了 GPU 上。"},
        {"key": "执行配置",
         "body": "<<<numBlocks, blockSize>>> 的两个数字决定并行规模，线程用 "
                 "blockIdx.x * blockDim.x + threadIdx.x 找到自己负责的元素。"},
        {"key": "提速结果",
         "body": "统一内存预取把单线程 91.8ms 压到多线程块 47.5 微秒，加速 1932 倍，"
                 "带宽达到 T4 峰值的 80% 以上。"},
    ],
    "lead": [
        "同一段加法程序，在 CPU 上要跑 91.8ms，改用 GPU 并行并加上内存预取之后只要 47.5 微秒。"
        "整个过程从一段普通 C++ 代码起步，每一步改动都用 profiler 验证效果。",
    ],
    "sections": S,
    "conclusion": [
        "**从 CPU 代码跨到 GPU 并行，改动量比想象中小：一个 __global__ 修饰符、一次 "
        "cudaMallocManaged、两个执行配置参数，就是全部改动。**",
        "① 并行规模由 <<<numBlocks, blockSize>>> 决定，线程用 blockIdx.x * blockDim.x + threadIdx.x "
        "找到自己的数据，网格步长循环让线程数不再受数组长度限制。",
        "② 统一内存不是免费的：页按需迁移会带来几十次缺页，一次 cudaMemPrefetchAsync 预取就把 "
        "kernel 从 4.5ms 压到 47 微秒。",
        "③ 最终 265 GB/s 超过 T4 峰值带宽的 80%，这类逐元素运算的瓶颈从来不在计算，而在访存。",
        "对刚开始学 CUDA 的人，顺序可以这样立起来：先跑通单线程版本，再用 profiler 看时间花在哪里，"
        "最后才谈并行和优化。",
    ],
    "reference_url": "https://developer.nvidia.com/blog/even-easier-introduction-cuda/",
    "title": "CUDA入门:从单线程到1932倍加速",
}

out_path = os.path.join(_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

_nparas = sum(len(s["paras"]) for s in S)
_nfigs = sum(len(v) for s in S for v in s.get("fig_after", {}).values())
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, "
      f"{len(S)} sections, {_nparas} paras, {_nfigs} figs)")
