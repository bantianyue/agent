import urllib.request
import os

base_url = "https://mimo.xiaomi.com/zh/blog"
dir_path = "D:\\06_Hermes\\articles\\mimo-1000tps"
proxy = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(proxy)

images = {
    "hero.jpg": "https://cdn.cnbj1.fds.api.mi-img.com/aife/mimo-blog-fe/doc_build/static/image/logo.99baaffe.png",
    "fp4_quant.png": f"{base_url}/mimo-tilert-1000tps/1000tpsfp4.png",
}

# GIFs
gifs = {
    "snake.gif": f"{base_url}/mimo-tilert-1000tps/snake.gif",
    "macos.gif": f"{base_url}/mimo-tilert-1000tps/1000tps_macos.gif",
}

all_files = {**images, **gifs}

for fname, url in all_files.items():
    path = os.path.join(dir_path, fname)
    try:
        with opener.open(url, timeout=30) as r:
            data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            print(f"✅ {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"❌ {fname}: {e}")

print("\n 目录文件:")
for f in sorted(os.listdir(dir_path)):
    fp = os.path.join(dir_path, f)
    if os.path.isfile(fp):
        print(f"  {f:30s} {os.path.getsize(fp)//1024:>5}KB")
