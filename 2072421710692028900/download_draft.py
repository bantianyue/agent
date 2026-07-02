import os, json, urllib.request, re, datetime

env_path = os.path.expanduser('~/.baoyu-skills/.env')
appid = ''
secret = ''
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('WECHAT_APP_ID'):
            appid = line.split('=', 1)[1].strip()
        elif line.startswith('WECHAT_APP_SECRET'):
            secret = line.split('=', 1)[1].strip()

# Get token
url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    token = json.loads(resp.read())['access_token']

# Read draft.id
with open(r'D:\06_Hermes\articles\2072421710692028900\draft.id') as f:
    media_id = f.read().strip()

# Get draft
get_url = f'https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}'
payload = json.dumps({'media_id': media_id}).encode()
req2 = urllib.request.Request(get_url, data=payload, method='POST')
req2.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req2, timeout=15) as resp:
    draft = json.loads(resp.read())

content = draft['news_item'][0]['content']
title = draft['news_item'][0].get('title', '')
digest = draft['news_item'][0].get('digest', '')
thumb_url = draft['news_item'][0].get('thumb_url', '')
update_time = draft.get('update_time', 0)

print(f'Title: {title}')
print(f'Update time: {update_time} ({datetime.datetime.fromtimestamp(update_time) if update_time else "unknown"})')
print(f'Content length: {len(content)}')
print(f'Has thumb_url: {"yes" if thumb_url else "no"}')

# Save meta
meta = {'title': title, 'digest': digest, 'thumb_url': thumb_url, 'update_time': update_time}
with open(r'D:\06_Hermes\articles\2072421710692028900\draft_meta.json', 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)

# Check encoding
if '要点速览' in content or '结语' in content:
    print('✅ Content encoding OK')
    fixed = content
else:
    print('⚠️ Trying latin-1 encoding fix...')
    fixed = content.encode('latin-1', errors='replace').decode('utf-8', errors='replace')
    if '要点速览' in fixed:
        print('✅ Fix worked')
    else:
        print('⚠️ Fix may not have worked, using original')
        fixed = content

with open(r'D:\06_Hermes\articles\2072421710692028900\draft_from_server.html', 'w', encoding='utf-8') as f:
    f.write(fixed)

# Download all inline images from the server HTML
imgs = re.findall(r'https://mmbiz\.qpic\.cn[^\s"\'<>]+', fixed)
seen = set()
for i, url in enumerate(imgs):
    url = url.rstrip('&').replace('&amp;', '&')
    if url in seen:
        continue
    seen.add(url)
    ext = 'jpg'
    if 'wx_fmt=png' in url:
        ext = 'png'
    elif 'wx_fmt=gif' in url:
        ext = 'gif'
    filename = f'server_img_{i+1:02d}.{ext}'
    try:
        req_img = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_img, timeout=30) as r:
            data = r.read()
            with open(os.path.join(r'D:\06_Hermes\articles\2072421710692028900', filename), 'wb') as f:
                f.write(data)
        print(f'OK {filename} ({len(data)//1024}KB)')
    except Exception as e:
        print(f'FAIL {filename}: {e}')

# Download cover
if thumb_url:
    try:
        req_thumb = urllib.request.Request(thumb_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_thumb, timeout=15) as r:
            data = r.read()
            with open(r'D:\06_Hermes\articles\2072421710692028900\cover_wx.jpg', 'wb') as f:
                f.write(data)
        print(f'✅ Cover downloaded: cover_wx.jpg ({len(data)//1024}KB)')
    except Exception as e:
        print(f'❌ Cover download failed: {e}')

print(f'\nServer images downloaded: {len(seen)}')
print('Done')
