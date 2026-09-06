#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess, re, os
url = "https://jaydenteoh.github.io/blog/2026/nextlat/"
out = r"D:/06_Hermes/articles/_nxt.html"
env = dict(os.environ, HTTPS_PROXY="http://127.0.0.1:7890", HTTP_PROXY="http://127.0.0.1:7890")
r = subprocess.run(["curl","-sL","--max-time","50","-A","Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/126.0","-e","https://jaydenteoh.github.io/",url,"-o",out,"-w","http=%(http_code)s size=%(size_download)s\n"],capture_output=True,text=True,env=env)
print(r.stdout, r.stderr[:200])
h=open(out,encoding='utf-8',errors='ignore').read()
print("len html:", len(h))
# 正文容器线索
for m in re.finditer(r'<(article|main|div|section)[^>]*class="([^"]*)"', h)[:0]: pass
# 看 script src 和正文关键词
links=sorted(set(re.findall(r'(?:src|href)="([^"]+)"', h)))
print("=== links/scripts ===")
for l in links[:40]: print(" ", l[:100])
print("=== 含 nextlat/manhattan 关键词? ===")
print('nextlat' in h.lower(), 'manhattan' in h.lower())
