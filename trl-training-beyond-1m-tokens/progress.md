✅ 完成 (trl-training-beyond-1m-tokens) — 2026-09-14 推送草稿
- 源: HuggingFace TRL 文档《Training Beyond 1M Tokens》
- 结构: 先跑起来 / 刚刚发生了什么（损失分块 · YaRN 位置重缩放 · 激活卸载 · 上下文并行） / 延伸阅读
- 正文图: 13（fig01-13，官方 documentation-images 原图，压缩到 1400 宽）
- 代码块: 9（accelerate 命令、首步输出、AutoConfig、rope_parameters、offload 配置、MLP 四张量、cp/sp 配置，均原样）
- 表格: 1（CP vs SP 对比：后端/设置项/切分对象/可扩展范围/注意力实现/依赖）
- 封面: 图 13（四杠杆叠加后单卡 256k vs 四卡 1M）
- 注: check-fig-layout 曾误报 fig11 连排（脚本把 <pre> 误判为 <p> 起点），把图 10 移到配置代码之前后 PASS
- preflight ALL PASS; FIG LAYOUT PASS; verify body 13 图
source: https://huggingface.co/docs/trl/long_context_training
| Step 0: 提取原文+下载图片 | completed |
| Step 1: 生成封面 | completed |
| Step 2: 写文章（含翻译+结语+参考区+传送门） | completed |
| Step 3: Humanizer 润色 | completed |
| Step 4: 预发布检查 | completed |
| Step 5: 推送草稿 | completed |
