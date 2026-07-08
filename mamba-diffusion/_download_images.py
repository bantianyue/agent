#!/usr/bin/env python3
"""Download all images from CDP extraction."""
import urllib.request, os

urls = [
    ('img1.jpg', "https://arxiv.org/static/base/1.0.1/images/icons/smileybones-small.svg"),
    ('img2.jpg', "https://arxiv.org/html/2606.15007v1/x1.png"),
    ('img3.jpg', "https://arxiv.org/html/2606.15007v1/assets/huggingface-color.png"),
    ('img4.jpg', "https://arxiv.org/html/2606.15007v1/x2.png"),
    ('img5.jpg', "https://arxiv.org/html/2606.15007v1/figures/NVFP4_Pretrain_Ultra3_Figure.png"),
    ('img6.jpg', "https://arxiv.org/html/2606.15007v1/x3.png"),
    ('img7.jpg', "https://arxiv.org/html/2606.15007v1/x4.png"),
    ('img8.jpg', "https://arxiv.org/html/2606.15007v1/x5.png"),
    ('img9.jpg', "https://arxiv.org/html/2606.15007v1/x6.png"),
    ('img10.jpg', "https://arxiv.org/html/2606.15007v1/x7.png"),
    ('img11.jpg', "https://arxiv.org/html/2606.15007v1/figures/super_residual_norm_vs_depth.png"),
    ('img12.jpg', "https://arxiv.org/html/2606.15007v1/figures/ultra_residual_norm_vs_depth.png"),
    ('img13.jpg', "https://arxiv.org/html/2606.15007v1/x8.png"),
    ('img14.jpg', "https://arxiv.org/html/2606.15007v1/x9.png"),
    ('img15.jpg', "https://arxiv.org/html/2606.15007v1/figures/5_26_aa_mean_token_ratio_highreso.png"),
    ('img16.jpg', "https://arxiv.org/html/2606.15007v1/x10.png"),
    ('img17.jpg', "https://arxiv.org/html/2606.15007v1/x11.png"),
    ('img18.jpg', "https://arxiv.org/html/2606.15007v1/figures/mamba_vs_kv_cache.png"),
    ('img19.jpg', "https://arxiv.org/html/2606.15007v1/x12.png"),
    ('img20.jpg', "https://arxiv.org/html/2606.15007v1/figures/mtp_dl_throughput.png"),
    ('img21.jpg', "https://arxiv.org/html/2606.15007v1/figures/swebench_verified_agent_matrix.png"),
    ('img22.jpg', "https://arxiv.org/html/2606.15007v1/figures/terminal_bench_2_1_agent_matrix.png"),
    ('img23.jpg', "https://arxiv.org/static/base/1.0.1/images/funders/simons-foundation.png"),
    ('img24.jpg', "https://arxiv.org/static/base/1.0.1/images/funders/schmidt-sciences.png"),
]

for fname, url in urls:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = r.read()
            # Detect actual format from content-type
            ct = r.headers.get("Content-Type", "")
            if "png" in ct: fname = fname.replace(".jpg", ".png")
            with open(fname, "wb") as f:
                f.write(data)
            print(f"  OK {fname} ({len(data)//1024}KB)")
    except Exception as e:
        print(f"  FAIL {fname}: {e}")
