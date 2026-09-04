# -*- coding: utf-8 -*-
"""构建 OpenAI Jalapeño Hot Chips 文章 v3：全中文（去掉英文引语），13图，Q/A区分"""
import os, re

base=r"D:/06_Hermes/articles/openai-jalapeno-hotchips"
OUT=[]
def add(s): OUT.append(s)
def img(n): add(f'<img src="imgs/img{n:02d}.png" style="max-width:100%;margin:6px 0;border-radius:6px;"/>')
def para(t): add(f'<p style="font-size:15px;line-height:1.85;color:#333;margin:10px 0;text-align:justify;">{t}</p>')
def quote(zh): add(f'<div style="background:#f7f7f7;border-left:4px solid #c0392b;border-radius:4px;padding:12px 14px;margin:10px 0;"><p style="font-size:15px;color:#222;margin:0;line-height:1.75;">{zh}</p></div>')
def h1(t): add(f'<h1 style="font-weight:bold;font-size:25px;color:#111;margin:16px 0 6px;line-height:1.35;">{t}</h1>')
def h2(t): add(f'<h2 style="font-weight:bold;font-size:20px;color:#0a7d91;margin:26px 0 12px;padding-bottom:6px;border-bottom:2px solid #e0f0f0;">{t}</h2>')
def h3(t): add(f'<h3 style="font-weight:bold;font-size:17px;color:#111;margin:18px 0 8px;">{t}</h3>')

add('<section style="background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;max-width:100%;box-sizing:border-box;">')
h1('🌶️ Hot Chips：OpenAI「Jalapeño」芯片演讲全要点')
add('<p style="font-size:14px;color:#777;margin:0 0 16px;">📝 编译自 Tae Kim（Key Context）· 2026-08-25 Hot Chips 大会 · OpenAI Jalapeño 展示</p>')
para('<strong>演讲人</strong>：Richard Ho（OpenAI 硬件副总裁）、Ravi Narayanaswami（技术成员）、Chris Leary（技术成员）。周二（2026年8月25日）在 Hot Chips 大会上发表。')
para('以下是演讲中最关键的要点摘录：')
para('Richard 领导 OpenAI 硬件团队，曾参与 Google TPU 团队；Ravi 在 Cruise 工作十年，也曾任职 Google；Chris 曾任 Google TPU 软件负责人。')

h2('第一位演讲人：Richard')
img(1)
quote('Jalapeño 芯片来了，它是真的，我们实验室里已经跑起来了。这颗芯片让 OpenAI 能实现从模型、软件、编译器一路到硅片的全栈优化。我们基本上在九个月内完成了全部 RTL 实现。')
img(2)
para('之所以能这么快，是因为他们从一张白纸起步、全新设计，无需兼容任何旧架构或旧芯片。他们把精力集中在加速 OpenAI 的工作负载上——而这些工作负载正是大语言模型，因此所有 LLM 都因此受益。')

h2('第二位演讲人：Ravi')
quote('只有两件事真正重要：用户等待多长时间，以及每个请求消耗多少能量。')
h3('OSS 性能')
img(3)
quote('每个用户接近每秒 1500 token。这曾是 SRAM 加速器的领域，但 HBM 根本不是瓶颈。右侧是我们今天以 4 倍更低延迟提供的最高吞吐。')
para('世界需要又快又便宜。Jalapeño 两者兼备。')
h3('DeepSeek 性能')
img(4)
quote('每个用户每秒 700 token，这明显是 SRAM 级别的领域。对当前最高吞吐有 5 倍更低的延迟。故事是相同的，只是优势变大了——模型越大，优势越大。')
h3('Kimi 性能')
img(5)
quote('我们几乎没有花时间优化 Kimi，我想只花了几天的功夫。')
h3('设计理念')
img(6)
quote('项目启动时我们必须决定：是做一颗重度解码、超优化的芯片，还是一颗既擅长解码、也擅长 pre-fill 的芯片。我们选择了后者。选择单芯片方案的另一个理由是保持数据局部性。')

h2('第三位演讲人：Chris')
quote('纸面上的 FLOPS 并不重要，重要的是你在实际工作负载中真正交付给用户的 FLOPS。')
quote('这就引出了 Jalapeño 架构——一种内存分片（memory-sliced）架构。每个核心都对自己的 HBM 分片拥有本地视图。')
img(7)
quote('这意味着全局内存子系统上不存在争用，但也意味着你必须仔细思考自己的工作负载该如何映射到这台机器上。')
para('Jalapeño 的设计目标是通过把数据放在需要的地方、并在需要时到达，来降低等待时间。架构最小化了芯片空闲时间和数据移动，让数据贴近计算。它是针对 LLM 推理优化的。')
img(8)
quote('我们实际构建的是一个专用的集合网络，让各核心能以高性能互相通信。同样，你必须规划好如何映射到机器上。但好处是它经过精心编排，能在你恰好需要时把那些值放进寄存器。')
img(9)

h2('团队（The Team）')
quote('想造世界上最好的芯片、又想推进得飞快，只有两种选择：建一支很大的团队，或一支很小的团队。我们选了后者。我们项目过程中发现让这行得通的诀窍——也就是让你在开场看到的超快节奏的真正关键：能运转这套循环。你可以叫它敏捷，也可以叫它协同设计。')
img(10)
para('该团队引入了一种全新的硬件编程环境，OpenAI 的 AI 模型在这个环境里编写程序达到了极高的熟练度。')
quote('但借助 Sol、Astra 这类现代前沿大模型，它在为这种空间架构编写 kernel 上非常擅长。即便是我们专家调优过的 kernel，AI 也常常能再榨出一些额外性能。')
img(11)
quote('我们想解锁的能力，是真正让它们服务于各种工作负载、交付性能和每瓦性能。因为归根结底，对端到端工作负载而言，唯一重要的事就是如何获得交付出来的每瓦性能。')
img(12)

h2('回到 Richard')
quote('这是多代路线图的第一步。第二代已经在顺利开发中，我们正朝着在数个月内流片（tapeout）推进。整个重点在于这一切都会降低基础设施成本，正如我开场时所说。我真心为团队感到骄傲。我还要特别感谢我们的合作伙伴 Broadcom 和 Celestica，他们是我们能在这里交付这一能力的关键伙伴。')
img(13)

h2('问答（Q&A）')
qa=[
 ('关于九个月流片，这里面有多少是现成的 Broadcom IP、多少是你们从零设计的？',
  '芯片大部分是从零设计的。计算 die 上只有一些接口 IP，还有一个 IO 芯片。正如图中所示，很多接口是现成 IP，其余全部是用 XLS plus 和 Verilog 重新写的 RTL。'),
 ('Michael，来自 NVIDIA。想请你详细说说你们的组网方案：scale-up 网络用的是 ESUN 协议还是自定义的？链路是 200 吉比特还是 100 吉比特？',
  '我们用的是 scale-up 以太网协议，200 吉比特。谢谢。'),
 ('你们用了什么专用单元、专用存储器之类的专门电路或硅片工艺技巧吗？',
  '用的是标准单元（standard cell）方法学。'),
 ('你们的目标频率是多少？',
  '我们实验室里现有的芯片跑到 1.7 GHz，但 POR（计划运行点）应该能到 1.8。所以留了一点余量。这是持续性能。'),
]
qi=0
for q,a in qa:
    qi+=1
    add(f'<div style="background:#e8f4ff;border-left:4px solid #2196F3;border-radius:4px;padding:12px 14px;margin:14px 0 8px;">'
        f'<span style="display:inline-block;background:#2196F3;color:#fff;font-weight:bold;font-size:13px;border-radius:3px;padding:2px 8px;margin-right:8px;">问 {qi}</span>'
        f'<span style="font-weight:bold;font-size:15px;color:#0b3d6e;">{q}</span></div>')
    add(f'<div style="background:#fafafa;border-left:4px solid #4CAF50;border-radius:4px;padding:12px 14px;margin:0 0 6px 18px;">'
        f'<span style="display:inline-block;background:#4CAF50;color:#fff;font-weight:bold;font-size:13px;border-radius:3px;padding:2px 8px;margin-right:8px;">答</span>'
        f'<span style="font-size:15px;color:#333;line-height:1.7;">{a}</span></div>')

add('<p style="font-size:14px;color:#555;margin:16px 0;line-height:1.7;">Tae 点评：想了解 OpenAI 芯片对投资者的意义，可读他上周的 Hot Chips 大会关键要点总结。</p>')
add('<div style="margin-top:26px;padding:14px;background:#f5f0eb;border-radius:6px;font-size:13px;color:#555;line-height:1.7;">'
    '<strong>📌 来源</strong><br>编译自 Tae Kim《Key Context》Substack：Hot Chips: OpenAI Jalapeno Presentation<br>'
    '演讲人：Richard Ho / Ravi Narayanaswami / Chris Leary · Hot Chips 2026<br>'
    '链接：https://taekim.substack.com/p/hot-chips-openai-jalapeno-presentation</div>')
add('</section>')
html=''.join(OUT)
open(base+"/article_zh.html","w",encoding="utf-8").write(html)
zh=len(re.findall(r'[\u4e00-\u9fff]',html))
en_tech=len(re.findall(r'[A-Za-z]{3,}', re.sub(r'<[^>]+>',' ',html)))
print(f"✅ len:{len(html)} 中文:{zh} 英文词(技术词):{en_tech}")
print("用图:", len(re.findall(r'<img',html)), "/ 13")
"全部中文（仅技术专名保留英文：Jalapeño/token/SRAM/HBM/RTL/fill 等）"
