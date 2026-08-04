# longcat-sparse-attention - progress.md

## Step 0: 提取 completed
- 2026-08-04: HTTP 提取 arxiv HTML 2608.01662v1
- 图片: 9 张正式图下载（Fig1-9），代理+缓存buster
- 图注: 从 HTML figcaption 提取原文翻译

## Step 1: 封面 completed
- 2026-08-04: cover-letterbox.py 从 fig00.png 生成

## Step 2: 写文章 completed
- 2026-08-04: 手写 article_data_build.py
- 5 个 sections, 18 段, 9 张配图
- 修复 fig_after 索引越界（fig07/fig08 未渲染）
- write-article-data.py 三重校验通过

## Step 3: 渲染+推送 completed
- 2026-08-04: render-article → preflight --fix → push-draft
