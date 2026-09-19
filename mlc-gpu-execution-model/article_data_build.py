#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
 "title": "GPU 执行模型：从线程层级到 Blackwell 的 GEMM 数据流水线",
 "summary": [
  {"key": "线程层级", "body": "thread、warp（32 线程）、warpgroup（128 线程）、CTA、cluster、grid 对应不同协作尺度；TMA 拷贝由单线程发起，完整 TMEM 累加器由 4 个 warp 各读 32 条 lane，2-CTA 协作 MMA 则横跨两个 CTA"},
  {"key": "内存空间", "body": "GMEM、SMEM、TMEM 与寄存器在容量、延迟、可见范围上各有取舍；B200 上单个 SM 的 SMEM 最多 228 KB，TMEM 有 128 行、最多 512 列、每列 32 位，逻辑上属于 CTA 但仍驻留在 SM 上"},
  {"key": "流水线", "body": "一个 GEMM tile 依次走 Load、Compute、Epilogue 三段，靠 barrier 与 phase 模型重叠：Tensor Core 算第 k 块时，TMA 搬第 k+1 块，epilogue 处理第 k-1 块"}
 ],
 "lead": [
  "要写高性能 GPU kernel，先得回答三个问题：线程怎么组织、数据放在哪里、不同硬件引擎如何协同。这一章按这条线索把 Blackwell 的基本结构讲清楚，最后用一个 GEMM 数据流水线把它们串起来。",
  "核心结论藏在重叠里：Load、Compute、Epilogue 三段不必严格串行，barrier 与 phase 模型让 Tensor Core、TMA 和 epilogue 同时保持忙碌，这也是后续所有 GEMM 优化的出发点。"
 ],
 "sections": [
  {
   "type": "h2",
   "title": "读这一章要抓住的三条线索",
   "paras": [
    "要写高性能 GPU kernel，首先要弄清三件事：线程如何组织、数据存在哪里、不同硬件引擎如何协同。本章按这条线索展开，先讲 GPU 线程层级，再讲用于存放和搬运数据的内存空间，最后介绍负责计算与数据搬运的引擎；结尾的 GEMM 流水线把这些内容串起来，展示计算如何与数据搬运重叠。",
    "- 线程层级决定协作尺度：thread、warp、warpgroup、CTA、cluster 和 grid 各对应一种组织粒度。Blackwell 上很多操作有自己天然的 scope——一次 TMA 拷贝由单个线程发起，一个完整的 TMEM 累加器由 4 个 warp 在各自的 32 lane 窗口上读回，而 2-CTA 协作 MMA 横跨两个 CTA。",
    "- 数据不只存在一个地方：GMEM、SMEM、TMEM 与寄存器在容量、延迟、访问范围上各有取舍，集群还通过 DSMEM 让一个 CTA 访问另一个 CTA 的共享内存。高性能 kernel 的核心任务之一，就是让数据在这些空间之间高效流动。",
    "- 计算与数据搬运由不同硬件引擎承担：CUDA core 负责地址计算、控制流与标量逻辑，Tensor Core 承担主要的矩阵计算，TMA 负责异步搬运数据。",
    "我们从 Blackwell 的 SM 架构看起，下图给出了本章用到的主要硬件单元。",
    "图 1 覆盖了 Blackwell SM 内部参与这些工作的单元：warp、warpgroup、共享内存、Tensor Memory、Tensor Core 与 TMA 引擎。"
   ],
   "fig_after": {"4": [{"src": "fig01.gif", "caption": "图 1：Blackwell SM 架构，本章用到的主要硬件单元"}]}
  },
  {
   "type": "h2",
   "title": "线程层级：从 thread 到 grid",
   "paras": [
    "GPU 不会把成千上万个线程当成一个平面集合来管理，而是把它们组织成若干层级，每一层的协作粒度都不同。下图按 thread、warp、warpgroup、CTA、cluster、grid 的顺序逐级展示 Blackwell 上的线程层级。",
    "- Thread：标量执行单元。每个线程有自己的程序计数器和寄存器，并由它所在 warp 内的 lane ID 标识。",
    "- Warp：32 个线程，以 SIMT（单指令多线程）方式执行。同一 warp 的 lane 一起发射同一条指令，但每个 lane 保留自己的寄存器，也可以被单独屏蔽，这正是同一 warp 内的 lane 能走不同分支的原因。",
    "- Warpgroup：连续 4 个 warp，也就是 128 个线程。Hopper 把 warpgroup 引入为发射 warpgroup 级 MMA（wgmma）的单位；在 Blackwell 上，这 4 个 warp 还可以覆盖 Tensor Memory 的 4 个 32 lane 窗口。",
    "- CTA（Cooperative Thread Array，CUDA 里也称为 thread block）：硬件调度的基本单位。一个 CTA 运行在单个 SM 上，并拥有该 SM 内一块私有的共享内存分配。多个 CTA 可以同时驻留在同一个 SM 上，此时它们会分摊这个 SM 的共享内存容量。",
    "- Cluster：一组可以跨不同 SM 协作的 CTA。cluster 内的 CTA 之间可以互相同步，也可以读写彼此的共享内存，这项能力称为分布式共享内存。",
    "Blackwell 的关键操作并不是都由同一组线程发起。一次 TMA 拷贝由单个线程发起，之后由硬件执行；每个 warp 为自己那 32 条 lane 的窗口发起 warp 级 TMEM 加载；一条 tcgen05 MMA 由某个指定线程提交，而 2-CTA 协作 MMA 横跨两个 CTA。",
    "我们把参与某个操作的线程集合称为它的 scope。分析一个 kernel 时，需要把操作的 scope 与它的数据布局、分发机制放在一起考虑。"
   ],
   "fig_after": {"0": [{"src": "fig02.gif", "caption": "图 2：Blackwell 的线程层级"}]}
  },
  {
   "type": "h2",
   "title": "内存空间：数据住在哪里",
   "paras": [
    "线程层级回答了计算如何组织，接下来要确定数据存在哪里。GPU 提供多种内存空间，它们在容量、延迟与访问范围上各有取舍，kernel 必须让数据在这些空间之间高效流动。",
    "Tensor Memory（TMEM）是 Blackwell 引入的片上存储空间。在更早的架构上，MMA 累加器通常放在寄存器里；随着 MMA tile 变大，这些累加器会占用寄存器文件的很大一部分。Blackwell 的 tcgen05 改为把累加器写入 TMEM，从而减轻寄存器压力。",
    "TMEM 可以看成 CTA 使用的一块二维暂存区：它有 128 行，对应 128 条 TMEM lane，最多 512 列，每列 32 位宽。逻辑上这块空间属于 CTA，物理上它仍然位于 SM 上。",
    "TMEM 由程序显式管理。kernel 必须自己分配和释放它，epilogue 也必须显式地把 MMA 累加器从 TMEM 读回寄存器。要读回一个完整的 128 lane 累加器，warpgroup 里的 4 个 warp 各自加载属于自己的那条 32 lane TMEM 窗口。"
   ],
   "table": {
    "head": ["内存空间", "归属", "作用", "说明"],
    "rows": [
     ["全局内存（GMEM）", "整个设备", "持久化张量存储", "大容量 HBM，所有 SM 共享"],
     ["共享内存（SMEM）", "每个 CTA（单个 SM）", "tile 暂存", "低延迟暂存区；B200 上每个 SM 最多 228 KB"],
     ["Tensor Memory（TMEM）", "每个 CTA", "MMA 累加器存储", "Blackwell 引入，供 tcgen05 使用"],
     ["寄存器文件（RF）", "每个线程", "标量与每线程 tile 片段", "访问速度快，存放 epilogue 与临时值"]
    ]
   }
  },
  {
   "type": "h3",
   "title": "集群内的分布式共享内存",
   "paras": [
    "一个 cluster 里可以包含运行在不同 SM 上的 CTA。每个 CTA 仍然拥有自己的共享内存，但分布式共享内存（DSMEM）允许同一 cluster 内的其他 CTA 访问这些数据。",
    "这项能力省掉了绕道 GMEM 的往返：一个 CTA 可以直接访问另一个 CTA 的 SMEM，而不需要数据所有者先写回 GMEM、再由对端重新读入。当异步操作搬运这类数据时，它会在传输完成后更新一个完成 barrier；使用方需要先等待该 barrier，再去消费结果。",
    "下图展示了 2-CTA 集群里的 DSMEM 访问路径：每个 CTA 保留自己的 SMEM，同时可以读取另一个 CTA 的 SMEM。",
    "在上面的 2-CTA GEMM 中，每个 CTA 存放自己那部分 A、B 分片，并通过 DSMEM 读取对端 CTA 的 B 分片。这里的共享并不会把两块 SMEM 合并，它只意味着同一 cluster 内的 CTA 可以跨 SM 访问彼此的数据。",
    "两个 CTA 可以组成一个 CTA pair，以 cta_group::2 模式执行协作 MMA，从而产出更大的输出 tile。"
   ],
   "fig_after": {"2": [{"src": "fig03.gif", "caption": "图 3：2-CTA 集群通过 DSMEM 互相访问共享内存"}]}
  },
  {
   "type": "h2",
   "title": "计算单元：CUDA Core 与 Tensor Core",
   "paras": [
    "线程层级决定了计算如何组织，内存空间决定了数据存在哪里，而真正的算术由 SM 内部的计算单元完成。一个 SM 主要有两类计算单元：CUDA core 与 Tensor Core。",
    "- CUDA core 是通用的 SIMT ALU，执行处理索引运算、逐元素数学、归约和控制流的标量与向量指令。",
    "- Tensor Core 是固定功能单元，以 tile 为粒度执行稠密矩阵乘加，在一条指令里完成 D = AB + C。",
    "Tensor Core 的算术吞吐远高于 CUDA core，在 FLOP/s 上常常高出一个数量级以上。GEMM、卷积、注意力这类稠密线性代数负载，只有有效利用 Tensor Core 才可能接近峰值性能。与此同时，高性能 kernel 还必须及时把数据准备好，否则 Tensor Core 会因为等待数据或依赖而空转。",
    "不同代 GPU 的变化不只在 Tensor Core 吞吐上，编程接口与累加器的存放位置也在变。Hopper 引入了异步的 warpgroup MMA（wgmma.mma_async）；Blackwell 的第五代 Tensor Core tcgen05 把累加器放在 Tensor Memory 而不是寄存器里。后续章节会详细讨论这些差异。",
    "Cluster 还带来两种对 GEMM 很重要的协作方式。2-CTA 协作 MMA 让两个 CTA 各提供一部分 SMEM 操作数，拼成更大的 Tensor Core MMA tile；TMA multicast 让一次 GMEM 加载把同一个 tile 送给多个 CTA，避免每个 CTA 各自重复读取同一份数据。两者都依赖前面介绍的 cluster 与 DSMEM 机制。"
   ]
  },
  {
   "type": "h2",
   "title": "GEMM 数据流水线：把三者连起来",
   "paras": [
    "前面几节分别介绍了线程层级、内存空间、数据搬运机制和计算单元。现在我们用一个 GEMM 流水线把它们连起来，看看这些硬件结构如何协同工作。下图给出了三段式 GEMM tile 流水线涉及到的主要单元。",
    "一个 GEMM tile 通常要走过三个阶段。",
    "- Load：一次 TMA 拷贝把 A 或 B 的操作数 tile 从 GMEM 搬到 SMEM。由单个线程发起这次拷贝，并记录预期到达的字节数。数据陆续抵达 SMEM 的过程中，TMA 引擎会更新进度计数；只有当所有预期字节都到达后，完成 barrier 才会变为 complete。",
    "- Compute：一条 tcgen05 MMA 从 SMEM 读取操作数 tile，把乘积累加进 TMEM tile。由某个指定线程提交这条 MMA；计算完成时，硬件会通知对应的 barrier。",
    "- Epilogue：一个 warpgroup 把 TMEM 累加器读回寄存器，把结果转换成输出 dtype，再写回 GMEM。这一步通常经由 SMEM 中转，最终写回可能使用 TMA store。",
    "这三个阶段之间存在数据依赖，但不必严格串行。朴素的 kernel 会按加载、等待、计算、等待、写回的顺序依次执行，硬件单元轮流空转。",
    "高性能 kernel 会把各阶段组织成流水线：Tensor Core 计算第 k 个 tile 时，TMA 引擎可以搬运第 k+1 个 tile，epilogue 可以处理第 k-1 个 tile 的输出。barrier 与 phase 模型负责协调这些异步阶段之间的安全交接，本书后续的 GEMM 优化都建立在这套机制之上。"
   ],
   "fig_after": {"0": [{"src": "fig04.gif", "caption": "图 4：Blackwell 上三段式 GEMM 数据流水线涉及的主要硬件单元"}]}
  }
 ],
 "conclusion": [
  "**这一章最值得记住的是三层视角必须一起看：线程层级决定谁来协作，内存空间决定数据住在哪，计算引擎决定谁在干活。** 任何一个 Blackwell GEMM 的优化决策，最后都能归到这三层的取舍上；缺了任何一层，性能问题都很难定位。",
  "真正拉开差距的是重叠。三段式流水线之所以有效，是因为它让 Tensor Core、TMA 与 epilogue 同时有事可做，而 barrier 与 phase 模型是让这种重叠安全成立的基础。后面所有的 GEMM 优化，基本都在这个框架里做文章：先把阶段拆开，再让它们错开运行。"
 ],
 "reference_url": "https://mlc.ai/modern-gpu-programming-for-mlsys/chapter_background/index.html"
}

if __name__ == "__main__":
    out = os.path.join(_article_dir, "article_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=2)
    n_para = sum(len(s.get("paras", [])) for s in DATA["sections"])
    n_fig = sum(len(v) for s in DATA["sections"] for v in (s.get("fig_after") or {}).values())
    print("OK wrote", out, len(DATA["sections"]), "sections", n_para, "paras", n_fig, "figs")