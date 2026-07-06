import urllib.request
import os

dir_path = "D:\\06_Hermes\\articles\\mimo-1000tps"

# These are Markdown-rendered versions, URLs are relative
# TileRT blog images
base = "https://www.tilert.ai/blog"
figures = {
    "execution_gap.png": f"{base}/figures/execution_gap_boundary.png",
    "microsecond_war.png": f"{base}/figures/microsecond_war_1000tps.png",
    "codesign.png": f"{base}/figures/model_system_codesign.png",
}

proxy = urllib.request.ProxyHandler({})
opener = urllib.request.build_opener(proxy)

for fname, url in figures.items():
    path = os.path.join(dir_path, fname)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=30) as r:
            data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            print(f"✅ {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"❌ {fname}: {e}")

# Re-check the MiMo blog for img src — maybe they're in CDN
# Let me also try tile-ai github assets
print("\n--- Checking TileRT GitHub README ---")
git_base = "https://raw.githubusercontent.com/tile-ai/TileRT/main"
for fname in ["execution_gap_boundary.png", "microsecond_war_1000tps.png", "model_system_codesign.png"]:
    url = f"{git_base}/assets/{fname}"
    path = os.path.join(dir_path, fname)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with opener.open(req, timeout=30) as r:
            data = r.read()
            with open(path, "wb") as f:
                f.write(data)
            print(f"✅ {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"❌ {fname}: {e}")

print("\n Directory:")
for f in sorted(os.listdir(dir_path)):
    fp = os.path.join(dir_path, f)
    if os.path.isfile(fp):
        print(f"  {f:35s} {os.path.getsize(fp)//1024:>5}KB")
