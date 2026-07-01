import json, urllib.request, os, re, subprocess

# Read .env file
with open(os.path.expanduser('~/.baoyu-skills/.env')) as f:
    content = f.read()

env = {}
for line in content.strip().split('\n'):
    line = line.strip()
    if '=' in line and not line.startswith('#'):
        k, v = line.split('=', 1)
        v = v.strip()
        if v.startswith("'") and v.endswith("'"):
            v = v[1:-1]
        elif v.startswith('"') and v.endswith('"'):
            v = v[1:-1]
        env[k] = v

appid = env.get('WECHAT_APPID', '')
secret = env.get('WECHAT_SECRET', '')

# Get token
url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
    token = data.get('access_token', '')
    if not token:
        print(f'Token error: {data}')
        exit(1)
    print(f'Token: {token[:20]}...')

# Upload each GIF as permanent image material
gifs = ['anim1.gif', 'anim2.gif', 'anim3.gif', 'anim4.gif', 'anim5.gif', 'anim6.gif']
results = {}

for gif in gifs:
    print(f'\nUploading {gif}...')
    
    # Build multipart form manually
    boundary = f'----WebKitFormBoundary{os.urandom(16).hex()}'
    
    with open(gif, 'rb') as f:
        gif_data = f.read()
    
    body_parts = []
    body_parts.append(f'--{boundary}'.encode())
    body_parts.append(f'Content-Disposition: form-data; name="media"; filename="{gif}"'.encode())
    body_parts.append(b'Content-Type: image/gif')
    body_parts.append(b'')
    body_parts.append(gif_data)
    body_parts.append(f'--{boundary}--'.encode())
    
    body = b'\r\n'.join(body_parts)
    
    upload_url = f'https://api.weixin.qq.com/cgi-bin/material/add_material?access_token={token}&type=image'
    req2 = urllib.request.Request(upload_url, data=body, method='POST')
    req2.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    
    try:
        with urllib.request.urlopen(req2, timeout=30) as resp:
            result = json.loads(resp.read())
            print(f'  Result: {json.dumps(result, ensure_ascii=False)[:200]}')
            if 'media_id' in result:
                results[gif] = result['media_id']
                # Also get the URL
                # Get material
                get_url = f'https://api.weixin.qq.com/cgi-bin/material/get_material?access_token={token}'
                get_body = json.dumps({"media_id": result['media_id']}).encode()
                get_req = urllib.request.Request(get_url, data=get_body, method='POST')
                get_req.add_header('Content-Type', 'application/json')
                try:
                    with urllib.request.urlopen(get_req, timeout=10) as get_resp:
                        get_result = json.loads(get_resp.read())
                        print(f'  Get material: {json.dumps(get_result, ensure_ascii=False)[:200]}')
                        if 'url' in get_result:
                            results[gif] = get_result['url']
                except Exception as e:
                    print(f'  Get material error: {e}')
    except Exception as e:
        print(f'  Upload error: {e}')
        if hasattr(e, 'read'):
            print(f'  Response: {e.read().decode()[:300]}')

print('\n\nFinal results:')
for k, v in results.items():
    print(f'{k}: {v}')
