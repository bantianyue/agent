#!/usr/bin/env python3
# 技术文章收藏 - 本地服务（SQLite 版）
# 数据存于同目录 candidate_articles.db；对外提供 /api/articles 的 GET(返回数组)/PUT(整体保存) 接口
# 用法：双击本文件，或终端 `python server.py`
# 浏览器打开 http://127.0.0.1:8765/文章.html
import http.server, socketserver, os, json, sqlite3

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(ROOT, "articles.db")
# 文章根目录（用于扫描 source.url 判断“已完成”）
ARTICLES_ROOT = r"D:\06_Hermes\articles"
SKIP_DIRS = {"__pycache__", "_src_tmp", "_tmp"}
# 兼容旧迁移：若存在 data.json 则导入
LEGACY_JSON = os.path.join(ROOT, "data.json")


def get_conn():
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA synchronous=FULL")
    # 候选文章：记录待生成公众号文章草稿的 URL
    conn.execute("""CREATE TABLE IF NOT EXISTS candidate_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pos INTEGER NOT NULL DEFAULT 0,
        title TEXT NOT NULL DEFAULT '',
        url TEXT NOT NULL UNIQUE,
        priority TEXT NOT NULL DEFAULT 'mid',
        done INTEGER NOT NULL DEFAULT 0,
        done_locked INTEGER NOT NULL DEFAULT 0,
        note TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT '未开始',
        created_at TEXT DEFAULT (datetime('now'))
    )""")
    # 状态字典：可用户自定义的状态列表
    conn.execute("""CREATE TABLE IF NOT EXISTS candidate_statuses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE
    )""")
    conn.execute("INSERT OR IGNORE INTO candidate_statuses (name) VALUES (?)", ("未开始",))
    conn.execute("INSERT OR IGNORE INTO candidate_statuses (name) VALUES (?)", ("完成",))
    conn.execute("INSERT OR IGNORE INTO candidate_statuses (name) VALUES (?)", ("失败",))
    # 已生成草稿的文章：含生成过程信息，预留扩展
    conn.execute("""CREATE TABLE IF NOT EXISTS article_drafts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL DEFAULT '',
        status TEXT NOT NULL DEFAULT 'pending',
        draft_media_id TEXT DEFAULT '',
        wechat_url TEXT DEFAULT '',
        error TEXT DEFAULT '',
        steps TEXT DEFAULT '[]',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""")
    return conn


def scan_done_urls():
    """扫描 ARTICLES_ROOT 下每个文章目录的 source.url，返回其中的 url 集合"""
    done = set()
    if not os.path.isdir(ARTICLES_ROOT):
        return done
    for name in os.listdir(ARTICLES_ROOT):
        d = os.path.join(ARTICLES_ROOT, name)
        if not os.path.isdir(d) or name in SKIP_DIRS:
            continue
        su = os.path.join(d, "source.url")
        if os.path.isfile(su):
            try:
                with open(su, "r", encoding="utf-8", errors="ignore") as f:
                    line = f.read().strip().splitlines()
                    if line:
                        done.add(line[0].strip())
            except Exception:
                pass
    return done


def migrate_from_json(conn):
    """首次运行：若库为空且存在旧 data.json，则导入（并扫描 done）"""
    cur = conn.execute("SELECT COUNT(*) FROM candidate_articles")
    if cur.fetchone()[0] > 0:
        return
    if not os.path.isfile(LEGACY_JSON):
        return
    try:
        with open(LEGACY_JSON, "r", encoding="utf-8") as f:
            arr = json.load(f)
    except Exception:
        return
    if not isinstance(arr, list):
        return
    done_set = scan_done_urls()
    seeded = False
    for i, a in enumerate(arr):
        url = a.get("url", "").strip()
        if not url:
            continue
        title = a.get("title", "") or ""
        priority = a.get("priority", "mid") or "mid"
        if "done" in a:
            done = 1 if a["done"] else 0
            locked = 1
        else:
            done = 1 if url in done_set else 0
            locked = 0 if done else 0
        try:
            conn.execute(
                "INSERT OR IGNORE INTO candidate_articles (pos,title,url,priority,done,done_locked,note,status) VALUES (?,?,?,?,?,?,?,?)",
                (i, title, url, priority, done, locked, "", "完成" if done else "未开始"),
            )
            seeded = True
        except Exception:
            pass
    if seeded:
        conn.commit()


def init_db():
    conn = get_conn()
    cur = conn.execute("SELECT COUNT(*) FROM candidate_articles")
    if cur.fetchone()[0] == 0:
        migrate_from_json(conn)
    # 首次扫描：对 done_locked=0 的记录，若其 url 命中 source.url 则置 done=1
    done_set = scan_done_urls()
    if done_set:
        conn.execute(
            "UPDATE candidate_articles SET done=1 WHERE done_locked=0 AND url IN ({})".format(
                ",".join("?" * len(done_set))
            ),
            tuple(done_set),
        )
    conn.commit()
    conn.close()


def load_articles():
    conn = get_conn()
    rows = conn.execute(
        "SELECT id,pos,title,url,priority,done,note,status FROM candidate_articles ORDER BY pos DESC"
    ).fetchall()
    conn.close()
    out = []
    for aid, pos, title, url, priority, done, note, status in rows:
        out.append({
            "id": aid,
            "pos": pos,
            "title": title,
            "url": url,
            "priority": priority,
            "done": bool(done),
            "note": note or "",
            "status": status or "未开始",
        })
    return out


def save_articles(arr):
    """整体替换：删除全部，按数组顺序（pos）重新插入。done 视为手动维护 -> done_locked=1"""
    conn = get_conn()
    try:
        conn.execute("BEGIN")
        conn.execute("DELETE FROM candidate_articles")
        for i, a in enumerate(arr):
            url = (a.get("url") or "").strip()
            if not url:
                continue
            title = a.get("title", "") or ""
            priority = a.get("priority", "mid") or "mid"
            done = 1 if a.get("done") else 0
            note = a.get("note", "") or ""
            status = a.get("status", "") or "未开始"
            conn.execute(
                "INSERT INTO candidate_articles (pos,title,url,priority,done,done_locked,note,status) VALUES (?,?,?,?,?,1,?,?)",
                (i, title, url, priority, done, note, status),
            )
        conn.execute("COMMIT")
    except Exception:
        conn.execute("ROLLBACK")
        raise
    finally:
        conn.close()


def res_json(handler, obj, code=200):
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def add_candidate(url, title="", priority="mid"):
    """新增一条候选文章：done=0（未完成），去重（url 已存在则返回已存在记录）"""
    url = (url or "").strip()
    if not url:
        return None, "url required"
    if priority not in ("high", "mid", "low"):
        priority = "mid"
    conn = get_conn()
    row = conn.execute(
        "SELECT id,pos,title,url,priority,done,note,status FROM candidate_articles WHERE url=?", (url,)
    ).fetchone()
    if row:
        conn.close()
        return {
            "id": row[0], "pos": row[1], "title": row[2],
            "url": row[3], "priority": row[4], "done": bool(row[5]),
            "note": row[6] or "", "status": row[7] or "未开始",
        }, "already exists"
    max_pos = conn.execute("SELECT COALESCE(MAX(pos),-1) FROM candidate_articles").fetchone()[0]
    conn.execute(
        "INSERT INTO candidate_articles (pos,title,url,priority,done,done_locked,note,status) VALUES (?,?,?,?,0,0,?,?)",
        (max_pos + 1, title or "", url, priority, "", "未开始"),
    )
    cid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.commit()
    conn.close()
    return {"id": cid, "pos": max_pos + 1, "title": title, "url": url, "priority": priority, "done": False, "note": "", "status": "未开始"}, "created"
    handler.send_response(code)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.end_headers()
    handler.wfile.write(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/Blog.html")
            self.end_headers()
            return
        if self.path == "/api/articles":
            res_json(self, load_articles())
            return
        if self.path == "/api/statuses":
            conn = get_conn()
            rows = conn.execute("SELECT name FROM candidate_statuses ORDER BY id").fetchall()
            conn.close()
            res_json(self, [r[0] for r in rows])
            return
        if self.path == "/scan":
            # 手动触发：仅对未锁定的记录按 source.url 刷新 done
            conn = get_conn()
            done_set = scan_done_urls()
            conn.execute(
                "UPDATE candidate_articles SET done=1 WHERE done_locked=0 AND url IN ({})".format(
                    ",".join("?" * len(done_set)) or "NULL"
                ),
                tuple(done_set),
            )
            conn.commit()
            conn.close()
            res_json(self, {"ok": True, "count": len(done_set)})
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_PUT(self):
        if self.path != "/api/articles":
            self.send_error(403, "Only /data.json writable")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            arr = json.loads(body.decode("utf-8"))
            if not isinstance(arr, list):
                raise ValueError("expected list")
        except Exception as e:
            self.send_error(400, f"Invalid JSON: {e}")
            return
        save_articles(arr)
        res_json(self, {"ok": True})

    def do_POST(self):
        if self.path == "/api/candidate":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("expected object")
            except Exception as e:
                self.send_error(400, f"Invalid JSON: {e}")
                return
            url = (data.get("url") or "").strip()
            if not url:
                res_json(self, {"ok": False, "error": "url required"}, 400)
                return
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            rec, status = add_candidate(url, data.get("title", "") or "", data.get("priority", "mid") or "mid")
            res_json(self, {"ok": True, "status": status, "record": rec}, 200)
            return
        if self.path == "/api/statuses":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body.decode("utf-8"))
                if not isinstance(data, dict):
                    raise ValueError("expected object")
            except Exception as e:
                self.send_error(400, f"Invalid JSON: {e}")
                return
            name = (data.get("name") or "").strip()
            if not name:
                res_json(self, {"ok": False, "error": "name required"}, 400)
                return
            old = (data.get("old") or "").strip()
            conn = get_conn()
            try:
                if old and old != name:
                    # 改名：先同步文章记录，再删旧名、插新名（避免 UNIQUE 冲突残留）
                    conn.execute("UPDATE candidate_articles SET status=? WHERE status=?", (name, old))
                    conn.execute("DELETE FROM candidate_statuses WHERE name=?", (old,))
                    conn.execute("INSERT OR IGNORE INTO candidate_statuses (name) VALUES (?)", (name,))
                else:
                    conn.execute("INSERT OR IGNORE INTO candidate_statuses (name) VALUES (?)", (name,))
                conn.commit()
            except Exception as e:
                conn.rollback()
                conn.close()
                res_json(self, {"ok": False, "error": str(e)}, 400)
                return
            conn.close()
            res_json(self, {"ok": True, "name": name}, 200)
            return
        self.send_error(404, "Not found")

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    os.chdir(ROOT)
    init_db()
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", PORT), Handler) as httpd:
        print(f"服务已启动： http://127.0.0.1:{PORT}/Blog.html")
        print("按 Ctrl+C 停止")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止")
