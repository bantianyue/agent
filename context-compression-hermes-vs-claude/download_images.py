import urllib.request
import os

proxy_handler = urllib.request.ProxyHandler({'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'})
opener = urllib.request.build_opener(proxy_handler)

images = [
    ("https://framerusercontent.com/images/mYKYMonoQ2UJ6t8Y38p2wQos.png", "context-compression-lifecycle.png"),
    ("https://framerusercontent.com/images/3EGxQ8pzyVcHdQgUUULiW2d5QY.png", "hermes-2-layer-architecture.png"),
    ("https://framerusercontent.com/images/H2WAr5d30Vep7Qucty89gl8TUg.png", "compression-gap-before-after.png"),
    ("https://framerusercontent.com/images/dQ7e2lbV6f4IhILHFVMIwtnnlE.png", "mem0-integration-hermes-claude.png"),
]

out_dir = "D:\\06_Hermes\\articles\\context-compression-hermes-vs-claude"
for url, filename in images:
    path = os.path.join(out_dir, filename)
    if os.path.exists(path):
        print(f"SKIP (exists): {filename}")
        continue
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with opener.open(req, timeout=30) as resp:
            with open(path, 'wb') as f:
                f.write(resp.read())
        print(f"OK: {filename} ({os.path.getsize(path)} bytes)")
    except Exception as e:
        print(f"FAIL: {filename}: {e}")
