# nvidia-attention - progress.md

## Step 0: 提取 completed
- 2026-08-04: HTTP 提取 NVIDIA Developer Blog
- 图片: 7 张正式 Figure 下载（webp→png）

## Step 1: 封面 completed
- 2026-08-04: cover-letterbox.py 从 fig00.png 生成

## Step 2: 写文章 completed
- 2026-08-04: 程序化翻译全部正文（llm_utils.translate_batch）
- 8 个 sections, 51 段（42正文+3lead+6结论）, 7 张配图
- ≥80% 保留（原文约57段，保留约90%正文，删减纯公式行）

## Step 3: 渲染+推送 completed
- 2026-08-04: render-article → preflight --fix → push-draft
