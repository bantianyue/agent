# skill 迁移报告（第二轮 · 排除 node_modules）

源 `C:\Users\twfehh7\.codex\skills`（只读，未改动） → 目标 `C:\Users\twfehh7\.workbuddy\skills`

## 清理残缺副本

- 已删除 `C:\Users\twfehh7\.workbuddy\skills\baoyu-post-to-wechat\scripts\node_modules`（3161 个文件）

## 复制结果

| skill | 副本文件数 | 副本体积 |
|---|---:|---:|
| article-collect | 3 | 0.02 MB |
| article-tracker-maintenance | 4 | 0.03 MB |
| articles-content-edit | 1 | 0.00 MB |
| baoyu-post-to-wechat | 38 | 0.37 MB |
| figure-extraction | 2 | 0.02 MB |
| paper-analysis-wechat | 18 | 0.15 MB |
| url-content-extraction | 6 | 0.03 MB |
| video-to-article | 1 | 0.01 MB |
| video-to-wechat-article | 4 | 0.02 MB |
| web-content-fetch | 4 | 0.01 MB |
| wechat-article-sop | 277 | 2.35 MB |
| **合计** | **358** | **3.02 MB** |

## 源目录完整性校验

| 项 | 复制前 | 复制后 | 一致 |
|---|---:|---:|:--:|
| 文件总数 | 419 | 419 | 是 |
| 总字节 | 3561361 | 3561361 | 是 |
| SKILL.md 哈希 | 17 | 17 | 是 |

## 路径改写（.codex/skills → .workbuddy/skills）

共 25 个文件、39 处。

| 副本内文件 | 处数 |
|---|---:|
| `wechat-article-sop/pipeline.json` | 9 |
| `wechat-article-sop/SKILL.md` | 4 |
| `wechat-article-sop/references/draft-lifecycle.md` | 3 |
| `wechat-article-sop/references/wcsop-push-tips.md` | 2 |
| `wechat-article-sop/references/article-data-build-guide.md` | 1 |
| `wechat-article-sop/references/article-git-watcher.md` | 1 |
| `wechat-article-sop/references/bulk-operations-tips.md` | 1 |
| `wechat-article-sop/references/draft-sync-workflow.md` | 1 |
| `wechat-article-sop/references/extraction-decision-record.md` | 1 |
| `wechat-article-sop/references/gemini-cover-generation.md` | 1 |
| `wechat-article-sop/references/html-first-path-portal-pitfalls.md` | 1 |
| `wechat-article-sop/references/html-first-pipeline-pitfalls.md` | 1 |
| `wechat-article-sop/references/playwright-extraction.md` | 1 |
| `wechat-article-sop/references/portal-missing-diagnosis.md` | 1 |
| `wechat-article-sop/references/proxy-chain-diagnostic.md` | 1 |
| `wechat-article-sop/references/quick-edit-figure-preview.md` | 1 |
| `wechat-article-sop/references/skill-md-integrity-check.md` | 1 |
| `wechat-article-sop/references/substack-image-format.md` | 1 |
| `wechat-article-sop/references/svg-to-png-wechat.md` | 1 |
| `wechat-article-sop/references/todo-recovery.md` | 1 |
| `wechat-article-sop/references/wechat-draft-download.md` | 1 |
| `wechat-article-sop/references/wechat-proxy-troubleshooting.md` | 1 |
| `wechat-article-sop/references/wechat-resync-workflow.md` | 1 |
| `wechat-article-sop/references/windows-push-path-pitfall.md` | 1 |
| `wechat-article-sop/references/wsl-to-windows-wechat-migration.md` | 1 |

## 副本可用性校验

| skill | SKILL.md | frontmatter name |
|---|:--:|---|
| article-collect | 有 | article-collect |
| article-tracker-maintenance | 有 | article-tracker-maintenance |
| articles-content-edit | 有 | articles-content-edit |
| baoyu-post-to-wechat | 有 | baoyu-post-to-wechat |
| figure-extraction | 有 | figure-extraction |
| paper-analysis-wechat | 有 | paper-analysis-wechat |
| url-content-extraction | 有 | url-content-extraction |
| video-to-article | 有 | video-to-article |
| video-to-wechat-article | 有 | video-to-wechat-article |
| web-content-fetch | 有 | web-content-fetch |
| wechat-article-sop | 有 | wechat-article-sop |

## 残留 .codex 路径

无残留：11 个副本已不含任何 `.codex/skills` 引用。
