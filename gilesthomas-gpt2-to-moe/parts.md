# 系列分篇记录 — gilesthomas-gpt2-to-moe

来源：https://www.gilesthomas.com/2026/09/gpt-2-to-moe （正文 89,325 英文字符 / 48 张唯一图 / 87 段代码 / 3 张表）
分篇依据：按原文 h3/h4 章节边界切分，每篇 ≈ 1.1 万到 2 万字源文本；图与代码 100% 保留。

| 篇 | 标题 | 源章节范围 | 图 | 代码 | draft.id |
|----|------|-----------|----|------|----------|
| 1 | 从 GPT-2 到 MoE（一）：MoE 怎么工作，以及路由器为什么训练不起来 | How MoEs work → The router's output as weights | fig01–fig04（5 处引用） | 2 | TIqnnVEu6Oy3-wtKttGa0bxIdk1J3j51UxFQhfkyae1HjWx35sPni3hnh060NtEd |
| 2 | 从 GPT-2 到 MoE（二）：用负无穷掩码把路由变稀疏，然后真正开始写代码 | Making the router's output sparse → h4 From context vectors to logits… | fig04–fig13（10 处） | 24 | TIqnnVEu6Oy3-wtKttGa0aOKwqO8pp5UphZ7cJ5NHw6U4iKDwDTpAP6VP5NpL8M6 |
| 3 | 从 GPT-2 到 MoE（三）：用掩码把上下文向量送进专家，并加一条路由日志 | h4 Running the experts → h4 Logging the router logits and weights | fig04–fig19（12 处） | 31 | TIqnnVEu6Oy3-wtKttGa0baH1mDZ9bd2Uu7cRSC249-HNtOP9p95wYpAVVxare7X |
| 4 | 从 GPT-2 到 MoE（四）：第一次训练暴露的专家偏食，与 Switch 式负载均衡 | The first, non-load-balanced run → h4 Differentiability | fig23–fig35（13 处） | 4 | TIqnnVEu6Oy3-wtKttGa0bhP6UH-Bu2-ZAHMWcuZdEXaarsOzOHHjCbtOY9ePLcS |
| 5 | 从 GPT-2 到 MoE（五）：辅助损失的向量化实现与 α 的一小时扫描 | The code for auxiliary loss → Seeking alpha | fig07/13/20/21/22（5 处） | 15 | TIqnnVEu6Oy3-wtKttGa0RSLWVEZcHs2sIsic3PftGgX1f-Uag6fLr7S1DXTyndZ |
| 6 | 从 GPT-2 到 MoE（六）：八天训练、3.254 测试损失与 IFT 评测排名 | The training run → Conclusion + 脚注 | fig36–fig48（13 处） | 5 | TIqnnVEu6Oy3-wtKttGa0VAw_wu7-xkWkT6R7QVs3F9V5W--Pq3sbQGZXdr9oxYh |

## 构建与资产

- 图资产：`fig01.png` … `fig48.png`（22 张原文 SVG 用独立 headless Chromium 按 viewBox 渲染、白边裁剪后降到 1900px 宽；26 张原文 PNG 直接转 RGB）。
- 逐篇构建脚本：`build_p1.py` … `build_p6.py`；目录里的 `article_data_build.py` 始终是最后一篇（P6）的。
- 逐层路由图（12 张/组）按原文顺序以 4 张一组嵌在同一 figure 内，图注标明层号区间，未做裁剪或改色。
- 封面：`cover.png` / `cover-square.png`，取自原文图 3（MoE 块轮廓）。

## 推送注意（已踩）

`push-draft.py` 会读目录里的 `draft.id`：文件存在就**覆盖**该草稿，不存在才新建。推下一篇文章前必须先删 `draft.id`，否则会把上一篇草稿的内容覆盖掉（本项目 P1 曾被 P2 覆盖一次，已重推修复）。
