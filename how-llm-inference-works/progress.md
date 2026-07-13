# 进度追踪 - how-llm-inference-works

| Step | 状态 |
|------|------|
| Step 0: 目录创建与TASKS.md | completed |
| Step 0a: 语言类型判断（英→翻译） | completed |
| Step 0b: 来源类型确认（X Article→fxtwitter） | completed |
| Step 1: 内容提取（fxtwitter，Article 正文+图） | completed |
| Step 2: 全部图片下载（7正文+1封面=8张） | completed |
| Step 3: 封面生成（900×383 + 500×500 letterbox） | completed |
| Step 4a: 列出关键素材清单 | completed |
| Step 4a-i: 写要点速览 | completed |
| Step 4b: 确定独立观点 | completed |
| Step 4c: 写正文（含full_translation） | completed |
| Step 4d: 写结语 | completed |
| Step 4e: 写参考区 | completed |
| Step 4f: Humanizer 润色 | pending |
| Step 4g: 文本格式修复 | completed |
| Step 4d-i: 写传送门 | pending |
| Step 5: 预发布检查 | in_progress |
| Step 6: 推送草稿 | pending |

## 备注
- 提取路径：fxtwitter API（X Article 正文在 article.content.blocks，图在 media_entities.original_img_url + cover_media）。CDP Chrome 在本机渲染 X Article 会 renderer 崩溃，已确认绕过。
- preflight "图片完整性" FAIL 为 false positive：脚本只扫根目录不递归 images/，图片实际完整（7张正文图在 images/，article.md 引用 images/xxx.jpg 正确）。
- 覆盖率 94.3%（跨语言翻译阈值 45%~70% 放宽，实际远超）。
