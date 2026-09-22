# 进度追踪 - moe-inference-engineering

| Step | 状态 |
|------|------|
| Step 0: 目录创建与TASKS.md | completed |
| Step 0a: 语言类型判断（中/英） | completed (en) |
| Step 0b: 来源类型确认 | pending |
| Step 1: 内容提取（全文） | pending |
| Step 2: 全部图片下载 | pending |
| Step 3: 封面生成（900×383 + 500×500） | pending |
| Step 4a: 列出关键素材清单 | pending |
| Step 4a-i: 写要点速览 | pending |
| Step 4b: 确定独立观点 | pending |
| Step 4c: 写正文（含full_translation） | pending |
| Step 4d: 写结语 | pending |
| Step 4d-i: 写传送门（published_articles.json 选最多8篇） | pending |
| Step 4e: 写参考区 | pending |
| Step 4f: Humanizer 润色 | pending |
| Step 4g: 文本格式修复 | pending |
| Step 5: 预发布检查 | completed |
| Step 6: 推送草稿 | pending |

创建时间: 2026-09-19
来源: https://x.com/_avichawla/status/2100876555409039605
| Step 4d-i: 传送门 | completed |


---

## 完成记录 2026-09-19

- ✅ 完成 (moe-inference-engineering)
- 标题：MoE 推理工程：一个 token 从路由到专家并行的完整路径
- source: https://x.com/_avichawla/status/2100876555409039605
- draft.id: TIqnnVEu6Oy3-wtKttGa0RxpyNlIGskKSKO8vS2NJBavyhdFV7aX9OxYZzmsXfnO
- 正文：12 节 165 段中译；正文图 25 张（含 1 张原文 GIF 动图），位置与 DOM 一致
- 预检：ALL CHECKS PASSED；check-fig-layout PASS；draft/get 回读 25 张 mmbiz 图，0 占位符

## 乱码修复 2026-09-19 11:09

- 问题：标题 / 要点速览 / 首段 / 第一节标题 / 结语 的中文在写入时被转成「?」，正文与其余章节正常
- 根因：这几个字段是当时用 PowerShell here-string 内联传入 python 的（命令行路径非 UTF-8），非 ASCII 全部塌成 `?`；其余字段来自文件读入，未受影响
- 修复：按会话记录里的原文逐字回填 article_data.json + _data.json → 重 render → add-portal → preflight(ALL CHECKS PASSED) → 覆盖重推同一草稿
- 核验：draft/get 标题正确、正文 0 处 `?`、回读 25 张图（1 张 mmbiz_gif 动图）、要点速览/结语/传送门/参考区齐全
