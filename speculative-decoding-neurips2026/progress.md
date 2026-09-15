# 进度追踪 - speculative-decoding-neurips2026

| Step | 状态 |
|------|------|
| Step 0: 目录创建与TASKS.md | completed |
| Step 0a: 语言类型判断（中/英） | completed (en) |
| Step 0b: 来源类型确认（交互式教程站点） | completed |
| Step 1: 内容提取（pw-extract + 站内结构化正文 _content.txt） | completed |
| Step 2: 全部图片下载（16 个交互动画 iframe 截图 + 6 张静态图，共 22 张） | completed |
| Step 3: 封面生成（900x383 + 500x500，源图 fig00_teaser.png） | completed |
| Step 4a: 列出关键素材清单（21 图 + 8 表 + 11 代码块） | completed |
| Step 4a-i: 写要点速览 | completed |
| Step 4b: 确定独立观点 | completed |
| Step 4c: 写正文（content.txt DSL -> build_gen.py -> article_data.json，174 段） | completed |
| Step 4d: 写结语 | completed |
| Step 4d-i: 写传送门（published_articles.json 选 16 篇） | completed |
| Step 4e: 写参考区 | completed |
| Step 4f: Humanizer 兜底（article.md / article_human.md baseline） | completed |
| Step 4g: 文本格式修复（preflight --fix：中英间距 + 标签格式） | completed |
| Step 5: 预发布检查（ALL CHECKS PASSED） | completed |
| Step 6: 推送草稿 | completed |

创建时间: 2026-09-15
来源: https://neurips2026-speculative-decoding.vercel.app/
draft.id: TIqnnVEu6Oy3-wtKttGa0Yc19w2NIfJb23RYHxTtEscmkZPXqY3VZ48w4G-fW8t2
图数核验: 22/22（verify-draft-images.py）
| Step 4d-i: 传送门 | completed |

## 动图修复（2026-09-15 21:38）
- 用户反馈：源站 16 个 iframe 交互动画被录成了静态图。
- 修复：用 Playwright 录制（点 replay 重启动画，25fps webm）→ ffmpeg 转 GIF，13 张动图（fig00/01/02/03/04/05/06/07/08/09/11/15/16），帧数 166-300，体积 0.7-8.3MB。
- 微信 uploadimg 实测上限：8.0MB 成功、10.6MB 报 40009 → 单图限额约 10MB。
- fig10/fig12/fig18 源文件本身是静态/交互控件（无动画），保留 PNG；fig13/14/17/19a/19b/20 为静态 SVG/PNG 数据图。
- 原草稿未动：media_id=TIqnnVEu6Oy3-wtKttGa0Yc19w2NIfJb23RYHxTtEscmkZPXqY3VZ48w4G-fW8t2（draft.old.id）
- 新草稿：media_id=TIqnnVEu6Oy3-wtKttGa0c3jsTmWAUv0DNpA4rXFcCN3TGSYfJujRiDpzaRYVxV8（draft.id），draft/get 核验 22 图 / 13 个 mmbiz_gif / 0 占位符。
- 静态版 PNG 备份在 _static_backup/
