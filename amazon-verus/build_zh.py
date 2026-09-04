# -*- coding: utf-8 -*-
"""构建 Amazon Science Verus 文章（中文编译，≥80%内容保留）"""
import os, re
base=r"D:/06_Hermes/articles/amazon-verus"
OUT=[]
def add(s): OUT.append(s)
def img(n,cap=None):
    add(f'<img src="{n}" style="max-width:100%;margin:8px 0;border-radius:6px;"/>')
    if cap: add(f'<p style="font-size:12px;color:#777;text-align:center;margin:0 0 12px;line-height:1.5;">{cap}</p>')
def para(t): add(f'<p style="font-size:15px;line-height:1.9;color:#333;margin:10px 0;text-align:justify;">{t}</p>')
def h1(t): add(f'<h1 style="font-weight:bold;font-size:24px;color:#111;margin:16px 0 6px;line-height:1.4;">{t}</h1>')
def h2(t): add(f'<h2 style="font-weight:bold;font-size:19px;color:#0a7d91;margin:24px 0 10px;padding-bottom:6px;border-bottom:2px solid #e0f0f0;">{t}</h2>')
def h3(t): add(f'<h3 style="font-weight:bold;font-size:16px;color:#111;margin:16px 0 6px;">{t}</h3>')

add('<section style="background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;max-width:100%;box-sizing:border-box;">')
h1('🔍 用 Verus 写出「可证明正确」的 Rust 代码（Amazon Science 深度解读）')
add('<p style="font-size:13px;color:#888;margin:0 0 16px;">📄 来源：Amazon Science 博客 · Rust 形式化验证 · Verus 程序验证器</p>')

h2('为什么是 Rust，又为什么还不够')
para('许多开源与工业软件项目——包括亚马逊这里的多个项目——都在采用 Rust 编程语言。Rust 提供与 C 语言相近的性能和灵活性，同时它的类型系统能自动阻止多种 bug 和安全漏洞。结果是：比平均水平更快、更正确、更安全的代码。')
para('但<strong>「更正确、更安全」不等于「真的正确、真的安全」</strong>。举个例子：在 C 里，越界访问数组——索引越过分配给它的内存边界——是危险的错误，可能带来难以预料的后果；在 Rust 里则会直接让程序终止，这确实安全得多，但一个真正正确的程序根本不会发生越界。同样地，Rust 也无法保证你的程序会算出你预期的结果，或不会泄漏它能访问到的机密。这正是 Verus 登场的地方。')
img('imgs/verus-16x9.gif','Verus 官方演示')

h2('Verus 是什么？')
para('<strong>Verus</strong> 是一个开源的、自动化的 Rust 程序验证器。所谓"程序验证器"，是指它接收一份描述代码应如何行为的<strong>形式化数学规格</strong>，然后<strong>机械化地检查</strong>你的代码是否在所有可能输入下都匹配这份规格。')
para('举个例子：你的代码实现了某种优化的二分查找算法，用于在已排序数组里查找某个值。规格可能会声明：当代码成功返回一个索引时，数组中对应位置的元素必须等于要查找的目标值。验证器会检查：这一规格对所有可能的输入数组和目标值都成立。')
para('相比之下，传统测试只试几个特定数组，可能漏掉边界情况（例如目标值是数组最后一个元素，或根本不存在）。<strong>程序验证的关键是构造一个数学证明</strong>，证明代码符合规格。而在 Verus 这样的<strong>自动化</strong>验证器里，工具会自动处理许多繁琐、底层的证明构造步骤，人类开发者只需提供高层指引（比如建立归纳证明，或提供循环不变量）。如今，正如后面谈到的，连这些高层步骤也常常能由 AI 自动化完成。')

h2('亚马逊为什么采用 Verus')
para('亚马逊是 Rust 基金会的创始成员，并大量使用 Rust 开发项目，比如支撑 AWS Lambda 和 AWS Fargate 无服务器数据库的 <strong>Firecracker</strong>，以及负责 Nitro 虚拟化层虚拟机隔离的 <strong>Nitro Isolation Engine</strong>。亚马逊对 Rust 的热情，加上过去<strong>十多年自动推理的研究积累</strong>，使采用 Verus 为所写的 Rust 代码提供更强的保证成为自然而然的选择。')
para('事实上，我们已经用 Verus 证明了 Nitro Isolation Engine 关键原语的正确性，以及若干亚马逊内部关键基础设施的正确性。我们会在后续文章中详谈这些用例。')

h2('用 Verus 验证 Rust 代码')
para('用 Verus，Rust 开发者可以直接在 Rust 源文件中为现有代码添加规格（和证明）。延续二分查找的例子，下面是 search 函数现有 Rust 实现的 Verus 规格（以 Rust 注解形式书写）：')
img('imgs/verus-spec.png','Verus 二叉搜索函数规格：requires（前置条件）+ ensures（后置条件）')
para('<strong>前置条件</strong>（用 requires 关键字表示）声明了函数执行前必须为真的条件。此例中，由于实现的是二分查找，我们要求数组是已排序的。')
para('<strong>后置条件</strong>（用 ensures 关键字表示）声明了函数执行后必须为真的条件。此例中，它表示：如果函数返回 Some(index)，则该 index 在数组边界内，且该位置的元素等于我们在查找的值。')
para('重要的是，它也说明：如果函数返回 None，则目标值不在数组中。<strong>如果没有这第二条从句，一个总是返回 None 的实现也能满足这条规格！</strong>注意，普通的 Rust 编译器会忽略这些 Verus 注解，因此带注解的代码既可用于已验证项目，也可用于未验证项目，包括使用 Rust 构建工具 Cargo 的项目。')
para('这个例子也体现了 Verus 一个关键的设计决策——正是这一点让它区别于许多其他 Rust 验证方法：在 Verus 中，<strong>由开发者用类 Rust 语法直接在源码里写规格和证明</strong>。当证明失败时，他们看到的是源码层面的 Rust 风格错误信息。这种方式让证明与实际代码保持同步，也让开发者无需为了写规格和证明而学习一门全新的语言与工具，还能让最了解代码的人（也就是写代码的人）参与到证明其正确性的过程中。')
para('Verus 还专注于提供<strong>快速、强大</strong>的自动化，为此它使用多种求解器来处理从程序和规格生成的证明义务。在实践中，这意味着开发者通常能在<strong>一秒以内</strong>收到关于代码和证明的反馈，足以支撑交互式开发循环（包括在 VS Code 这类 IDE 里显示"红色波浪线"）。')
para('在项目层面，Verus 能在某些先前的自动验证器验证单个函数所需的时间内，验证数千行代码和证明的复杂项目。这种强大的自动化与快速反馈循环显然帮了人类，也帮助了 AI 智能体——因为自动化意味着智能体要做的工作更少，可以更快地在证明上迭代。')

h2('处理 unsafe 与并发的正确性')
para('Rust 的类型系统提供了强大的安全保证，但有时会阻止开发者写出高性能代码。因此 Rust 也允许开发者写显式标记为 unsafe 的代码。这类代码仍必须满足 Rust 对安全代码的全部期望，但编译器不再机械化地检查这些期望——要靠开发者自己保证正确。而用 Verus，开发者能<strong>数学上证明 unsafe Rust 代码的安全性</strong>，重新建立起机检安全保证。')
para('同样，Rust 以"无畏并发"著称——类型系统能防止其他语言允许的许多并发错误（并发即程序中至少有一部分并行执行的运行方式）。Verus 在此基础上，让开发者能够证明其并发代码不仅安全，而且正确。')
para('举例来说，并发执行通常涉及<strong>锁</strong>，它让一个处理器线程获得对当前操作数据的独占访问。Verus 允许开发者给锁添加一个<strong>不变量（invariant）</strong>属性：任何获得锁的人都得到一个满足该不变量的值（例如，该值恒为偶数），释放锁时必须证明锁背后的值仍满足该属性。此外，Verus 还支持证明锁实现本身是正确的。这对像 Nitro Isolation Engine 这样依赖复杂、定制锁方案来实现高性能的程序尤为重要。')

h2('验证链的信任基础')
para('和所有程序验证器一样，Verus 的保证依赖于：Verus 自身的正确性、程序预期行为的"顶层"规格、对底层运行时（如 Rust 标准库）所做的"底层"假设，以及把源码转换成可执行程序的<strong>编译器工具链</strong>的正确性。在后续文章中，我们会详细探讨如何增强对这些组件的信心。')

h2('Verus 在开源生态中的运用')
para('除了在亚马逊的使用，Verus 还被用于为多种开源项目证明有趣的属性。Verus 本身也是一个自由开源项目，由学术界和工业界研究者分布式协作开发。')

add('<p style="font-size:14px;color:#555;margin:16px 0;line-height:1.7;">📌 相关阅读：<strong>Isabelle/HOL · Nitro Hypervisor · XEX 分组加密结构</strong>（Amazon Science 相关文章）</p>')
add('<div style="margin-top:26px;padding:14px;background:#f5f0eb;border-radius:6px;font-size:13px;color:#555;line-height:1.7;">'
    '<strong>📌 来源</strong><br>Amazon Science：Developing provably correct Rust code with Verus<br>'
    '链接：https://www.amazon.science/blog/developing-provably-correct-rust-code-with-verus</div>')
add('</section>')
html=''.join(OUT)
open(base+"/article_zh.html","w",encoding="utf-8").write(html)
zh=len(re.findall(r'[\u4e00-\u9fff]',html))
print(f"✅ len:{len(html)} 中文:{zh}")
print("图:", len(re.findall(r'<img',html)))
