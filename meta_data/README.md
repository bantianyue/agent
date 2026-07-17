# meta_data — 技术文章收藏追踪器

本地文章候选库与草稿状态追踪服务。用于管理「待写成公众号文章」的候选 URL 队列，以及已生成草稿的文章过程信息。

前端页面名为 **Blog**（原 `文章.html` 已重命名为 `Blog.html`，访问 `/Blog.html`）。

---

## ⚠️ 用户铁律（改这个项目前必读，勿重复踩坑）

### 1. 数据绝对不能丢
- **禁止删除 `articles.db` 文件**（哪怕为了"从零重建干净库"也不行）。
- 加字段用 `ALTER TABLE ... ADD COLUMN`（在线迁移），**绝不**删库重建。
- 如果必须结构变更：先 `ALTER TABLE`，保留所有原数据行。
- 用户原话：「任何时候不能丢数据」「滚你妈的，任何时候不能丢数据」。
- 已发生过的错误：2026-07-17 调试时为重建干净库**误删了 articles.db**，
  虽用导出备份完整导回（45 条无丢失），但这是禁止行为，绝不再犯。

### 2. 页面布局铁律
- **每行所有字段必须横向一排从左到右排**（优先级 | 标题+URL | 状态 | 备注 | Run | 保存 | 复制 | 删除）。
- **禁止纵向堆叠 / 上下叠加**。用户原话：「一个文章的各字段往右排啊，都上下放 干你妈啊」。
- 列表整体可宽，但**不要上下滚动条**（`ul.list` 不加 `max-height` / `overflow-y`）。
- 行高要紧凑（参考原 `文章.html` 的 `padding:9px 12px; margin-bottom:7px`）。

### 3. 标题 / URL 列宽
- 标题和 URL 列宽限制为 **200px**（用 `max-width:200px` + `text-overflow:ellipsis` 截断）。
- 用户原话：「可以把标题和 url 调窄一些」→ 明确为 200px。

### 4. 配色
- **清爽浅色**（白卡片 / 浅灰蓝底 / 蓝紫强调色）。
- **禁止暗色主题**（深黑底白字那种）。
- 用户原话：「白底黑子太单调，难看」→ 改浅色；后又明确「不要暗色」。

### 5. 按钮图标规范
- **Run 按钮 = 执行图标**（▶ 播放三角 `<path d="M8 5v14l11-7z"/>`），**不是文字 "Run"**。
- **保存按钮 = 软盘图标**（💾 `<path d="M19 21H5..."/>`），**不是对勾 ✓**。
- 用户原话：「Run按钮用个执行的图标」「保存用保存的图标 不能用对勾」。

### 6. 排序 / 显示顺序铁律
- **列表默认按 id 倒序（新→旧）**，顶部必须是最新添加的文章。
- `pos` 字段**不可信**（历史重建/测试打乱过），排序真源用 **id**（自增 id 严格随添加时间递增）。
- 后端 `load_articles` 的 `ORDER BY` 必须是 **id DESC**。
- 前端 `sort==='time'` 排序必须按 **(b.id)-(a.id)**。
- 用户原话：「顶部不上我最新加的」→ 根因是之前按 pos 倒序，而新加的 pos 偏小被顶到底部。
- 注意：用户通过对话收藏的文章（如 LatentMoE id=318 / SWA id=317）可能 id 较小，
  排在更早收藏的 319~360 之后——这是**正确的时间顺序**，不是数据丢失。

### 7. 功能需求（已实现，勿回退）
- 每条文章有 **note（备注）字段**，默认空，可编辑。
- 每行有 **Run 按钮**：点击暂不做任何事（提示"Run 功能待实现"），功能后续接。
- "完成" checkbox **改为状态下拉框**（字段名 `status`），默认「未开始」，含「完成 / 失败 / 未开始」+ 用户自定义。
- 列表每行可编辑：**标题（contentEditable）、优先级、备注、状态**；其他字段（id/url/pos）不可改。
- 每行右侧有 **保存按钮（软盘图标）**，点击 PUT 整表落库。
- 状态可管理：工具栏「管理状态」按钮（prompt 输入 `/` 分隔的状态列表，支持新增 + 改名）。
- 改名状态时，已使用该状态的文章会被同步改掉（用户已确认 OK）。

---

## 功能

- **候选文章管理**：记录待生成公众号草稿的文章（标题 / URL / 优先级 / 状态 / 备注），支持增删改。
- **完成态自动判定**：扫描 `D:\06_Hermes\articles\<slug>\source.url`，若某候选 URL 命中已存在文章目录的 `source.url`，自动标记为「完成」（除非该记录被手动锁定）。
- **草稿过程追踪**：`article_drafts` 表记录每篇文章草稿的生成状态、微信 media_id、草稿链接、错误信息与步骤日志。
- **本地 Web 界面**：`Blog.html` 提供可视化操作面板。
- **HTTP API**：对外暴露 REST 接口，供脚本 / agent 程序化调用。

## 文件说明

| 文件 | 作用 |
|------|------|
| `server.py` | 本地 HTTP 服务（端口 8765），SQLite 读写 + 静态文件服务 + REST API |
| `articles.db` | **唯一真相源**（SQLite）。三张表：`candidate_articles`（候选）、`candidate_statuses`（状态字典）、`article_drafts`（草稿） |
| `Blog.html` | 前端操作面板，浏览器打开 `http://127.0.0.1:8765/Blog.html` |
| `start_server.bat` | 双击启动服务（最小化后台运行 Hermes venv 的 python） |
| `articles_backup.json` | ⚠️ 2026-07-17 误删库时的导出备份，**数据已导回，此文件可删**（但删库行为本身被禁止，见铁律 1） |
| `data.json` | ⚠️ 遗留文件，已不再使用。DB 初始化时若为空会一次性导入它，之后不再读取。后端 `/data.json` 虚拟路由名仍被前端使用，勿删路由代码 |
| `__pycache__/` | Python 缓存，忽略 |

## 数据表结构

### candidate_articles（候选文章）

| 字段 | 说明 |
|------|------|
| id | 自增主键（**排序真源**，ORDER BY id DESC） |
| pos | 排序位置（**不可信**，历史打乱过，勿用于排序） |
| title | 文章标题（可编辑） |
| url | 文章 URL（UNIQUE，去重键） |
| priority | 优先级：high / mid / low |
| done | 是否已生成草稿（0/1） |
| done_locked | 完成态是否被手动锁定 |
| note | 备注（可编辑，默认空） |
| status | 状态：未开始 / 完成 / 失败 / 自定义 |
| created_at | 创建时间，格式 `YYYY-MM-DD HH:MM:SS`，中国时区；首次创建时设为当前时间，之后永不变化 |
| updated_at | 修改时间，格式 `YYYY-MM-DD HH:MM:SS`，中国时区；每次保存更新为当前时间 |

### candidate_statuses（状态字典）

| 字段 | 说明 |
|------|------|
| id | 自增主键 |
| name | 状态名（UNIQUE） |

### article_drafts（已生成草稿）

| 字段 | 说明 |
|------|------|
| id | 自增主键 |
| url | 文章 URL（UNIQUE） |
| title | 标题 |
| status | 状态：pending / generating / done / error 等 |
| draft_media_id | 微信草稿 media_id |
| wechat_url | 草稿 / 发布链接 |
| error | 错误信息 |
| steps | 生成步骤日志（JSON 字符串） |
| created_at / updated_at | 时间戳 |

## 启动

双击 `start_server.bat`，或终端执行：

```bat
C:\Users\twfehh7\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe server.py
```

浏览器访问 `http://127.0.0.1:8765/Blog.html`。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` 或 `/index.html` | 重定向到 `Blog.html` |
| GET | `/api/articles` | 返回候选文章数组（按 id DESC） |
| PUT | `/api/articles` | 逐条 UPSERT 候选列表（按 id 存在则 UPDATE 保留 id/pos，否则 INSERT；done 视为手动锁定） |
| POST | `/api/candidate` | 新增一条候选（body: `{url, title?, priority?}`），自动去重 |
| GET | `/api/statuses` | 返回状态字典数组 |
| POST | `/api/statuses` | 新增/改名状态（body: `{name, old?}`）；改名时同步文章记录 |
| GET | `/scan` | 手动触发：按 `source.url` 刷新未锁定记录的完成态 |
| 任意 | `/*.html` / 静态文件 | 静态文件服务 |

> 注：前端以 `data.json` 作为逻辑接口名调用 GET/PUT，但后端实际读写的是 `articles.db`。

## 已踩坑记录（勿重复）

1. **WAL 多连接视图不一致**：原 `journal_mode=WAL` 导致服务端多连接/多线程读到旧快照。已改为 `DELETE` 模式（`get_conn` 设 `isolation_level=None` 手动事务）。
2. **`BEGIN` 嵌套事务错误**：`save_articles` 原 `conn.execute("BEGIN")` 在 sqlite3 默认事务下报 `cannot start a transaction within a transaction`。修复：设 `isolation_level=None` 后 BEGIN/COMMIT 合法。
3. **误删 articles.db**：2026-07-17 调试时删库重建，虽导回但属禁止行为。今后只用 ALTER TABLE 在线迁移。
4. **多个服务进程堆积**：反复 kill/重启时旧进程未死透，多个绑定 8765，curl 随机命中旧进程读到脏数据。改前先 `netstat -ano | grep :8765` 清掉所有残留 PID，确保只跑 1 个。
5. **保存重置所有 id**：`save_articles` 原 DELETE+全 INSERT 导致每次保存 id/pos 全变。已改为 UPSERT（按 id 存在则 UPDATE 否则 INSERT）。
6. **前端图标误用**：保存按钮原用对勾 ✓，Run 原用文字。已按铁律 5 改执行图标 / 软盘图标。
7. **行纵向堆叠**：原 `li.item` 内元素默认块级上下排。已用 `.row { display:flex }` 包一层横向排布。
8. **列表滚动条**：原 `ul.list` 加了 `max-height:62vh; overflow-y:auto`。已按铁律 2 去掉。
9. **时间字段需求全记录**（2026-07-17）：新增 `created_at` / `updated_at` 字段，
   - 格式 `YYYY-MM-DD HH:MM:SS`，中国时区（用 `datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")`）
   - 旧数据默认 `2026-07-17 00:00:00`
   - `created_at` 首次设当前时间后永不变化（INSERT 时写入，UPDATE 不碰它）
   - `updated_at` 每次保存（UPSERT 的 UPDATE 分支）设为当前时间
   - 前端：时间列放在状态与备注之间，上下紧凑显示（上面创建时间、下面修改时间），`width:140px` 对齐时间串长度
   - 备注列缩窄：`flex:0 1 64px; min-width:60px`
10. **前端布局更新务必写 README**：每次改前端/后端需求后必须同步更新 README.md，用户需求不要漏记（这次第 9 条就是漏补的）。
