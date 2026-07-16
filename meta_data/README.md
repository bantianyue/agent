# meta_data — 技术文章收藏追踪器

本地文章候选库与草稿状态追踪服务。用于管理「待写成公众号文章」的候选 URL 队列，以及已生成草稿的文章过程信息。

## 功能

- **候选文章管理**：记录待生成公众号草稿的文章（标题 / URL / 优先级 / 是否已完成），支持增删改与拖拽排序。
- **完成态自动判定**：扫描 `D:\06_Hermes\articles\<slug>\source.url`，若某候选 URL 命中已存在文章目录的 `source.url`，自动标记为「已完成」（除非该记录被手动锁定）。
- **草稿过程追踪**：`article_drafts` 表记录每篇文章草稿的生成状态、微信 media_id、草稿链接、错误信息与步骤日志，预留扩展字段。
- **本地 Web 界面**：`文章.html` 提供可视化操作面板（候选列表、新增、排序、标记完成）。
- **HTTP API**：对外暴露 REST 接口，供脚本 / agent 程序化调用（新增候选、整体保存、手动刷新完成态）。

## 文件说明

| 文件 | 作用 |
|------|------|
| `server.py` | 本地 HTTP 服务（端口 8765），SQLite 读写 + 静态文件服务 + REST API |
| `articles.db` | **唯一真相源**（SQLite）。两张表：`candidate_articles`（候选）、`article_drafts`（草稿） |
| `文章.html` | 前端操作面板，浏览器打开 `http://127.0.0.1:8765/文章.html` |
| `start_server.bat` | 双击启动服务（最小化后台运行 Hermes venv 的 python） |
| `data.json` | ⚠️ **遗留文件，已不再使用**。旧版纯 JSON 存储的残留；DB 初始化时若为空会一次性导入它，之后不再读取。磁盘上的内容已与 DB 不同步，可安全删除（但后端 `/data.json` 这个虚拟 API 路由名仍被前端使用，勿删路由代码） |
| `__pycache__/` | Python 缓存，忽略 |

## 数据表结构

### candidate_articles（候选文章）
| 字段 | 说明 |
|------|------|
| id | 自增主键 |
| pos | 排序位置（ORDER BY pos DESC） |
| title | 文章标题 |
| url | 文章 URL（UNIQUE，去重键） |
| priority | 优先级：high / mid / low |
| done | 是否已生成草稿（0/1） |
| done_locked | 完成态是否被手动锁定（锁定后不被自动扫描覆盖） |

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

浏览器访问 `http://127.0.0.1:8765/文章.html`。

## API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/` 或 `/index.html` | 重定向到 `文章.html` |
| GET | `/data.json` | 返回候选文章数组（从 SQLite 读取） |
| PUT | `/data.json` | 整体替换候选列表（写入 SQLite，`done` 视为手动锁定） |
| POST | `/api/candidate` | 新增一条候选（body: `{url, title?, priority?}`），自动去重 |
| GET | `/scan` | 手动触发：按 `source.url` 刷新未锁定记录的完成态 |
| 任意 | `/*.html` / 静态文件 | 静态文件服务 |

> 注：前端以 `data.json` 作为逻辑接口名调用 GET/PUT，但后端实际读写的是 `articles.db`，磁盘上的 `data.json` 文件不参与运行时数据流转。
