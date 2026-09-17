/* 传送门统一样式（add-portal.py 动态注入时引用此 class） */
.portal-title { font-size:12px; color:#888; }
.portal-links { font-size:12px; color:#888; }
.portal-links a { color:#888; text-decoration:none; }

要点速览

- 两条路线：cuda-oxide 走 SIMT，用自定义 rustc codegen 后端把内核原生编译到 PTX；cutile-rs 走 Tile，每个 tile block 当做一个逻辑线程，经 CUDA Tile IR 做 JIT。选型上先 Tile，要控制线程和内存再下探 SIMT。- 编译期安全：cuda-oxide 用 DisjointSlice 把可变借用拆给各线程，再用启动合约校验 launch 配置；cutile-rs 靠主机端张量分区，让每个 tile 独占一块可写子张量。别名错误在两边都编译不过。- 落地门槛：cuda-oxide 仍是早期 alpha，需要 Linux、固定 nightly 工具链和自备 LLVM；cutile-rs 只需 stable Rust 1.89+ 与 CUDA 13.3，已发布在 crates.io，并被 HuggingFace 的 Grout 与 mistral.rs 采用。

2026 年 9 月，NVIDIA 宣布正式投入原生 Rust GPU 编程。CUDA C++ 与 CUDA Python 是成熟的、企业级工具链，而 CUDA Rust 会在 2027 年及之后持续成长。
AI 的系统层横跨推理引擎、服务基础设施、驱动和智能体运行时，并且随着模型与技术的更迭不断变化。其中越来越多的部分用 Rust 编写，它在不牺牲性能的前提下，把整类 bug 拦在编译期。
NVIDIA 出于同样的理由参与这场迁移：Nova Linux 驱动用 Rust 写，NVIDIA Dynamo 构建在 Rust 内核之上，NVTX 也提供了 Rust 绑定。

两条路线：SIMT 与 Tile
GPU 内核是那个例外。你可以从 Rust 启动内核，但内核本身往往得用另一种语言来写。
NVIDIA CUDA Rust 补上了这个缺口：GPU 内核可以直接用 Rust 写、原生编译成 PTX，而不是对别处代码的一层包装。
用 Rust 有两条路线，对应 CUDA 自身已有的两条路线。SIMT 是你在 CUDA C++ 或 numba-cuda 里已经熟悉的模型：你描述一个线程做什么，然后启动成千上万个线程。Tile 是更新的编程模型，C++ 和 Python 里也已提供。这些前端都让你描述一个数据 tile 要做什么，剩下的交给 Tile IR 编译器。
真要选一个动手，先选 Tile。编译器决定 tile 如何映射到每种架构，源码里不必写死架构相关的选择；需要那层控制、想自己管理内存和线程时，再下探到 SIMT。
选哪种语言和选哪种模型是两件事。用最贴合你现有技术栈的那套 CUDA 接口即可，下面两个项目面向技术栈是 Rust 的场景。NVIDIA 计划支持跨语言互操作，所以这个选择不会把你锁死在其他生态之外。
下面是同一条内核在两条路线上的实现，都对 1024 个浮点数做逐元素相加。两个都是完整程序，都能跑，也都会打印同一行结果，可以并排对照看差异。

SIMT 路线：cuda-oxide
cuda-oxide 是一个自定义的 rustc codegen 后端。它拦截编译过程，把 #[kernel] 函数经由 Rust MIR、社区的 Pliron IR 框架、LLVM IR 一路降到 PTX，其余一切都交回标准后端。构建在 Pliron 之上的 GPU dialect 由 NVIDIA 自己实现，在标准 LLVM 后端接手之前，dialect 和每一次变换都留在 Rust 里。
环境要求是 Linux、算力 8.0 及以上的 GPU、CUDA 工具包（12.x 或更新）、带 libclang 头文件的 clang，以及固定版本的 nightly 工具链。cargo oxide doctor 会逐项检查，包括可选的系统 LLVM。先安装驱动构建的 Cargo 子命令 cargo-oxide：
cargo&nbsp;+nightly-2026-04-03&nbsp;install&nbsp;--git&nbsp;https://github.com/NVlabs/cuda-oxide.git&nbsp;cargo-oxide
然后新建项目并运行。模板就是一个完整的向量加法程序：
cargo&nbsp;oxide&nbsp;new&nbsp;vecadd_democd&nbsp;vecadd_democargo&nbsp;oxide&nbsp;doctorcargo&nbsp;oxide&nbsp;run
第一次 cargo oxide run 会构建 codegen 后端，所以会花上一段时间，之后的运行复用缓存。
它会打印 PASSED: all 1024 elements correct。下面是完成这件事的完整程序，与 cargo oxide new 写出的内容一致，只是加了注释：
use&nbsp;cuda_device::{kernel,&nbsp;launch_bounds,&nbsp;launch_contract,&nbsp;thread,&nbsp;DisjointSlice};use&nbsp;cuda_host::cuda_module;use&nbsp;cuda_core::{CudaContext,&nbsp;DeviceBuffer,&nbsp;LaunchConfig1D};//&nbsp;===&nbsp;DEVICE&nbsp;CODE&nbsp;-&nbsp;everything&nbsp;in&nbsp;here&nbsp;is&nbsp;compiled&nbsp;to&nbsp;PTX&nbsp;===//&nbsp;The&nbsp;macro&nbsp;also&nbsp;generates&nbsp;the&nbsp;host-side&nbsp;API&nbsp;used&nbsp;further&nbsp;down://&nbsp;`load`,&nbsp;`prepare_vecadd`,&nbsp;and&nbsp;the&nbsp;safe&nbsp;`vecadd`&nbsp;launch&nbsp;method.#[cuda_module]mod&nbsp;kernels&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;use&nbsp;super::*;&nbsp;&nbsp;&nbsp;&nbsp;#[kernel]&nbsp;//&nbsp;GPU&nbsp;entry&nbsp;point&nbsp;&nbsp;&nbsp;&nbsp;#[launch_bounds(256)]&nbsp;//&nbsp;max&nbsp;threads&nbsp;per&nbsp;block;&nbsp;lets&nbsp;the&nbsp;compiler&nbsp;budget&nbsp;registers&nbsp;&nbsp;&nbsp;&nbsp;#[launch_contract(domain&nbsp;=&nbsp;1,&nbsp;block&nbsp;=&nbsp;(256,&nbsp;1,&nbsp;1))]&nbsp;//&nbsp;indexes&nbsp;in&nbsp;1-D,&nbsp;256-thread&nbsp;blocks&nbsp;&nbsp;&nbsp;&nbsp;pub&nbsp;fn&nbsp;vecadd(a:&nbsp;&amp;[f32],&nbsp;b:&nbsp;&amp;[f32],&nbsp;mut&nbsp;c:&nbsp;DisjointSlice&lt;f32&gt;)&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;idx&nbsp;=&nbsp;thread::index_1d();&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;idx_raw&nbsp;=&nbsp;idx.get();&nbsp;//&nbsp;the&nbsp;plain&nbsp;usize,&nbsp;for&nbsp;reading&nbsp;the&nbsp;inputs&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;if&nbsp;let&nbsp;Some(c_elem)&nbsp;=&nbsp;c.get_mut(idx)&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;*c_elem&nbsp;=&nbsp;a[idx_raw]&nbsp;+&nbsp;b[idx_raw];&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;}&nbsp;&nbsp;&nbsp;&nbsp;}}fn&nbsp;main()&nbsp;-&gt;&nbsp;Result&lt;(),&nbsp;Box&lt;dyn&nbsp;std::error::Error&gt;&gt;&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;===&nbsp;HOST&nbsp;SETUP&nbsp;-&nbsp;device,&nbsp;stream,&nbsp;and&nbsp;buffers&nbsp;===&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;ctx&nbsp;=&nbsp;CudaContext::new(0)?;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;stream&nbsp;=&nbsp;ctx.default_stream();&nbsp;&nbsp;&nbsp;&nbsp;const&nbsp;N:&nbsp;usize&nbsp;=&nbsp;1024;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;a_host:&nbsp;Vec&lt;f32&gt;&nbsp;=&nbsp;(0..N).map(|i|&nbsp;i&nbsp;as&nbsp;f32).collect();&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;b_host:&nbsp;Vec&lt;f32&gt;&nbsp;=&nbsp;(0..N).map(|i|&nbsp;(i&nbsp;*&nbsp;2)&nbsp;as&nbsp;f32).collect();&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;a_dev&nbsp;=&nbsp;DeviceBuffer::from_host(&amp;stream,&nbsp;&amp;a_host)?;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;b_dev&nbsp;=&nbsp;DeviceBuffer::from_host(&amp;stream,&nbsp;&amp;b_host)?;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;mut&nbsp;c_dev&nbsp;=&nbsp;DeviceBuffer::&lt;f32&gt;::zeroed(&amp;stream,&nbsp;N)?;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;===&nbsp;LOAD,&nbsp;PREPARE,&nbsp;LAUNCH&nbsp;===&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;SAFETY:&nbsp;this&nbsp;package&nbsp;owns&nbsp;the&nbsp;embedded&nbsp;device&nbsp;bundle&nbsp;produced&nbsp;for&nbsp;the&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;kernels&nbsp;module&nbsp;above.&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;module&nbsp;=&nbsp;unsafe&nbsp;{&nbsp;kernels::load(&amp;ctx)?&nbsp;};&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;4&nbsp;blocks&nbsp;of&nbsp;256&nbsp;threads,&nbsp;0&nbsp;bytes&nbsp;of&nbsp;dynamic&nbsp;shared&nbsp;memory.&nbsp;`prepare_vecadd`&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;checks&nbsp;that&nbsp;against&nbsp;the&nbsp;contract&nbsp;above&nbsp;and&nbsp;against&nbsp;the&nbsp;live&nbsp;device&nbsp;limits.&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;The&nbsp;safe&nbsp;`vecadd`&nbsp;below&nbsp;takes&nbsp;that&nbsp;token&nbsp;where&nbsp;a&nbsp;raw&nbsp;config&nbsp;would&nbsp;go.&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;prepared&nbsp;=&nbsp;module.prepare_vecadd(LaunchConfig1D::new((N&nbsp;as&nbsp;u32).div_ceil(256),&nbsp;256,&nbsp;0))?;&nbsp;&nbsp;&nbsp;&nbsp;module.vecadd(&amp;stream,&nbsp;&amp;prepared,&nbsp;&amp;a_dev,&nbsp;&amp;b_dev,&nbsp;&amp;mut&nbsp;c_dev)?;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;===&nbsp;READ&nbsp;BACK&nbsp;AND&nbsp;VERIFY&nbsp;===&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;Copies&nbsp;down&nbsp;and&nbsp;synchronizes,&nbsp;so&nbsp;the&nbsp;launch&nbsp;has&nbsp;finished&nbsp;by&nbsp;the&nbsp;time&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;`c_host`&nbsp;can&nbsp;be&nbsp;read.&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;c_host&nbsp;=&nbsp;c_dev.to_host_vec(&amp;stream)?;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;errors&nbsp;=&nbsp;(0..N)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.filter(|&amp;i|&nbsp;(c_host[i]&nbsp;-&nbsp;(a_host[i]&nbsp;+&nbsp;b_host[i])).abs()&nbsp;&gt;&nbsp;1e-5)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.count();&nbsp;&nbsp;&nbsp;&nbsp;if&nbsp;errors&nbsp;==&nbsp;0&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;println!(&quot;PASSED:&nbsp;all&nbsp;{}&nbsp;elements&nbsp;correct&quot;,&nbsp;N);&nbsp;&nbsp;&nbsp;&nbsp;}&nbsp;else&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;eprintln!(&quot;FAILED:&nbsp;{}&nbsp;errors&quot;,&nbsp;errors);&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;std::process::exit(1);&nbsp;&nbsp;&nbsp;&nbsp;}&nbsp;&nbsp;&nbsp;&nbsp;Ok(())}
主机端和设备端代码在同一个文件里，一条命令构建，不需要单独的内核 crate。
先看内核签名，整个安全论证都在这里。a 和 b 是普通的共享切片，每个线程都能读。c 是 DisjointSlice，这个类型把每个元素的所有权独占交给对应线程，不交别的。之所以需要它，是因为 &mut [f32] 在这里形状不对：所有线程都需要同一个 &mut，而 Rust 正确地拒绝了这种做法。DisjointSlice 把这一次可变借用拆成按线程切分的若干份。
thread::index_1d() 返回的是一个索引类型，不是裸整数，c.get_mut(idx) 也只接受这个类型。拿回来的是 Option，所以越界是一种你要显式处理的分支，而不是事后才发现的内存错误。
启动是经过校验的，不是被信任的。#[launch_contract] 声明这条内核按一维索引、块大小 256 线程。prepare_vecadd 拿你的 LaunchConfig1D 去对照这份声明和设备的实时限制，校验通过后返回一个凭据，安全的 vecadd 方法需要这个凭据。没有合约的内核只暴露原始的 unsafe 启动方法，因为裸的 LaunchConfig 并不能说明自己在启动什么内核。
Tile 路线：cutile-rs
cutile-rs 站得更高一层：你在 tile 上做计算，而不是在标量上。每个 tile block 把内核体当作一个逻辑线程，在一次子张量的数据上跑一遍，具体用多少真实 GPU 线程由编译器决定。#[cutile::module] 宏把内核的 AST 嵌进主机端二进制，在内核第一次真正需要时，通过 CUDA Tile IR（NVIDIA 的 tile 级编译器 IR）做 JIT。
环境要求比 SIMT 路线轻：算力 8.0 及以上的 GPU、CUDA 13.3、stable Rust 1.89 或更新，以及 Linux，不需要 nightly 工具链，也不需要自备 LLVM。
cutile 已经发布，不用克隆仓库：
cargo&nbsp;new&nbsp;vecadd_democd&nbsp;vecadd_democargo&nbsp;add&nbsp;cutile
下面是同一段逐元素加法，改用 tile 的写法。把它贴进 src/main.rs，然后 cargo run：
use&nbsp;cutile::prelude::*;//&nbsp;The&nbsp;macro&nbsp;captures&nbsp;this&nbsp;module&#39;s&nbsp;AST&nbsp;into&nbsp;the&nbsp;host&nbsp;binary.&nbsp;The&nbsp;kernel&nbsp;is//&nbsp;JIT-compiled&nbsp;through&nbsp;CUDA&nbsp;Tile&nbsp;IR&nbsp;the&nbsp;first&nbsp;time&nbsp;it&nbsp;is&nbsp;actually&nbsp;launched.#[cutile::module]mod&nbsp;kernel&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;use&nbsp;cutile::core::*;&nbsp;&nbsp;&nbsp;&nbsp;#[cutile::entry()]&nbsp;&nbsp;&nbsp;&nbsp;fn&nbsp;add&lt;const&nbsp;B:&nbsp;i32&gt;(&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;B&nbsp;is&nbsp;the&nbsp;tile&nbsp;width,&nbsp;a&nbsp;static&nbsp;dimension.&nbsp;A&nbsp;different&nbsp;B&nbsp;produces&nbsp;a&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;different&nbsp;specialization.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;z:&nbsp;&amp;mut&nbsp;Tensor&lt;f32,&nbsp;{&nbsp;[B]&nbsp;}&gt;,&nbsp;//&nbsp;exclusive&nbsp;output,&nbsp;one&nbsp;sub-tensor&nbsp;of&nbsp;B&nbsp;elements&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;x:&nbsp;&amp;Tensor&lt;f32,&nbsp;{&nbsp;[-1]&nbsp;}&gt;,&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;shared&nbsp;input;&nbsp;-1&nbsp;is&nbsp;a&nbsp;dynamic&nbsp;dimension,&nbsp;resolved&nbsp;at&nbsp;launch&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;y:&nbsp;&amp;Tensor&lt;f32,&nbsp;{&nbsp;[-1]&nbsp;}&gt;,&nbsp;&nbsp;&nbsp;&nbsp;)&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;This&nbsp;body&nbsp;runs&nbsp;once&nbsp;per&nbsp;mut&nbsp;sub-tensor,&nbsp;as&nbsp;a&nbsp;single&nbsp;logical&nbsp;thread.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;Tile&nbsp;kernels&nbsp;load&nbsp;tiles,&nbsp;not&nbsp;scalars,&nbsp;from&nbsp;x&nbsp;and&nbsp;y.&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;tx&nbsp;=&nbsp;load_tile_like(x,&nbsp;z);&nbsp;//&nbsp;the&nbsp;slice&nbsp;of&nbsp;x&nbsp;lining&nbsp;up&nbsp;with&nbsp;this&nbsp;sub-tensor&nbsp;of&nbsp;z&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;ty&nbsp;=&nbsp;load_tile_like(y,&nbsp;z);&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;z.store(tx&nbsp;+&nbsp;ty);&nbsp;//&nbsp;elementwise&nbsp;across&nbsp;the&nbsp;whole&nbsp;tile&nbsp;&nbsp;&nbsp;&nbsp;}}fn&nbsp;main()&nbsp;-&gt;&nbsp;Result&lt;(),&nbsp;Error&gt;&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;device&nbsp;=&nbsp;Device::new(0)?;&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;stream&nbsp;=&nbsp;device.new_stream()?;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;These&nbsp;are&nbsp;lazy.&nbsp;Nothing&nbsp;has&nbsp;touched&nbsp;the&nbsp;GPU&nbsp;yet.&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;x&nbsp;=&nbsp;api::ones::&lt;f32&gt;(&amp;[1024]);&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;y&nbsp;=&nbsp;api::ones::&lt;f32&gt;(&amp;[1024]);&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;Partitioning&nbsp;does&nbsp;three&nbsp;things&nbsp;at&nbsp;once:&nbsp;gives&nbsp;each&nbsp;tile&nbsp;exclusive&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;ownership&nbsp;of&nbsp;its&nbsp;own&nbsp;128-element&nbsp;chunk,&nbsp;fixes&nbsp;the&nbsp;grid&nbsp;at&nbsp;1024/128&nbsp;=&nbsp;8&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;tiles,&nbsp;and&nbsp;supplies&nbsp;B.&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;z&nbsp;=&nbsp;api::zeros::&lt;f32&gt;(&amp;[1024]).partition([128]);&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;c:&nbsp;Vec&lt;f32&gt;&nbsp;=&nbsp;kernel::add(z,&nbsp;x,&nbsp;y)&nbsp;//&nbsp;takes&nbsp;ownership&nbsp;of&nbsp;all&nbsp;three&nbsp;tensors&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.first()&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;...and&nbsp;returns&nbsp;them;&nbsp;pick&nbsp;the&nbsp;output&nbsp;back&nbsp;out&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.unpartition()&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;drop&nbsp;the&nbsp;host-side&nbsp;partition&nbsp;wrapper;&nbsp;no&nbsp;data&nbsp;moves&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.to_host_vec()&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;record&nbsp;the&nbsp;copy&nbsp;back&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;.sync_on(&amp;stream)?;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;//&nbsp;and&nbsp;only&nbsp;now&nbsp;does&nbsp;any&nbsp;of&nbsp;it&nbsp;run&nbsp;&nbsp;&nbsp;&nbsp;let&nbsp;errors&nbsp;=&nbsp;c.iter().filter(|&amp;&amp;v|&nbsp;(v&nbsp;-&nbsp;2.0).abs()&nbsp;&gt;&nbsp;1e-5).count();&nbsp;&nbsp;&nbsp;&nbsp;if&nbsp;errors&nbsp;==&nbsp;0&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;println!(&quot;PASSED:&nbsp;all&nbsp;{}&nbsp;elements&nbsp;correct&quot;,&nbsp;c.len());&nbsp;&nbsp;&nbsp;&nbsp;}&nbsp;else&nbsp;{&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;eprintln!(&quot;FAILED:&nbsp;{errors}&nbsp;errors&quot;);&nbsp;&nbsp;&nbsp;&nbsp;}&nbsp;&nbsp;&nbsp;&nbsp;Ok(())}
输出是 PASSED: all 1024 elements correct。Tile 路线用 stable Rust 得到同样的答案，它的签名给出同样的安全论证。这次没有 DisjointSlice：主机端的分区只对可变张量才需要，它把一块可写的子张量交给一个 tile block，别的 block 无法与之重叠。这种独占性正是 &mut 本来就保证的。
输入形状里的 -1 是哨兵值，不是尺寸。这个维度在启动时从张量上读出来，所以形状可以变化而不用重新编译。
主机端有意思的一行是 .partition([128])，它同时做三件事。第一，让独占性落到实处：每个 tile 拥有自己那 128 个元素的块，别的 tile 碰不到。第二，定死启动几何：1024 除以 128 就是 8 个 tile 的网格。
网格由分区推导出来，而不是另算一遍再拿去和内核的索引方式对账。它还顺带提供了 B，调用点从来不写这个值，因为启动器会从分区上读 tile 宽度。这也是为什么 &mut 输出必须先分区才能传进去。
再看启动返回什么。你在主机端调用的 add 是宏生成的启动器，不是上面那个设备函数。它拿走三个张量的所有权，在 GPU 完成后把它们作为元组还给你，.first() 就是从里面把输出挑出来。
在 .sync_on(&stream) 之前什么都不会运行。它之前的一切都是惰性的描述，只记录、不提交，包括 ones、zeros、内核调用，甚至拷回主机。整个程序是一条链，只有一个同步点。
编译器能挡住什么
两条路线的内核在内存上作出同样的声明：输入是共享的，输出只属于唯一的写入者。区别只在于它们在哪一层作出这个声明，以及是否需要为此专门造一个类型。
这件事要紧，是因为成千上万个线程以不保证的顺序访问同一批缓冲区。当两个线程命中同一地址、其中一个在写时，顺序决定结果。这类 bug 很少能按需复现，它们往往先通过测试，然后在生产环境里炸掉。
把 SIMT 内核的输出缓冲区当作它自己的输入传进去，编译不过，不管这条内核实际上会不会真的竞争：
module.vecadd(&amp;stream,&nbsp;&amp;prepared,&nbsp;&amp;c_dev,&nbsp;&amp;b_dev,&nbsp;&amp;mut&nbsp;c_dev)?;
error[E0502]: cannot borrow `c_dev` as mutable because it is also borrowed as immutable
Tile 这边的同一处别名问题同样编译不过：
let&nbsp;z&nbsp;=&nbsp;api::zeros::&lt;f32&gt;(&amp;[1024]);kernel::add(z.partition([128]),&nbsp;z,&nbsp;y)
error[E0382]: use of moved value: `z`
两个例子都在编译期抓住了经典的别名错误，但划线的地方不同。cuda-oxide 检查每一次启动调用；cutile-rs 的所有权跟着张量跨过启动边界，这是两者中更强的声明。
Tile 没有共享内存和线程索引可以写错，因为两者都归编译器管。一个 tile block 就是一个逻辑线程，没有线程可竞争，这就是它构造上安全的来源，也是你交换出去的东西。SIMT 保留了那层控制，而今天那里的共享内存还需要 unsafe。共享内存是高性能 SIMT 内核的地基，把这条路径变安全是正在进行的工作。
两个项目的现状
两个项目都处于早期，都还没到生产可用。cuda-oxide 是早期 alpha；cutile-rs 走得更远，已发布在 crates.io，并在 NVIDIA 之外被 HuggingFace 的 Grout 推理引擎和 mistral.rs 使用。覆盖面还不完整，API 也会变动，遇到粗糙的地方欢迎反馈。
Cargo 和 crates 让上手简单成为默认预期，而 GPU 编程历来相反，缩短这段距离本身就是工作的一部分。SIMT 路线仍然需要固定版本的 nightly 工具链，这正是 NVIDIA 希望不再向开发者索取的东西。
GPU 上的 Rust 并不新鲜。这个领域有早于 NVIDIA、并且仍在并行推进的工作，cuda-oxide 手册里的生态附录梳理了自身相对 Rust-GPU、rust-cuda、CubeCL 等项目的位置，NVIDIA 也在与 rust-cuda 维护者合作，让两个项目一起成熟。
新鲜的是 NVIDIA 投入其后的工程力量，以及对方向走向的清晰判断。
今天你可以做什么
●&nbsp;跑 SIMT 示例：在 cuda-oxide 里执行 cargo oxide new，然后 cargo oxide run。
●&nbsp;跑 Tile 示例：克隆 cutile-rs，然后执行 cargo run -p cutile-examples --example hello_world。
●&nbsp;读文档：cuda-oxide 手册与 cuTile Rust 文档。
●&nbsp;读论文：Fearless Concurrency on the GPU。
●&nbsp;提 issue：哪里坏了、缺了什么，cuda-oxide 或 cutile-rs 都可以。
●&nbsp;加入讨论：两个仓库的 GitHub Discussions，或 cuda-oxide 的 Discord。
●&nbsp;来听演讲：Melih Elibol 将在 RustConf 2026（9 月 8 日至 11 日，蒙特利尔）讲 Fearless Concurrency on the GPU，NVIDIA 还有其他同事到场。
拿现有的东西动手试试，然后一起做。它还早，它是开放的，你现在写的东西会塑造接下来发生的事。
Rust 社区
NVIDIA 乐于和 Rust 社区一起推进原生 Rust GPU 编程。rust-cuda、rust-gpu 和 cudarc 等项目开创了 GPU 与 Rust 的结合，包括 VectorWare 团队在内的这些项目维护者，在 NVIDIA 构建自身工作时持续影响着它对这件事的思考。

结语

CUDA Rust 真正的卖点不是「用 Rust 写 GPU」，而是把内存安全从运行期挪到了编译期。SIMT 的别名检查落在每一次启动调用上，Tile 的所有权跟着张量跨过启动边界，后者是更强的声明。两条路线的分工很清楚：Tile 让编译器接管线程映射和内存布局，换来构造上安全，代价是你放弃那层控制；SIMT 保留控制权，代价是共享内存这条快路径今天还要 unsafe。要动手就从 Tile 起步，需要精调再下探。生态位也分得开：cutile-rs 已经登上 crates.io，被 HuggingFace 的 Grout 和 mistral.rs 采用，是可用的今天；cuda-oxide 还在早期 alpha，要求固定 nightly 工具链，决定的是明天的方向。对做推理引擎和 kernel 库的人来说，现在跟紧 cutile-rs 的 API 演进成本很低。Rust 已经在系统层赢下不少位置，Dynamo 的 Rust 内核、Nova 驱动都是明证，这股力量正往内核里渗透；等跨语言互操作落地，前端语言的选择就不再是一场技术栈赌注。

【传送门】

Agent卷向AI Infra: SGLang团队用硬核Agent优化框架和CUDA Kernal性能
vLLM+Mooncake: 把agentic前缀复用从1.7%拉到92.2%
英伟达Kernel Agent: 编译器与算子调优Agent的协同设计
RL的下一个大突破：不是优化可验证问题而是把'不可验证'领域变得'可验证'
在NVFP4上超越cuBLAS: 从零手写+Claude极限优化Blackwell GEMM
KVCache缝合术: 突破前缀匹配天花板,首Token快14倍 多文档快2~4倍
TokenSpeed-Kernel：把推理内核做成一等公民
Kimi K3技术报告-后训练Infra: 三阶段 RL,MoonEP3,五千万沙箱,KDA感知缓存

参考：https://developer.nvidia.com/blog/introducing-cuda-rust-two-tracks-for-writing-gpu-kernels/