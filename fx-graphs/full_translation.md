# Torch 内部机制（第 1 部分）- FX Graphs

作者：Jino Rohit · 2026 年 6 月 26 日 · 阅读时间 10 分钟

这是一个新的博客系列，我将尝试拆解 PyTorch 和 PyTorch Compile 的整个生态。我一直想找一个深入挖掘的借口，了解 torch 做什么以及为什么这么做，以及它如何出色地完成这些事。希望在这个系列结束时，你能更深入理解 PyTorch 2.0 生态的工作原理，并能更舒适地调试程序。

## 什么是 FX Graph？

什么是 FX Graph？我为什么需要关心？我想读 torch.compile，跳过这些无聊的图。

坏消息！理解 FX Graphs 是理解编译生态所有其他组件的基础。从 Dynamo 到 Inductor，每个组件都以某种方式使用 FX Graph。好消息！我准备在一篇博客里全部讲清楚！

FX Graph 是 PyTorch 提供的一种中间表示（IR），它将 Python 代码转换为有向无环图（DAG）。

## 经典 DAG

DAG 意为有向无环图，基本由节点和有向边组成。

## 三个核心对象

FX Graph 只有三个概念你需要理解：`Graph`、`Node` 和 `GraphModule`。

| 概念 | 含义 |
|------|------|
| Graph | 由多个节点组成的有向图，代表整个计算过程 |
| Node | 图中的操作节点（输入、算子调用、输出等） |
| GraphModule | nn.Module 的子类，包装了 Graph |

下面是用 `torch.fx.symbolic_trace` 追踪一个简单模型的例子：

```python
import torch
import torch.fx

class MyModel(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.linear = torch.nn.Linear(4, 8)

    def forward(self, x):
        return torch.relu(self.linear(x))

gm = torch.fx.symbolic_trace(MyModel())
gm.graph.print_tabular()
```

输出：

| opcode | name | target | args | kwargs |
|--------|------|--------|------|--------|
| placeholder | x | x | () | {} |
| call_module | linear | linear | (x,) | {} |
| call_function | relu | built-in fn relu | (linear,) | {} |
| output | output | output | (relu,) | {} |

FX Graph 将 Python 代码展平为一系列节点。

### Graph

torch.fx.Graph 是一个内部持有节点序列的计算图。打印 gm.graph 可以看到完整结构：

```
graph():
    %x : [num_users=1] = placeholder[target=x]
    %linear : [num_users=1] = call_module[target=linear](args = (%x,), kwargs = {})
    %relu : [num_users=1] = call_function[target=torch.relu](args = (%linear,), kwargs = {})
    return relu
```

### Node

Node 是基本单元，代表一个输入、函数调用或输出。每个 Node 主要有 6 个字段。

### node.op

`node.op` 告诉你节点的广义类别，共 6 种取值：

| node.op | 含义 |
|---------|------|
| placeholder | 函数输入 |
| get_attr | 模块参数/属性 |
| call_function | Python 函数调用 |
| call_method | 值上的方法调用（如 .view()） |
| call_module | 子模块调用（如 self.linear） |
| output | 返回值 |

### node.name

`node.name` 是打印图时以 `%` 开头的临时变量名。

### node.args

`node.args` 是当前节点依赖的其他 Node 的元组，用于追踪数据流。

### node.kwargs

与 args 类似，但针对关键字参数。

### node.users

`node.users` 是当前节点被其他节点使用的次数。这对图变换至关重要——删除节点前必须检查 `len(node.users) == 0`，否则需要先将引用重定向到其他节点。它也是检测死代码的方法。

### node.target

这是最重要的字段，也是最令人困惑的，因为它的含义**取决于 node.op**。不能孤立地读 target。

| node.op | target 含义 | 示例 |
|---------|-------------|------|
| placeholder | 参数名 | "x" |
| get_attr | 属性的点分路径 | "linear.weight" |
| call_function | 实际的函数对象 | torch.relu, operator.add |
| call_method | 方法名（字符串） | "view", "permute" |
| call_module | 子模块路径 | "linear", "block.0" |

比如 `target="linear"`。如果 op 是 `call_module`，意味着"调用 self.linear"；如果 op 是 `get_attr`，意味着"读取 self.linear"（对模块类型 tensor 会报错）。所以**总是先检查 op 再读 target**。

### node.meta

`node.meta` 存储节点相关的元数据信息。

## FX Graph 是如何构建的

我们已经看到 torch.fx 神奇地将 Python 代码转换为图，但它是如何做到的？通过一种叫**符号追踪**（symbolic tracing）的机制。

### 符号追踪

为什么需要符号追踪？

普通 Python 代码运行时立即执行，执行完成后你只有结果，但不知道结果是如何产生的——也就是计算图不可见。

因此我们转向符号追踪。在符号追踪中，torch.fx 拦截每次调用并说"嘿，我看到一个 relu 操作"，然后创建一个 `Node`。实际计算并不发生，只做模拟。

这种拦截由 **Proxy** 对象完成。Proxy 包装每个输入值，并覆盖神经网络 forward 中可能用到的每个 Python dunder 方法：

- `__add__` — `x + 1`
- `__mul__` — `x * 2`
- `__sub__` — `x - 3`
- `__getattr__` — `.shape`, `.view()`
- `__getitem__` — `x[0]`
- `__torch_function__` — `torch.relu(x)`
- `__call__` — `self.linear(x)`

每次这些钩子被触发时，Proxy 创建一个新的 Node 并记录操作。

### 符号追踪的局限性

**1. 动态控制流** — 如果条件分支依赖运行时数据（变量、用户输入等），无法追踪，因为 Proxy 没有真实值来计算条件：

```
def forward(self, x):
    if x.sum() > 0:        # proxy 无法求值！
        return torch.relu(x)
    else:
        return torch.neg(x)
```

只有追踪时实际执行的那个分支会被记录，导致图不完整。

**2. 非 torch 的 Python 函数** — 普通 Python 函数不会被拦截。

**3. 静态控制流没问题** — 如果条件在初始化时就已知，追踪可以完美工作：

```python
class MyModule(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.do_activation = False
        self.linear = torch.nn.Linear(512, 512)

    def forward(self, x):
        x = self.linear(x)
        if self.do_activation:  # 静态条件，不依赖数据
            x = torch.relu(x)
        return x
```

## 总结

理解 FX Graphs 是理解整个 PyTorch 2.0 编译栈的第一步。下一篇文章中，我们将探讨 **TorchDynamo**——字节码级别的 JIT 编译器——以及它是如何处理这些问题的。
