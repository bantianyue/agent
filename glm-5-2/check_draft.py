import urllib.request, json, os, re

env_path = os.path.expanduser('~/.baoyu-skills/.env')
appid = secret = None
with open(env_path) as f:
    for line in f:
        line = line.strip()
        if line.startswith('WECHAT_APP_ID='):
            appid = line.split('=', 1)[1].strip().strip("'").strip('"')
        if line.startswith('WECHAT_APP_SECRET='):
            secret = line.split('=', 1)[1].strip().strip("'").strip('"')

url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
token = data['access_token']
print(f'Token: {token[:10]}...')

draft_id = 'TIqnnVEu6Oy3-wtKttGa0WgBWNiC3TVyXM37wHAH3C9AzmRUqYb5lYk7Gdah2LOb'
get_url = f'https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}'
get_body = json.dumps({'media_id': draft_id}).encode()
req = urllib.request.Request(get_url, data=get_body, method='POST')
req.add_header('Content-Type', 'application/json')
with urllib.request.urlopen(req, timeout=10) as resp:
    draft = json.loads(resp.read())

item = draft['news_item'][0]
content_html = item['content']
print(f'Title: {item["title"]}')
print(f'Content length: {len(content_html)}')

placeholders = re.findall(r'WECHATIMGPH_\d+', content_html)
print(f'Placeholders remaining: {placeholders}')
