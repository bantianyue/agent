# Torch 内部解析（第二篇）- TorchDynamo

## 原文信息
- 标题：Torch Internal (Part 2) — TorchDynamo
- 作者：Jino Rohit
- 发布时间：2026年6月24日
- 阅读时间：10分钟

---

## 引言部分

在上篇文章中，我们看到了 torch.fx 如何通过 Proxy 对象的符号追踪（symbolic tracing）将 Python 代码转换为计算图。

而 TorchDynamo 则是一个在 Python 字节码级别操作的 JIT 编译器，它捕获计算图并交给后端做进一步优化。

本文将重点探讨 Dynamo 的工作原理，以及它与符号追踪的差异。

## Dynamo 的不同之处

Dynamo 是一个追踪器（tracer）：给定一个函数及其输入，它会执行该函数并记录一个线性的指令序列（不含控制流）到图中。

与 FX 使用 Proxy 对象的符号追踪不同，Dynamo 通过**在字节码级别模拟 Python 虚拟机**来工作。

## Python 字节码

在理解 Dynamo 之前，我们需要理解 Python 实际如何运行代码。Python 将函数编译为**字节码**——这是供 Python 虚拟机（PVM）执行的低级指令序列。

当函数被调用时，Python 会创建一个**帧（frame）**，其中存储：
- 字节码指令
- 局部变量
- 全局变量
- 求值栈（evaluation stack）
- 块栈（block stack）

PVM 维护三个栈：

| 栈 | 用途 |
| --- | --- |
| 调用栈（Call stack） | 跟踪活跃的函数调用。当 foo() 调用 bar() 时，bar 的新帧被压入栈顶。 |
| 求值栈（Evaluation stack） | 存储字节码执行期间的临时值。a + b 的过程：压入 a，压入 b，弹出两个值计算结果，再将结果压回栈。 |
| 块栈（Block stack） | 跟踪活跃的控制流块，如循环、try/except、finally 和 with 语句。当控制流变化时（如 break、continue、异常或退出 with 块），它告诉 VM 该跳转到哪里。 |

## Dynamo 如何捕获计算图

这张图是 Dynamo 的核心思想。通常情况下，当调用函数时，Python 创建一个帧并直接交给 PVM 执行。

Dynamo 拦截了这个过程——在 PVM 即将执行帧之前，它有机会对该帧进行检查。帧中包含了函数的字节码、局部变量和求值栈。

因此，现在不再让 Python 立即执行字节码，Dynamo 逐条遍历指令，维护求值栈的符号版本，并将张量操作记录到 FX 图中。

这种利用字节码的技术显然比简单地使用 FX 追踪器进行符号追踪能处理更多场景。

## Guard（守卫）

Dynamo 捕获计算图后，通常将其交给 Inductor 进行下沉和优化。

现在有了一个被捕获的图，我们能一直复用这张图吗？在什么情况下这张图会失效，需要重新追踪？

Guard 就是干这件事的。Guard 是一个函数，用于检查编译函数输入属性是否发生变化。如果 Guard 通过，缓存的计算图被复用。如果 Guard 失败，函数被重新编译。

import torch
@torch.compile(backend=my_reallycoolcompilerhehe)
def foo(x, y):
  return (x + y) * x

foo(torch.randn(10), torch.ones(10))  # 首次编译
foo(torch.randn(10), torch.ones(10))  # 形状相同，不重新编译
foo(torch.randn(20), torch.ones(20))  # 形状变化，重新编译
foo(torch.randn(10, dtype=torch.float64), torch.ones(10, dtype=torch.float64))  # dtype 变化，重新编译
foo(torch.randn(10, device="cuda"), torch.ones(10, device="cuda"))  # 设备变化，重新编译

函数可以被重新编译的次数有上限。如果超过任一限制，则不再尝试编译该函数，而是直接以 eager 模式运行。

通常，张量的所有属性（dtype、device、shape 等）变化都会触发重新编译。

## Graph Break（图断裂）

当 Dynamo 遇到不支持的算子时，它会创建一个**图断裂**（graph break），将计算图拆分为几个它能支持的子图，并将控制权交还给 Python 解释器来执行不支持的算子。

def foo(x):
  x = torch.relu(x) # 被捕获到图 1
  print("hello") # 图断裂！无法捕获 print()
  x = torch.neg(x) # 被捕获到图 2
  return x

这是底层的执行流程：
1. torch.relu(x) 被捕获到图 1
2. print("hello") 导致图断裂——控制权返回给解释器
3. torch.neg(x) 被捕获到图 2

图断裂一般来说开销很大，但它也取决于图断裂发生的位置。每次图断裂意味着 Dynamo 必须暂停并将控制权交给解释器，等解释器执行完毕后再把控制权交回。这种来回切换通常是性能瓶颈所在，因此需要非常谨慎地尽量减少图断裂。

常见的图断裂原因：
- if x.sum() > 0：数据依赖的控制流
- print()：不支持的第三方操作

## 总结

下一篇我们将探讨 AOT Autograd，以及 Dynamo 捕获的计算图如何被转换为反向传播并下沉到后端编译器。