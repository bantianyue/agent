# mixture-of-kittens - progress.md

## Step 0: 提取 completed
- 2026-08-04: HTTP 提取 Cursor 博客（Next.js SSR）
- 图片: 6 张正文图（light 版，blob.vercel-storage 直连），排除作者头像/深色版

## Step 1: 封面 completed
- 2026-08-04: cover-letterbox.py 从 fig00.png 生成

## Step 2: 写文章 completed
- 2026-08-04: 程序化翻译全部正文（llm_utils.translate_batch 146项）
- 22 个 sections, 116 段正文, 6 张配图
- ≥80% 保留（原文约125段，保留约92%）

## Step 3: 渲染+推送 completed
- 2026-08-04: render-article → preflight --fix → push-draft
