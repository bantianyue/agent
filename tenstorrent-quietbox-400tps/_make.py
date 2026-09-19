#!/usr/bin/env python3
# 文本 DSL（content.txt）→ article_data.json
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DSL = os.path.join(HERE, 'content.txt')
OUT = os.path.join(HERE, 'article_data.json')

BULLET = '<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;'

sections = []
cur = None


def new_section(kind, title):
    global cur
    cur = {"type": kind, "title": title, "paras": [], "fig_after": {}}
    sections.append(cur)


def add_fig(name, caption):
    i = len(cur["paras"]) - 1
    assert i >= 0, 'F 行出现在任何 T 行之前: ' + name
    cur["fig_after"].setdefault(str(i), []).append({"src": name, "caption": caption})


for raw in open(DSL, encoding='utf-8'):
    line = raw.rstrip('\n').strip()
    if not line:
        continue
    if line.startswith('S# '):
        new_section('h2', line[3:].strip())
    elif line.startswith('H# '):
        new_section('h3', line[3:].strip())
    elif line.startswith('T '):
        cur["paras"].append(line[2:].strip())
    elif line.startswith('B '):
        cur["paras"].append(BULLET + line[2:].strip())
    elif line.startswith('F '):
        payload = line[2:].strip()
        name, _, caption = payload.partition('|')
        add_fig(name.strip(), caption.strip())
    else:
        raise SystemExit('无法解析的行: ' + line[:60])

DATA = {
    "title": "1.2万美元的 Tenstorrent QuietBox 跑出 400 token/s：桌面级 SRAM 推理的极限（8B MoE）",
    "summary": [
        {"key": "结果", "body": "Marco-Nano-Instruct（8B MoE，每 token 激活约 6 亿参数）在 1.2 万美元的 Tenstorrent QuietBox 上完成全自回归解码，交付路径 397.7 token/s，不含最终 token 日志交付的 trace 重放 402.6 token/s。"},
        {"key": "方法", "body": "绕开外部内存天花板的关键是把循环复用的关键张量驻留（residency）在 720MB 片上 SRAM，只让选定的冷专家权重从 GDDR6 流式加载，而不是每个 token 都往返外部内存。"},
        {"key": "对比", "body": "项目记录中最强的全 DRAM 端到端约 260 token/s，把交付路径改为 SRAM 驻留后提升约 53%；同层驻留 A/B 在 2048 上下文实测 1.248 倍，四芯片结果成为 Galaxy 32 芯片扩展的架构证明。"},
    ],
    "lead": [
        "我们拿 **Marco-Nano-Instruct**（80 亿参数的混合专家模型，每个 token 激活约 6 亿参数），把完整的自回归解码流水线，在一台放在桌边的 **1.2 万美元 Tenstorrent QuietBox（Blackhole）**上推到了 **397.7 token/s**。",
        "这个数字不是靠投机解码、草稿模型或跳层换来的：token 完整穿过全部 28 层、最终归一化和语言模型头，再通过设备端反馈回到下一步。真正的杠杆是 **SRAM 驻留**，把每个 token 都要用到的关键数据留在芯片上，而不是反复去外部内存取。",
    ],
    "sections": sections,
    "conclusion": [
        "**把循环复用的数据从外部内存搬到片上 SRAM，是这次 400 token/s 的真正来源**。Marco Nano 的 8B 规模不大，但它包含大规模 MoE 必须做的全部工作类别：注意力、路由、专家执行、集合通信与自回归反馈。",
        "机制上有三点值得记住：关键解码状态常驻 SRAM，消除了每个 token 的重复往返；冷专家权重继续从 GDDR6 流式加载，保证容量不被模型规模卡住；而 1.248 倍的同层驻留 A/B 才是做完融合、预取、trace 重放之后，内存摆放带来的干净收益。",
        "对做推理的人来说，这个桌面级结果把一个方向性判断变成了可验证的路线：把芯片加到关键路径能装进分布式 SRAM 为止。当 Galaxy 把片上 SRAM 从 720MB 推到 6.2GB、四 Galaxy 再堆到 24.8GB，400 token/s 这一档就不再只是桌面玩具。",
    ],
    "reference_url": "https://medium.com/&#64;arnis.us/400-tokens-per-second-on-a-12-000-tenstorrent-quietbox-425aaf55bbeb",
}

# 越界/缺图自检
figs = []
for s in sections:
    for k, items in s["fig_after"].items():
        assert int(k) < len(s["paras"]), 'fig_after 越界: %s key=%s paras=%d' % (s["title"], k, len(s["paras"]))
        for it in items:
            figs.append(it["src"])
            assert os.path.exists(os.path.join(HERE, it["src"])), '缺图: ' + it["src"]

disk = sorted(f for f in os.listdir(HERE) if f.startswith('fig') and f[-4:] in ('.png', '.gif'))
print('sections=%d paras=%d figs=%d' % (len(sections), sum(len(s["paras"]) for s in sections), len(figs)))
print('引用图:', figs)
print('磁盘图:', disk)
print('缺引用:', [f for f in disk if f not in figs], '| 多引用:', [f for f in figs if f not in disk])

with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print('已写出', OUT)
