#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""inductor-internals 文章数据（TorchInductor 解析）。

生成链：python write-article-data.py .  →  python render-article.py .
原文无图（纯代码/文字页），因此无 fig_after；代码块逐字原样保留。
"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()


def C(s):
    """行内代码样式（浅灰底蓝字）。"""
    return '<code style="background:#f3f4f5;padding:2px 5px;border-radius:3px;color:#0F4C81;">' + s + '</code>'


# ===== 原文代码块（逐字保留，不翻译） =====
CODE_F = '''@torch.compile
def f(x):
    b = torch.floor(x) + torch.ceil(x)
    c = b.sum(dim=-1)
    d = c + 1
    return d'''

CODE_INPUT = '''TensorBox(
    StorageBox(
        InputBuffer(
            name="arg0",
            layout=FixedLayout(
                device="cuda:0",
                dtype=torch.float32,
                size=[32, 512, 1024],
                stride=[524288, 1024, 1]
            )
        )
    )
)'''

CODE_FLOOR = '''TensorBox(
    StorageBox(
        Pointwise(
            device='cuda:0',
            dtype=torch.float32,

            def inner_fn(index):
                i0, i1, i2 = index
                tmp0 = ops.load(arg0_1, i2 + 1024*i1 + 524288*i0)
                tmp1 = ops.floor(tmp0)
                return tmp1

            ranges=[32, 512, 1024]
        )
    )
)'''

CODE_FUSION = '''TensorBox(
    StorageBox(
        Pointwise(
            def inner_fn(index):
                i0, i1, i2 = index

                tmp0 = ops.load(arg0_1, i2 + 1024*i1 + 524288*i0)
                tmp1 = ops.floor(tmp0)

                tmp2 = ops.load(arg0_1, i2 + 1024*i1 + 524288*i0)
                tmp3 = ops.ceil(tmp2)

                tmp4 = tmp1 + tmp3
                return tmp4
        )
    )
)'''

CODE_REDUCTION = '''TensorBox(
    StorageBox(
        ComputedBuffer(
            name="buf0",
            data=Reduction(
                ranges=[32, 512],
                reduction_ranges=[1024],

                def inner_fn(index, rindex):
                    i0, i1 = index
                    r0 = rindex

                    tmp0 = ops.load(arg0_1, r0 + 1024*i1 + 524288*i0)
                    tmp1 = ops.floor(tmp0)

                    tmp2 = ops.load(arg0_1, r0 + 1024*i1 + 524288*i0)
                    tmp3 = ops.ceil(tmp2)

                    tmp4 = tmp1 + tmp3
                    return tmp4
            )
        )
    )
)'''

CODE_REDUCTION_LOOPS = '''for i0 in range(32):
    for i1 in range(512):
        total = 0
        for r0 in range(1024):
            total += floor(x[i0,i1,r0]) + ceil(x[i0,i1,r0])
        output[i0,i1] = total'''

CODE_LAST_POINTWISE = '''TensorBox(
    StorageBox(
        Pointwise(
            def inner_fn(index):
                i0, i1 = index
                tmp0 = ops.load(buf0, i1 + 512*i0)
                tmp1 = ops.constant(1, torch.float32)
                tmp2 = tmp0 + tmp1
                return tmp2
        )
    )
)'''

CODE_TRITON_OVERRIDES = '''class TritonOverrides(OpOverrides):
    @staticmethod
    def floor(x):
        return f"tl.math.floor({x})"

    @staticmethod
    def ceil(x):
        return f"tl.math.ceil({x})"

    @staticmethod
    def add(x, y):
        return f"({x} + {y})"

    @staticmethod
    def load(name, index):
        return f"tl.load({name} + ({index}), None)"'''

CODE_INNER_EXAMPLE = '''
def inner_fn(index):
    tmp0 = ops.load("in_ptr0", "x0")       # "tl.load(in_ptr0 + (x0), None)"
    tmp1 = ops.floor(tmp0)                 # "tl.math.floor(tl.load(...))"
    tmp2 = ops.ceil(tmp0)                  # "tl.math.ceil(tl.load(...))"
    tmp3 = ops.add(tmp1, tmp2)             # "(tl.math.floor(...) + tl.math.ceil(...))"
    return tmp3'''

CODE_TMP = '''tmp0 = tl.load(in_ptr0 + (x0), None)
tmp1 = tl.math.floor(tmp0)
tmp2 = tl.math.ceil(tmp0)          # reuses tmp0, no second load'''

CODE_CSE = '''class CSE:
    def generate(self, buffer, expr):
        var = self.cache.get(expr)
        if not var:
            var = self.newvar()
            self.cache[expr] = var
            buffer.writeline(f"{var} = {expr}")
        return var'''


DATA = {
    "title": "TorchInductor 是怎么工作的：从 FX 图降级到 Triton 内核",

    "summary": [
        {"key": "整体定位",
         "body": "torch.compile 编译栈的最后一站：接过 Dynamo 捕获的 FX 图，把它们变成真正跑在 GPU 上的 Triton 内核。"},
        {"key": "三阶段流程",
         "body": "先把 FX 图降级成自己的 IR，再调度并融合这些 IR 节点，最后遍历 IR 生成 Triton 代码。"},
        {"key": "两个关键机制",
         "body": "IR 只保存每个输出元素的计算配方，不真正执行；逐点算子的配方层层套进同一个 inner_fn 完成融合，CSE 再去掉重复加载。"},
    ],

    "lead": [
        "Dynamo 捕获前向图、AOTAutograd 切出后向图之后，torch.compile 只剩最后一站：TorchInductor 把 FX 图降级成自己的 IR，调度融合，再生成 Triton 内核。这层 IR 是整条链路的分水岭，读懂它就读懂了 Inductor 的取舍。",
    ],

    "sections": [
        # ===== 0：IR 总览 =====
        {
            "type": "h2",
            "title": "先看 Inductor 的 IR",
            "paras": [
                "在 torch.compile 这套编译栈里，前面几站已经把图准备好了：FX 图、TorchDynamo 在字节码层面的捕获，以及 AOTAutograd 切出的前向图与后向图。最后一站是 **TorchInductor**，它接过这些 FX 图，把它们变成高效的 Triton 内核。",
                "Inductor 分三个阶段工作。先把自己的 IR 建起来，这份 IR 记录的是每个元素该怎么算；然后调度这些 IR 节点并做融合；最后遍历 IR，生成 Triton 代码。",
                "第一步决定了后面能看到什么，所以先看这层 IR 长什么样。",
                "从一个最小的函数开始：",
                "__CODE__python::" + CODE_F,
                "下面逐行看这个函数被降级成了什么。",
            ],
        },
        # ===== 1：输入 =====
        {
            "type": "h3",
            "title": "1. 占位符与输入",
            "paras": [
                "输入 " + C("x") + " 被转换成的 IR 是这样：",
                "__CODE__python::" + CODE_INPUT,
                C("InputBuffer") + " 只保存输入张量的元信息，device、dtype、形状这些都记在里面，本身不涉及任何计算。可以把它理解成对一块已经在显存里的数据的一份引用。",
            ],
        },
        # ===== 2：逐点算子 =====
        {
            "type": "h3",
            "title": "2. 逐点算子",
            "paras": [
                C("torch.floor(x)") + " 会变成：",
                "__CODE__python::" + CODE_FLOOR,
                "对逐点算子，Inductor 保存的是一份「怎么算出一个输出元素」的配方，而不会真的去算。保存这份配方的函数叫 " + C("inner_fn") + "。",
                "读这个函数，就能看出它是怎么按 stride 把元素取出来、再算 floor 的。",
            ],
        },
        # ===== 3：逐点融合 =====
        {
            "type": "h3",
            "title": "3. 逐点算子的融合",
            "paras": [
                "逐点算子是这样，那两个逐点算子相加呢，比如 " + C("floor(x) + ceil(x)") + "？",
                "__CODE__python::" + CODE_FUSION,
                "两次计算没有各自留下一个 " + C("inner_fn") + "，而是被卷进了同一个函数。",
            ],
        },
        # ===== 4：归约 =====
        {
            "type": "h3",
            "title": "4. 归约算子",
            "paras": [
                "归约算子的表达方式不一样。它不像逐点算子那样只依赖对应位置的元素，而是依赖一大片元素。",
                "__CODE__python::" + CODE_REDUCTION,
                "概念上它做的事情是这样：",
                "__CODE__python::" + CODE_REDUCTION_LOOPS,
                "这行代码要表达的是 " + C("c = b.sum(dim=-1)") + "，所以 floor、ceil、加法又一次出现在归约内部。这不是重复计算，而是那些配方被原样复制进了这份归约配方。",
                "还要注意，归约结果被包在 " + C('ComputedBuffer(name="buf0")') + " 里。这说明它现在是后续算子可以读的逻辑张量，但不代表显存已经分配好，它最终住在寄存器、共享内存还是全局内存，要由调度器稍后决定。",
            ],
        },
        # ===== 5：最后一个逐点算子 =====
        {
            "type": "h3",
            "title": "最后一个逐点算子",
            "paras": [
                "函数最后一行 " + C("c + 1") + " 变成：",
                "__CODE__python::" + CODE_LAST_POINTWISE,
                "和前面的逐点节点不同，这次它从 " + C("buf0") + " 读数据，也就是归约的结果，而不是从输入张量读。",
                "输出节点把最终计算包进另一个 " + C('ComputedBuffer(name="buf1")') + "，它就是编译后函数返回的那个张量。",
            ],
        },
        # ===== 6：降级过程 =====
        {
            "type": "h2",
            "title": "降级是怎么发生的",
            "paras": [
                "上面几种 IR 只是结果，降级过程本身是这样的。",
                "我们已经看到，" + C("inner_fn") + " 是一个塞满 " + C("ops.load") + "、" + C("ops.floor") + " 的 Python 函数。但这些并不是 PyTorch 的算子，而是一层抽象算子，它们会被替换成什么，取决于代码生成阶段装上了哪个 handler。",
                C("ops.floor") + "、" + C("ops.load") + "、" + C("ops.add") + " 这类 " + C("ops.*") + " 定义在一个叫 " + C("OpOverrides") + " 的类上，长这样：",
                "__CODE__python::" + CODE_TRITON_OVERRIDES,
                "所以 " + C("inner_fn") + " 在代码生成阶段被执行时，返回的是这些写死的代码字符串，本身不计算任何东西。",
                "看个例子。",
                "__CODE__python::" + CODE_INNER_EXAMPLE,
                "这些 " + C("tmp0") + "、" + C("tmp1") + " 之类的中间变量又是从哪来的？",
            ],
        },
        # ===== 7：CSE =====
        {
            "type": "h3",
            "title": "公共子表达式消除",
            "paras": [
                "回头看 IR，" + C("inner_fn") + " 把同一份输入加载了两次，一次给 floor，一次给 ceil。但在生成的 Triton 代码里，这份输入只加载了一次。",
                "__CODE__python::" + CODE_TMP,
                "这件事由 Inductor 的 " + C("CSE") + " 类完成，它会把内容相同的表达式去重：",
                "__CODE__python::" + CODE_CSE,
                "两次加载的地址表达式完全一样，所以第二次直接复用同一个 " + C("tmp0") + " 变量。",
            ],
        },
        # ===== 8：收尾 =====
        {
            "type": "h2",
            "title": "编译栈到这里闭合",
            "paras": [
                "从 FX 图、Dynamo、AOTAutograd 一路走到 Inductor，torch.compile 这条链路就完整了。走完这一遍再回头看这套代码库，会轻松很多。",
            ],
        },
    ],

    "conclusion": [
        "**Inductor 的核心设计是先描述、后决定**：IR 阶段只保存每个输出元素该怎么算，既不分配显存也不执行计算，把「算什么」和「怎么排布」两件事彻底分开。",
        "① 逐点算子的融合发生在 IR 构建过程中。" + C("floor(x) + ceil(x)") + " 最终只留下一个 " + C("inner_fn") + "，两份配方被卷进同一个函数，而不是先各自成节点再靠额外的融合处理合并。",
        "② 归约算子单走一套表达。它依赖一大片元素，所以自带 reduction_ranges 这类描述；中间结果被包成 " + C("ComputedBuffer") + " 成为可读的逻辑张量，但真正分配到哪一级存储，要等调度阶段才定。",
        "③ 生成 Triton 代码时，" + C("ops.*") + " 交给 " + C("OpOverrides") + " 的子类，每个算子直接返回一段代码字符串，不碰数据；" + C("CSE") + " 再把地址表达式相同的加载合并，同一份输入因此只加载一次。",
        "对想读编译器源码的人，这层 IR 比调度策略更适合当入口：调度和代码生成改写的都是 IR 节点，而节点的形状在降级这一步就定下来了。看懂 TensorBox 里那几层包装，再读 Triton 模板就不会迷路。",
    ],

    "reference_url": "https://jino-rohit.github.io/blogs/15_inductor.html",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
nparas = sum(len(s.get("paras", [])) for s in DATA["sections"])
ncodes = sum(1 for s in DATA["sections"] for p in s.get("paras", []) if p.startswith("__CODE__"))
nfigs = sum(len(v) for s in DATA["sections"] for v in (s.get("fig_after") or {}).values())
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections, {nparas} paras, {ncodes} code blocks, {nfigs} figs)")
