# -*- coding: utf-8 -*-
"""article_data_build.py — cuda-rust-two-tracks（NVIDIA Technical Blog）
源：https://developer.nvidia.com/blog/introducing-cuda-rust-two-tracks-for-writing-gpu-kernels/
代码块来自源页 <pre class="brush:..."> 原文（SyntaxHighlighter 渲染后 <pre> 消失，故从原始 HTML 逐字提取）。
"""

CODE_1 = r"""cargo +nightly-2026-04-03 install --git https://github.com/NVlabs/cuda-oxide.git cargo-oxide"""

CODE_2 = r"""cargo oxide new vecadd_demo
cd vecadd_demo
cargo oxide doctor
cargo oxide run"""

CODE_3 = r"""use cuda_device::{kernel, launch_bounds, launch_contract, thread, DisjointSlice};
use cuda_host::cuda_module;
use cuda_core::{CudaContext, DeviceBuffer, LaunchConfig1D};

// === DEVICE CODE - everything in here is compiled to PTX ===
// The macro also generates the host-side API used further down:
// `load`, `prepare_vecadd`, and the safe `vecadd` launch method.
#[cuda_module]
mod kernels {
    use super::*;

    #[kernel] // GPU entry point
    #[launch_bounds(256)] // max threads per block; lets the compiler budget registers
    #[launch_contract(domain = 1, block = (256, 1, 1))] // indexes in 1-D, 256-thread blocks
    pub fn vecadd(a: &[f32], b: &[f32], mut c: DisjointSlice<f32>) {
        let idx = thread::index_1d();
        let idx_raw = idx.get(); // the plain usize, for reading the inputs
        if let Some(c_elem) = c.get_mut(idx) {
            *c_elem = a[idx_raw] + b[idx_raw];
        }
    }
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // === HOST SETUP - device, stream, and buffers ===
    let ctx = CudaContext::new(0)?;
    let stream = ctx.default_stream();

    const N: usize = 1024;
    let a_host: Vec<f32> = (0..N).map(|i| i as f32).collect();
    let b_host: Vec<f32> = (0..N).map(|i| (i * 2) as f32).collect();

    let a_dev = DeviceBuffer::from_host(&stream, &a_host)?;
    let b_dev = DeviceBuffer::from_host(&stream, &b_host)?;
    let mut c_dev = DeviceBuffer::<f32>::zeroed(&stream, N)?;

    // === LOAD, PREPARE, LAUNCH ===
    // SAFETY: this package owns the embedded device bundle produced for the
    // kernels module above.
    let module = unsafe { kernels::load(&ctx)? };

    // 4 blocks of 256 threads, 0 bytes of dynamic shared memory. `prepare_vecadd`
    // checks that against the contract above and against the live device limits.
    // The safe `vecadd` below takes that token where a raw config would go.
    let prepared = module.prepare_vecadd(LaunchConfig1D::new((N as u32).div_ceil(256), 256, 0))?;
    module.vecadd(&stream, &prepared, &a_dev, &b_dev, &mut c_dev)?;

    // === READ BACK AND VERIFY ===
    // Copies down and synchronizes, so the launch has finished by the time
    // `c_host` can be read.
    let c_host = c_dev.to_host_vec(&stream)?;
    let errors = (0..N)
        .filter(|&i| (c_host[i] - (a_host[i] + b_host[i])).abs() > 1e-5)
        .count();

    if errors == 0 {
        println!("PASSED: all {} elements correct", N);
    } else {
        eprintln!("FAILED: {} errors", errors);
        std::process::exit(1);
    }
    Ok(())
}"""

CODE_4 = r"""cargo new vecadd_demo
cd vecadd_demo
cargo add cutile"""

CODE_5 = r"""use cutile::prelude::*;

// The macro captures this module's AST into the host binary. The kernel is
// JIT-compiled through CUDA Tile IR the first time it is actually launched.
#[cutile::module]
mod kernel {
    use cutile::core::*;

    #[cutile::entry()]
    fn add<const B: i32>(
        // B is the tile width, a static dimension. A different B produces a
        // different specialization.
        z: &mut Tensor<f32, { [B] }>, // exclusive output, one sub-tensor of B elements
        x: &Tensor<f32, { [-1] }>,    // shared input; -1 is a dynamic dimension, resolved at launch
        y: &Tensor<f32, { [-1] }>,
    ) {
        // This body runs once per mut sub-tensor, as a single logical thread.
        // Tile kernels load tiles, not scalars, from x and y.
        let tx = load_tile_like(x, z); // the slice of x lining up with this sub-tensor of z
        let ty = load_tile_like(y, z);
        z.store(tx + ty); // elementwise across the whole tile
    }
}

fn main() -> Result<(), Error> {
    let device = Device::new(0)?;
    let stream = device.new_stream()?;

    // These are lazy. Nothing has touched the GPU yet.
    let x = api::ones::<f32>(&[1024]);
    let y = api::ones::<f32>(&[1024]);

    // Partitioning does three things at once: gives each tile exclusive
    // ownership of its own 128-element chunk, fixes the grid at 1024/128 = 8
    // tiles, and supplies B.
    let z = api::zeros::<f32>(&[1024]).partition([128]);

    let c: Vec<f32> = kernel::add(z, x, y) // takes ownership of all three tensors
        .first()                           // ...and returns them; pick the output back out
        .unpartition()                     // drop the host-side partition wrapper; no data moves
        .to_host_vec()                     // record the copy back
        .sync_on(&stream)?;                // and only now does any of it run

    let errors = c.iter().filter(|&&v| (v - 2.0).abs() > 1e-5).count();
    if errors == 0 {
        println!("PASSED: all {} elements correct", c.len());
    } else {
        eprintln!("FAILED: {errors} errors");
    }
    Ok(())
}"""

CODE_6 = r"""module.vecadd(&stream, &prepared, &c_dev, &b_dev, &mut c_dev)?;"""

CODE_7 = r"""let z = api::zeros::<f32>(&[1024]);
kernel::add(z.partition([128]), z, y)"""

IC = '<code style="background:#f3f4f5;padding:2px 5px;border-radius:3px;color:#0F4C81;">%s</code>'
DOT = '<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;'
QUOTE = ('<span style="display:block;background:#f5f8fb;border-left:3px solid #0F4C81;'
         'padding:10px 14px;border-radius:4px;">%s</span>')


def c(t):
    return IC % t


DATA = {
    "title": "引入 CUDA Rust：编写 GPU 内核的两条路线",
    "summary": [
        {"key": "两条路线", "body": "cuda-oxide 走 SIMT，用自定义 rustc codegen 后端把内核原生编译到 PTX；cutile-rs 走 Tile，每个 tile block 当做一个逻辑线程，经 CUDA Tile IR 做 JIT。选型上先 Tile，要控制线程和内存再下探 SIMT。"},
        {"key": "编译期安全", "body": "cuda-oxide 用 DisjointSlice 把可变借用拆给各线程，再用启动合约校验 launch 配置；cutile-rs 靠主机端张量分区，让每个 tile 独占一块可写子张量。别名错误在两边都编译不过。"},
        {"key": "落地门槛", "body": "cuda-oxide 仍是早期 alpha，需要 Linux、固定 nightly 工具链和自备 LLVM；cutile-rs 只需 stable Rust 1.89+ 与 CUDA 13.3，已发布在 crates.io，并被 HuggingFace 的 Grout 与 mistral.rs 采用。"},
    ],
    "lead": [
        "2026 年 9 月，NVIDIA 宣布正式投入原生 Rust GPU 编程。CUDA C++ 与 CUDA Python 是成熟的、企业级工具链，而 CUDA Rust 会在 2027 年及之后持续成长。",
        "AI 的系统层横跨推理引擎、服务基础设施、驱动和智能体运行时，并且随着模型与技术的更迭不断变化。其中越来越多的部分用 Rust 编写，它在不牺牲性能的前提下，把整类 bug 拦在编译期。",
        "NVIDIA 出于同样的理由参与这场迁移：Nova Linux 驱动用 Rust 写，NVIDIA Dynamo 构建在 Rust 内核之上，NVTX 也提供了 Rust 绑定。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "两条路线：SIMT 与 Tile",
            "paras": [
                "GPU 内核是那个例外。你可以从 Rust 启动内核，但内核本身往往得用另一种语言来写。",
                "NVIDIA CUDA Rust 补上了这个缺口：GPU 内核可以直接用 Rust 写、原生编译成 PTX，而不是对别处代码的一层包装。",
                "用 Rust 有两条路线，对应 CUDA 自身已有的两条路线。" + c("SIMT") + " 是你在 CUDA C++ 或 numba-cuda 里已经熟悉的模型：你描述一个线程做什么，然后启动成千上万个线程。" + c("Tile") + " 是更新的编程模型，C++ 和 Python 里也已提供。这些前端都让你描述一个数据 tile 要做什么，剩下的交给 Tile IR 编译器。",
                "真要选一个动手，先选 Tile。编译器决定 tile 如何映射到每种架构，源码里不必写死架构相关的选择；需要那层控制、想自己管理内存和线程时，再下探到 SIMT。",
                "选哪种语言和选哪种模型是两件事。用最贴合你现有技术栈的那套 CUDA 接口即可，下面两个项目面向技术栈是 Rust 的场景。NVIDIA 计划支持跨语言互操作，所以这个选择不会把你锁死在其他生态之外。",
                "下面是同一条内核在两条路线上的实现，都对 1024 个浮点数做逐元素相加。两个都是完整程序，都能跑，也都会打印同一行结果，可以并排对照看差异。",
            ],
            "fig_after": {"5": [{"src": "fig01.png", "caption": ""}]},
        },
        {
            "type": "h2",
            "title": "SIMT 路线：cuda-oxide",
            "paras": [
                c("cuda-oxide") + " 是一个自定义的 rustc codegen 后端。它拦截编译过程，把 " + c("#[kernel]") + " 函数经由 Rust MIR、社区的 Pliron IR 框架、LLVM IR 一路降到 PTX，其余一切都交回标准后端。构建在 Pliron 之上的 GPU dialect 由 NVIDIA 自己实现，在标准 LLVM 后端接手之前，dialect 和每一次变换都留在 Rust 里。",
                "环境要求是 Linux、算力 8.0 及以上的 GPU、CUDA 工具包（12.x 或更新）、带 libclang 头文件的 clang，以及固定版本的 nightly 工具链。" + c("cargo oxide doctor") + " 会逐项检查，包括可选的系统 LLVM。先安装驱动构建的 Cargo 子命令 " + c("cargo-oxide") + "：",
                "__CODE__bash::" + CODE_1,
                "然后新建项目并运行。模板就是一个完整的向量加法程序：",
                "__CODE__bash::" + CODE_2,
                "第一次 " + c("cargo oxide run") + " 会构建 codegen 后端，所以会花上一段时间，之后的运行复用缓存。",
                "它会打印 " + c("PASSED: all 1024 elements correct") + "。下面是完成这件事的完整程序，与 " + c("cargo oxide new") + " 写出的内容一致，只是加了注释：",
                "__CODE__rust::" + CODE_3,
                "主机端和设备端代码在同一个文件里，一条命令构建，不需要单独的内核 crate。",
                "先看内核签名，整个安全论证都在这里。" + c("a") + " 和 " + c("b") + " 是普通的共享切片，每个线程都能读。" + c("c") + " 是 " + c("DisjointSlice<f32>") + "，这个类型把每个元素的所有权独占交给对应线程，不交别的。之所以需要它，是因为 " + c("&mut [f32]") + " 在这里形状不对：所有线程都需要同一个 " + c("&mut") + "，而 Rust 正确地拒绝了这种做法。" + c("DisjointSlice") + " 把这一次可变借用拆成按线程切分的若干份。",
                c("thread::index_1d()") + " 返回的是一个索引类型，不是裸整数，" + c("c.get_mut(idx)") + " 也只接受这个类型。拿回来的是 " + c("Option") + "，所以越界是一种你要显式处理的分支，而不是事后才发现的内存错误。",
                "启动是经过校验的，不是被信任的。" + c("#[launch_contract]") + " 声明这条内核按一维索引、块大小 256 线程。" + c("prepare_vecadd") + " 拿你的 " + c("LaunchConfig1D") + " 去对照这份声明和设备的实时限制，校验通过后返回一个凭据，安全的 " + c("vecadd") + " 方法需要这个凭据。没有合约的内核只暴露原始的 unsafe 启动方法，因为裸的 " + c("LaunchConfig") + " 并不能说明自己在启动什么内核。",
            ],
        },
        {
            "type": "h2",
            "title": "Tile 路线：cutile-rs",
            "paras": [
                c("cutile-rs") + " 站得更高一层：你在 tile 上做计算，而不是在标量上。每个 tile block 把内核体当作一个逻辑线程，在一次子张量的数据上跑一遍，具体用多少真实 GPU 线程由编译器决定。" + c("#[cutile::module]") + " 宏把内核的 AST 嵌进主机端二进制，在内核第一次真正需要时，通过 CUDA Tile IR（NVIDIA 的 tile 级编译器 IR）做 JIT。",
                "环境要求比 SIMT 路线轻：算力 8.0 及以上的 GPU、CUDA 13.3、stable Rust 1.89 或更新，以及 Linux，不需要 nightly 工具链，也不需要自备 LLVM。",
                c("cutile") + " 已经发布，不用克隆仓库：",
                "__CODE__bash::" + CODE_4,
                "下面是同一段逐元素加法，改用 tile 的写法。把它贴进 " + c("src/main.rs") + "，然后 " + c("cargo run") + "：",
                "__CODE__rust::" + CODE_5,
                "输出是 " + c("PASSED: all 1024 elements correct") + "。Tile 路线用 stable Rust 得到同样的答案，它的签名给出同样的安全论证。这次没有 " + c("DisjointSlice") + "：主机端的分区只对可变张量才需要，它把一块可写的子张量交给一个 tile block，别的 block 无法与之重叠。这种独占性正是 " + c("&mut") + " 本来就保证的。",
                "输入形状里的 " + c("-1") + " 是哨兵值，不是尺寸。这个维度在启动时从张量上读出来，所以形状可以变化而不用重新编译。",
                "主机端有意思的一行是 " + c(".partition([128])") + "，它同时做三件事。第一，让独占性落到实处：每个 tile 拥有自己那 128 个元素的块，别的 tile 碰不到。第二，定死启动几何：1024 除以 128 就是 8 个 tile 的网格。",
                "网格由分区推导出来，而不是另算一遍再拿去和内核的索引方式对账。它还顺带提供了 " + c("B") + "，调用点从来不写这个值，因为启动器会从分区上读 tile 宽度。这也是为什么 " + c("&mut") + " 输出必须先分区才能传进去。",
                "再看启动返回什么。你在主机端调用的 " + c("add") + " 是宏生成的启动器，不是上面那个设备函数。它拿走三个张量的所有权，在 GPU 完成后把它们作为元组还给你，" + c(".first()") + " 就是从里面把输出挑出来。",
                "在 " + c(".sync_on(&stream)") + " 之前什么都不会运行。它之前的一切都是惰性的描述，只记录、不提交，包括 " + c("ones") + "、" + c("zeros") + "、内核调用，甚至拷回主机。整个程序是一条链，只有一个同步点。",
            ],
        },
        {
            "type": "h2",
            "title": "编译器能挡住什么",
            "paras": [
                "两条路线的内核在内存上作出同样的声明：输入是共享的，输出只属于唯一的写入者。区别只在于它们在哪一层作出这个声明，以及是否需要为此专门造一个类型。",
                "这件事要紧，是因为成千上万个线程以不保证的顺序访问同一批缓冲区。当两个线程命中同一地址、其中一个在写时，顺序决定结果。这类 bug 很少能按需复现，它们往往先通过测试，然后在生产环境里炸掉。",
                "把 SIMT 内核的输出缓冲区当作它自己的输入传进去，编译不过，不管这条内核实际上会不会真的竞争：",
                "__CODE__rust::" + CODE_6,
                QUOTE % "error[E0502]: cannot borrow `c_dev` as mutable because it is also borrowed as immutable",
                "Tile 这边的同一处别名问题同样编译不过：",
                "__CODE__rust::" + CODE_7,
                QUOTE % "error[E0382]: use of moved value: `z`",
                "两个例子都在编译期抓住了经典的别名错误，但划线的地方不同。cuda-oxide 检查每一次启动调用；cutile-rs 的所有权跟着张量跨过启动边界，这是两者中更强的声明。",
                "Tile 没有共享内存和线程索引可以写错，因为两者都归编译器管。一个 tile block 就是一个逻辑线程，没有线程可竞争，这就是它构造上安全的来源，也是你交换出去的东西。SIMT 保留了那层控制，而今天那里的共享内存还需要 " + c("unsafe") + "。共享内存是高性能 SIMT 内核的地基，把这条路径变安全是正在进行的工作。",
            ],
        },
        {
            "type": "h2",
            "title": "两个项目的现状",
            "paras": [
                "两个项目都处于早期，都还没到生产可用。cuda-oxide 是早期 alpha；cutile-rs 走得更远，已发布在 crates.io，并在 NVIDIA 之外被 HuggingFace 的 Grout 推理引擎和 mistral.rs 使用。覆盖面还不完整，API 也会变动，遇到粗糙的地方欢迎反馈。",
                "Cargo 和 crates 让上手简单成为默认预期，而 GPU 编程历来相反，缩短这段距离本身就是工作的一部分。SIMT 路线仍然需要固定版本的 nightly 工具链，这正是 NVIDIA 希望不再向开发者索取的东西。",
                "GPU 上的 Rust 并不新鲜。这个领域有早于 NVIDIA、并且仍在并行推进的工作，cuda-oxide 手册里的生态附录梳理了自身相对 Rust-GPU、rust-cuda、CubeCL 等项目的位置，NVIDIA 也在与 rust-cuda 维护者合作，让两个项目一起成熟。",
                "新鲜的是 NVIDIA 投入其后的工程力量，以及对方向走向的清晰判断。",
            ],
        },
        {
            "type": "h2",
            "title": "今天你可以做什么",
            "paras": [
                DOT + "**跑 SIMT 示例：**在 cuda-oxide 里执行 " + c("cargo oxide new") + "，然后 " + c("cargo oxide run") + "。",
                DOT + "**跑 Tile 示例：**克隆 cutile-rs，然后执行 " + c("cargo run -p cutile-examples --example hello_world") + "。",
                DOT + "**读文档：**cuda-oxide 手册与 cuTile Rust 文档。",
                DOT + "**读论文：**Fearless Concurrency on the GPU。",
                DOT + "**提 issue：**哪里坏了、缺了什么，cuda-oxide 或 cutile-rs 都可以。",
                DOT + "**加入讨论：**两个仓库的 GitHub Discussions，或 cuda-oxide 的 Discord。",
                DOT + "**来听演讲：**Melih Elibol 将在 RustConf 2026（9 月 8 日至 11 日，蒙特利尔）讲 Fearless Concurrency on the GPU，NVIDIA 还有其他同事到场。",
                "拿现有的东西动手试试，然后一起做。它还早，它是开放的，你现在写的东西会塑造接下来发生的事。",
            ],
        },
        {
            "type": "h2",
            "title": "Rust 社区",
            "paras": [
                "NVIDIA 乐于和 Rust 社区一起推进原生 Rust GPU 编程。rust-cuda、rust-gpu 和 cudarc 等项目开创了 GPU 与 Rust 的结合，包括 VectorWare 团队在内的这些项目维护者，在 NVIDIA 构建自身工作时持续影响着它对这件事的思考。",
            ],
        },
    ],
    "conclusion": [
        "**CUDA Rust 真正的卖点不是「用 Rust 写 GPU」，而是把内存安全从运行期挪到了编译期。**SIMT 的别名检查落在每一次启动调用上，Tile 的所有权跟着张量跨过启动边界，后者是更强的声明。",
        "两条路线的分工很清楚：Tile 让编译器接管线程映射和内存布局，换来构造上安全，代价是你放弃那层控制；SIMT 保留控制权，代价是共享内存这条快路径今天还要 " + c("unsafe") + "。要动手就从 Tile 起步，需要精调再下探。",
        "生态位也分得开：cutile-rs 已经登上 crates.io，被 HuggingFace 的 Grout 和 mistral.rs 采用，是可用的今天；cuda-oxide 还在早期 alpha，要求固定 nightly 工具链，决定的是明天的方向。",
        "对做推理引擎和 kernel 库的人来说，现在跟紧 cutile-rs 的 API 演进成本很低。Rust 已经在系统层赢下不少位置，Dynamo 的 Rust 内核、Nova 驱动都是明证，这股力量正往内核里渗透；等跨语言互操作落地，前端语言的选择就不再是一场技术栈赌注。",
    ],
    "reference_url": "https://developer.nvidia.com/blog/introducing-cuda-rust-two-tracks-for-writing-gpu-kernels/",
}


def main():
    import json
    import os
    import sys
    d = sys.argv[1] if len(sys.argv) > 1 else "."
    ncode = sum(1 for s in DATA["sections"] for p in s["paras"] if p.startswith("__CODE__"))
    nfig = sum(len(v) for s in DATA["sections"] for v in (s.get("fig_after") or {}).values())
    nparas = sum(len(s["paras"]) for s in DATA["sections"])
    print("[build] sections=%d paras=%d code_blocks=%d figs=%d" % (len(DATA["sections"]), nparas, ncode, nfig))
    print("[build] summary=%d conclusion=%d lead=%d" % (len(DATA["summary"]), len(DATA["conclusion"]), len(DATA["lead"])))
    out = os.path.join(d, "article_data.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(DATA, f, ensure_ascii=False, indent=2)
    print("written", out)


if __name__ == "__main__":
    main()
