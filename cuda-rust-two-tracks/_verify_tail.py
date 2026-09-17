import json, os, io, re, requests

ART = 'D:/06_Hermes/articles/cuda-rust-two-tracks'
MID = io.open(ART + '/draft.id', encoding='utf-8').read().strip()
appid = secret = None
for line in io.open(os.path.expanduser('~/.baoyu-skills/.env'), encoding='utf-8'):
    line = line.strip()
    if line.startswith('WECHAT_APP_ID='):
        appid = line.split('=', 1)[1]
    elif line.startswith('WECHAT_APP_SECRET='):
        secret = line.split('=', 1)[1]
tok = requests.get('https://api.weixin.qq.com/cgi-bin/token',
                   params={'grant_type': 'client_credential', 'appid': appid, 'secret': secret}).json().get('access_token')
r = requests.post('https://api.weixin.qq.com/cgi-bin/draft/get',
                  params={'access_token': tok}, json={'media_id': MID})
raw = r.content
d = json.loads(raw.decode('utf-8'))
html = d['news_item'][0]['content']
if isinstance(html, str):
    try:
        html = html.encode('latin-1', errors='ignore').decode('utf-8')
    except Exception:
        pass
print('len(html) =', len(html))
print('portal?', 'portal' in html, 'mp.weixin?', html.count('mp.weixin.qq.com'))
print('参考 count:', html.count('参考'))
print('--- tail 1200 ---')
print(html[-1200:])
