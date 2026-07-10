---
name: wechat-article-sop
description: "wcsop 公众号文章生成→推送草稿完整SOP。从X/Twitter/YouTube/论文等生成高质量文章，含预发布检查清单。每次写公众号前必须严格执行本技能。"
version: 1.131.0
---

# 公众号文章生成 SOP

<details>
<summary><strong>📑 目录（点击展开）</strong></summary>

- [使用条件](#使用条件)
- [完整工作流](#完整工作流)
  - [再生模式](#再生模式regeneration已有文章的快速重做)
  - [编辑模式](#编辑模式quick-edit已有文章的定向修改)
  - [恢复模式](#恢复模式recovery从上次中断处继续)
  - [Step 0：确定存储位置](#step-0确定存储位置)
  - [Step 0a：更新 TASKS.md 任务追踪](#step-0a更新-tasksmd-任务追踪)
  - [Step 0b：判断语言类型](#step-0b判断语言类型翻译-vs-转写)
  - [Step 0c：确认来源类型](#step-0c确认来源类型)
  - [Step 1：提取原文内容](#step-1提取原文内容)
  - [Step 2：下载原文全部图片](#step-2下载原文全部图片)
  - [Step 3：生成封面](#step-3生成封面)
  - [排版全局规则](#排版全局规则所有文章必须遵守)
  - [Step 4：写文章](#step-4写文章--核心步骤必须拆解执行)
    - [4a. 列出关键素材](#4a-阅读原文列出关键素材清单)
    - [4a-i. 写要点速览](#4a-i-写要点速览)
    - [4b. 确定独立观点](#4b-确定独立观点)
    - [4c. 写正文](#4c-写正文)
    - [4c-iii. 机器之心排版格式](#4c-iii-机器之心排版格式用户参考标准)
    - [4d. 写结语](#4d-写结语章节文末独立段)
    - [4d-i. 写传送门（往期推荐）](#4d-i-写传送门往期推荐)
    - [4e. 写参考区](#4e-写参考区)
    - [Step 4f：去 AI 痕迹润色](#step-4f去-ai-痕迹润色humanize-zh)
    - [Step 4g：文本格式统一修复（两次）](#step-4g文本格式统一修复--30s)
  - [Step 5：预发布检查清单](#step-5预发布检查清单硬闸门)
  - [Step 6：推送草稿](#step-6推送草稿)
  - [Step 7：嵌入视频](#step-7可选嵌入视频到文章)
- [补充技巧](#补充技巧)
- [常见失败模式](#常见失败模式每次写之前读一遍)
- [参考文件索引](references/INDEX.md)

</details>

---

## Git 自动提交（基础设施）

`D:\\06_Hermes\\articles\\` 是一个 **git 仓库**，由后台守护进程 `article-watcher` 驱动自动 commit。

**机制：**
- 一个常驻 Python 守护进程（`article-watcher.py`）每 60s 扫描 `articles/` 目录
- 检测到任何文件变动（新建、修改、删除）→ `git add -A && git commit && git push`
- 相同 changeset 不会重复 commit（`.watcher.seen` 文件记录 hash 去重）
- **Windows 登录自动启动**（`startup` 文件夹中的 VBS 脚本→拉起 Python daemon）
- 日志：`D:\\06_Hermes\\articles\\.watcher.log`（自动轮转）

**commit message 格式：** `auto: <目录名> (+, ~, D 计数)`

**无需手动操作。** 每步写完内容 + 更新 progress.md 后，最长 60s 内自动 snapshot。`git log -- <article-dir>/` 可查看单篇文章历史。

**初始状态：** `.watcher.seen` 已将现存文章的历史 step 全部标记为「已处理」，不会重复提交旧数据。

### 架构变化（2026-07-04）

| 旧 | 新 |
|----|----|
| Hermes cron 每 1 分钟触发 | 独立 daemon `while True` 轮询 |
| 依赖 Hermes 进程存活 | Windows 启动独立拉起，与 Hermes 解耦 |
| 无代理硬编码（靠 Hermes env） | 脚本内硬编码 `HTTP_PROXY=http://127.0.0.1:7890` |

**⚠️ 关键 pitfall — 独立 daemon 必须硬编码代理：** 当脚本从 Hermes cron 迁移到 Windows 自启 daemon 时，**不能再依赖 Hermes 进程的代理环境变量**。`git push` 走网络，必须在 `git_cmd()` 中显式传入 `env={"HTTP_PROXY": "http://127.0.0.1:7890", ...}`。否则 daemon 启动后 git push 会在代理不可达时静默失败。

## 优化铁律（2026-07-06 用户强制）

**任何对 SKILL.md 的优化/新增/修改，必须先向用户提交方案，用户同意后才能实施。** 包括但不限于：
- 新增脚本或中间层封装
- 合并/删除现有步骤
- 修改推送参数（theme、color 等）
- 改变封面生成策略
- 任何可能影响发布行为的变更

不问不动。违反此规则=用户发火。

## 卡死预防（每次执行前读一遍）

**wcsop 流程在 deepseek-v4-flash 模型下最容易在 Step 4f（Humanizer subagent）卡死。** 以下规则必须遵守：

### 规则 1：Step 4f 永远不走 delegate_task subagent
delegate_task subagent 在 deepseek-v4-flash 下极容易不返回（2-5 分钟无响应），导致父 session 空等。**Step 4f 的默认路径是手动 humanize：** 加载 humanizer-zh skill → 用 `execute_code` 或 `terminal` 中直接读取文件并扫描 AI 模式 → 用 patch/write_file 修复。不走 `delegate_task`。

### 规则 2：每篇完整执行，不跳过中间步骤
不要并行启动多个 subagent。**每步完成后再开始下一步。** 用 `progress.md` 记录每个步骤的完成状态，session 中断后通过 `wcsop <directory>` 恢复。

### 规则 3：覆盖率修复走大段补丁
覆盖率检查 < 70% 时，不要逐句加。一次加一整段（100-500 字符），2-3 轮内解决。如果 >3 轮仍未达标，收紧 full_translation.md 长度而非膨胀 article.md。

### 规则 4：execute_code 中不要用 read_file 后 write_file 回写
`read_file(path)['content']` 返回带行号的 LINE_NUM|CONTENT 格式。绝不能直接 `write_file` 写回——会用行号前缀污染文件。如需在 execute_code 中读写文件，用原生 Python `open()` 直接读写。

### 规则 5：永远不等，永远不轮询
需要等待后台步骤时，不等。**直接做下一件独立的事。** 不写轮询循环。`ls .done` 最多查 1 次，之后当不存在处理。

### 规则 6：被截断后第一件事是恢复 todo
如果上一步的 tool call 被系统超限截断导致 todo 未更新，必须优先清理 todo 列表——这是用户看得见的状态。先走 `references/todo-recovery.md` 修复 todo，再继续工作。**在清理 todo 之前不做任何其他操作。**

---

## 使用条件

**触发词：** 生成微信公众号文章、推送公众号、公众号草稿、写公众号文章、wcsop

**触发机制：** `wcsop` **不是 Hermes slash command**（本技能 name 是 `wechat-article-sop`，slug 为 `/wechat-article-sop`）。你发的 `wcsop <url>` 是普通用户消息，模型从系统提示的 `<available_skills>` 列表（100+ 技能）中自行判断应加载哪个技能。相似描述技能（`paper-analysis-wechat`、`video-to-wechat-article`、`khazix-writer`、`wechat-official-account`）可能被误触发。

**初始化（推荐，解决误触发问题）：** 将 `wcsop` 注册为 Hermes quick_command，确保无论模型如何判断，`wcsop` 开头的消息都精确路由到本技能：
```bash
hermes config set quick_commands '{"wcsop": "wechat-article-sop"}'
```
执行后验证：发 `wcsop test` 应看到技能内容被注入。未配置时 `wcsop` 只是纯文本，模型可能在其他技能间误判。

**⚠️ quick_commands 的限制（Agent 桌面聊天模式不生效）：** `quick_commands alias` 只在 Hermes CLI（终端会话）和 Gateway（微信/Telegram 等）模式中生效。在 Hermes Desktop 聊天框（当前会话的 AI Agent 模式/run_agent.py）中，`wcsop` 仍作为普通消息直接发给 LLM，不经 slash 预处理。这意味着：
- 微信/Telegram 发 `wcsop URL` → ✅ 精确触发本技能
- Desktop 聊天框发 `wcsop URL` → ❌ 仍需 LLM 在 100+ 技能中自行匹配
- **完全兜底：** 在 SOUL.md 中加一句规则「当用户发 `wcsop` 开头时，必须先用 `skill_view(name='wechat-article-sop')`」，可为所有 Agent 模式 session 解决误触发

**快捷指令：** 用户可通过 `wcsop <url>` 或 `wcsop <directory>` 格式直接激活本流程——以 `wcsop` 开头后跟一个 URL（新建）或文章目录路径（编辑已有文章），自动按本 SOP 处理。无需写完整指令。**这是全自动化流水线：从提取内容到推送草稿，中间无任何用户确认环节。检查清单通过后直接执行 Step 6 推送，不问用户「要不要推」「准备好了吗」。**

**批量生成模式（多篇文章串行）：** 当用户要求同时生成多篇文章（如「为 #4 #6 #8 各生成 1 篇」），必须串行依次处理——一篇完整走完 Step 0→Step 6 后，再开始下一篇。不并行，不使用 `delegate_task` 分配给 subagent。

**⚠️ 串行模式的注意事项：**
1. 每篇文章的处理是独立的，但所有步骤在当前 session 中完成，不走 subagent
2. 串行意味着总耗时=单篇耗时×篇数，提前告知用户预计时间
3. 用户明确说「不要并行」或「串行执行」时，必须严格遵守

**todo 列表使用规则（强制，代码层）：**
- 使用 `todo` 工具追踪任务进度，**每个任务完成时必须立即标记为 `completed`**，推送完成后必须清理所有待办项
- **同步写入 progress.md**：每次通过 `todo` 更新状态后，必须同步将当前进度写入文章目录下的 `progress.md` 文件
- **⚠️ todo 同步铁律（违反必出 BUG）：每完成一个 Step，写 progress.md → 立即调用 todo → 才进入下一步。中间不能插入任何其他操作。** tool call 超限截断时 todo 停在"进行中"→用户看到任务没完成
- **代码层强制**：每步完成后必须执行 `python scripts/todo-enforce.py <dir> <step-id>` 写哨兵文件，然后下一个工具调用必须是 `todo`。哨兵文件存在时我不应做其他工作
- **恢复规则**：如果 session 被截断导致 todo 残留，下个 session 第一件事就是读 `references/todo-recovery.md` 清理 todo 列表

```
# 进度追踪 - <article-name>

| Step | 状态 |
|------|------|
| Step 0: 目录创建与TASKS.md | completed |
| Step 0a: 语言类型判断（中/英） | completed |
| Step 0b: 来源类型确认 | pending |
| Step 1: 内容提取（全文） | pending |
| Step 2: 全部图片下载 | pending |
| Step 3: 封面生成（900×383 + 500×500） | pending |
| Step 4a: 列出关键素材清单 | pending |
| Step 4a-i: 写要点速览 | pending |
| Step 4b: 确定独立观点 | pending |
| Step 4c: 写正文（含full_translation） | pending |
| Step 4d: 写结语 | pending |
| Step 4d-i: 写传送门（published_articles.json选4-8篇） | pending |
| Step 4e: 写参考区 | pending |
| Step 4f: Humanizer 润色 | pending |
| Step 4g: 文本格式修复 | pending |
| Step 5: 预发布检查 | pending |
| Step 6: 推送草稿 | pending |
```

**恢复规则：** 当 `wcsop <directory>` 收到的是目录路径（非 URL）时，先读取该目录下 `progress.md`，从标记为 `pending` 或 `in_progress` 的步骤继续执行，已完成的步骤跳过。

> **为什么这么细？** 过去因为 progress.md 只有 9 个顶层 Step，Step 4 一勾覆盖了 4a~4e 六个子步骤，导致传送门等子步骤被跳过。每个子步骤独立成行后，完成和遗漏一目了然。`create-article-dir.py` 在初始化时自动创建此模板。

**参考文件：** 全部参考文件索引见 `references/INDEX.md`。常用快速入口：

- **X Article CDP Chrome 提取** → `references/x-article-twitter-cli.md`
- **draft-sync（从服务器草稿同步）** → `scripts/draft-sync.py`
- **X Article Hero 封面图** → `references/x-article-cover-hero-extraction.md`
- **X 推文线程提取** → `references/x-self-reply-thread-extraction.md`
- **预发布检查脚本** → `scripts/preflight-check.py`
- **TASKS.md 管理** → `scripts/update-tasks.py`
- **通用图片下载器** → `scripts/download_images.py`
| **SVG 伪装 JPG** | → `references/svg-disguised-as-jpg.md` |
| **SVG 高清渲染** | → `references/svg-hd-rendering.md` |
  - 合并中英间距去空格 + 破折号替换(→：) + 图片完整性检查。支持 `--check` 预览模式
- **CHANGELOG** → `CHANGELOG.md`
- **目录一键初始化** → `scripts/create-article-dir.py`
- **模式检测（再生/恢复/新建）** → `scripts/detect-mode.py`
- **内容提取路径探测** → `scripts/check-fetch-path.py`
- **自审流程** → `references/skill-audit-workflow.md`
- **自动 Git 版本控制** → `references/article-git-watcher.md`
|- **CDP Chrome 提取脚本（推荐）** → `scripts/cdp-extract.py`
- **CDP 不可用时降级** → `references/source-fallback.md`
- **图片下载失败降级** → `references/image-download-fallback.md`

**操作结果报告规则：**
- 修改文件后报告结果时，必须明确说明：**改了什么文件、改动前的内容是什么、改动后的内容是什么**。禁止使用「已加到XXX」「已修复」「搞定了」等模糊说法替代具体 diff
- 即使是一次简单的改动，也要让用户能确切知道发生了什么变化

**必须加载的技能（执行前加载）：**
1. `skill_view(name='wechat-article-sop')` — 本技能

---

## 完整工作流

> **每步完成后序列：完成操作 → update-tasks.py progress → 调用 todo → 下一步。中间不能插入任何其他工具调用。违反此顺序 = todo 残留 BUG。**

### 再生模式（Regeneration）：已有文章的快速重做

**当用户要求对 TASKS.md 中已有完稿的文章（状态 ✅ 已推送）按新版 SOP 重新生成时，应当走

**编辑模式（Quick Edit）：已有文章的定向修改**

**当用户以 `wcsop <directory>`（目录路径而非 URL）发起时，表示要定向修改已存在的文章，不走全流程。** 编辑模式仅执行用户明确指定的操作，然后走缩减版检查清单后推送覆盖。

**操作范围（仅限用户指定的项目）：**\n- 修改标题（更新 TASKS.md 生成标题列）\n- 修改正文（润色、新增/删除段落）\n- 中英间距格式化（英文/数字与中文之间去空格）\n- humanizer-zh 去AI化（通过 delegate_task 隔离执行）\n- 封面替换\n- 其他用户指定的编辑\n\n#### 📛 Format-Only 子模式（最高危操作 — 先做预检查，再动手）\n\n⚠️ **预检查：在触碰任何文件之前，先用 draft/get 下载当前草稿查看图片数量和内容。**\n**操作前必须先回答以下问题：**\n1. 服务器草稿有多少张图？全是 `mmbiz.qpic.cn` CDN URL 吗？\n2. 图片内容是什么？是自己配的论文截图还是我上次推的官方图？\n3. 内容文字是否和我本地版本一致？\n\n**必须逐条回答后才能动手。** 这是防「图片弄丢了」的第一道防线。\n\n**当用户明确说「从服务器下载最新内容，只改格式不换图」时，必须走此子模式。绝不用 markdown 重建文章。**\n\n**核心原则：图片 URL 一条不动。** 用户在微信编辑器里手动配的图全部是 `mmbiz.qpic.cn` CDN URL，重新上传本地图片会覆盖这些 URL → 旧图丢失 → 用户发火。\n\n**精确流程：**\n\n1. **下载草稿 HTML** — `draft/get` API 获取完整 HTML\n2. **提取所有 `<img>` 标签** — 全量保留原 `src`，**不做任何替换**\n3. **只改 CSS 结构** — 要点速览卡片、结语卡片、引用块的 `<div>` 样式/wrapper\n4. **生成纯 HTML 文件**（不是 markdown）\n5. **推送 HTML 文件** — wechat-api.ts 的 HTML 模式自动跳过 `mmbiz.qpic.cn` 已有图片。**必须显式传入 `--title`、`--cover`、`--author`**，因为 HTML 文件无 frontmatter。\n6. **绝不跑 md-to-wechat** — 那会生成 placeholder → 重新上传 → 丢失旧图\n\n**验证：** 推送后 `draft/get` 检查图片数量 + URL 与下载前一致。结语只出现 1 次且有暖色卡背景。如果结语重复 > 1 次，先用 regex 删除所有旧卡片结构再重建。\n\n**⚠️ 创建新草稿，绝不覆盖。** 推送格式优化版时永远不传 `--draft-media-id`，走 `draft/add` 创建新草稿。用户手动编辑的原始草稿保留不动。推送后把新 media_id 告知用户。

**禁止操作：**\n- ❌ 用 markdown 重建文章（丢失 img → mmbiz 映射）\n- ❌ 跑 `md-to-wechat`（生成 WECHATIMGPH_× 占位符 → 重新上传 → 旧 URL 丢失）\n- ❌ 用备份的 `article.md` 中的 `![](...)` 图片引用替换 mmbiz 地址\n\n**💡 速度第一原则 — 封面替换等简单操作：**

对于仅替换封面的操作，**不要走完整编辑流程**（不查标题/不读源码/不翻历史）。直接：
1. `session_search("<目录名> push")` — 找到上次推送成功的完整命令
2. 复制那条命令，只改 `--cover` 参数为新封面文件路径
3. 直接跑

**不需要做的：**
- ❌ 查脚本路径（就在 baoyu-post-to-wechat/scripts/wechat-api.ts）
- ❌ 读脚本源码确认参数名（`--cover` `--draft-media-id` 已知）
- ❌ 翻历史找标题/作者（已成功过的命令里已有）
- ❌ 先试 `npx tsx` 再倒回 bun（必须用 `npx -y bun`）

**缩减版检查清单：**
- [ ] 标题是否已更新（TASKS.md）
- [ ] 用户指定的修改是否全部完成
- [ ] humanizer-zh 是否已执行（如果需要）
- [ ] 中英间距是否已格式化（如果需要）
- [ ] 开头的 `---` 是否已移除

**推送方式：** 覆盖推送（同一 media_id，走 draft-update + submit）

**触发条件：** 用户明确引用 TASKS.md 中的任务编号（如「#10 按 wechat-article-sop 重新生成」），且该任务状态为 ✅ 已推送。

#### 🔧 技术精简模式（用户高频要求：「侧重点在技术，文字精简，不要重复」）

当用户对已推送/已生成的文章提出「精简」「技术侧重点」「去重复」「文字太多」类要求时，按此变体重写，不走全文重建：

**重写铁律：**
- **技术优先，删掉叙事铺垫。** 背景/动机段只留 1-2 句点出「原文解决了什么断层」，不展开故事线。把篇幅让给方法细节、实验数字、消融结论。
- **去重复是硬指标。** 同一条信息只能出现一次。常见重复源：① 背景段结尾的设问（"能不能直接利用ICL…"）与第2段重复 → 只留一处；② 结语第1条与背景/方法段重复（"借力ICL""不另起炉灶"类）→ 删结语重复条，结语只留原文没有的独立观点；③ 摘要/TLDR 与要点速览重复 → 合并。
- **短章节并入相邻章。** 原文独立的「实验设置」「配置说明」等 1-2 行短节，并入「结果」章首段，不单独成节（除非它有独立图片）。
- **偏题内容压缩。** 玩具任务/定性演示（如 ARC 颜色映射）从 3 段压到 1 段，只留技术结论（迭代0=ICL → 逐步收敛），不展开剧情。
- **保留：** 9 图一张不能少（精简不删图）；核心数字（44.2% vs 43.3%、75% 标签损坏、训练时间一半）必须留；章节标题 `##` 结构保留。
- **覆盖率：** 精简后正文允许降到 70% 附近（技术压缩，非内容缺失）。preflight 覆盖率 ≥ 70% 即通过；若略低于 70% 但章节齐全、无内容丢失，按「用户明确要求精简」标注跳过。

**触发时机补充：** 用户不仅在「修改已有文章」时提精简，也会在**新建文章**时直接要求「简练、直奔主题、核心突出、文字精简」。此时**初稿即按技术精简风格写**，不要先写全量翻译版再事后压缩——一步到位效率更高，也避免压缩时丢图/丢章节。初稿精简同样遵守：N图一张不能少、章节 `##` 结构对齐原文、要点速览+结语卡片齐全、核心数字保留。覆盖率允许降到 45%~70%（跨语言翻译阈值），按「用户明确要求精简」标注跳过。

**流程：** 直接重写 `article.md` → `cp article.md article_human.md` → `text-format.py` → 引用块/独立加粗修正（独立行 `**加粗**` 改 HTML 引用 `<div>` 或自然段落）→ preflight → 覆盖推送（`--draft-media-id "$(cat draft.id)"`）。

**验证：** 推送前 `diff article.md.bak article.md` 确认无图片/章节丢失，仅文字压缩与去重。

#### 📄 论文来源精简模式（新建 + 修改均适用）

当来源是 arXiv 论文（Step 0c 判断为「arXiv 论文」）时，无论新建还是修改，正文一律按此模式写：**技术优先、叙述克制、实验压缩**。

**核心原则：**
- **简洁直接，不绕弯。** 第一句就是核心贡献/结论。背景段只留 1-2 句点出「解决什么断层」，不讲故事线、不铺垫动机、不设问引出。
- **同样的意思不重复。** 背景段设问、摘要 TLDR、要点速览、结语之间，同一条信息只出现一次。常见重复源：① 摘要与要点速览重复 → 合并；② 背景设问与方法段重复 → 只留一处；③ 结语第 1 条与背景/方法重复 → 删结语重复条，结语只留原文没有的独立观点。
- **技术原理重点讲。** 方法、机制、架构、公式、算法细节详写，给足篇幅。这是论文类文章的主体，不能压缩。
- **实验过程简化。** 实验设置、训练配置、数据预处理等过程性描述压到最短（并入方法章或结果章首段，不单独成节）；**核心结果数字（SOTA 对比、提升点数、消融结论）必须保留**；玩具/定性演示从多段压到 1 段，只留技术结论。

**保留项（不因精简而丢）：**
- 论文图片：主架构图（Figure 1）必须嵌入正文；核心实验结果图、关键机制图保留 3-6 张，附录补充图可省略
- 章节 `##` 结构对齐原文
- 要点速览 + 结语卡片齐全
- 论文标题/链接 `·` 制表符格式（见 4c-iii）

**覆盖率：** 论文精简后允许降到 45%~70%（跨语言翻译 + 技术压缩），按「原文为论文且明确要求精简」标注跳过。

**再生模式流程（速度优先，用户不耐等候）：**

| 跳过 | 原因 |
|------|------|
| Step 0 （新建目录） | 目录已存在 |
| Step 1 （提取原文） | 原文内容已提取在 `full_text.txt` 或已有 `article.md` |
| Step 2 （下载图片） | ⚠️ **不能直接跳过。必须先用 CDP Chrome 重新打开原文，确认图片列表与已有文件一致**。原文可能新增或更换了图片，老文件可能不全 |
| Step 3 （生成封面） | 封面文件已存在 |

| 执行 | 优先级 |
|------|--------|
| Step 4a — 重建 `full_translation.md` | 获取近期 `article.md` 正文纯文本（去 HTML 标签）作为完整翻译基线 |
| Step 4c — 逐章结构对齐 + 更新正文 | **必须先做结构对齐：** 列出 full_translation.md 的所有章节 → 对比当前 article.md 的章节结构 → 找出缺少/合并的章节 → 补写后再做其他正文修改 |
| Step 4c+4f — 更新正文 + 快速 humanize | 结构对齐后更新正文内容；humanize 走「快速 humanize」路径：先 diff article.md vs article_human.md 确认文章原来的干净度，只扫高频模式（破折号、AI 词汇）修复，不重复做完整 humanize |
| Step 5 — 覆盖率检查 | 自动跑 `preflight-check.py`，用文章正文为 baseline |
| Step 6 — 推送 | `--draft-media-id "$(cat draft.id)"` 覆盖推送 |

**⚠️ 注意：再生模式不需要重新提交给用户审查。** 所有额外步骤（图片→章节映射再确认、原文对比检查等）在首次发布时已完成。再生模式的目的是让文章匹配最新 SOP，不是重新翻译。**用户对 Step 0 过久的容忍度很低。** 收到再生指令后，5 秒内确认目录存在，直接跳到步骤执行。

**⚠️ 再生模式陷阱：收到 wcsop URL 后先查 TASKS.md 再建目录。** 不要一收到 `wcsop <URL>` 就立刻 `mkdir -p`。先运行 `detect-mode.py` 判断模式，或手动查 TASKS.md。如果已有 ✅ 已推送记录，直接跳到再生模式。判断方法：

**⚠️ 再生模式陷阱：`article_human.md` 已存在 ≠ humanize 已完成。** 再生模式下，已有的 `article_human.md` 是上一次推送时的产物。当前 SOP 可能有新规则（如新 AI 模式识别、新排版要求），**必须重新执行 humanize-zh**。即使 `article_human.md` 存在，也必须走 Step 4f 手动 humanize 流程（见 `references/manual-humanize-workflow.md`），然后审查 diff 确认改动合理 → 推送。

### 恢复模式（Recovery）：从上次中断处继续

**当 wcsop 流程在前一次 session 中因超时/崩溃/卡死中断，但目录已创建、大部分文件已存在时，走恢复模式。** 用户的表现是重新发相同 URL 时说「卡死了」「执行到 XX 步停了」。

**恢复模式不是再生模式。两者的区别：**

| 维度 | 再生模式 | 恢复模式 |
|------|----------|----------|
| 触发条件 | 用户要求对 ✅ 已推送的文章按新版 SOP 重做 | 用户说流程卡死了/中断了，目录已有文件但从未推送过 |
| TASKS.md 状态 | ✅ 已推送 | 📥 进行中 或 其他非 ✅ 状态 |
| article_human.md | 上一次推送的产物，**必须重新 humanize** | 可能包含上一次 subagent 完成但 session 中断的润色结果 |
| 目标 | 匹配最新 SOP | 延续未完成的工作到推送完成 |

**恢复模式流程（速度优先，不做多余操作）：**

1. **查目录完整性**：`ls` 确认 `article.md`、`full_translation.md`、图片文件、`cover.png` 都存在
2. **查 humanize 状态**：
   - `article_human.md` 存在 → 用 `diff article.md article_human.md` 检查差异
   - 有实质性差异（>5 处改动）→ humanize 已完成，**不需要重新执行 humanize**
   - 无差异或只有 1-2 处 → 前一次 humanize 没跑完，走标准 humanize 流程（Step 4f）
3. **修复 humanizer 引入的格式问题**（已知高频问题）：
   - **破折号被重新引入**：扫描 `grep -cP '——|—' article_human.md`，humanizer 经常将中文冒号 `：` 误改为破折号 `——`。每处逐一修复为 `：`（引出解释/说明）或 `，`（分隔）
   - **重复/误插图片**：扫描 `grep -oP '!\[\w*\]\(\w+\.\w+\)' article_human.md | sort | uniq -d`，检查是否有同一图片名被复制到了错误章节（如 img19 同时出现在 Engram 和 MoE 两个章节）。发现重复后，对比 article.md 中该图片的原始位置，删除 article_human.md 中多余的那一行
4. **记录 humanize 改动总结**：给用户改了什么/没改什么的对比报告
5. **执行 Step 5 检查清单**（破折号、开头、图片、参考区等）
6. **执行 Step 6 推送**
7. 更新 TASKS.md 状态历史追加完成行

**⚠️ 注意：** 恢复模式下 humanize 不重新执行的前提是 diff 确认差异合理且包含实质性改动（>5 处 AI 模式修复）。如果 diff 显示 humanizer 只改了 1-2 个词或根本没改动，说明 subagent 并未完成工作，必须重新执行 humanize。

### Step 0：确定存储位置 ⏱ 1min

每次写文章前，在 `D:\06_Hermes\articles\` 下创建一个独立文件夹，命名规则为 `文章英文简称（短横线连接）`。所有内容存放在此：
- 下载的原文图片 → `D:\06_Hermes\articles\<article-name>\`
- 文章 markdown → `D:\06_Hermes\articles\<article-name>\article.md`
- 封面 → `D:\06_Hermes\articles\<article-name>\cover.png` / `cover-square.png`
- wechat-api.ts 发布命令时 `cd` 到这个目录
- **原始来源链接** → `D:\06_Hermes\articles\<article-name>\source.url`（仅一行，即原始 URL，如 `https://x.com/user/status/123`）。方便后续通过子目录名重新修改文章时快速获取原文。

**视频来源的额外规则：** 视频文件统一存到 `D:\\06_Hermes\\video\\<video-name>\\`，不在 articles 目录下。视频下载选 720P 控制文件大小。

**⚠️ 路径确认陷阱：** `mkdir -p` 之前先检查是否真的用了 `D:\\06_Hermes\\articles\\` 路径，不要直接用 `C:\\Users\\...` 或其他路径创建。SOP 明确指定了 D 盘路径，但容易在快速操作时误用默认工作目录。创建后立刻 `ls` 确认目录在正确位置。

```bash
# 一键初始化（建目录 + 写 source.url + progress.md + 语言检测 + TASKS.md）
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/create-article-dir.py" \
  "<原始URL>" --auto-lang [--name "<article-name>"]
```

**更新 progress.md：**（脚本自动完成，无需手动调用）

### Step 0a：更新 TASKS.md 任务追踪 ⏱ 1min

**每次 wcsop 流程开始后，必须在 `D:\06_Hermes\articles\TASKS.md` 中创建或更新任务记录。**

TASKS.md 是全局任务追踪文件，记录所有公众号文章的生成状态，格式如下：

参考 `D:\06_Hermes\articles\TASKS.md` 现有文件格式。

**状态 Emoji 约定：**

| 📥 | 开始 | 📝 | 写作中 | 🎨 | 封面中 | ⏳ | 推送中 |
| ✅ | 完成 | 🔄 | 修改中 | ❌ | 失败 | ⏸️ | 暂停 |

用 `"$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/update-tasks.py"` 操作（保留所有历史状态不覆盖），需从 `D:\06_Hermes\articles\` 目录下执行（脚本内部相对路径解析该目录下的 TASKS.md）：
```bash
cd "D:\06_Hermes\articles"
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/update-tasks.py" add-task "<URL>" "<title>" "<dir>"
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/update-tasks.py" status "<dir>" "<emoji>" "<desc>"
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/update-tasks.py" complete "<dir>" "<title>" "<cover>" "<media_id>"
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/update-tasks.py" modify "<dir>" "<emoji>" "<desc>"
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/update-tasks.py" regenerate "<dir>" "<emoji>" "<desc>"
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/update-tasks.py" regenerate-complete "<dir>" "<title>" "<cover>" "<desc>"
```

**注意：** TASKS.md 中不要覆盖已有状态行。每个状态变化追加新行，保留完整时间线供回溯。**文章修改后（如改标题、换封面等），也要追加状态行标注 🔄 + ✅。**

**⚠️ update-tasks.py 大文件 timeout / 写入失败（最高危数据损坏）：** TASKS.md 超过 500KB（约 600+ 行）时，`update-tasks.py` 脚本读写整个文件可能超时（30s+）。更严重的是：如果文件因重复行膨胀到数百 MB（`OSError: [Errno 22]`），**不要尝试修复受损文件**——走 `references/tasks-md-corruption-recovery.md` 直接从尾部提取有效历史段并完整重建。平时改用 `patch` 工具在文件末尾追加新行——以最后一条 `###` 标题为锚点，在其前插入新行。注意：patch 的 old_string 需要唯一且包含足够上下文行。失败时先 `read_file offset=640+` 确认文件末尾精确内容。

更新 progress.md：由脚本自动完成（无需手动调用）

### Step 0b：判断语言类型（翻译 vs 转写）⏱ 30s

**关键决策：原文是中文还是英文？**

- **英文来源** → 走完整翻译流程：**逐句对照原文，一字不动**、保真度 ≥70%、英文术语翻译规则、Agent/memory 等核心概念保留英文
- **中文来源** → 走转写/重排版流程：无需翻译，保真度检查针对「内容完整性」而非「翻译准确性」，重点在 WeChat 格式适配（加粗、要点速览、结语、参考区）

**中文来源文章的规则差异：**
- 跳过所有翻译相关规则（英文段落翻译、术语翻译、memory/Agent 翻译规则）
- 保真度检查改为「原文内容是否全部保留」，不涉及「逐句对照翻译」
- 「不堆英文引文」规则不适用（原文就是中文）
- 「不编号分段」规则不适用——如果原文本身使用中文编号（如「案例一」「方法二」「3. 实现」），保留原文的编号结构，不要强行改为自然段落
- 「开头不写未编号的引言段」规则不适用——如果原文在第一节之前有引言段落，保留该段落
- 要点速览、结语、参考区、加粗规则、封面规则**全部照常执行**
- 如果原文包含英文术语/引文（如 Crescendo、Morris II 等专有名词），保留原文英文写法，不加翻译
- 如果原文引用了英文推文/评论，保留原文中的中文翻译版本（原文作者已翻译过的），不要重新翻译

更新 progress.md：由脚本自动完成（无需手动调用）

### Step 0c：确认来源类型 ⏱ 30s

**默认路径：CDP Chrome 优先。** 对任何网页来源，先用 CDP Chrome 打开页面 → 提取正文文本 + 所有图片 URL。CDP 不可用时退回到 `references/source-fallback.md` 中的降级方案。

| 来源 | 默认方式（CDP Chrome） | 降级路径 |
|------|----------------------|----------|
| **X Article 长文** | CDP Chrome 打开 x.com/i/article/<ID> → Runtime.evaluate 提取 img[src*=pbs.twimg.com/media/] + Hero 封面图。⚠️ 先检查 tab 登录态：curl http://localhost:9222/json 的 title 字段必须含 X 上的 @user（🟢）。title 仅为 URL 路径的 tab（🔴）无登录态。用 🟢 tab 通过 Target.createTarget 新建 tab。详见 references/cdp-manual-extract.md | references/x-article-twitter-cli.md + references/cdp-manual-extract.md |
| **X 普通推文** | CDP Chrome 提取推文正文 + img[src*="pbs.twimg.com/media/"] | references/x-tweet-browser-extraction.md |
| **X 推文回复串（self-reply thread）** | CDP Chrome 打开主推文 URL → 慢速 scroll 加载完整 thread → DOM 遍历 article 元素提取每条自回复的文本和图片 → 按 author 筛选目标账号 | references/x-self-reply-thread-extraction.md |
| **YouTube 视频** | yt-dlp --write-auto-sub 字幕 + 帧提取（不走 CDP） | references/youtube-keyframe-blogger.md |
| **arXiv 论文** | CDP Chrome 打开 `arxiv.org/html/<paperID>` | `references/arxiv-pdf-fallback.md`（含 CDP 不可用时 HTML 图片提取降级）→ 写文走 `📄 论文来源精简模式`（技术优先、实验压缩） |\n| **arXiv 论文（TeX Source）** | 用户给 `arxiv.org/src/<id>` 或 `e-print/<id>` 时走源码路径：下载 tarball → 读 `sections/*.tex` 章节 → `figures/*.pdf` 用 pymupdf 栅格化为 PNG。详见 `references/arxiv-tex-source-extraction.md` | 同 HTML 路径的精简模式规则；不走 CDP、不跑 cdp-extract.py 的图片下载脚本、不依赖代理 |
| **微信公众号** | 直接 curl 下载 HTML（不用 CDP） | `references/wechat-article-extraction.md` |
| **Cloudflare 站点** | CDP Chrome 自动过 CF 验证 | `references/cloudflare-site-extraction.md` |
| **其他网页/博客** | CDP Chrome 打开 → 提取正文 + 所有图片 URL → 如果 `img` 提取为 0，检查 `document.querySelectorAll('svg')` | `references/source-fallback.md` |\n| **SVG 内嵌博客**（NVIDIA Research/技术博客） | **先分情况：** 内联 `<svg>` → CDP `getBoundingClientRect()` + `Page.captureScreenshot` clip + `deviceScaleFactor:2` 逐张截图；`<img src=\".svg\">` → 下载 SVG 源码后用 Playwright 内联渲染并截图（CDP clip 原理上不可行）。详见 `references/svg-blog-extraction.md` | `references/svg-blog-extraction.md` |

更新 progress.md：由脚本自动完成（无需手动调用）

### Step 1：提取原文内容 ⏱ 1-5min

**默认路径：CDP Chrome 优先。** 对绝大多数网页来源，CDP Chrome 同时提取正文文本和全部图片。不需要为每种来源写不同的提取脚本。

#### 通用 CDP Chrome 提取流程

```bash
# 通过 CDP Chrome 提取页面正文 + 所有图片
# 前置条件：Chrome 已在 9222 端口开启 CDP
# 脚本会自动打开新标签页、等页面渲染、滚动触发懒加载、提取正文和图片
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/cdp-extract.py" \
  "<目标URL>" \
  "D:\\\\06_Hermes\\\\articles\\\\<article-dir>"
```

输出包含：
- 所有图片 URL（按 Hero/BODY 分类，宽高比 >= 2.0 的为 HERO 封面候选）
- 页面正文纯文本（已保存到 `full_text.txt`）
- 自动生成图片下载脚本 `_download_images.py`（在 article-dir 下）
- 图片列表 `image_list.txt`

**对 X.com 推文的特殊处理：** 脚本会优先复用 Chrome 中已有的 X 已登录标签页，保证登录态 cookie 继承。新建标签页后等待页面渲染（最长 20 秒），然后直接取所有 `img[src*="pbs.twimg.com"]` 的 `src` 属性——不依赖 `naturalWidth`、`complete` 等加载状态，DOM 中有就是有。

**⚠️ X.com 图片提取铁律：不过滤 naturalWidth/complete。** X.com 的图片是 React 懒加载的，`naturalWidth` 和 `complete` 不可靠（懒加载图片这两个字段可能为 0/false）。必须直接匹配 `img[src*="pbs.twimg.com"]`（排除 `profile_images`）。 `cdp-extract.py` 已按此规则实现，不要修改提取逻辑。如果提取结果为 0 张图，先确认是否有登录态（`document.title` 是否包含用户名/文章标题），而非加回 `naturalWidth > 0` 过滤。

**⚠️ X 自动翻译陷阱（英文来源文章高频坑，cdp-extract.py 默认踩）：** 对非中文推文，`cdp-extract.py` 抓取的正文默认是 X 的**机翻中文**（页面顶部带「翻译自 英语」按钮、正文里有「显示原文」）。如果本次任务是**英文→中文翻译**（Step 0b 判为英文来源、`full_translation.md` 必须逐句对照英文原文），**绝不能把机翻中文当原文 baseline**——否则覆盖率检查会变成「中文比中文」，且 translator 自己重构的中文会污染 baseline。正确做法：在 CDP 已打开的标签页上点击「显示原文」按钮（按钮文本 `显示原文` / `Show original`，通常是 `<span>` 或 `<button>`）切回英文，再重新 `Runtime.evaluate` 抓 `article.innerText`。判断是否被翻译：在提取文本里搜「翻译自」或「Translated from」，命中即说明抓到了翻译版，必须先点「显示原文」再抓。完整 CDP 点击脚本见 `references/x-tweet-browser-extraction.md` 的「X 自动翻译陷阱」章节。

#### 特殊情况处理

| 来源 | 特殊说明 |
|------|----------|
| **X Article 长文** | 用 `twitter tweet TWEET_ID --json` 的 `urls[0]` 提取 Article ID，打开 `x.com/i/article/<ID>` |
| **X 普通推文** | CDP 直接打开推文 URL 即可 |
| **YouTube 视频** | 不走 CDP，用 yt-dlp 下载字幕（`video-to-wechat-article` 技能） |
| **arXiv 论文** | CDP 打开 `arxiv.org/html/<paperID>`，提取图片 URL + 正文 |
| **微信公众号** | 直接 curl 下载 HTML（微信无 CDP 环境），见 `references/wechat-article-extraction.md` |\n| **Cloudflare 站点** | CDP Chrome 自动过 Cloudflare 验证，不需额外步骤 |\n| **SVG 内嵌博客**（NVIDIA Research / 技术博客） | **先分情况：** 内联 `<svg>` → CDP `getBoundingClientRect()` + `Page.captureScreenshot` clip + `deviceScaleFactor:2` 逐张截图；`<img src=\".svg\">` → 下载 SVG 源码后用 Playwright 内联渲染并截图（CDP clip 原理上不可行）。详见 `references/svg-blog-extraction.md` |

#### 区分 Hero 封面图和正文图

CDP 提取的图片列表中：
- **HERO**（宽高比 >= 2.0）：通常是页面顶部的封面/hero 图，直接拉伸到 900x383 做 cover.png
- **BODY**（宽高比 < 2.0）：正文内嵌图片，按 DOM 顺序下载并嵌入对应段落

**⚡ X 推文封面铁律：永远从 X 推文 URL 本身的 pbs.twimg.com/media/ 图片中取 Hero 图做封面，不要去外部搜索。** X 推文/Article 自带的 Hero 封面图就是最佳封面，直接用。只有纯文本推文（图片提取为 0 张且确认页面确实无图）时才走外部来源搜索。

⚠️ **关键：用 CDP 返回的完整 URL 原样下载，不要追加或修改任何参数。**
CDP `Runtime.evaluate` 返回的 `img.src` 已包含完整的 format 和 size 参数（如 `?format=jpg&name=900x900`）。直接使用这个完整 URL 下载。
`?name=orig` / `?name=large` 对 pbs.twimg.com 不一定存在，擅自追加会导致 404。**经实测验证：**
- `?name=orig` → 可能 404
- `?name=large` → 可能 404
- CDP 返回的原始 URL → 正常下载

封面 Hero 图用下载后的文件直接拉伸：
```bash
python -c "
from PIL import Image
img = Image.open('hero_image.jpg').convert('RGB')
img.resize((900, 383), Image.LANCZOS).save('cover.png')
img.resize((500, 500), Image.LANCZOS).save('cover-square.png')
"
```

#### CDP 不可用时

如果 CDP Chrome 不可用（端口不通、用户没有 Chrome），走 `references/source-fallback.md` 查看降级方案。

**⚠️ 如果 `cdp-extract.py` 报错：** 脚本会优先从已有的 X 已登录 tab 连接（title 含用户名）。如果找不到已登录 tab，脚本会自动用 `Target.createTarget` 新建标签页。新标签页继承浏览器上下文（含 cookie），等待渲染 + 滚动触发懒加载后提取。

**关键原则：**
- CDP 提取的图片中宽高比 >= 2.0 的为 Hero 封面图，直接拉伸即可
- 正文图按 DOM 出现的顺序嵌入文章，一张不能少
- `twitter tweet --json` 返回 `media: []` **不代表原文无图**——图片在渲染 DOM 的 `<img>` 标签中
- 不要在没有 CDP 确认的情况下判定文章为「纯文本」

更新 progress.md：由脚本自动完成（无需手动调用）

### Step 2：下载原文全部图片 ⏱ 2-5min

**原文图片一张不能少。** 从 CDP Chrome 提取的图片列表中全部下载，按 DOM 顺序嵌入对应章节。

`cdp-extract.py` 会在 article 目录下自动生成 `_download_images.py` 下载脚本，直接运行即可：

```bash
# 从 cdp-extract.py 自动生成的下载脚本
cd "D:/06_Hermes/articles/<article-dir>"
python _download_images.py
```

也支持通用下载脚本：
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/download_images.py" \
  "D:\06_Hermes\articles\<article-dir>" --from-md article.md --parallel 4

# 或手动从 CDP 提取结果下载：
python -c "
import urllib.request, os
urls = {
    'img1_hero.jpg': 'CDP_RETURNED_HERO_URL',
    'img2_body.jpg': 'CDP_RETURNED_BODY_URL',
}
for fname, url in urls.items():
    # Use the exact CDP-returned URL, do not append ?name=orig
    with urllib.request.urlopen(req, timeout=30) as r:
        with open(fname, 'wb') as f:
            f.write(r.read())
    print(f'OK {fname} ({os.path.getsize(fname)//1024}KB)')
print('All images downloaded')
"
```

**铁律：** 图片按 CDP 提取的 DOM 顺序嵌入正文，一张不能少。CDP 确认 DOM 中无 pbs.twimg 图片，才是真正纯文本文章。

**纯文本文章处理流程：** 当 CDP Chrome 确认正文中无 pbs.twimg/media/ 图片（仅 1 张 Hero 封面图），即为纯文本文章。此时：
- Step 2 的「图片一张不能少」规则转换为「确认确实无正文图片」，而不是「缺图需要补」— 不需要惊慌
- Step 4a 的图片清单明确标注「0 张正文图片」
- Step 5 preflight 的图片完整性检查会输出「正文引用 0 张，目录文件 1 个」— 这是正确结果，不是失败
- 常见于：X 原生长文推文（long-form tweet）、纯技术博客、个人叙事类内容

**⚠️ SVG 图片下载规则（根据文件后缀分流）：**

CDP 提取的图片列表包含 `.svg` 后缀文件时，**Clip 截图方案从原理上不可行**——Chrome 安全策略不允许 `Page.captureScreenshot` 读取 `<img src="external.svg">` 的渲染像素，结果必为全白。

在 Step 1 的 CDP 提取阶段应根据 `src` 扩展名分流：

```
CDP 提取图片列表
  ├─ .jpg/.jpeg/.png/.gif/.webp  → curl 直接下载源文件 ✅
  └─ .svg  → 必须走 Playwright 内联 SVG 渲染路径：
       1. 下载 SVG 源码（curl）
       2. 用 Playwright 创建页面，将 SVG 内联到 HTML DOM 中
       3. `page.screenshot()` 截取渲染结果
       4. 用 PIL 验证非全白（<5% 白色像素则告警）
```

**判断依据：** 文件后缀 `.svg` + 引入方式为 `<img>` 标签（而非内联 `<svg>` 元素）。内联 `<svg>` 元素走 CDP clip 截图（情况 A），`<img src="...svg">` 走 Playwright 内联渲染（情况 B）。完整流程见 `references/svg-blog-extraction.md` 的「情况 B」章节。

**Playwright 高清渲染代码模板：** 必须用 scale 放大容器（scale=3 将 300px 宽的典型 SVG 放大到 900px），详见 `references/svg-hd-rendering.md` 的完整指南。
```python
import asyncio
from playwright.async_api import async_playwright

async def render_svg(svg_file: str, png_file: str, scale: int = 3):
    """
    scale: 放大系数。默认 3。对 naturalWidth=300px 的 SVG，容器设为 900px 宽。
    输出 PNG 约 940px 宽，适合公众号配图。
    """
    w, h = 300 * scale, 105 * scale  # 根据 SVG 原始 naturalWidth 调整基值
    with open(svg_file, 'r', encoding='utf-8') as f:
        svg_content = f.read()
    html = f'''<!DOCTYPE html>
<html><body style="margin:0;background:white;">
<div style="width:{w}px;height:{h}px;">{svg_content}</div>
</body></html>'''
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.set_content(html, wait_until='networkidle')
        await page.set_viewport_size({'width': w + 40, 'height': h + 40})
        await asyncio.sleep(0.5)
        await page.screenshot(path=png_file, full_page=True)
        await browser.close()
```

**⚠️ CDP URL 下载铁律：用 CDP 返回的原 URL，不要追加任何参数。**
CDP 返回的 URL 已包含正确的 format 和 size 参数（如 `?format=jpg&name=900x900`）。
`?name=orig` / `?name=large` 对 pbs.twimg 不一定存在，擅自追加会导致 404。
直接用 CDP 返回的完整 URL 原样下载，不修改任何参数。

**下载失败 / 降级场景？** → 见 `references/image-download-fallback.md`

**⚠️ CDP 提取返回空 URL 图片（常见）：** 非内容元素（导航/banner/侧栏图标）的 `src` 为空，下载报 `FAIL ... unknown url type: ''`。直接丢弃该图，剩余图片顺序重命名为 img1..imgN 连续嵌入。详见 `references/cdp-empty-url-image.md`。

更新 progress.md：由脚本自动完成（无需手动调用）

### Step 3：生成封面 ⏱ 2-5min

**封面是文章的第一印象。封面难看的文章，用户不会点开。** 本章记载了生成微信公号封面的完整指引，分四种场景处理。开始前先加载完整参考：

**⚠️ 封面质量铁律：文字渐变封面被用户批评为"太low了"。** 禁止使用纯文字渐变封面。必须搜索与文章主题相关的真实照片/截图做封面基底——如 keynote 现场照、产品图、人物高清照。从 Microsoft Build 官方新闻页、Getty Images 等来源下载高清照片，叠加深色渐变+文字。

**用户提供封面图时：** 用户可能在推送后发来一张自定义封面图（如 `img1 - 副本.jpg`），要求替换封面。此时直接复制该图到文章目录，用 ffmpeg 拉伸生成 cover.png + cover-square.png，然后通过 `--draft-media-id "$(cat draft.id)"` 覆盖草稿。**不要问用户要不要替换——直接执行。**

```bash
cd "D:\\06_Hermes\\articles\\<article-dir>"
cp "来源路径" source-cover.jpg
ffmpeg -y -i source-cover.jpg -vf "scale=900:383,format=yuv420p" -update 1 cover.png
ffmpeg -y -i source-cover.jpg -vf "scale=500:500,format=yuv420p" -update 1 cover-square.png
```

```
skill_view(name='wechat-article-sop', file_path='references/cover-design.md')
```

#### 3a. 选择封面来源（按优先级）

**铁律：永远优先检查原文是否有可用封面图，只有原文完全无图时才用程序化封面。** 用户反复纠正过这一点。

| 优先级 | 来源 | 适用场景 | 方法 |
|--------|------|----------|------|
| 0 | arXiv HTML x0.png | arXiv 论文 teaser/head 图，比正文图更宽扁，最接近封面比例 | 直接 resize 到 900×383（拉伸）|
|| 1 | **X Article Hero 封面图** | CDP Chrome 提取的图片中宽高比 >= 2.0 的第 1 张 | 用 CDP 返回 URL 原样下载 → 直接 resize 到 900×383（拉伸）|
| 2 | X/Twitter 推文媒体图 | CDP Chrome 提取的 pbs.twimg.com/media/ 图片（不含 Hero 图） | 用 `name=orig` 下载 |
| 3 | **正文核心架构图/机制图** | **技术文章（模型发布、架构解读）优先选架构图/机制图**，它们比基准测试图表更有视觉吸引力。用户偏好：IndexShare 架构图 > 基准测试对比图 | 宽高比 ≥ 2.0 时直接拉伸；< 2.0 时 letterbox（模糊背景 + 居中等比叠加，用 PIL GaussianBlur radius=15）|
| 4 | 正文核心彩色图（非架构图） | 图表/对比图内容丰富、色彩饱满 | 直接 resize 到 900×383（拉伸）|
| 5 | **知名人物官方现场照** | 作者是知名公众人物（CEO、行业领袖、名人），原文无配图或配图质量低。从官方新闻页/媒体库搜索高清现场照 | 下载高清照 → ffmpeg 直接拉伸到封面尺寸 |
| 6 | **Gemini 生成（CDP Chrome）** | `image_generate` 不可用（FAL 余额耗尽）且原文无可用封面图 | CDP Chrome → gemini.google.com → 输入 prompt → 截图生成的图片 → ffmpeg 拉伸（详见 references/gemini-cover-generation.md）|
| 7 | **ffmpeg drawtext 文字封面** | 原文完全无图时的兜底方案。用 ffmpeg drawtext 生成深色背景+文字的封面 | ffmpeg drawtext 生成（详见 references/cover-design.md） |
| 8 | 纯文字渐变封面 | 最后兜底，已被用户批评过"太low" | 深色渐变+标题 |

**⚠️ 知名人物封面来源搜索方法：** 当文章作者是 Satya Nadella、Jensen Huang、Sam Altman、Demis Hassabis 等知名公众人物时，不要用纯文字渐变封面。搜索官方新闻页（news.microsoft.com、openai.com/blog、gettyimages 等）获取高清现场照。用 CDP Chrome 打开官方新闻页，提取所有大图 URL（筛选 >1000px 宽度的图片），下载后直接 ffmpeg 拉伸到封面尺寸。

名人封面模板参考 `references/cover-design.md`（含封面拉伸规则）。

**X/Twitter Hero 封面图提取：** CDP Chrome 提取的图片列表中，宽高比 >= 2.0 的第 1 张即为 Hero 封面图。用 CDP 返回的 URL 原样下载，不要追加 `?name=orig`。直接 resize 到 900×383（拉伸），不需 letterbox。

CDP Chrome 排障（进程残留 / origin 403 / 代理直连失败）见 `references/cdp-chrome-proxy-troubleshooting.md` 和 `references/cdp-websocket-origin-403.md`（Chrome 126+ WebSocket 403）。**⚠️ 用用户真实 profile：** `--user-data-dir="C:/Users/<user>/AppData/Local/Google/Chrome/User Data"`，不要单独建 `chrome_debug_profile`。见 `references/gemini-cover-generation.md` 的「启动 CDP Chrome」章节。

**⚠️ 全链路失败封面兜底：** CDP Chrome 提取的图片中选取 → ffmpeg 拉伸。

**⚠️ arXiv 论文架构图封面 padding 背景色陷阱：** arXiv 论文的架构图/流程图通常是深色背景（纯黑 `#000000` 或深灰），需要 padding 补齐 2.35:1 比例时，**必须用白色 `#FFFFFF` 补齐两侧**。白色 padding 在微信文章里最干净。不要想当然用深色或黑色补齐——用户偏好白色。详见 `references/cover-design.md` 情况 B 的「背景色选择规则」。

| `references/preflight-false-positives.md` | Preflight-check 已知误报：短文件名匹配错误 + 技术名称误判来源泄漏 |\n| `references/append-official-thread-to-article.md` | 已发表文章补充来源官方 X thread 的流程 |\n| `references/cdp-websocket-origin-403.md` | Chrome 126+ CDP WebSocket 403 处理 |\n| `references/svg-disguised-as-jpg.md` | SVG 伪装为 .jpg 扩展名的检测与渲染 |
| `references/svg-chart-extraction.md` | SVG 内嵌图表提取方法（折线图、柱状图等，Cursor Insights 等数据驱动页面常见） |
| `references/cursor-insights-extraction.md` | Cursor Insights (cursor.com/cn/insights) 图表提取：Share as image 按钮 → Vercel Blob URL 模式 |
| `references/data-report-chart-extraction.md` | 数据报告类文章（含大量 SVG/Canvas/JS 图表）的完整提取 SOP + fallback 流程 |
| `references/cdp-image-section-mapping.md` | CDP WebSocket 图片→章节映射：DOM 遍历法 |
| `references/x-article-cover-extraction.md` | X 推文封面提取方法 |
| `references/x-article-cover-hero-extraction.md` | X Article Hero 封面图 vs 内嵌图区分方法 |
| `references/cover-replacement.md` | 推送后替换封面（微信 API 直调）— 不重新推送全文 |
| `references/substack-image-format.md` | Substack CDN 图片扩展名与实际格式不匹配处理 |
| `references/gemini-cover-generation.md` | Gemini 封面生成完整工作流（CDP Chrome + 数据写入 prompt 铁律） |
| `references/gemini-cover-prompt-examples.md` | 实际验证过的 Gemini 封面 Prompt 示例（含 Hermes vs OpenClaw 冲突等真实案例） |
| `scripts/gemini-cover-cdp.py` | **已知良好脚本**：Gemini CDP 生成封面全流程（点「显示原文」无关，但含 returnByValue 入 params / PIL 叠中文 / fontTools 提字体 / recv 按 id 配对 四大修复）。直接 `python scripts/gemini-cover-cdp.py <TAB_ID> "<PROMPT>" <OUT_DIR> [标题] [副标题] [底部行]` |
| `references/gif-video-embed-workflow.md` | GIF 动画保留 + 视频嵌入微信草稿的完整工作流（手动调 API） |
| `references/paper-roundup-format.md` | 论文榜单/周报类文章排版格式：17px 正文、图片说明、论文标题+URL 链接块结构 |
| `references/youtube-screenshot-quality-control.md` | YouTube 视频截图质量控制：talking-head 检测、PIL 筛选、CDP Chrome clip 截图方案 B2（yt-dlp 限流时兜底）、多轮扫描寻找有内容时间点 |
| `references/wechat-gif-embed.md` | 微信文章嵌入 GIF 动图（手动上传素材 + draft/update 替换 URL） |
| `references/wechat-publish-api-limits.md` | 微信 API 获取已发布文章的限制（订阅号+个人主体不可用） |
| `references/published-articles-registry.md` | 已发表文章登记册维护（传送门用）：从发表记录页批量提取 + 推送后自动追加 |
| `references/wechat-draft-download.md` | 从微信公众号草稿箱下载草稿 |
| `references/draft-lifecycle.md` | 草稿生命周期与 40007 恢复 |
| `references/wechat-proxy-troubleshooting.md` | WeChat API 推送 40164 排查：Bun fetch 被系统代理劫持的诊断与修复 |
| `references/typography-reference-jiqizhixin.md` | 机器之心公众号排版参数参考（17px 正文、12px 图片说明、颜色体系等），可作为排版基准参考 |
| `references/body-font-size-control.md` | 正文字号失效根因 + 实测证据（Playwright）+ 三种修法对比。⚠️ SKILL 原有的「容器级联可控」前提已被实测推翻，正文 `<p>` 实测=16px、要点速览=14px |
| `references/draft-sync-workflow.md` | 从微信草稿同步修改到本地 article.md — 用户在公众号后台修改后要求同步时的工作流 |
| `references/humanizer-subagent-completion.md` | Humanizer subagent 完成判定 + delegate_task 卡住处理 |
| `references/humanizer-lifecycle-fix.md` | Humanizer 子任务卡死：根因与修复 |
| `references/humanizer-subagent-conflict.md` | Humanizer subagent 冲突防范 |
| `references/manual-humanize-workflow.md` | 手动 Humanize 工作流（替代 subagent，防卡死） |
| `references/regeneration-mode-detection.md` | 收到 wcsop URL 后的再生/恢复/新文章模式判断流程 |

**🚫 SVG 转换的图 + 白底线条图不用于封面。** 这类图转 PNG 后四周透明/白色，内容居中占比小，放在封面上像"水印图"，毫无吸引力。见 cover-design.md 实际踩坑记录。

#### 3b. 封面裁剪规则

- 2.35:1 主封面 (900×383) + 1:1 方形封面 (500×500)
- **源图宽高比决定拉伸策略：**
  - **宽高比 ≥ 2.0（宽图）**：直接拉伸到目标尺寸（变形轻微）
  - **宽高比 < 2.0（近方形/竖图/技术架构图）**：**禁止直接拉伸**，用 blur-background 方案（模糊背景 + 居中等比叠加），详见 `references/cover-design.md` 的情况 B。PIL 实现：等比缩放使一边贴满 → 缩放到 900×383 并模糊 (GaussianBlur radius=15) → 居中等比叠加原图 → 保存
- **铁律：原图内容不能少，不能半个图。** 用户反复纠正：封面必须保留原图全部内容，禁止任何裁剪。
- 封面选择完整视觉单元（完整的架构图/对比图/图表），不是大图局部碎片
- amplify_video_thumb 类型的视频缩略图也可用作封面

#### 3c. 生成命令

**有来源图时——比例适配方案（按宽高比选择）：**

**宽高比 ≥ 2.0：ffmpeg 直接拉伸**
```bash
ffmpeg -y -i source.jpg -vf "scale=900:383,format=yuv420p" -update 1 cover.png
ffmpeg -y -i cover.png -vf "scale=500:500,format=yuv420p" cover-square.png
```

**宽高比 < 2.0：PIL letterbox（模糊背景 + 居中等比叠加）**
```bash
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/cover-letterbox.py" source.jpg
```

更新 progress.md：由脚本自动完成（无需手动调用）

**⚠️ 封面被用户否决后的处理流程：** 如果用户说"封面没吸引力"或"封面不好看"，不要只换个滤镜或调个颜色。直接启动 CDP Chrome 用 Gemini 生成定制封面（见 references/gemini-cover-generation.md）。先问用户是否接受 Gemini 生成，用户同意后再操作。

**⚠️ Windows ffmpeg 8.1+ 需要 `-update 1` 标志：** 否则会报 `The specified filename does not contain an image sequence pattern` 警告。加 `-update 1` 可消除该警告，输出单张图片。

**无可用图时（文字封面方案）：**
```bash
# ffmpeg drawtext 文字封面 — 无可用来源图时的兜底方案
# ⚠️ Windows ffmpeg: fontfile 路径含 .（如 msyh.ttc / segoeui.ttf）会导致 parser 崩溃
# 必须先复制字体到本地目录，重命名为不含点的新文件名
cd "D:/06_Hermes/articles/<article-dir>"
cp /c/Windows/Fonts/segoeui.ttf  segoeui_font.ttf
cp /c/Windows/Fonts/segoeuib.ttf segoeuib_font.ttf
# 然后用 filter_complex + Python subprocess（见 references/cover-design.md §Windows ffmpeg drawtext 坑）
cd "D:/06_Hermes/articles/<article-dir>"
ffmpeg -y -f lavfi -i "color=c=#0c0e12:s=900x383:d=1" \
  -vf "drawbox=x=0:y=0:w=900:h=4:color=#3290ff:t=fill, \
       drawtext=text='主标题':fontfile='segoeuib_font.ttf':fontsize=36:fontcolor=white:x=30:y=275, \
       drawtext=text='副标题':fontfile='segoeui_font.ttf':fontsize=17:fontcolor=#a0b4c8:x=30:y=320, \
       drawtext=text='标签':fontfile='segoeui_font.ttf':fontsize=13:fontcolor=#8ca0b4:x=12:y=355" \
  -frames:v 1 cover.png
ffmpeg -y -i cover.png -vf "scale=500:500,format=yuv420p" cover-square.png
```

**⚠️ Windows ffmpeg drawtext 坑：fontfile 路径本身不能包含 `.` 字符**（如 `segoeui.ttf` 中的 `.ttf`），否则 filtergraph parser 崩溃报 `No option name near`。**不要把 SKILL.md 中这个命令直接复制到 shell 中执行——它一定会失败！** 正确做法见 `references/cover-design.md` 的「Windows ffmpeg drawtext 坑」章节：复制字体到本地重命名后，用 Python subprocess 传 `filter_complex` 参数，或用 PIL ImageDraw 替代。

---

### 排版全局规则（所有文章必须遵守）

### 标点符号规则

- **禁止使用破折号 `——` 或 `—` 符号。** 文章中所有中文/英文破折号必须替换为：`：`（冒号，用于引出解释/说明）、`，`（逗号，用于分隔）或直接重写句子去掉破折号。原文中的 em dash / en dash 在翻译时同样处理，不保留破折号。
- 允许例外：ASCII 短横 `-`（如 `35B-A3B`、`SWE-Bench`）属于技术术语组成部分，保留不变。
- **推送前执行一次全文件扫描：** `grep -c '——\|—' article_human.md`，返回值必须为 0。不为 0 则全部清除后再推送。

### 图片说明文字格式

- **图片与说明之间不留空行。** 图片 markdown `![](img.jpg)` 直接后接说明文字，中间不空行。
- **说明文字字体必须与正文明显区分。** 使用 HTML `<span style="font-size:12px;color:rgb(153,153,153);">说明文字</span>`，12px 灰色（rgb(153,153,153)）。禁止使用 markdown 斜体 `_text_` 做图片说明。
- 图片说明文字不带标点符号前的空格，紧贴图片 tag。

### 文章开头结构

- **文章正文第一行不能是标题重复。** 标题仅在 `--title` 参数中传入，正文直接以要点速览开始。不要在正文开头加 `**重复标题**`。
- 要点速览使用 HTML `<div>` 卡片包裹（浅蓝灰色背景 `#e8f4fd`），非纯文本。
- 推前验证：`head -1 article_human.md` 应以 `<div` 开头，不能以 `**` 开头包含标题文字。

### HTML 卡片紧凑规则（重要）

要点速览和结语等 HTML `<div>` 卡片内部，**标签之间不能有空行**。空行在微信公众号渲染引擎中会转为额外留白，导致卡片左侧和上方出现多余空白。

❌ 错误写法（标签间有空行引入留白）：
```html
<div style="...#e8f4fd...">

<div style="text-align:center;">

<strong>要点速览</strong>
</div>
```

✅ 正确写法（紧凑无空行）：
```html
<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>要点</strong>：内容<br><br>
- <strong>要点</strong>：内容
</div>
</div>
```

同样规则适用于结语卡片、引用块 `<div>` 等所有 HTML 容器。写完后用 `grep -cP '^\s*$' article_human.md | head -1` 验证段落间是否有过多空行（图片说明、卡片内部、段落间均不应有多余空行）。

## 质量标准：什么是一篇好的 AI 圈公众号文章

以下质量标准在推送前逐条自我检查，不符合的不发。

#### 内容调性

- **独立视角，不是转述。** 单源文章必须有「结语」章节（见 Step 4d），必须有自己的判断。纯翻译/转述的文章不发。
- **反对来源转述式开头。** 不要"XX在播客里说""XX发了一篇长文""XX在X上发了一条推文""XX最近写了一篇"。第一句就是核心论点。
- **不堆英文引文。** 英文引用必须翻译成自然中文。如果非保留原文不可（专有名词、API 名、Prompt 模板），用代码块/引用块包裹，控制在 3 行以内。
- **不编号分段。** 不用"1. 2. 3."或"一、二、三"给段落编号。用自然段落过渡。例外：论文榜单/综述类文章（多篇论文的周报、Top N 盘点），每篇论文章节标题前加数字序号（1. 2. 3. ...），方便读者定位和引用。非论文类文章（博客合集、新闻盘点等）不需要此格式。
- **顺序问题/步骤用编号列表分行展示。** 当正文中连续出现多个问题、步骤或检查项时，不要写在同一段内用逗号/句号分隔（如"问三个问题：A？B？C？"），必须改用有序列表分行展示（`1. A？\n2. B？\n3. C？`）。每个问题/步骤独占一行，让读者逐条阅读。这条规则适用于"怎么开始"中的引导问题、各类checklist、操作步骤等所有序列性内容。

#### 开头与结尾

- **强开头：** 第一句话必须让读者知道这篇文章在说什么，且为什么值得看。用一句硬事实、一个反常识结论、一个具体数字开头。
- **自然段落：** 每段不超过 5 行。一段只讲一个 point。段间空行分隔。
- **一句收尾：** 结尾不写"综上所述""希望这篇文章对你有帮助"。用一句有重量的话收住——可以是一句判断、一个反问、一个行动号召。

## 配图准则

- **严禁使用 AI 生成图做配图。** 用户明确批评过 AI 生成图是「垃圾」。所有配图必须是**真实来源**——官网新闻稿截图、官方博客页面截图、新闻媒体报道截图、产品页面截图、官方文档截图。
- **来源配图一张不能少。** 原文所有图片（截图、图表、对比图）必须下载并嵌入正文，不能只放链接。
- **写一段嵌一张。** 不允许攒到最后统一加图。每张图片放在它对应的文字附近。
- **图片描述有意义。** 不是「图1」「图2」，而是「Anthropic 官方新闻稿 — Blackstone 官网」这样的来源+内容描述。
- **截图只裁剪关键信息区。** 对于产品截图、推文卡片、代码截图，只保留标题+描述+核心视觉区域，不要整页长截图。
- **封面选完整视觉单元。** 封面图选择完整的架构图/对比图/图表，不是大图的局部碎片。
- **封面用真实场景照，不用纯文字/AI图。** 封面使用从官网新闻稿下载的真实 Hero 图、产品场景照、Keynote 现场照。禁止用纯文字渐变封面或 AI 生成封面。
- **图片说明格式（铁律）：** 图片 markdown 与说明文字之间不留空行。说明文字用 <span style="font-size:12px;color:rgb(153,153,153);"> 包裹（12px 灰色小字），禁止用 markdown 斜体 _text_ 做图片说明。这是为了在手机上图片说明能与正文一眼区分。

#### 中英文混排

- 英文术语/数字与中文之间**不要加空格**（"月费$62,000" 不是 "月费 $62,000"）
- 英文翻译为自然中文（`特化 → 专门化` `知見 → 洞见` `実装 → 实现/方案` `标杆 → 基准测试/评测` `管线 → 流程/流水线`）
- 保持术语一致性。同一篇文章里同一个英文术语的译法不能变。
- **核心概念词保留英文不翻译。** 当原文使用一个特定的英文术语作为全文的核心概念框架（如 **Agent**、**Harness**、**Skill**、**Memory**、reasoning、tool-calling 等），应直接保留英文（首字母大写），不要译为"智能体""工具层""技能""推理"。判断标准：去掉这个英文词，中文译文是否还能准确传达原文的概念框架？如果不能，保留英文。常见案例：原文以 "harness" 为核心隐喻贯穿全文 → 译为 "Harness"，不译为"工具链""编排层""工具层"。只有纯描述性术语（特化→专门化、実装→实现）才需要翻译为自然中文。
- **特别规则 — memory 必须译为「记忆」，不是「内存」。** Memory 在 Agent 语境中指持久化记忆/存储系统（session history、facts、traces），不是计算机硬件中的 RAM 内存。任何时候翻译为「记忆」「记忆层」「记忆系统」，不得出现「内存」。
- **⚠️ 区分 Agent memory 和 computer memory。** 当原文讨论的是 GPU 显存、KV cache、RAM 等计算机硬件/内存概念时（如 KV caching 文章中的 "GPU memory"、"memory bandwidth"），应译为「内存」而非「记忆」。判断标准：如果上下文是推理优化、显存占用、缓存机制，用「内存」；如果是 Agent 的持久化状态、会话历史、知识存储，用「记忆」。
- **特别规则 — Agent 绝对不翻译。** 即使中文语境中「Agent」在单句中出现多次，也不得替换为「智能体」「代理」「AI助手」。原文写 Agent 就保留 Agent。如果原文全小写 agent，统一首字母大写处理为 Agent。

#### 标点符号规则

详见「**排版全局规则**」章节的「标点符号规则」——本处不重复列出。

#### 加粗与蓝色高亮

- **除背景介绍段外，正文每段至少要有1句或半句加粗**，作为段落重点。不加粗的段落读起来太平淡、无重点突出。背景介绍段（文章开头1-2段交代背景的段落）可豁免。
- **不加粗单个术语/名词/数据。** 不加粗「Agent」「Memory」「5倍」「$62,000」这类孤立概念。单独一个词加粗在视觉上像标签而不是金句，读者扫一眼就过去了，不会留下判断。
- **加粗只用于完整观点句或半个金句。** 加粗的对象必须是承载了一个完整判断的短语或句子——去掉加粗，读者是否漏掉一个不可跳过的逻辑环节？如果是，加粗。例：「人类是绝对的瓶颈」✓、「整个流水线的速度取决于最慢的人工审阅者」✓、「编码成本的下降让这个事实更扎眼了，但没有改变它」✓。过渡句、描述句、例证句不加粗。
- **每段最多 1 处加粗。** 全篇加粗过多等于没加粗。宁少勿滥。
- HTML 表格内的 `<strong>` 同样会被 md-to-wechat 染成蓝色（#0F4C81），所以在 HTML 原始块里也用 `<strong>` 来标注观点句。

#### 参考区

- 必须小字灰色 12px，以"参考：**裸 URL**"开头（见 Step 4e）
- 参考区字体用等宽字体（`font-family:'Courier New',monospace;`）与正文区分（见 Step 4e）
- [ ] 所有来源统一放纯文本裸 URL，**不用 `<a>` 标签**（微信正文不支持任何可点击超链接，`<a>` 被无声过滤）
- **⚠️ 多来源时不要用 <br> 分行**：微信 API 返回 45166 `invalid content hint`。只放一个主来源 URL，其余在正文中用文字提及
- **⚠️ 正文中引用前作/外部链接时，禁止裸 URL。** md-to-wechat 检测到裸 URL 会自动生成 `<a>` 标签，且中文标点（句号、括号、引号等）会被吞进 href 属性值中，导致微信 API 返回 45166 `invalid content hint`。正确做法：用反引号包裹 URL（`URL`），渲染为 `<code>` 标签，避免生成 `<a>` 标签。
- 非 X 来源放裸 URL，不加"原文链接""原视频"等描述

---


更新 progress.md：由脚本自动完成（无需手动调用）

### Step 4：写文章 ← 核心步骤 ⏱ 10-30min

| TASKS.md `patch` 用 `replace_all=True` 导致表格行重复/错位 | TASKS.md 中相同文本模式出现多次（如 `✅ 已推送` 结尾），`replace_all` 无差别替换全部匹配，破坏表格结构 | 不用 `replace_all=True` 更新 TASKS.md。提供足够上下文使 old_string 唯一，或在 patch 前用 `read_file` 确认精确的待替换字符串。最好用 `python` 追加新行而非 `patch` |
| **TASKS.md 手动 patch 主表行导致 `update-tasks.py complete` 无法匹配** | `complete` 函数旧版正则要求行格式必须为 `| TBD | TBD | 📥 进行中 |`，但手动 patch 改掉了标题/封面/状态列，正则找不到匹配→主表行未更新 | **不要手动 patch 主表行。** 用 `update-tasks.py status` 更新中间状态（它自动管理格式），最后用 `complete` 收尾。如果确实需要手动改表，则必须补跑 `complete` 命令后再检查主表行状态
|  文章开头铁律：article.md 第一行绝不能是 `---`。文章直接以要点速览 HTML 卡片开头，前面不写任何内容（不加标题行、不加 hook、不加分隔线）。写完文章后立刻验证：`head -1 article.md` 必须返回 `<div`（要点速览卡片开头），不能返回 `---` 或 `**` 或纯文字。

#### 4a. 阅读原文，列出关键素材清单

在写正文之前，先列出：
- 原文的核心论点（1-3 个）
- 关键数据/引用
- 所有图片文件名（和 Step 2 下载的文件一一对应）
- 原文中的表格/对比图

**⚠️ SVG 图表陷阱（高频遗漏）：** 页面中的内嵌 SVG 图表（折线图、柱状图、饼图等）在 CDP Chrome 正文提取时不会被识别为 `<img>`。通过 CDP Chrome 的 `document.querySelectorAll('svg')` 检查 SVG 元素数量。对于 Chart.js/D3 生成的图表，通过 CDP 执行 JS 提取 chart data URL。

**⚠️ 数学公式碎裂陷阱（技术类 X/文章高频）：** CDP 提取含 LaTeX/数学公式的推文或文章时，公式常被拆成单个 Unicode 数学字形（如 `𝑧`、`𝑖`、`Δ`、`Σ`、`∑`、`≥`、`̃`）逐行散落在 `full_text.txt`，而非连续可辨的公式字符串。这些碎裂字符若原样抄入 `full_translation.md`，会污染覆盖率 baseline 并在文章里显示乱码。**正确做法：** 写 `full_translation.md` 和正文时，将碎裂字形按原公式语义重组为连贯的行内 LaTeX（如 `z̃_i = z_i^(0) + Δz_i`、`τ_emp = 1 + Σ_{i=1}^{γ} q_i`）或自然语言描述，不要逐字保留散落字符。封面/图表不受此影响。无 `vision_analyze` 工具时，图片内容靠提取文本中的 Figure caption（如 `图1：…`）和 PIL 尺寸检查确认，不靠肉眼看图。

#### 图片说明提取（vision 不可用时）

当 `vision_analyze` 因区域限制不可用时，用 CDP Chrome 的 DOM 遍历提取每张图片的原文说明。**不要因为 vision 受限就自己编造图片描述。**

在 CDP Chrome 已打开页面的 websocket 连接上执行 DOM 遍历脚本：
```python
script = '''
(() => {
  const results = [];
  const imgs = Array.from(document.querySelectorAll('img[src*=\"pbs.twimg.com/media/\"]'))
    .filter(i => !i.src.includes('profile_images') && i.naturalWidth > 0);
  imgs.forEach((img, idx) => {
    let el = img;
    let text = '';
    for (let i = 0; i < 8; i++) {
      el = el.parentElement;
      if (!el) break;
      const t = (el.textContent || '').trim();
      if (t.length > text.length) text = t;
      if (t.length > 50) break;
    }
    results.push({
      idx: idx + 1,
      src: img.src.split('?')[0].split('/').pop(),
      w: img.naturalWidth, h: img.naturalHeight,
      containerText: text.substring(0, 300),
      alt: img.alt || '',
    });
  });
  return JSON.stringify(results);
})()
'''
```
结果中的 `containerText` 字段包含图片所在 DOM 容器的原文文字，通常即为图片说明（如 `Source: Nvidia`、`Source: Huawei — CloudMatrix 384 互联架构`）。**直接作为图片说明使用，不要自行编造。** 如果 `containerText` 为空或仅含"图像"等无意义内容，使用简洁的实体名（如"Nvidia/华为/LongCat"）作为兜底。

#### 图片说明提取（vision 不可用时）

当 `vision_analyze` 因区域限制不可用时，用 CDP Chrome 的 DOM 遍历提取每张图片的原文说明。不要因为 vision 受限就自己编造图片描述。

```python
script = '''
(() => {
  const results = [];
  const imgs = Array.from(document.querySelectorAll('img[src*=\\\"pbs.twimg.com/media/\\\"]'))
    .filter(i => !i.src.includes('profile_images') && i.naturalWidth > 0);
  imgs.forEach((img, idx) => {
    let el = img;
    let text = '';
    for (let i = 0; i < 8; i++) {
      el = el.parentElement;
      if (!el) break;
      const t = (el.textContent || '').trim();
      if (t.length > text.length) text = t;
      if (t.length > 50) break;
    }
    const aria = img.getAttribute('aria-label') || '';
    results.push({
      idx: idx + 1,
      src: img.src.split('?')[0].split('/').pop(),
      w: img.naturalWidth, h: img.naturalHeight,
      containerText: text.substring(0, 300),
      alt: img.alt, aria: aria,
    });
  });
  return JSON.stringify(results);
})()
'''
```
结果中的 `containerText` 字段包含图片所在 DOM 容器的原文文字，通常即为图片说明（如 `Source: Nvidia`、`Source: Huawei — CloudMatrix 384 互联架构`）。**直接作为图片说明使用，不要自行编造。** 如果 `containerText` 为空或仅含"图像"等无意义内容，使用简洁的实体名（如"Nvidia/华为/LongCat"）作为兜底。

**写文章前必须核对：Step 2 下载的图片数量 ≥ Step 4a 列出的图片清单数量。** 数量对不上=有遗漏，必须回去补抓。

**⚠️ 图片→章节映射表（高频失败点）：** 写正文前，必须从 CDP 提取的原文中按出现顺序列出每张图片/视频所属的章节。具体做法：
1. 从 CDP 提取的完整内容中，逐段标注每张图片/视频的 URL 和它所在的章节标题
2. 特别留意：**视频（amplify_video）通常放在引言区**（Part 1 之前），展示核心概念对比（如"有/无 KV Cache 的 5 倍速度差异"），不是某个具体章节的配图
3. 记录每个章节的 GIF/图片数量：Part 1 可能有 2 个 GIF，Part 2 可能有 2 个 GIF，Part 3（冗余）可能没有配图
4. 写正文时严格按照映射表嵌入，每嵌一张就在映射表上打 ✓
5. 全部嵌入后，统计正文中的图片总数 = 映射表中的总数

#### 配图嵌入铁律（2026-07 新增）

**① 原文图片全部嵌入，一张不能少。** CDP Chrome 提取到 N 张图，正文就必须嵌入 N 张。不允许筛选/缩减——即使图片看起来"重复"或"冗余"也是原文内容的一部分。

**② 图片说明必须来自原文，不得自己编造。** X Article 的推文 thread 中每条推文自带图片及说明文字，用 CDP 提取正文时一并提取。图片说明直接使用原文的描述，不要"概括"或"润色"。

**③ 图说 +1 错位铁律（实测高频根因）。** 当来源是单条 X 长推文（非带 `##` 章节的博客）时，所有 `<img>` 在 DOM 里挂在同一个（或极少数）标题下，本文件的「最近 h2/h3」信号全部塌缩成同一个值 → 写作步骤被迫另起一轮由 LLM 给每图编 caption，这轮没有可靠的「图→其说明」绑定，整体相对图片序列发生 **+1 偏移**（尤其当线程头部有 HERO/封面图吞掉一个 caption 槽时）。表现：每张图说的是「下一张的 caption」，且可能凭空塞入源文无对应图的说明。

- **根防**：图与 caption 必须在**同一次 DOM 遍历**里绑定成一对记录（`<img>` + 其紧邻前导文本节点），绝不允许「先抓图数组、再单独编 caption 数组、最后 zip」——这正是 +1 偏移的温床。
- **提取后断言** `图片数 == caption 数`，不等立即告警。
- **X 线程特例**：caption 取「`<img>` 前一个文本节点」，不用最近 h2/h3（线程里该信号无效）。HERO/封面图在提取阶段单独标记，不参与正文 caption 配对，避免吞槽。
- **修复**：若用户给出 ground truth 描述清单，直接以此为准重写 caption，不要信当前文件里的 zip 结果。
- **推前验证（必做）**：生成并排预览 HTML（`scripts/check_caption_pairing.py` 或手写 3 列卡片页）让用户逐张核对图↔说明一一对应，确认后才推送。详见 `references/image-caption-integrity.md`。

#### 引用块样式规则（关键视觉元素）

**🚫 禁止使用 `>` markdown 引用块语法。** md-to-wechat 将 `>` 渲染为微信公众号默认灰色竖线引用样式，**不会保留任何自定义背景色、字体颜色、边距**，导致同一篇文章内引用块与要点速览（`#e8f4fd`）、结语（`#f5f0eb`）卡片的外观割裂。

**✅ 必须使用 HTML `<div>` 容器模拟引用块。** 所有引用/强调段落统一使用以下样式：

```html
<div style="background:#f0f7fa;padding:16px 18px 14px 18px;border-radius:6px;margin:16px 0;border-left:4px solid #5b9bd5;">
<div style="font-size:15px;color:#2c6a9e;line-height:1.7;">
引用内容...
</div>
</div>
```

**样式参数固定：**
- 背景色 `#f0f7fa`（浅蓝灰）
- 左侧 4px 实线边框 `#5b9bd5`（深蓝）
- 字体颜色 `#2c6a9e`（深蓝）
- 圆角 `6px`，上下边距 `16px`

**正文写作时直接写 HTML，不使用 `>`。** 推送前验证：`grep -c '^>' article_human.md` 必须返回 0。

#### 4a-i. 写要点速览

在正文之前增加「要点速览」章节，提炼原文的 2~5 条核心要点。这是给没时间读全文的读者准备的速览。

**格式规则：**
- 要点速览在文章最开头，前面不写任何内容。文章第一个字符就是要点速览内容
- 使用 HTML `<div>` 卡片包裹，浅蓝灰色背景（`#e8f4fd`），标题文字蓝色（`#1a6ba0`），正文深灰（`#3f3f3f`）
- 要点速览总条数严格控制在 2~5 条，宁少勿滥
- 要点速览内容必须来自原文，不能自己编造要点
- 用 `---` 分隔线与正文隔开

**HTML 卡片模板：**
```html
<div style="background:#e8f4fd;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:18px;">
<div style="text-align:center;margin-bottom:10px;">
<strong style="font-size:16px;color:#1a6ba0;">要点速览</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
- <strong>要点关键词</strong>：核心内容<br><br>
- <strong>要点关键词</strong>：核心内容
</div>
</div>

---

```

#### 4b. 确定独立观点

单源文章天然容易写成"原文翻译"。在写正文前想清楚：
- 这篇文章的独立观点是什么？
- 对原文论点有什么质疑或补充？
- **独立观点只放在文章最后一段「结语」，不分散到各节**

**如果想不到独立观点，不发。** 先做相关搜索补充素材。

**关于「结语」的写作规则：**
- **禁止每节都写分析。全文只在最后有一段「结语」。**
- **必须精简，每条 1-2 句**，不展开长篇分析
- **总条数不超过 4 条**，宁少勿滥
- 只写对原文论点的质疑、补充、或行业意义
- **不评价作者。** 不要用"作者是高手""这篇是迄今为止最X的"——除非作者是公认的名人/名企（如 OpenAI 官方博客、Karpathy 等）。普通作者不提名字，只说"本文"
- 不写"最后，这篇文章本身就是一个例证"这类自指评论
- **格式区分：** 「要点速览」是原文要点的客观提炼（用无序列表），「结语」是独立观点的主观分析（用自然段落，不用列表）。两者视觉上必须一眼能区分

#### 4c. 写正文

**🚩 写正文前先加载文章模板：** `skill_view(name='wechat-article-sop', file_path='references/article-template.md')` — 模板定义了要点速览卡片、结语卡片、传送门、参考区的精确 HTML 结构和排列顺序。严格按模板写，不偏离。

**🚩 生成时格式规则（必须写正文时就做到，不依赖后续检查修复）：**

- **中英文/数字间不加空格** — 写正文时直接写`月费$62,000`而非`月费 $62,000`，`5倍`而非`5 倍`
- **禁止使用破折号** — 原文的 em dash (——) 在翻译时直接替换为中文冒号`：`（引出解释）或逗号`，`（分隔）
- **图片说明用 HTML** — 直接写 `<span style="font-size:12px;color:rgb(153,153,153);">` 而不是 markdown 斜体
- **开头无 frontmatter** — `article.md` 第一个字符必须是要点速览卡片的 `<div`，不是 `---`
- **写一段嵌一张图** — 不攒到最后统一加图，每段完成后立即嵌入对应图片
- **🚩 正文字号与要点速览对齐（14px）。** ⚠️ **2026-07-08 实测修正**：正文 `<p>` 的实际字号**不由 SOP 的 `font-size:14px` 包裹 div 控制**——`baoyu-md`（baoyu-post-to-wechat 依赖）会在根 `<section>` 和 `data-role="outer"` section 上**写死 `font-size:16px`**，正文 `<p>` 继承这个 16px，而 SOP 模板里的 14px div 只包住了卡片内容（`- 列表`+`<br>`，不是 `<p>`）。实测：正文 `<p>` computed = 16px，要点速览 = 14px，故视觉上正文更大。**改 SKILL 模板里的 14px 包裹 div 无法让正文变 14px。**
- **让正文真正 = 14px 的唯一已验证路径（已实施）**：`baoyu-md` 的 `renderMarkdownDocument` 原生支持 `fontSize` 参数；`wechat-api.ts` 现已透传 `--font-size` 且**默认 14px**，`md-to-wechat.ts` 同步接收并传给 `renderMarkdownDocument`。wcsop 现有推送命令（`--theme default --no-cite`，不加 `--font-size`）自动渲染正文 14px，与要点速览一致。需要其他字号时显式传 `--font-size 15px`（可选值 14/15/16/17/18px）。改前正文 `<p>` 实测 16px，改后 14px（Playwright computed）。
- **🚫 禁止在 SKILL 模板里加 `font-size:14px` 包裹 div 来「控制正文 `<p>`」——实测无效。** `<p>` 根本不在该 div 内（正文 prose 的 `<p>` 继承 `baoyu-md` 根 section 的 16px），外层 16px 优先级盖过模板的 14px。完整根因、实测数据、修复落地记录见 `references/body-font-size-control.md`。
- **🚫 章节标题必须用 `##` markdown 语法**。正文中的章节/小节标题必须使用 `## 标题` 格式（加 `## ` 前缀），md-to-wechat 会自动渲染为**居中加粗 + 深蓝色背景框**。不得使用 `**加粗文字**` 纯加粗格式做章节标题。子分类标签（如「第一类」「第二类」等）可继续用 `**加粗**`。推送前验证：`grep -nP '^\\*\\*[^*]+\\*\\*$' article_human.md` 无独立行加粗（仅允许段落内加粗）。原文有编号结构（1. 2. 3. 或 a. b. c.）的，翻译后必须保留编号。不能用自然段落替换原文的表格/编号结构。每个章节都要覆盖，不能合并或省略。用户对「改成自己摘要」的容忍度为零。
- **🚫 正文中的 markdown 表格所有列用左对齐 `|---`**，不用居中 `:-:` 或右对齐 `---:`。md-to-wechat 渲染左对齐表格阅读体验最佳。推送前验证：`grep -cP '^\|:\-\|' article_human.md` 必须返回 0。

- **🚩 正文结构逐章对齐（要点速览→结语之间的正文区域）。** 「要点速览」卡片之后、「结语」卡片之前的正文部分，章节/段落结构必须与原文逐一对齐：
  - 原文有几个章节，正文就有几个章节，不允许合并、省略或重排顺序
  - 每个章节内部的段落组织方式与原文一致（不随意合并段落、不改变叙述顺序）
  - 章节标题的层级关系（隶属/并列）保持不变
- **📊 每章内容建议覆盖原文（参考指标，非强制）。** 写完后可用 `full_translation.md` 对应章节做 baseline 对比内容完整性。覆盖率为参考指标，不强制逐章 ≥ 70%，不达标也不阻断推送。

**后续的 Step 4g 会自动修复遗漏，但生成时就做对可以避免后续重复修改。**

### 4c-0. 结构对齐清单（写正文前必须执行）

在写正文之前，先做结构对齐检查，防止写了半天发现缺章节：

1. **提取原文章节树**：从 `full_translation.md` 中提取所有章节标题（`##` 级别），列出完整结构（无编号/编号保留原样）
2. **对比当前 article.md 的章节树**（仅要点速览→结语之间的正文区域）
3. **标记差异**：
   - ❌ 缺失的章节 — 注明需要新增
   - ❌ 合并的章节 — 注明需要拆分为独立节
   - ❌ 重排的章节 — 注明需要恢复原文顺序
4. **执行修复**：先补缺失章节，再拆分合并章节，最后恢复顺序
5. **验证**：要点速览→结语之间的所有 `##` 标题与原文一一对应，数量一致

> **常见缺章模式：** 原文的「动机/背景/引言」在翻译时容易被压缩进文章开头的引言段落、「结论/未来工作」容易被吞或直接跳过（因为 4d 结语让模型误以为原文结论不需要了）。**这两个是最常见的缺失源。**

**🚩 先判断文章类型：翻译文章 vs 访谈实录。**

### 🎙️ 访谈实录模式（Summary + 对话翻译）⏱ 15-25min

当文章来源是视频/播客访谈（口语对话），用户要求「前面是总结，后面是对话原文」时走此模式。完整指南见 `references/interview-transcript-mode.md`。

**核心差异（与标准翻译模式）：**

| 维度 | 标准翻译 | 访谈实录 |
|------|---------|---------|
| 正文结构 | 章节编号与原文一致 | 无编号，`---` 分隔「总结」和「对话实录」|
| 内容来源 | 原文逐段翻译 | 从字幕提取对话 → 翻译 |
| 人物引用 | 正文不提作者名 | 标注说话人：`**说话人：**` |
| 结语 | 文末独立观点 | 无结语（访谈是素材记录）|
| 图片 | 原文一张不能少 | 无配图，封面用程序化生成 |

**正文结构模板：**

```
**标题**
前导段落（2-3 段，交代访谈背景、嘉宾身份、核心话题）

---

**对话实录**
**Raytar：** 说话内容
**Boris：** 回应内容
```

**格式要点：** 对话不编号；技术术语保留英文；翻译为口语化中文；对话部分结束后用 `---` + 参考区收尾。

#### 4c-iii. 机器之心排版格式（用户参考标准）

**用户明确以机器之心文章（https://mp.weixin.qq.com/s/no9D3gqUzEKJHIFDW56-7w）为排版参考标准。** 以下是从该文章 HTML 中提取的精确结构。

**正文结构：** 用 `<section>` + `<span>` 组合，**不是** `<p>` 标签：

```html
<section style="text-align: justify;margin-left: 8px;margin-right: 8px;line-height: 1.75em;">
<span style="color: rgba(0, 0, 0, 0.9);font-size: 17px;font-family: mp-quote, &quot;PingFang SC&quot;, system-ui, -apple-system, BlinkMacSystemFont, &quot;Helvetica Neue&quot;, &quot;Hiragino Sans GB&quot;, &quot;Microsoft YaHei UI&quot;, &quot;Microsoft YaHei&quot;, Arial, sans-serif;letter-spacing: 0.034em;font-style: normal;font-weight: normal;">正文内容...</span>
</section>
```

**关键参数：**
- `font-family`：完整字体栈（含 mp-quote、PingFang SC、system-ui 等）
- `letter-spacing: 0.034em`（不是 `0.544px`）
- `font-weight: normal`（正文不加粗，全文无 `<strong>` 标签）
- `margin-left: 8px; margin-right: 8px`
- 每个段落一个独立的 `<section>` 标签

**图片说明文字：**
```html
<span style="font-size: 12px;color: rgb(153, 153, 153);">说明文字</span>
```
颜色用 `rgb(153, 153, 153)` 而非 `#888888`。

**论文标题/链接（制表符格式，仅限论文类文章）：**
```html
· <span style="font-size: 15px;color: rgb(0, 66, 123);font-weight: bold;">标题：</span><span style="font-size: 15px;color: rgb(0, 66, 123);">论文英文标题</span><br>
· <span style="font-size: 15px;color: rgb(0, 66, 123);font-weight: bold;">链接：</span><span style="font-size: 15px;color: rgb(0, 66, 123);">https://arxiv.org/abs/XXXX.XXXXX</span>
```
- 用 `·` 制表符开头
- 显式标注「标题：」「链接：」前缀
- 深蓝色 `rgb(0, 66, 123)`，15px
- 标题和链接分两行
- **仅限论文类文章**（arXiv 论文、学术论文等），非论文类文章（博客、推文、新闻等）不需要此格式

**图片嵌入：** 用 markdown `![](imgX.jpg)` 语法（让 md-to-wechat 识别占位符），不要用 `<img>` HTML 标签。

**⚠️ 链接占位符陷阱：** 推送前必须排查所有链接，确保没有 `xxxxx` 或 `xxx` 等占位符残留。未找到 arxiv ID 的论文应明确告知用户，不要用 `xxxxx` 占位符推送。

**多论文综述文章序号规则（仅限论文类）：** 当文章是多篇论文的综述/列表（如「Top 10 论文」），每篇论文的章节标题前加数字序号（1. 2. 3. ...），方便读者定位和引用。非论文类文章（博客合集、新闻盘点等）不需要此格式。

**禁止项：**
- 正文中不要使用 `<strong>` 或 `<b>` 标签——机器之心全文无 `<strong>`
- 正文中不要使用 `<p>` 标签——改用 `<section>` + `<span>` 结构
- 不要用 `letter-spacing: 0.544px`——实测值为 `0.034em`

#### 4d. 写「结语」章节（文末独立段）

这是与纯翻译转述的关键区别。**全文只在文章最后（正文之后、参考区之前）有一段「结语」，禁止在正文各节中穿插。** 不要每节都写，不要编号（1. 2. 3.），就是连贯的一段或几段话。

**⚠️ 原文自带结论段必须包装成结语卡片，不要保持原段落格式。** 当原文在末尾有作者自带的结论段（如 "The honest part" "Final thoughts" "Conclusion" 等），不要只把它翻译成普通加粗标题段落。必须去掉原文结论标题，把内容放入 `结语` 暖灰卡片（#f5f0eb）中。原文的结论内容忠实保留在卡片正文内，只是视觉上包装成统一卡片。**推前检查：digest 之后正文最后一段是 `</div>` 不是普通段落。** 注意：wcsop 默认是严格翻译模式，不要添加自己编造的独立观点——但原文自带的结论段落用卡片包装不算「添加内容」，这是保留原文的格式策略。

**格式规则：**
- 标题用 HTML `<div>` 卡片包裹，居中显示，暖灰背景色（`#f5f0eb`），圆角，标题文字暖棕色（`#8b6f4c`）
- 正文内容也放在同一卡片内，14px 深灰（`#3f3f3f`），行距 1.75
- 每条用 `<br><br>` 分隔
- 标题为「结语」，不用「一点观察」
- 必须精简，每条 1-2 句，总条数不超过 4 条
- 用自然段落，不用列表（与「要点速览」的列表格式形成视觉区分）

**HTML 卡片模板：**
```html
<div style="background:#f5f0eb;padding:14px 16px 10px 16px;border-radius:6px;margin-bottom:16px;">
<div style="text-align:center;margin-bottom:8px;">
<strong style="font-size:15px;color:#8b6f4c;">结语</strong>
</div>
<div style="font-size:14px;color:#3f3f3f;line-height:1.75;">
分析内容<br><br>
分析内容
</div>
</div>
```
#### 4d-i. 特别模式：作者亲历视角 + 产品定位（thought leadership）
这是最常见的科技思想领导力文章形态——作者以"我在某公司的亲身经历"建立可信度，然后推出自己当前公司的解决方案。如：前 HashiCorp 员工写"模型锁定像云锁定"，最后推荐自己当前公司的产品。

**这种文章的陷阱：** 作者的历史视角通常是真实的，但选择性呈现的。他们用亲身经历强化类比的说服力，同时省略不利于自己论点的细节。

**处理原则：**

1. **审视类比精度，而不是全盘接受。** 作者说"A 就像 B"，问自己：B 时代的哪些关键变量在 A 时代不存在？作者省略了什么？如：云时代的"工具层锁定"（CloudFormation）和模型时代的"工具层锁定"（Agent SDK）在切换成本、供应商集中度、开源替代品成熟度上有本质差异。这些差异需要在分析中点明。

2. **区分"行业诊断"和"开药方"。** 作者对行业问题的诊断可能完全正确，但推荐的具体方案有强烈利益导向。分析中可以认可前者，同时对后者保持审视。在「结语」中用一两句话分开讨论，不让读者误认为"问题=特定方案"。

3. **直接点明作者当前身份。** 不要把作者的当前雇主当作需要隐藏的信息。在正文中（而非仅在「结语」中）适度交代作者背景（如"前 HashiCorp 工程师、现任 LangChain 员工"），让读者自己也有判断框架。

4. **反问：如果换一个人写同一话题会怎样？** 问自己：如果由这个作者的竞争对手或一个独立研究员写同一个论点，框架会有什么不同？这种思维实验能帮你找到被选择性忽略的角度。

5. **指出商业模式中的悖论。** "中立"的中间层本身也是一种商业模式。HashiCorp 靠"中立"成为百亿美元公司，LangChain 也在走同一条路。在分析中点出这一点——不是因为"商业=坏"，而是让读者知道"中立层"本身也有自己的增长压力和产品方向。

详见 `references/insider-perspective-articles.md`。

#### 4d-i. 写传送门（往期推荐）

> 使用 `scripts/add-portal.py` 自动完成选文+注入。**published_articles.json 只读不写。**

在「结语」卡片之后、「参考区」之前插入「传送门」区块。使用专用脚本一键完成：

```bash
# 自动选8篇（4篇相关+4篇多样性）并注入 article_human.md
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/add-portal.py" "D:\\06_Hermes\\articles\\<article-name>"
```

**选文规则（脚本内实现）：**
- 4 篇与当前文章主题相关（按预定义关键词组打分）
- 4 篇多样性（选得分最低的无关文章）
- **published_articles.json 只读不写**，由用户手动维护

**格式规则（脚本内实现）：**
- 字体 14px（`font-size:14px`）
- 链接间 `<br>` 无空行
- 前后各有 `---` 分割线
- 标题「【传送门】」
- `<a class="normal_text_link mp_article_text_link" data-linktype="2">` 可点击标签
- href 必须为短 slug（如 `/s/xxxx`），非 media_id

**注意：**
- 如果 `published_articles.json` 不存在或为空，跳过传送门步骤
- 推前检查传送门无当前文章自身
- **推前检查传送门无 `xxxx` 或 `xxx` 占位符残留**
- **传送门随机化**：`add-portal.py` v2+ 引入日期种子 + `.portal_history.json` 历史排除，同一篇文章每次跑选文不同。脚本自动在 `D:\\\\06_Hermes\\\\articles\\\\.portal_history.json` 记录已选文章URL，下次优先选没用过的
- **⚠️ 结语纯文本格式时 `add-portal.py` 会失败**：当结语使用纯文本格式（`**结语**`）而非旧版 `<div>` 卡片时，脚本搜索 `<div style="background:#f5f0eb;...` 找不到，报 `找不到结语卡片结束位置` 并退出。此时手动注入传送门 HTML：先跑 `add-portal.py` 获取其输出中的选文列表和生成的 HTML → 复制 HTML 片段 → 用 `execute_code` 或 `write_file` 在 `article_human.md` 的 `**原文：**` 行与参考区 `<span>` 之间插入传送门 HTML。见下方「传送门脚本失败的手动 fallback」。
- **⚠️ 传送门 64-char media_id 污染 → 45166（高频新增坑）**：`published_articles.json` 若某条 `url` 存的是 **64 字符 media_id**（如 `.../s/TIqnnVEu6Oy3-wtKttGa0RLS-...5p-Tz`）而非 **22 字符短 slug**，`add-portal.py` 会原样写进 portal 的 `href` → 微信 API 报 `45166 invalid content hint`（根因见 `references/portal-wechat-api-limitation.md`）。**推送前必须验证：**
  1. 跑完 `add-portal.py` 后，立即扫 portal 所有 href：`grep -oP 'mp.weixin.qq.com/s/[A-Za-z0-9_-]{40,}' article_human.md`
  2. 若有命中（40+ 字符 = 坏 slug），说明 `published_articles.json` 对应条目 URL 错了。**真实短 slug 只能从已发布的可靠来源取得**，按优先级查：① 其他文章的 portal 里是否链接过该文（`grep -rhoP 'mp.weixin.qq.com/s/[A-Za-z0-9_-]{22}' */article_human.md | sort -u` 找候选）；② 该文章自己目录的 `draft.id`（但 draft.id 存的是 media_id，不是 slug，通常不可用）；③ TASKS.md 该任务的历史推送记录。
  3. **修复方式**：把 `published_articles.json` 中那条坏 URL 替换为真实 22-char slug（用 `patch` 精确改那一行），然后**重新跑 `add-portal.py`** 让 portal 用正确 slug 重建。若实在找不到真实 slug，宁可删掉该条目让脚本另选一篇，也**绝不能伪造 slug**。
  4. **🚫 两条铁律（踩过坑）：** ① **绝不编造 slug** —— 随便写个 22 字符字符串作 href，推到线上是死链，且污染 `published_articles.json`；② **绝不在 json 里造重复条目** —— 不要把坏条目改成一个「看起来相关」的已有文章（会生成第二个同名条目，dir 重复）。正确做法是修该条目本身的 URL，或删掉它。
- **⚠️ published_articles.json 语法损坏 → add-portal 全局崩溃（2026-07 新增）：** 该文件是手维护的 JSON 数组，任意一处语法错误（最常见：某条目末尾缺逗号、缺 `"score"` 字段、引号不配对）会让 `add-portal.py` 在 `load_published()` 阶段抛 `json.decoder.JSONDecodeError` 直接退出，**所有文章都无法生成传送门**，不只是当前这篇。修复流程：先 `python -c "import json; json.load(open('published_articles.json',encoding='utf-8'))"` 定位报错行（如 `Expecting ',' delimiter: line 14 column 2`），补逗号/字段使 JSON 合法，复验 `json.load` 0 报错后重跑 add-portal。该文件为只读来源，只修语法错误、**不要**顺手增删条目内容（除非确属坏 slug，见上）。
- **⚠️ 传送门标题截断必须按「显示宽度（用户规则）」而非「字节数」（2026-07 已修复，勿回退）：** 旧实现按 UTF-8 字节（86 字节）截断，但公众号一行宽度按字符显示宽度算。用户实测规则：**1 个汉字 = 1 单位，2 个英文/符号 = 1 单位（即半角按 0.5 计）**。微信手机端一行约 41 个汉字，2 行上限 = **81 单位**（留 1 单位余量，保险）。当前 `add-portal.py` 已实现 `truncate_to_width(title, 81)`（汉字=1、半角=0.5，封顶 81 单位）。**绝不要把截断逻辑改回字节数，也不可误用全角×2/半角×1 规则**——字节规则（86）会复现 3 行问题；而全角×2/半角×1（cap 56）会把大量本来 1 行宽的标题也截断残缺，看起来像「很多不该截的都被截了」。验证：重跑后扫所有 portal 标题，显示宽度 `sum(1.0 if unicodedata.east_asian_width(c) in ('W','F') else 0.5 for c in t)` 必须全部 ≤ 81。

  **⚠️ 维护陷阱（实测踩坑）：** 用 `patch` 工具改 `add-portal.py` 可能报告成功但**未真正落盘**（文件位于 `bak_another` 备份/同步目录，会被还原成原始字节版）。改完必须用 `write_file` 整文件覆盖确认，并删除 `__pycache__/*.pyc` 防止旧字节码运行。验证方式是直接 `importlib.util.spec_from_file_location` 导入磁盘真实文件跑断言，而非依赖内存态。
- **⚠️ 重跑 `add-portal.py` 后会重新引入中英间距**：脚本重写 `article_human.md` 的传送门块时可能带入空格，导致 preflight 的「中英间距」FAIL。重跑 portal 后**必须再跑一次 `text-format.py`**，然后**再跑一次 `preflight-check.py`** 确认全绿，才推送。顺序：写正文 → text-format(1) → humanize → text-format(2) → add-portal → **text-format(3)** → preflight → 推送。

#### 4d-i-fallback. 传送门脚本失败的手动注入

当 `add-portal.py` 因结语纯文本格式（或其他原因）报错退出时，用以下步骤手动注入传送门：

1. **先跑一次脚本获取选文 HTML**：`add-portal.py` 即使最后报错退出，也会在 stderr/stdout 中输出完整的选文列表和生成的 HTML 片段。从输出中复制 `<span>【传送门】<br>...` 到 `</span>` 之间的全部内容
2. **定位插入位置**：在 `article_human.md` 中找到 `**原文：https://...**` 行和参考区 `<span>` 之间的空白区域
3. **注入传送门 HTML**：用 `execute_code` 中的原生 Python `open()` + `read()` + `write()`（不要用 `read_file` → 它返回行号格式）。将传送门 `<span>` 块插入在 `**原文：**` 行之后、`---` 分割线之前。执行后验证：`grep '传送门' article_human.md` 返回 1 行匹配
4. **推前验证**：`grep 'xxxx' article_human.md` 返回 0（无占位符残留）
- **⚠️ 结语纯文本格式时 `add-portal.py` 会失败**：当结语使用纯文本格式（`**结语**`）而非旧版 `<div>` 卡片时，脚本搜索 `<div style="background:#f5f0eb;...` 找不到，报 `找不到结语卡片结束位置` 并退出。此时手动注入传送门 HTML：先跑 `add-portal.py` 获取其输出中的选文列表和生成的 HTML（输出中包含完整片段但以错误码退出）→ 复制 HTML 片段 → 用 `execute_code` 或 `write_file` 在 `article_human.md` 的 `**原文：**` 行与参考区 `<span>` 之间插入传送门 HTML。见本 SKILL.md 下方「传送门脚本失败的手动 fallback」段落。

更新 progress.md：由脚本自动完成（无需手动调用）

#### 4e. 写参考区

|**格式（铁律）：**
```
---
<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：

https://example.com/article</span>
```

**所有来源统一放裸 URL，包括 X。** 不使用标题文字，不使用可点击 `<a>` 标签。

**⚠️ 微信标题长度限制：** 微信 API 对 `--title` 参数有长度限制，过长的标题会返回 `45003 title size out of limit`。标题应控制在 30 字以内，避免使用过长的副标题式标题。
- 推送前可用 `echo -n "$TITLE" | wc -c` 检查长度
- 如果收到 45003，缩短标题后重试即可（草稿不会因此丢失）
- 推荐标题结构：核心信息 + 一个吸引点，不超过一句话

**参考区格式（铁律，单行）：**
- 所有来源放裸 URL，**不用 `<a>` 标签**（微信正文不支持可点击链接）
- **参考区必须是单行 HTML**。`<span>` 内换行会被 md-to-wechat 渲染为 `<br>`，裸 URL+`<br>` 叠加触发微信 API 45166
- 格式：`<span style="font-size:12px;color:#888888;font-family:'Courier New',monospace;">参考：URL1，URL2</span>`
- 多来源时「参考：」只出现 1 次，所有 URL 放在同一个 `<span>` 内，**用中文逗号 `，` 分隔**。不要用 `<br>` 分行，不要写多行
- font-family 用等宽字体 `'Courier New',monospace` 与正文区分
- **主来源 URL 放在最前面**（如 arXiv 页面），后续补充来源用逗号追加
- 论文/引用来源只放 arXiv/OpenReview 等主页面 URL，不放引用字符串
- 续篇/前作引用在参考区加 `上篇：https://mp.weixin.qq.com/s/...`

**正文中引用链接时：** 用反引号包裹 URL（`URL`），渲染为 `<code>` 标签。**禁止裸 URL**——md-to-wechat 会生成破损 `<a>` 标签且中文标点被吞进 href，导致 45166。


更新 progress.md：由脚本自动完成（无需手动调用）

### Step 4f：去 AI 痕迹润色（Humanize-zh）⏱ 1-2min

**🚨 铁律：此步骤绝对不可跳过。** 无论什么原因——时间紧、文章短、中文原文——都必须执行。这是硬闸门。

**默认路径：手动 humanize（不走 delegate_task subagent）。** subagent 在 deepseek-v4-flash 下极易卡死（2-5 分钟不返回），父 session 空等。手动模式 1-2 分钟完成，立即进入下一项。

#### 手动 humanize 流程

1. `cp article.md article.md.bak` + `cp article.md article_human.md`
2. 用 `terminal` 或 `execute_code` 中的原生 `open()` 直接读取文件（**不要用 `read_file`**，它返回带行号的格式）
3. 检查高频 AI 模式（按优先级）：
   - **模式 13：破折号** — `grep -cP '——|—'`，逐处替换为 `：` 或 `，` 或 `。`
     ⚠️ **注意：不要误伤 `Step N — label` 和 `Stage N — label` 结构**。当正文使用 `Step 1 — xxx` 或 `Stage 2 — yyy` 这类编号+分隔符结构时，其中的独立 en dash `—` 不属于"破折号"语义，而是结构化列表分隔符。如果这些出现在正文中，humanize 时先跳过（保留原样），等 text-format.py 运行后 preflight 仍报错时再手动判断替换。
     判断标准：`—` 前后是结构编号（Step/Stage/第N步/Phase N）和标题/说明文字 → 属于分隔符，可保留为 `：` 或改为中文冒号；`—` 前后是完整句子成分 → 属于破折号，必须替换。
   - **模式 7：AI 词汇** — `标志着`→删, `至关重要`→删, `此外`→删, `值得注意的是`→删
   - **模式 23：过度限定** — `非常`/`极其`/`相当` → 删或替换
   - **模式 1：夸大意义** — `本质上`/`本质上来说` → 删
   - **模式 22：填充短语** — `总的来说`/`值得注意的是` → 删
   - **模式 9：否定排比** — `不仅...而且...` → 拆分短句
4. 所有修改在内存中做完，一次 `write_file` 全部写回
5. 重新扫描确认破折号 = 0 且覆盖率下降 < 2%
6. 用 `diff article.md article_human.md | head -20` 确认有实际改动
7. 如果手动扫描后发现改动 > 15 处或需大段重写，可改用 `delegate_task` 走 subagent（仅此情况）

#### 再生模式快速 humanize（已有文章的重做）

再生模式下，文章通常已经经过 humanize 且干净度较高。走快速路径：

1. `diff article.md article_human.md | head -40` — 检查文章原先的干净度
2. **如果原 humanize 改动 < 5 处**（说明文章本来就干净）：只扫 3 个高频模式（破折号、`极其`/`非常`、`不仅...而且`），修复后直接通过
3. **如果原 humanize 改动 ≥ 5 处**（说明文章有 AI 痕迹）：走完整手动 humanize 流程
4. 不需要预审 diff 是否足够「大」——干净文章就是少改动，不强行凑改动字数

#### preflight「humanize 差异微小」假阳性处理

preflight-check 报告 `[FAIL] Humanize 差异微小` 时：

- **先用 `diff article.md article_human.md` 看实际差异**。如果改动是实质性修复（去 AI 词汇、破折号替换等），即使字符数 < 50 也可以跳过此 FAIL
- **如果 diff 无差异**（空 diff），说明 humanize 没执行，才需要回头补做
- **常见假阳性场景**：原文本身干净（技术翻译、新闻简报类），humanize 只做了 2-3 处精准修复。此时不改文章质量，直接跳过 FAIL 继续推送

#### subagent 模式（仅当手动模式不够时）

仅当文章 > 3000 字且 humanizer 规则发现 15+ 处需修复时才使用此路径：

```python
from hermes_tools import delegate_task
delegate_task(
    goal="对公众号文章进行去 AI 痕迹润色（humanize-zh）",
    context=f"""
文件路径：D:\\\06_Hermes\\\articles\\\<article-name>\\\article_human.md
...
""",
    toolsets=["skills", "file"],
)
```

启动 subagent 后立即做其他工作。**只检查 1 次哨兵文件**。不存在则当 subagent 失败处理，走手动模式收尾。**永远不轮询。**

#### 最终产出约定

- 推送用 `article_human.md`
- `article.md` 保留原始版供对比
- 如果在推送前发现 humanize 改动有问题，从 `article.md` 重新 cp


更新 progress.md：由脚本自动完成（无需手动调用）

### Step 4g：文本格式统一修复 ⏱ 30s

**🚨 铁律：此步骤不可跳过。** 模型在写正文时默认会在中英文/数字间加空格（如`月费 $62,000`），破折号也可能遗漏。即使 Step 4c 已注意格式，也必须执行此步兜底。

统一脚本 `text-format.py` 覆盖三项修复：
| 功能 | 原独立脚本 | 说明 |
|------|----------|------|
| 中英间距去空格 | ~~format-cn-spacing.py~~ | 中文与英文/数字之间的空格 |
| 破折号替换 | ~~remove-dashes.py~~ | em dash (——) → 中文冒号（：） |
| 图片完整性检查 | ~~verify-images.py~~ | 正文引用的图片文件是否存在于目录 |

**每次运行都会自动处理 article.md + article_human.md 两个文件。**

#### 第1次：写在正文后执行（4c → 4g第1次）

在写完正文（含要点速览、结语、参考区）后立即执行：

```bash
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/text-format.py" \
  "D:\\\\06_Hermes\\\\articles\\\\<article-name>"
```

预期输出应显示"无需修复"或少量修复。**如果有图片缺失报错，必须回头补下载再继续。**

#### 第2次：Humanize 后执行（4f → 4g第2次）

Humanize（Step 4f）可能重新引入破折号或空格，所以 humanize 完成后必须再跑一次 text-format.py：

```bash
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/text-format.py" \
  "D:\\\\06_Hermes\\\\articles\\\\<article-name>"
```

**验证：** 输出必须显示"无需修复"或"修复完成"且无 ❌ 错误。破折号和空格问题在 humanize 后仍可能残留——这一步是推送前最后一次格式兜底。

⚠️ **已知 gap：text-format.py 的破折号替换比 preflight-check.py 的检测窄。** text-format.py 主要处理中文 em dash（——）和常见中文 en dash 模式（`—`后跟中文/空格）。结构化编号列表（如 `1. **Item** — description`）中的独立英文 en dash `—`，不会被 text-format.py 的 regex 命中，但会被 Step 5 的 preflight-check 标记为 `[FAIL] 无破折号（当前 N 处）`。如果 preflight-check 报破折号失败且 text-format.py 已运行过，用 `grep -nP '——|—'` 定位，检查是否是列表项中的独立 `—`，手动替换为中文冒号 `：`。

#### 干跑预览模式

如果只想看问题不修改，加 `--check` 参数：
```bash
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/text-format.py" \
  "D:\\06_Hermes\\articles\\<article-name>" --check
```

---


更新 progress.md：由脚本自动完成（无需手动调用）

### Step 5：预发布检查清单（硬闸门）⏱ 2-3min

**🚩 覆盖率检查（信息指标，不阻断推送）**

在推送前，可运行以下自动化检查查看覆盖率。优先使用一键检查脚本：

```bash
# 一键预发布检查（自动先跑 text-format 修复格式，再跑全部检查）
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/preflight-check.py" \
  "D:\\06_Hermes\\articles\\<article-name>" --fix

# 如果仍有 FAIL（非覆盖率），根据提示手动修复后重跑（不加 --fix 避免重复修复）
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/preflight-check.py" \
  "D:\\06_Hermes\\articles\\<article-name>"
```

或单独运行覆盖率检查（已弃用 inline Python，统一使用脚本）：

```bash
# 覆盖率已由 preflight-check.py 自动计算，不必手动跑
# 如果仍需单独看覆盖率百分比：
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/preflight-check.py" \
  "D:\\06_Hermes\\articles\\<article-name>" --json | python -c "import json,sys; d=json.load(sys.stdin); print(f'覆盖率: {[c for c in d[\"checks\"] if \"覆盖率\" in c[\"check\"]][0].get(\"coverage_pct\")}')"
```

**覆盖率仅为信息指标，不强制要求达标，也不阻断推送。**

- **同一语言**（如中文→中文转写、英文→英文摘要）：覆盖率仅供参考，低覆盖率不强制退回补充。
- **跨语言翻译**（如英文→中文）：中文信息密度高，相同内容字符数只有英文的 15-25%，覆盖率天然偏低，属正常现象。
- **多源合成/综述文章**（非逐段翻译，而是从多个来源提炼叙事）：覆盖率通常落在 50-65%，属正常范围。

**可选自检（不做强制要求）：** 若想确认内容完整性，可对比 `full_translation.md` 的每个章节/段落是否在 `article.md` 中有对应翻译段落。这仅作为质量参考，不达标也不阻断推送。

注意：`full_translation.md` 是纯文本翻译，不包含 markdown 图片标签 `![...](...)`，计算覆盖率时应按 pure text 长度比较。

**覆盖率低时的排查（仅建议，非强制）：**

不要一次加一两个字逐步逼近 70%——这需要 10+ 轮迭代，效率极低。正确做法：

1. **先做段落数对比**：比较 `full_translation.md` 的段落数（按空行分割）和 article.md 正文段落数。如果 article 的段落数远少于 full_translation，问题是大段内容缺失，不是措辞差异
2. **找最大的 3-5 个缺失块**：遍历 full_translation 的每一段，用前 20 个字符在 article.md 正文中搜索，标记未匹配的段落
3. **每次加一整段，不是一句话**：每个补丁应增加 100-500 字符（一整段原文内容），不是 5-30 字符的小修小补
4. **2-3 轮大型补丁解决**：目标是在 2-3 轮 patch 内达标。如果一轮不够，检查是否跳过了大段内容
5. **重新运行覆盖率检查**，不要手工估算

常见低覆盖率原因（优先检查）：
- 原文开头段落被省略（"XX发了一篇长文"型开头已避，但直接省略了原文开头的 hook 段）
- 原文的代码块/列表被完全跳过（代码块在 full_translation 中算字符，在 article.md 中如果省略则大幅拉低覆盖率）
- 原文的自荐/推广段落（"作者在另一篇文章中说…"、"想了解更多请关注…"）被误判为不相关而省略——保留，算在覆盖率内
- 原文的总结/TLDR 段落被大幅缩短

> 以上仅为排查参考。覆盖率不强制达标，不阻断推送。

**在推送之前，必须先跑一条自动化验证，确认正文没有被 frontmatter 吞掉。这条验证不可跳过，因为 `---` 开头的 bug 已连续出现 3 次：**

```bash
# 验证 article.md 开头不是 ---（否则正文会被吞）
head -1 "D:\\06_Hermes\\articles\\<article-name>\\article.md" | grep -q "^\\-\\-\\-$" && echo "❌ 第一行是 ---，必须移除！" || echo "✅ 开头正确"
```

如果输出 `❌ 第一行是 ---`，**立即修复（删掉文件开头的 `---` 和紧随的空行），不要继续推送。** 不执行此步直接推送，正文为空几乎必然发生。

**推送前执行 `"$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/preflight-check.py"`（自动覆盖以上全部检查）：**
```bash
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/preflight-check.py" "D:\\06_Hermes\\articles\\<article-name>"
```

**⚠️ 引用块样式检查（已在 preflight-check.py v2.3.0 自动化）：**
- preflight 自动扫描 `^>` markdown 引用块语法，计数 > 0 则报 FAIL
- 必须全部替换为 HTML `<div>` 容器后再推送
- 手动验证（preflight 不可用时）：`grep -c '^>' article_human.md`

如果以上任何检查输出 `❌`，**必须修复后再推送。**

然后加载并逐项核对 checklist：

```
skill_view(name='wechat-article-sop', file_path='references/checklist.md')
```

**逐项打勾，有一项不通过就不推送。**


更新 progress.md：由脚本自动完成（无需手动调用）

### Step 6：推送草稿 ⏱ 1-3min

#### 6a. 前置检查：技能完整性

在调用 wechat-api.ts 之前，先检查 baoyu-post-to-wechat 技能脚本是否存在：

**Linux / WSL：**
```bash
ls ~/.hermes/skills/baoyu-post-to-wechat/scripts/wechat-api.ts 2>/dev/null
```

**Windows：**
```bash
ls "$LOCALAPPDATA/hermes/skills/baoyu-post-to-wechat/scripts/wechat-api.ts" 2>/dev/null
# 或直接路径
ls "/c/Users/<user>/AppData/Local/hermes/skills/baoyu-post-to-wechat/scripts/wechat-api.ts"
```

如果脚本不存在（`No such file or directory`），**不要写 Python 替代脚本**。直接重装技能：

1. `hermes skills install skills-sh/jimliu/baoyu-post-to-wechat --force --yes`
2. `cd <skill_scripts_dir> && bun install`（Windows 下用 `npm install` 兜底）

装好后再执行发布命令。如果后续推送报 `Cannot find module`（如 `@jsquash/webp`），说明 node_modules 缺失，需要 `cd $LOCALAPPDATA/hermes/skills/baoyu-post-to-wechat/scripts && npx -y bun install`。

**⚠️ wechat-http.ts 的 Google DoH 在中国不可用：** `wechat-http.ts` 中用 `curl -s --noproxy '*' 'https://dns.google/resolve?...'` 做 DNS 绕过。但 Google DNS（dns.google）在中国被防火长城阻断，该调用会在 5 秒后静默超时，回退到原始 URL。这不影响功能（回退后正常请求），但会导致控制台无 `[wechat-http] DOH resolved` 日志输出——见到这个缺失是正常现象，不代表有问题。如果图片上传异常，可手动关闭 TUN 代理或直连 WeiXin API。

**⚠️ wechat-api.ts 报 `Missing WECHAT_APP_ID or WECHAT_APP_SECRET`：** 这是首次推送时常遇到的凭证缺失问题。wechat-api.ts 按以下优先级查找凭证：
1. 环境变量 `WECHAT_APP_ID` / `WECHAT_APP_SECRET`
2. `<cwd>/.baoyu-skills/.env`
3. `~/.baoyu-skills/.env`
4. EXTEND.md account config （`accounts[].app_id` / `accounts[].app_secret`）

推前先检查 `~/.baoyu-skills/.env` 是否存在且内容正确。如不存在，问用户要 AppID 和 AppSecret 并创建：
```bash
mkdir -p ~/.baoyu-skills
python -c "
import os
secret = '用户给的完整AppSecret'
content = 'WECHAT_APP_ID=用户AppID\\nWECHAT_APP_SECRET=*** + secret + '\\n'
path = os.path.expanduser('~/.baoyu-skills/.env')
os.makedirs(os.path.dirname(path), exist_ok=True)
with open(path, 'w') as f:
    f.write(content)
print('Credential file written')
"
```
注意：`~/.baoyu-skills/.env` 中不要用 bash heredoc 写，因为这可能被 bash 特殊字符影响导致内容截断。用 Python 写最安全。

**⚠️ wechat-api.ts 已知内部缺陷：** `replaceAllPlaceholders` 函数体可能为空（缺少实现体），导致 `npx tsx` 因 esbuild 语法检查失败。`npx -y bun` 因解析更宽松可直接通过。如果 `npx tsx` 报错 `Transform failed with 1 error` 且指向 wechat-api.ts 某行，先用 `patch` 工具补上函数体：

**⚠️ GIF 动图被转 JPEG 问题：** wechat-api.ts 将 `.gif` 列为不支持格式，自动转码为 JPEG 导致动画丢失。如需保留动画，见 `references/gif-upload-workaround.md`——分两步：先用静态 JPG 占位推送，再手动上传 GIF 到素材库替换。

```patch
function replaceAllPlaceholders(html: string, placeholder: string, replacement: string): string {
+  const escaped = placeholder.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
+  const regex = new RegExp(escaped, 'g');
+  return html.replace(regex, replacement);
+}
```

#### 6b. 发布命令

**草稿生命周期管理（关键规则）：**
1. **首次推送** — 不传 `--draft-media-id`，`draft/add` 创建新草稿
2. **记下 media_id** — 从推送成功输出的 `media_id` 字段中提取，**写入 `D:\06_Hermes\articles\<article-dir>\draft.id`**（仅一行 media_id）。不要只放在 memory 或 session 里——memory 有容量限制，session 翻不到
3. **默认规则：第二和后续本地修改推送，必须加 `--draft-media-id "$(cat draft.id)"`，调用 `draft/update` 覆盖已有草稿。** 每篇文章在微信后台只能有 1 个草稿。违反此规则将产生多个废弃草稿，微信 API 无删除草稿接口，废弃草稿 30 天后才自动过期。

   **📛 例外：resync（从服务端同步编辑）绝不传 `--draft-media-id`。** 当用户在 mp.weixin.qq.com 后台新增/修改了图片或文字后执行 resync 时，**必须新建草稿**（不传 `--draft-media-id`），否则本地旧版本会覆盖服务器端新编辑，导致「上次把我新编辑的都丢了」。

   **📛 例外2：format-only（只改格式不动图）绝不重新上传图片 — 这条规则 2026-07-07 被严重违反过，用户发火「图片被你弄丢了」。** 当用户要求「从服务器下载最新内容，只改格式不换图」时：① 下载 draft HTML → ② **保留所有 `img` 标签的 mmbiz.qpic.cn URL 原样不动**（wechat-api.ts 会自动跳过已有 CDN 地址） → ③ 只改外层卡片的 CSS 样式/结构 → ④ 推送此 HTML 文件（不走 markdown 模式，避免重新上传图片导致 URL 变更）。**重新上传图片 = 旧图丢失 = 用户发火。**
   
   **⚠️ resync 铁律 — 先检查再恢复：** 执行 `draft/get` 前必须先 `draft/batchget` 列出所有草稿，检查是否有 `imgs > 0` 的历史版本。如果最新草稿是你之前推的空白版本（`imgs = 0`），从历史有图版本恢复。**永远不要用 `draft/get` 只拉最新草稿就覆盖。**

**例外：用户明确要求新建草稿或标题/内容做了大幅重写时**，可以省略 `--draft-media-id` 新建草稿。推送后必须更新 `draft.id` 为新 media_id。判断标准：只修正格式/润色文字 → 覆盖；从服务器下载了大幅改写的内容、用户说「别覆盖推送个新的」→ 新建。
4. **前置检查（每次推送前必做）：** 检查 `draft.id` 是否存在。存在 → 必须传 `--draft-media-id`。不存在 → 首次推送，不传该参数。
5. **⚠️ 40007 失效恢复：** 如果 `--draft-media-id` 推送失败并返回 `40007 invalid media_id`，说明该 draft ID 已失效（多次更新后微信可能作废它）。此时只能去掉 `--draft-media-id` 新建草稿。重建后立刻更新 `draft.id`。同时更新 TASKS.md 中的 media_id 列。
6. 用户不会提醒你用覆盖模式——这是默认行为，不是例外
   if [ -f "D:\\06_Hermes\\articles\\<article-dir>\\draft.id" ]; then
     DRAFT_MEDIA_ID="--draft-media-id \"$(cat "D:\\06_Hermes\\articles\\<article-dir>\\draft.id")\""
     echo "覆盖推送，media_id: $(cat "D:\\06_Hermes\\articles\\<article-dir>\\draft.id")"
   else
     DRAFT_MEDIA_ID=""
     echo "首次推送，新建草稿"
   fi
   ```
5. 用户不会提醒你用覆盖模式——这是默认行为，不是例外

**首次推送后，从输出中提取 media_id 并写入文件：**
```bash
# 首次推送成功后，从输出末尾提取 media_id
# 输出中会有 "media_id": "xxx..."，复制 xxx 部分
echo "复制得到的media_id" > draft.id
```

**推送命令（直接调用 wechat-api.ts，禁止改 theme/color）：**

```bash
cd "D:/06_Hermes/articles/<article-dir>"
unset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy

if [ -f draft.id ]; then
  npx -y bun "$LOCALAPPDATA/hermes/skills/baoyu-post-to-wechat/scripts/wechat-api.ts" article_human.md \
    --theme default \
    --title "文章标题" \
    --author "AI圈的9527" \
    --cover cover.png \
    --no-cite \
    --draft-media-id "$(cat draft.id)" 2>&1
else
  npx -y bun "$LOCALAPPDATA/hermes/skills/baoyu-post-to-wechat/scripts/wechat-api.ts" article_human.md \
    --theme default \
    --title "文章标题" \
    --author "AI圈的9527" \
    --cover cover.png \
    --no-cite 2>&1
fi
```

**🚫 铁律：`--theme` 必须为 `default`，不加 `--color`。** 任何其他 theme（grace、modern 等）或 color 参数会改变标题颜色和背景，不允许使用。这条铁律不可违反。

首次推送成功后，记下输出的 `media_id`，写入 `D:/06_Hermes/articles/<article-dir>/draft.id`。

**⚠️ 必须用 `npx -y bun`，不能用 `npx tsx`：** wechat-api.ts 内部 import 了其他 `.ts` 文件（如 `md-to-wechat.ts`），`npx tsx` 解析不了嵌套的 ts import，会报 `ERR_UNKNOWN_FILE_EXTENSION`。`npx -y bun` 解析更宽松，可直接运行。

**说明：**\n- Linux 优先用本地 `bun`；Windows 上 `npx -y bun` 实测可用（会自动下载 bun 缓存到 npm-cache）\n- `wechat-api.ts` 会自动走 WeChat API（不走代理），依赖公众号 IP 白名单\n- `--title` 必须显式传入，wechat-api.ts 不解析 YAML frontmatter 的 title\n- 更新已有草稿：加 `--draft-media-id <media_id>`，调用 `draft/update` API 覆盖，不新建草稿\n\n**⚠️ 前台推送超时陷阱（大文章）：** 正文图片 ≥ 10 张或 body 文本 ≥ 15K 字符时，前台 `npx -y bun wechat-api.ts` 可能因图片上传耗时超过 120s 而 timeout。此时改为 background 模式 + `notify_on_complete=true` 运行，timeout 设 300s：\n```bash\ncd \"D:\\\\06_Hermes\\\\articles\\\\<article-dir>\"\nunset HTTP_PROXY HTTPS_PROXY http_proxy https_proxy\nterminal(background=true, notify_on_complete=true, timeout=300, command=\"npx -y bun '$LOCALAPPDATA/hermes/skills/baoyu-post-to-wechat/scripts/wechat-api.ts' article_human.md --theme default --title '标题' --author 'AI圈的9527' --cover cover.png --no-cite --draft-media-id \\\"\\$(cat draft.id)\\\"\") 2>&1\n```\n轻量文章（1-5 张图）仍用前台模式，更快反馈。

**⚠️ Windows 图片上传 "The system cannot find the file specified" 是良性报错：**
Windows git-bash 下 bun/npx 在 print 图片路径时可能报这个错，**不影响实际上传和发布**。检查输出末尾是否有 `"success": true` 和 `"media_id": "..."`，有就是成功了。

**🔥 铁律：推送途中绝对不要停下来分析这个报错。** 这个 DOH DNS 解析的 `execSync('curl ...')` stderr 错误已经在上百次成功推送中出现，纯属 Windows curl 路径问题（被 catch 后 fallback 到原始 URL）。看到它不等于上传失败。直接继续直到输出 `"success": true`。停下来分析 = 浪费时间 + 用户骂你傻逼。

**✅ 推送后验证 body 图片上传（防沉默失败）：**
```bash
python "$LOCALAPPDATA/hermes/skills/content-creation/wechat-article-sop/scripts/verify-draft-images.py" <media_id>
```
如果 `count` 少于正文应嵌入的图片数，说明确实有图片没传上去。用 Python 直调 `media/uploadimg` API 逐张补传，获取返回的 CDN URL 后替换 HTML 中的占位符，再用 `draft/update` 覆盖更新草稿。

**⚠️ 推送后 body 图片缺失 → 自己处理，不要告诉用户手动补充：** 如果推送后 body 图片没上传成功，**不要告诉用户"body 图片需手动补充"**。用户明确要求所有事都由你完成。正确做法：用 Python 直调微信 API 上传图片到素材库，获取 CDN URL 后替换文章 HTML 中的占位符，再通过 `draft/update` 更新草稿。上传脚本模板见 `references/cover-replacement.md`。

#### 6b-i. GIF 动画保留方案（wechat-api.ts 不支持）

wechat-api.ts 把 GIF 转成 JPEG（丢失动画）。保留动画的正确流程：

1. **上传 GIF 到微信素材库**（用 Python/curl 直调 API）：
完整方案见 `references/gif-upload-workaround.md` 和 `references/wechat-gif-embed.md`。

#### 6b-ii. 视频嵌入方案（wechat-api.ts 不支持）

完整方案见 `references/wechat-video-embed.md`（含上传 MP4、获取 mp_vid、iframe 嵌入、封面处理）。

**⚠️ `--title` 中的 `$` 符号陷阱：**
title 中如果包含 `$` 后跟数字（如 `$62,000` 或 `$7,800`），bash 在双引号内会把 `$6`、`$7` 解析为位置参数（为空），导致标题变成 `2,000` 和 `,800`。三种解决方式：
1. **不用 `$` 符号**：写"6万2"或"62,000美元"替代
2. **用反斜杠转义**：`--title "月费\$62,000"`（每个 `$` 前加 `\`）
3. **硬编码在变量中**：先 `TITLE='月费$62,000降到$7,800'` 再用 `--title "$TITLE"`（单引号赋值防止展开）
推荐方式 1，最不易出错。

#### 6c. IP 白名单问题处理

如果返回 `40164: invalid ip, not in whitelist`：

```bash
# 查当前出口 IP
curl -s https://api.ipify.org
# 查代理出口 IP
curl -s --proxy http://127.0.0.1:7890 https://api.ipify.org
```

- **两个 IP 可能不同**：直连 IP 和代理出口 IP 都要加白名单
- 用户操作：mp.weixin.qq.com → 设置 → 安全中心 → IP 白名单
- 加完后等 1-5 分钟（微信服务端缓存）
- 如果 IP 是动态宽带 IP，每次拨号都可能变 — 多个出口 IP 都要加

**个人订阅号 IP 白名单上限 10 个：** 如果列表超过 10 个，新添加的可能保存失败。（详见 `references/ip-whitelist-troubleshooting.md`）

```bash
# 用 Bun 检查 DNS 是否被劫持
bun -e "console.log(JSON.stringify(await Bun.dns.resolve('api.weixin.qq.com')))"
# 如果返回 198.18.0.x 说明被劫持
# 返回 198.18.0.x 说明被劫持 — 修复见 `references/mihomo-dns-hijack-fix.md`

最后兜底：`skill_view(name='wechat-article-sop', file_path='references/chrome-publish-fallback.md')`

#### 6d. 推送报告

推送成功后，输出结构化报告：

```
📮 推送报告
文章：<标题>
Media ID：<media_id>
图片数：<N> 张
覆盖率：<N>%（来自 Step 5）
Humanize 改动：<N> 处（主要模式：模式X、模式Y）
推送方式：<首次/覆盖>
推送时间：<YYYY-MM-DD HH:MM>
```

记入 `draft.id`（仅 media_id）和 `TASKS.md` 状态历史。

#### 6e. 更新已发表文章数据库（已废弃——用户手动维护）

> `published_articles.json` 由用户手动维护，推送后不自动追加。该文件为只读来源，仅用于 `add-portal.py` 脚本读取代选文。
>

#### 6f. 添加传送门（可选）

> 已弃用，所有传送门生成由 `add-portal.py` 在 Step 4d-i 处理。这里不再做。

更新 progress.md：由脚本自动完成（无需手动调用）

### Step 7（可选）：嵌入视频到文章 ⏱ 5-10min

如果原文包含视频且用户要求嵌入，wechat-api.ts 不支持视频上传。需在 Step 6 推送第一版草稿后，手动通过微信 API 上传视频 + 更新草稿。

详见 `references/wechat-video-embed.md`。

**⚠️ GIF 动图处理：** wechat-api.ts 自动将 GIF 转为 JPEG，动画丢失。如需保留动画，手动上传 GIF 到微信素材库后通过 draft/update 替换 URL。详见 `references/wechat-gif-embed.md`。

**流程概要：**
1. 用 `material/add_material?type=video` 上传视频到素材库
2. 用 `material/get_material` 获取视频 CDN URL 和 `mp_vid`
3. 上传截图作为 poster 封面
4. 在文章 HTML 中插入 `<iframe class="video_iframe rich_pages">` 标签（`data-src` 指向 `mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl&action=mpvideo&vid=wxv_xxx`）
5. 用 `draft/update` API 更新草稿（手动构造 payload）

---



更新 progress.md：由脚本自动完成（无需手动调用）

## 补充技巧

### 左右对比排版（With/Without 对比文章）

当原文包含大量"有记忆 vs 无记忆""旧方案 vs 新方案""A vs B"等对比内容时，**不要写成上下分段结构**。

必须使用 HTML 侧边对照表格，每侧有独立滚动条，手机端横向可滑：

```
skill_view(name='wechat-article-sop', file_path='references/side-by-side-comparison.md')
```

**铁律：**
- 两侧必须有相同的问题/输入，对比是"相同输入下不同输出"
- 内容保留原文细节，不缩写不概括（SKU 编号、营业时间、日计划等不能省略），fidelity ≥ 80%
- 所有原文图片嵌入 `<td>` 内部的原始位置（不攒末尾，不放表格下方）
- 总结句放在独立 `<tr>` 行（不在滚动框内），`border-top:none` + `background:#f9f9f9` 灰色斜体小字
- 滚动条用 `overflow-y:scroll`（不是 auto）。**不要在文章里加 `<style> 块**——md-to-wechat 会过滤掉所有 `<style>` 标签，`::-webkit-scrollbar` 伪元素无法生效。
- **强制滚动条默认可见**（Chrome 121+ Windows）：在 scrollable `<div>` 的 inline style 上加 `scrollbar-color:#bbb #f1f1f1;scrollbar-width:auto`。`scrollbar-color` 声明后会触发 Chrome 从 overlay 滚动条切换到经典常驻滚动条。这是 inline style，不被 md-to-wechat 过滤。
- **overflow 永远放在内层 `<div>` 上，不要放 `<td>` 上**：给 `<td>` 加 `display:block;overflow-y:scroll` 会破坏 table 布局（两列变上下叠放）。内层 `<div>` 接 overflow 是唯一可行的方案。
- **用户问题和 AI 回答用不同背景色区分**：用户问题 `#edf2f7` 浅蓝灰卡片 + 蓝色左边框，AI 回答 `#f9f9f9` 浅灰卡片（详见 side-by-side-comparison.md 第 3 节）。AI 回答的 `</div>` 必须包在 scrollable div 内。

参考文件包含完整 HTML 模板和参数说明。

---

### 将原文图片表格转为中文文本表格

当用户要求"用中文整理表格中的内容"时，使用 OCR 提取原文表格图片中的文字，转为 markdown 表格：

```
skill_view(name='wechat-article-sop', file_path='references/ocr-table-extraction.md')
```

流程：下载原图 `name=orig` → tesseract OCR → 手动解析为 markdown 表格 → 保留原文图片作为视觉参考。

---

### arXiv 论文图片选择

下载全部图片，正文嵌入最重要的 **3-6 张**（主图 + 核心实验结果 + 关键机制图），附录补充图不嵌入。封面从论文主图选标志性图表。精简模式下附录补充图可省略（见 `📄 论文来源精简模式`）。

---

## 常见失败模式（每次写之前读一遍）

仅保留最高频条目。完整列表见 `references/failure-modes.md`。

| 失败模式 | 原因 | 预防 |
|----------|------|------|
| **📛 Format-Only 重建文章丢图（最高危！2026-07-07 新增）** | 用户说「从服务器下载最新内容只改格式」→ 下载 HTML 后用 markdown 重建文章 → 重新上传本地图片 → 旧 mmbiz.qpic.cn URL 全部丢失 → 用户发火「图片被你弄丢了」 | 走 Format-Only 子模式：保留下载 HTML 中所有 img src=mmbiz.qpic.cn 原样不动，只改卡片 CSS，直接推 HTML。绝不用 markdown 重建。 |\n| 图片下载了没嵌入正文 | Step 2 和 Step 4c 脱节 | 写一段就嵌一张。**写完后 `grep -c '!\\[.*\\](img' article.md` 验证，数字必须等于 `ls img*.jpg | wc -l`** |\n| **论文主架构图（Figure 1 / x1.png / figure1_chunked.png）未嵌入正文** | 写论文文章时主架构图只用来做封面，正文中没引用 | **论文主架构图必须嵌入正文「核心洞察」或引言后，不能只做封面。** 推前检查 `grep -c 'figure1\|x1\.png\|scaffold' article_human.md`，返回值必须 >= 1 |
| 开头提到了来源作者姓名/平台名称 | 惯性转述时引用原文来源 | 正文绝对不提原文作者姓名、社交账号或平台名称。所有归属只放参考区裸URL |
| 纯翻译转述，缺独立观点 | 没做 Step 4b | 先确定独立观点再动笔 |
| **图片/视频与章节不匹配** | 写正文时凭记忆分配图片位置 | **写正文前先列出图片→章节映射表，每嵌一张打 ✓** |
| GIF 动图被转 JPEG 动画丢失 | wechat-image-processor.ts 不支持 GIF | 分两步：先用 JPG 占位推送，再手动上传 GIF 替换（见 gif-upload-workaround.md） |
| **<strong>cdp-extract.py 报 405 但 CDP 实际可用</strong> | `cdp-extract.py` 用 HTTP 请求检测 CDP 但响应 405。`curl http://localhost:9222/json` 正常 | 不走脚本检测，用 `references/cdp-manual-extract.md` 的 Python websockets 手动连接提取 |\n| **X Article 独立页面空白（JS 不可用）** | CDP 无登录态时 `/i/article/` 页面无法渲染 React 组件 | 改走原始推文 URL 从 `document.body.innerText` 提取——文章内容在推文页中 inline 渲染 | | 网站使用相对路径 `/blog/images/x.jpg` 而非绝对 URL `https://domain/blog/images/x.jpg`，`img[src*="://"]` 过滤器匹不到 | Step 3 后紧跟兜底 all-imgs 查询。如果 abs=0 且 all>0，用第二轮的 URL 列表下载。CDP 会返回完整渲染后的 URL（含协议和域名），直接使用 |
| **18张图推送后只有前几张正确** | `WECHATIMGPH_1` 正则匹配到 `WECHATIMGPH_10` | 正则末尾加 `\b` 边界符（已修复在 wechat-api.ts line 462） |
| **后续修改又创建了新草稿（本地编辑）** | 忘了记下 `--draft-media-id`，每次都新建草稿 | 首次推送后立即保存 media_id，后续本地修改传 `--draft-media-id` 覆盖 |
| **📛 Resync 覆盖推送丢失服务端编辑（最高危）** | 用户说「上次把我新编辑的都丢了」——服务端新增图片/文字被本地旧版本覆盖 | resync 必须永远不传 `--draft-media-id`，新建草稿推送。旧草稿保留作为历史 |
| **再生模式/编辑模式漏图片（最高频用户投诉）** | 默认认为已有图片文件=完整，但原文可能新增/更换了图片（尤其是 X Article 的 thread 中新插入了推文配图），或者历史第一次推的文章本身就没抓图 | 再生模式必须在 Step 2 用 CDP Chrome 重新打开原文对比图片列表。`ls img*.* | wc -l` 和 CDP 返回值对比。不匹配时必须补下载，然后按章节嵌入 |
| **标题太"平"** | 只陈述事实，没提炼核心框架 | 标题要包含价值判断和冲突感，见 Step 4c 标题规则⑤ |
| 正文插入了个人评论 | 误以为正文可以掺独立观点 | 独立观点只放文末「结语」，正文必须忠于原文 |
| **中英文混排有空格** | 数字/英文与中文间误加空格 | 英文术语/数字与中文之间**不加空格**（月费$62,000 非 月费 $62,000）。Step 4g 的 text-format.py 会自动修复遗漏 |
| **memory 翻译成了「内存」** | Agent 记忆与计算机内存混淆 | Agent 语境下永远译为「记忆」，GPU/RAM 语境下用「内存」 |
| **Agent 被翻译成了中文** | 默认将英文术语翻译 | Agent 在 AI Agent 语境中绝对不翻译，保留英文大写 |
| **章节标题没用 `##` 格式** | 用了 `**加粗文字**` 而非 `## 标题`，md-to-wechat 不渲染蓝色背景框 | 章节标题必须用 `## 标题` markdown 语法（而非 `**加粗文字**`），md-to-wechat 自动渲染为居中加粗+深蓝色背景框。参考 `13_dynamo-html` 文章格式 |
| 参考区换行 + 裸 URL 触发 45166 | `<span>` 内换行被 md-to-wechat 渲染为 `<br>`，裸 URL 被自动包装为 `<a>`，两者叠加触发微信 content hint 校验 | 参考区 **必须单行**：`参考：URL` 写在同一行，无换行。或 `参考：` 后直接跟 URL<br>传送门 `<a>` 标签 `45166` 的根因：href 用了 64 字符 media_id 而非 22 字符短 slug（见 `references/portal-wechat-api-limitation.md`） |
| **传送门 `xxxx` 占位符残留 → 45166（新增）** | 写 article.md 时在传送门中放了 `href="/s/xxxx"` 占位符，md-to-wechat 渲染为非法链接，微信 API 拒绝 | Step 4d-i 必须在推送前用 `add-portal.py` 注入真实传送门。推送前 `grep 'xxxx' article_human.md` 验证为 0 |
| **published_articles.json 语法损坏 → 所有文章传送门全挂（2026-07 新增）** | 该手维护 JSON 数组任一处缺逗号/缺字段/引号不配对，导致 `add-portal.py` 在 `load_published()` 抛 `json.decoder.JSONDecodeError` 直接退出，当前及以后每篇文章都无法生成传送门 | 跑 `python -c "import json; json.load(open('published_articles.json',encoding='utf-8'))"` 定位报错行（如 `Expecting ',' delimiter: line 14 column 2`），补逗号/字段使 JSON 合法，复验 0 报错后重跑 add-portal。只读来源，只修语法、勿顺手改条目内容 |
| **用户说「服务器上编辑过」= 微信公众号草稿箱，不是外部服务器** | 惯性问服务器连接方式，用户纠正 | 公众号文章语境下「服务器」特指 mp.weixin.qq.com 草稿箱。直接走 `references/draft-sync-workflow.md` 的 API 拉取流程，不问 SSH/连接方式 |
| 正文裸 URL 被转为破损 `<a>` 标签 | md-to-wechat 自动生成 `<a>` 标签，中文标点被吞进 href | 正文中引用链接用反引号包裹 `URL`，渲染为 `<code>` 标签 |
| 检查清单通过后问用户要不要推送，或等待用户提醒才推送 | 错误插入确认环节；用户在推后被问「推送了吗」会生气 | Step 5 通过后**必须自动执行 Step 6**，SOP 是命令序列不是选择题。修改/补充文章内容后也是同样——改完立即推，不等用户说「推」。用户说「补充对比内容」意味着：补充完→立即推送。|
| **推送途中停下来问用户「要继续吗？」或分析良性报错** | 遇到 DOH curl stderr 或 tool call 超限截断后问用户能否继续/分析报错 | 不要停。遇到问题直接解决、工具超限就直接继续。`The system cannot find the file specified` 是已知良性 DOH 报错，上百次成功推送都有它。忽略，只看尾部 `"success": true`。用户说 wcsop 就是让你一条路跑到黑，中间不问「要不要推」「出错了怎么办」「能继续吗」。
| humanize-zh 被跳过 | 急于完成流程 | Step 4f 是推送前**硬闸门**，不可跳过。用户要求 humanize 后必须给改动报告 |
| Humanize subagent 假成功 | subagent 返回摘要但未修改文件 | 必须用 `diff` 验证有实际改动。空 diff → 回退到手动 humanize |
| **引用块用 `>` 导致丢失背景色和字体样式** | 用了 markdown `>` 语法，md-to-wechat 渲染为默认灰色竖线，与卡片样式割裂 | 引用块必须用 HTML `<div>` 容器，禁止 `>` 语法。推前 `grep -c '^>'` 验证为 0 |\n| **Humanizer 重复插入图片** | subagent 将其他章节的图片复制到错误的章节（如 img19 同时出现在 Engram 和 MoE 两个章节） | recovery 模式/Phase C 差异审查时用 `diff` 检查图片行是否出现重复（同一图片名出现 >1 次），而不仅是检查删除 |
| 再生模式中跳过 humanize-zh | 认为 article_human.md 已存在=已完成 | 再生模式中仍必须重新执行 humanize（新 SOP 规则可能更新了 AI 检测模式） |
| **TASKS.md 主表行未更新** | `update-tasks.py complete` 只追加状态历史，不修改主表行的状态列 | complete 后必须手动 patch 主表行（将 `📝 写作中` 改为 `✅ 已推送`），或直接在 patch 中用唯一上下文定位主表行 |
| **依赖记忆中的旧 SKILL.md 规则执行操作（v1.114→1.115 背景框格式反转）** | SKILL.md 版本更新后未重新读取全文，按记忆中已过时的 4d-ii 纯文本规则写了无背景框的文章 | 每次 `wcsop` 开始前，先检查 SKILL.md 的 version 字段，与记忆中版本号对比。不同则从头到尾读一遍 SKILL.md 再开始。特别留意 `要点速览`、`结语`、`封面` 的格式规则是否被修改过 |
| **SVG 渲染 PNG 模糊（scale=1 默认渲染）** | Playwright `page.screenshot()` 默认在容器 div 原始尺寸（~300px）渲染，输出 281×190 低清图 | 必须用 `scale=3`（见 `references/svg-hd-rendering.md`）将容器设为 900px 宽。关键参数：`w, h = 300 * scale, 105 * scale`。验证：`file output.png` 应显示 ~940px 宽，~24KB+ |
| **Todo 残留（最高频投诉）** | Step 完成但 tool call 超限截断，没来得及调用 todo | 每步完成后按「progress.md → todo-enforce.py → 立即 todo」顺序执行。被截断时下次 session 第一件事走 `references/todo-recovery.md` 清理 |
| **Humanize subagent 卡死不返回（最高频卡死原因）** | deepseek-v4-flash 模型下 subagent 2-5 分钟无返回 | 不走 delegate_task，走手动 humanize |
| **CDP websocket 客户端 403 Forbidden** | Chrome 126+ 默认拒绝来自非浏览器来源的 WebSocket 连接 | Chrome 启动参数加 `--remote-allow-origins=*`。重启所有 Chrome 进程后重新启动 |
| **websocket vs websockets：pip 装错包** | cdp-extract.py 用 `websockets`（async），`pip install websocket-client` 装的是 sync 包，名相似但不同。`from hermes_tools import terminal` 中 pip install 装的跟在哪个 venv 里 | venv 内 `pip install websockets`（带 s，async 版）。从执行环境统一：如果 `cdp-extract.py` 报 module missing，检查是否装了正确的包 |
| **X thread 提取漏掉自身回复** | 只提取了推文页面可见的 public replies，忽略了推文作者自己的回复串 | 用 CDP Chrome 打开主推文页面 → 慢速 scroll（6 次×600px，间隔 0.8s）加载全部 article → JavaScript querySelectorAll('article') 遍历每条自回复 → 按 @AnthropicAI 精确筛选。忽略 public replies |\n| **cdp-extract.py 抓到机翻中文当英文原文（英文来源文章）** | `cdp-extract.py` 对非中文推文默认返回 X 机翻中文（带「翻译自 英语」/「显示原文」），若直接当英文 baseline 写 `full_translation.md`，覆盖率会变成「中文比中文」且翻译基线被污染 | 提取文本搜「翻译自」/「Translated from」，命中即先点「显示原文」按钮切回英文，再抓 `article.innerText`。详见 Step 1 的「X 自动翻译陷阱」与 `references/x-tweet-browser-extraction.md` |\n| **execute_code 中 read_file→write_file 污染文件** | `read_file(path)['content']` 返回 LINE_NUM|CONTENT 格式，write_file 写回后文件被行号污染 | 用原生 Python `open()` 读文件，不做 read_file→write_file 的 round-trip |\n|| **正文缺原文章节（最高频结构问题）** | 翻译时把「动机/背景」压缩进引言段、认为「结语」卡片可替代原文「结论/未来工作」节、或直接跳过不翻译 | 写正文前先做 4c-0 结构对齐清单：提取原文章节树 → 对比 article.md 章节树 → 缺的直接补写。动机必须是独立节，结论/未来工作不能只放在结语卡片里 |
| **arXiv HTML 提取混入站点样板图（smiley/funder logo）** | `cdp-extract.py` 抓 `arxiv.org/html/<id>` 时，`_download_images.py` 会把 `arxiv.org/static/base/...` 下的站点样板（smileybones-small.svg、funders/simons-foundation.png、funders/schmidt-sciences.png）当成内容图列入，直接跑脚本会把表情图标/资助方 logo 当正文配图嵌入 | arXiv HTML 论文只下载 `arxiv.org/html/<id>/xN.png` 内容图；凡 `arxiv.org/static/` 域的 URL 一律丢弃，不进 `_download_images.py`。推前 `ls img*.png` 应等于正文章节图数，不含 static 样板 |
| **preflight 中英间距误报（表格行，含列名与单元格）** | preflight-check.py 的 CN-EN spacing regex 不排除表格行，`单 GPU`、`GPU 数量` 等列名，以及单元格内分数记法（`98 / 98`）、中文+数字单元格（`逐字的 12 字符`、`Opus 4.8 上`）等被标记为间距问题。text-format.py 跳过了表格故不修复 | 假阳性，表格行可安全跳过。验证：`execute_code` 跑相同 regex 确认只命中表格行即跳过并标注「表格内格式，假阳性」。⚠️ 循环阻断：text-format(3) 报「无需修复」但 preflight 仍 FAIL 中英间距 → 残留必为表格行，勿再跑 text-format，直接验证跳过 |
| **preflight-check 将手动 humanize 标记为失败** | preflight 的 humanize 检查阈值 50 字符对破折号修复型 humanize 过严 | preflight-check.py v2.0.2+ 已加入破折号修复加分（dash_fixes * 3），手动修复通过 |
| **preflight-check 报破折号失败但 text-format.py 已运行过** | text-format.py 的 dash regex 不覆盖结构化列表中的独立英文 en dash（`1. **Item** — description` 的 `—`） | preflight-check 报破折号失败时先 `grep -nP '——|—'` 定位，检查是否是列表项中的独立 `—`。手动替换为中文冒号 `：`，不要重复跑 text-format.py——它同样不会抓到这些 |
| **resync 后丢失用户手动编辑的配图（2026-07 新增）** | resync 时用 `draft/get` 拉到了自己刚推的空白版本（无图），覆盖了用户手动配图的旧草稿 | resync 必须先 `draft/batchget` 检查所有草稿列表，找到 `imgs > 0` 的那个。如果最新草稿 `imgs = 0` 而历史版本有图→从历史版本恢复。推送时永远不传 `--draft-media-id`（新建草稿）。推送后立即更新 `draft.id` 为新 media_id。 |
| **「只改格式」操作时替换了图片URL（2026-07 新增）** | 用户说「下载最新内容只改格式不换图」→ 下载草稿 HTML 后用自己的 markdown 重建文章并重新上传本地图片，旧图片的 mmbiz.qpic.cn URL 全部被替换 | 当用户明确要求「只改格式，内容不要改」时：① 下载 draft HTML → ② 提取所有 `<img src="...mmbiz.qpic.cn...">` 标签，**原样保留它们的 CDN URL** → ③ 只修改 CSS 样式/卡片包裹结构 → ④ 推送本地 HTML 文件（此时 wechat-api.ts 的 `uploadImagesInHtml` 正好跳过已有 CDN 地址的图片）。**绝不重新上传本地图片替换已有 CDN URL。** |
| **resync 后要点速览卡片内容在 card 外部（2026-07 新增）** | 从历史版本恢复的 HTML 中 card `<div>` 为空、内容 `<p>` 在 `</div></div>` 外 | 用 `html.find('line-height:1.75;\"')` 定位，提取整个 `<p>` 块移入 card 内，再将 card 关闭标签移到 `<hr` 之前。详见 `references/draft-sync-workflow.md` 的恢复流程。 |
| **以"假阳性""误报"为由跳过 preflight 检查结果** | preflight-check.py 是程序化硬检查，输出 `[FAIL]` 就是确凿的失败。用"文章太干净了/技术翻译不需要/图表页没有图是正常的"等理由跳过检查，导致文章带着问题推送 | preflight 所有 `[FAIL]` 必须先看 `references/preflight-false-positives.md` 确认是否属于已知误报类别。如果是已知假阳性（如：代码块间距、表格管道符空格、`@torch.compile` 等装饰器被当来源泄漏、跨语言翻译覆盖率），可以跳过并标注原因。如果不在已知列表里，必须逐一修复、重新检查通过后才推送 |
| **portal 脚本找不到参考区** | `add-portal.py` 用 `content.find('<span', content.find('参考：'))` 查找参考区，但当参考区 `<span>` 和文字在同一行时（`<span ...>参考：URL</span>`），`find('参考：')` 在 `<span` 位置之后，向前找 `<span` 找不到 | 2026-07-03 已修复 `scripts/add-portal.py`：从 `参考：` 位置往前 200 字符找最近的 `<span` |\n| **补充对比内容后忘记推送** | 用户说「补充和XX对比」，改完文章后等人提醒才推 | 编辑模式改完内容后立即自动推送。用户说「补充对比内容」= 改完->推。参考 `references/article-add-competitor-comparison.md` |
| **卡片内部多余空行导致留白过大** | write_file 时 LLM 在 HTML 标签间保留可读性空行，微信渲染引擎将空行转为额外边距（左侧/上方留白）| 要点速览/结语卡片的 `<div>` 标签之间必须无空行。写完后用 `head -1 article_human.md` 验证开头无空行，全文段落空行数控制在预期值 |\n| **full_translation.md 写成摘要而非逐句翻译（跨语言文章）** | 以为覆盖率 baseline 只需"大致内容匹配"，用概括性中文替代逐句翻译，导致 baseline 不可靠且推前降级为人工结构验证 | full_translation.md 必须是对照原文的**逐句完整翻译**（保真度 ≥ 90%），不是自己概括的"概述版"。每个章节、每个实验数据、每个引文的表述都必须精准保留。判断标准：用原文任意段落开头 15-20 字搜索，应在 full_translation.md 中找到对应的翻译段 |\n| **TASKS.md 膨胀到数百 MB（最高危数据损坏）** | `update-tasks.py` 的 `complete` 函数或手动 `patch replace_all=True` 反复追加同一表行，文件从 ~50KB 增长到 500MB+。`update-tasks.py` 此时报 `OSError: [Errno 22]` 无法写入 | **不要 patch TASKS.md 主表行。** 出现此症状时走 `references/tasks-md-corruption-recovery.md`：提取尾部有效的 `###` 历史段 → 重建干净的 TASKS.md → 恢复任务追踪 |
| **文章啰嗦、信息重复（用户要求「精简、技术侧重点、不要重复」）** | 初稿按全量翻译展开，背景段设问与第2段重复、结语第1条与背景/方法重复、玩具任务/定性演示展开成剧情、1-2行短节独立成章 | 写初稿即按「技术优先」克制：背景只点断层不讲故事；同信息只出现一次；结语只留原文没有的独立观点；短节并入相邻章；偏题内容压到1段。用户提精简要求时走「技术精简模式」变体（见编辑模式章节）重写 |
| **`_pending_portal_`/占位符泄漏进正文（手写 article.md + add-portal.py 高频坑）** | 手写 article.md 时在结语卡片内部写了 `_pending_portal_` 之类占位符，以为 add-portal.py 会替换它。但 add-portal.py 是在「结语卡片结束」与「参考区」之间**自动插入**传送门块，并不消费任何占位符，导致占位符原样留在正文、推到草稿里变成可见乱码 | 永远不要在 article.md 里写传送门占位符。`add-portal.py` 自行定位结语卡片边界注入。写完正文直接跑脚本即可，结语 div 内保持干净。推前 `grep '_pending_portal_\|xxxx' article_human.md` 必须为 0 |

## 文章重写规则（从用户反复纠正中提炼）

- **英文原文引用必须翻译为中文后插入正文。** 不要直接保留英文原文，也不要直接删掉。用户对这两种错误都发过火。
- **重写/修改文章时不得丢失已有的配图和内容段落。** 每次修改必须对照原始完整版，确保所有图片（hero-banner、infographic、quote、blog-header 等）和文本内容都保留。用户说「谁让你丢的」= 不可接受的错误。
- **Theme 选择直接影响背景色：** `--theme modern` 会为全文添加 `rgba(250,249,245)` 米灰底，用户明确不喜欢。推送公众号文章时用 `--theme grace` 或 `--theme default` 保持白底。
- **行业分析文章的内容结构规则：先讲行业全景，再深入具体公司。** 当文章主题是一家公司的新举措（如 Microsoft Frontier Company），但该举措属于更大的行业趋势的一部分（如 FDE 军备竞赛）时，正文结构应为：**先按时间线/故事线讲完所有玩家的动作（Anthropic→OpenAI→Amazon→Microsoft），再深入分析该公司的具体细节**。不要在正文第一段直接写"今天微软宣布……"然后后面再补行业背景。先让读者知道「发生了什么」再讲「意味着什么」。最开头一段必须是叙事性的行业全景。
- **正文中的原始官方引述/描述不能删除，必须翻译为中文保留。** 当用户或原文提供了特定的英文原句（如微软官网的 "Outcome-driven engineering runs on Microsoft's integrated enterprise-grade platform…"），这句话属于文章的关键内容，不能删掉。必须翻译为流畅的中文后保留在正文对应位置。规则：内容重组时，原文中有信息量的引述/描述要保留并翻译，而不是删掉——用户说「谁让你丢的」= 不可接受的错误。
- **重写文章时，先用 `cp article.md article.md.bak` 备份原始完整版，再逐段对比修改后的版本与原始版，确保没有「丢内容」。** 不能依靠记忆判断「上次有什么内容」。

## 技能维护

### 维护入口

| 文档 | 用途 |
|------|------|
| `CHANGELOG.md` | 版本变更记录，每次结构性更新后必须追加 |
| `references/skill-audit-workflow.md` | 完整维护流程：脚本提取、脚本合并、大精简模式、覆盖检查 |
| `references/article-git-watcher.md` | 自动 Git 版本控制基础设施（cron + watcher 脚本） |
| `references/todo-recovery.md` | Todo 同步恢复：tool call 超限截断后的标准处理流程 |
| **SKILL.md 自身** | 规则放对位置（生成>自动修复>检查），见 Step 4c 开头 |

### 编辑本 SKILL.md 的铁律（大文件 patch 陷阱）

本文件 1700+ 行，用 `patch` 修改时极易误伤相邻必需内容：

- **old_string 必须严格圈定目标块**，不要把相邻段落也包进去。一次想删「覆盖率硬性阈值」整段时，若 old_string 蔓延到下一句的「在推送之前，必须先跑一条自动化验证…」，会把真正的硬闸门（开头 `---` 验证）一起删掉。
- **patch 后立刻 grep/读 确认相邻必需内容没丢**（如开头的 `---` 验证、`[FAIL]` 闸门逻辑、preflight 调用处），并确认没有重复行。
- **大段改写优先用精确短锚点 + 多轮小 patch**，不要一次替换跨越多段的长 old_string。
- 改完用 `read_file` 重新读改动区段上下文，确认前后句连贯，再结束。

## 基础设施

### Article Git Watcher

常驻 Python 守护进程 `article-watcher.py` 每 60s 扫描 `D:\\\\06_Hermes\\\\articles\\\\`，自动 commit + push 文件变动。
- **启动方式**：Windows 用户登录时通过 `startup` 文件夹的 VBS 脚本自动拉起
- **不再使用 Hermes cron**（2026-07-04 迁移）
- **代理**：脚本内硬编码 `HTTP_PROXY`（独立 daemon 不依赖 Hermes 环境）
- 日志：`D:\\06_Hermes\\articles\\.watcher.log`

详见 `references/article-git-watcher.md`。

