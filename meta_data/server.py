#!/usr/bin/env python3
# 技术文章收藏 - 本地服务
# 用法：双击本文件，或终端 `python server.py`
# 然后浏览器打开 http://127.0.0.1:8765/文章.html
import http.server, socketserver, os, sys

PORT = 8765
ROOT = os.path.dirname(os.path.abspath(__file__))


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def do_GET(self):
        # 根路径重定向到文章页面（中文名需 URL 编码）
        if self.path in ('/', '/index.html'):
            self.send_response(302)
            self.send_header('Location', '/%E6%96%87%E7%AB%A0.html')
            self.end_headers()
            return
        super().do_GET()

    def end_headers(self):
        # 禁用缓存，保证打开即最新
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

    def do_PUT(self):
        # 仅允许写入 data.json
        if os.path.basename(self.path) != 'data.json':
            self.send_error(403, 'Only data.json writable')
            return
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length)
        try:
            # 校验 JSON
            import json
            json.loads(body.decode('utf-8'))
        except Exception as e:
            self.send_error(400, f'Invalid JSON: {e}')
            return
        path = os.path.join(ROOT, 'data.json')
        with open(path, 'wb') as f:
            f.write(body)
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"ok":true}')

    def log_message(self, fmt, *args):
        pass  # 安静


if __name__ == '__main__':
    os.chdir(ROOT)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"服务已启动： http://127.0.0.1:{PORT}/文章.html")
        print("按 Ctrl+C 停止")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n已停止")
