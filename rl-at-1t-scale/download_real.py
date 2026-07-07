import urllib.request, os

base = "D:/06_Hermes/articles/rl-at-1t-scale"
urls = {
    'img1_cover.png': 'https://www.primeintellect.ai/_next/image?url=%2Fblog%2Frl-at-1t-scale%2Fcover.png&w=3840&q=75&dpl=dpl_AXb2e6kRVX8BunzSYXzUJrh1JRUc',
    'img2_hero-steptime-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/hero-steptime-preview.png',
    'img3_async-rl-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/async-rl-preview.png',
    'img4_weight-updates-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/weight-updates-preview.png',
    'img5_wide-ep-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/wide-ep-preview.png',
    'img6_pd-disagg-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/pd-disagg-preview.png',
    'img7_routing-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/routing-preview.png',
    'img8_r3-kl-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/r3-kl-preview.png',
    'img9_fsdp-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/fsdp-preview.png',
    'img10_ep-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/ep-preview.png',
    'img11_cp-dsa-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/cp-dsa-preview.png',
    'img12_fp8-training-preview.png': 'https://www.primeintellect.ai/blog/rl-at-1t-scale/fp8-training-preview.png',
}

os.chdir(base)
opener = urllib.request.build_opener(urllib.request.ProxyHandler({
    'http': 'http://127.0.0.1:7890', 'https': 'http://127.0.0.1:7890'
}))
for fname, url in urls.items():
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with opener.open(req, timeout=60) as r:
            data = r.read()
        with open(fname, 'wb') as f:
            f.write(data)
        print(f'OK {fname} ({len(data)//1024}KB)')
    except Exception as e:
        print(f'FAIL {fname}: {e}')
print('done')
