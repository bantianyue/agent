✅ 完成 (gva-grouped-value-attention) — 补齐 5 张原文图后覆盖推送（2026-09-10 第二版）
- 源: GitHub 论文 PDF《Grouped Value Attention: Efficient KV Caching via On-Demand Key Reconstruction》(FrontiersMind, GVA_Efficient-KV.pdf) 16p
- 覆盖范围: 概念与方法（摘要 / 引言 / 记法与现状 MHA-MQA-GQA-MLA / 方法 K=V·M 与 per-head 映射 / 吸收进 query / 解耦 RoPE / 缓存规模估算），实验与消融不展开
- 本次修复（用户报「缺少图片」）: 上一版把「PDF 论文无嵌入图」当成结论 → 0 图 + 文字卡封面。实际该 PDF 有 10 张图，用 PyMuPDF get_pixmap clip 按图注定位渲染，补入概念/方法部分需要的 5 张：图1 五种缓存策略对比（Fig.1）/ 图2 GQA-MLA-GVA 训练损失（Fig.2）/ 图3 共享 KV 损失对比（Fig.3）/ 图4 尺度失配热力图（Fig.4）/ 图5 尺度同步热力图（Fig.5）；实验节的 5 张基准准确率曲线（Fig.6-10）未纳入
- 同批修掉的缺陷: 空章节「尺度匹配的初始化」（段落被误挂到上一节 t(a,…)）、正文残留 LaTeX 片段与两处断句（吸收/decode 一步的公式缺失）、lead 与「关于本稿的剪裁」中的内部处理标记、封面由文字卡换成原文图1（900x383 + 500x500）
- 正文: 15 段 / 5 图（中文图注，逐图核对 图↔注 一一对应）
- 核验: preflight ALL CHECKS PASSED；check-fig-layout PASS（无连排 / 图序单调 / 无越界）；verify-draft body 5 图
- 推送: 2026-09-10 13:06 覆盖草稿 media_id: TIqnnVEu6Oy3-wtKttGa0ci4836WGr4qvl59f6oOCfE6joq37Lud1YgOwZO-pi1O
source: https://github.com/FrontiersMindAI/GVA/blob/main/GVA_Efficient-KV.pdf
| Step 0: 提取原文+下载图片 | completed |
| Step 1: 生成封面 | completed |
| Step 2: 写文章（含翻译+结语+参考区+传送门） | completed |
| Step 3: Humanizer 润色 | completed |
| Step 4: 预发布检查 | completed |
| Step 5: 推送草稿 | completed |
| Step 5: 预发布检查 | completed |
