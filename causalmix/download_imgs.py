import os, urllib.request

paper_dir = 'D:\\06_Hermes\\articles\\causalmix'
base_url = 'https://arxiv.org/html/2607.01104v1'

# Download x1.png, x2.png, x3.png
files = {
    'x1.png': f'{base_url}/x1.png',
    'x2.png': f'{base_url}/x2.png', 
    'x3.png': f'{base_url}/x3.png',
}

for fname, url in files.items():
    path = os.path.join(paper_dir, fname)
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        print(f'{fname} exists, skip ({os.path.getsize(path)//1024}KB)')
        continue
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            with open(path, 'wb') as f:
                f.write(data)
        print(f'{fname}: {len(data)//1024}KB')
    except Exception as e:
        print(f'{fname}: FAILED - {e}')

print('All downloads complete')
