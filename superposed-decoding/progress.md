# Superposed Decoding - progress.md

## Step 0: 提取 completed
- 2026-07-31: web_extract 提取 arxiv HTML 2405.18400v6
- 图片: 18 张 (x1-x18) 下载

## Step 1: 封面 completed
- 2026-07-31: cover-letterbox.py 从 fig00.png 生成

## Step 2: 写文章 completed
- 2026-07-31: 手写 article_data_build.py
- 6 个 sections, 15 段, 7 张配图
- write-article-data.py 三重校验通过

## Step 3: 渲染+推送 completed
- 2026-07-31: render-article → preflight --fix → push-draft
