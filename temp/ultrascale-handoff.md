# Handoff — The Ultra-Scale Playbook (nanotron)
状态: 巨型交互 playbook,本节已定性并落素材,尚未产出可推成稿。由下轮/子代理续跑分篇。

## 真相源
- 主正文: D:/06_Hermes/articles/ultrascale_blog.md  (209 KB, 208,381 字符, ≈31,400 英文词, 82 heading)
- 公网 md: https://huggingface.co/spaces/nanotron/ultrascale-playbook/raw/main/ultra_blog.md
- Space 仓库文件树: https://huggingface.co/api/spaces/nanotron/ultrascale-playbook/tree/main?recursive=true
  → 交互图 assets/data/benchmarks/*.html (17个), assets/images/*.html(parallel_coordinates 4.6MB), assets/data/fp8/*.html,
    ultra_cheatsheet.svg, screenshot.png(cover候选), dist/ 为 webpack 产物, python/ measurement 代码。

## 三个元结构
High level overview 的"木桶三挑战"(全书主线):
  1) Memory Usage                  —— 训练步装不下则无法训练(硬约束)
  2) Compute Efficiency            —— 让硬件多在计算、少等传输/别人
  3) Communication overhead        —— 多用 intra-node(快)与 overlap 通信与计算
三者可互相 trade(memory↔compute 如 recomputation/TP),找 balance 即 scaling 核心。

## 章节地图(82 headings 主要章节)
Single GPU(记忆建模/激活重算/grad累积) → DP(3优化) → global batch → ZeRO-1/2/3 → TP/SP/CP → Ring Attention / Zig-Zag → PP(流水/dualpipe/zero bubble) → Expert parallelism → 5D → config 搜索(4000+ benchmark) → kernel(内存合并/tile/fuse/FlashAttention 1-3) → mixed precision(FP16/BF16/FP8) → Conclusion / What's next / refs

## 推进计划(方案A - 逐篇自主, 分篇推送)
建议分 ~8 篇微信推送, 每篇一个纵深主题:
 P1 全书导航+Single-GPU与记忆建模(记忆公式/激活/dan重算/grad累加)
 P2 DP + global batch + 3 优化
 P3 ZeRO-1/2/3
 P4 TP/SP/CP + Ring/Zig-Zag Attention
 P5 PP 流水/zero bubble/DualPipe + 专家并行 →5D
 P6 benchmark 导航与 config 搜索/lessons(fig 抽文字)
 P7 Kernel/FlashAttention/FP16-BF16-FP8
 P8 Conclusion+what's next
每个正文段落: 交互 HTML(benchmarks_interactive/memory-profile/parallel_coordinates/fp8 curves)不内嵌 → 抽图中关键结论用文字转述 + 注明为可交互演示; ultra_cheatsheet.svg 需按 refs/svg-rasterization-viewbox 转 png 作副封面/cheatsheet(宽图)如放文作为 info 卡。
cover: screenshot.png(可) 用 make-cover-from-original。
命名约定沿用: content.txt DSL (S#/T/F figNN|cap) + build_gen.py 通用 parser(取自已成功 moe/spectrum 目录)。

## 本轮已做
- 抓到全文 md(209KB)入库
- overview 摘译见上述,可复用于 P1/P8
- 图表 inventory(17+ 巨型 html)→ 方案定: 文字转述结论,不伪造静态帧
- 决定与交接: 结束于定性+计划,非卡死。未建 wcsop文章目录;下一篇从 ultrascale-playbook-<篇名> slug 新建。
继续方: 下条指令可让"继续 P1"直接推
