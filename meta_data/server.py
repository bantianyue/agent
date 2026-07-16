#!/usr/bin/env python3
# 技术文章收藏 - 本地服务
# 用法：双击本文件，或终端 `python server.py`
# 然后浏览器打开 http://127.0.0.1:8765/文章.html
import http.server, socketserver, os, sys, json

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))
# 文章根目录（用于扫描 source.url 判断“已完成”）
ARTICLES_ROOT = r"D:\06_Hermes\articles"
SKIP_DIRS = {"__pycache__", "_src_tmp", "_tmp"}

DATA_FILE = os.path.join(ROOT, "data.json")


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
                    url = f.read().strip().splitlines()
                    if url:
                        done.add(url[0].strip())
            except Exception:
                pass
    return done


def load_data():
    """读取 data.json；对缺失 done 字段的条目，用扫描结果初始化（手动维护优先）"""
    if not os.path.isfile(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        try:
            arr = json.load(f)
        except Exception:
            return []
    # 检查是否已有任意条目带 done 字段 —— 若整文件都没有，则首次扫描填充
    has_done_field = any("done" in a for a in arr)
    if not has_done_field:
        done_set = scan_done_urls()
        changed = False
        for a in arr:
            a.setdefault("priority", "mid")
            a["done"] = a.get("url", "") in done_set
            changed = True
        if changed:
            save_data(arr)
    else:
        # 已有 done 字段：仅给缺 priority 的补默认，不覆盖手动 done
        changed = False
        for a in arr:
            if "priority" not in a:
                a["priority"] = "mid"
                changed = True
        if changed:
            save_data(arr)
    return arr


def save_data(arr):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(arr, f, ensure_ascii=False, indent=2)


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", "/%E6%96%87%E7%AB%A0.html")
            self.end_headers()
            return
        if self.path == "/scan":
            # 手动触发：仅对缺失 done 字段的条目填充（手动维护优先）
            arr = load_data()
            done_set = scan_done_urls()
            changed = False
            for a in arr:
                if "done" not in a:
                    a["done"] = a.get("url", "") in done_set
                    changed = True
            if changed:
                save_data(arr)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "count": len(done_set)}).encode("utf-8"))
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_PUT(self):
        if os.path.basename(self.path) != "data.json":
            self.send_error(403, "Only data.json writable")
            return
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        try:
            arr = json.loads(body.decode("utf-8"))
        except Exception as e:
            self.send_error(400, f"Invalid JSON: {e}")
            return
        save_data(arr)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    os.chdir(ROOT)
    load_data()  # 启动时初始化 done 字段
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"服务已启动： http://127.0.0.1:{PORT}/文章.html")
        print("按 Ctrl+C 停止")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止")
