# scaling-understanding - progress.md

## Step 0: 提取 completed
- 2026-08-05: HTTP 提取 Antimetal 博客（Next.js SSR）
- 图片: header 1 张 + 内嵌 SVG 2 张（节点图/遥测压缩图），headless Chrome 转 PNG

## Step 1: 封面 completed
- 2026-08-05: cover-letterbox.py 从 fig_header.jpg 生成

## Step 2: 写文章 completed
- 2026-08-05: 程序化翻译全部正文（llm_utils.translate_batch 27段）
- 3 个 sections, 18 段正文, 2 张配图
- ≥85% 保留（全文几乎全保留）

## Step 3: 渲染+推送 completed
- 2026-08-05: render-article → preflight --fix → push-draft
