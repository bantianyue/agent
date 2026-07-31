# Attention 机制演变 - progress.md

## Step 0: 提取 completed
- 2026-07-31: pw-extract 提取 X 推文 AI_Whisper_X
- 16K 字符中文长文
- 图片: 15 张下载（fig00-fig14）

## Step 1: 封面 completed
- 2026-07-31: cover-letterbox.py 从 fig00.jpg 生成

## Step 2: 写文章 completed
- 2026-07-31: 手写 article_data_build.py（中文原文，不翻译）
- 7 个 sections, 17 段, 2 张配图
- write-article-data.py 三重校验通过

## Step 3: 渲染+推送 completed
- 2026-07-31: render-article → preflight --fix → push-draft
