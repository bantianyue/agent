import json, os, sys, re, io, requests

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
r.encoding = 'utf-8'
d = r.json()
if 'news_item' not in d:
    print('DRAFT GET FAILED', json.dumps(d, ensure_ascii=False)[:400])
    sys.exit(1)
item = d['news_item'][0]
html = item['content']
if isinstance(html, str):
    try:
        html = html.encode('latin-1', errors='ignore').decode('utf-8')
    except Exception:
        pass

print('title        :', item.get('title'))
print('digest       :', (item.get('digest') or '')[:80])
print('author       :', item.get('author'))
print('thumb_media  :', item.get('thumb_media_id'))
srcs = re.findall(r'<img[^>]+src="([^"]+)"', html)
print('img count    :', len(srcs))
for s in srcs:
    print('   img       :', s[:110])
print('mmbiz count  :', html.count('mmbiz.qpic.cn'))
print('placeholder  :', html.count('WECHATIMGPH_'))
print('pre count    :', html.count('<pre'))
print('h2 count     :', html.count('<h2'))
print('strong count :', html.count('<strong'))
print('stray **     :', html.count('**'))
print('inline code  :', html.count(':7px') + html.count('3f4f5'))
print('portal idx   :', html.find('【传送门】'))
print('jieyu idx    :', html.find('f5f0eb'))
print('ref idx      :', html.find('参考：'))
# 代码空格保真抽查
for probe in ['use&nbsp;cuda_device', 'cargo&nbsp;oxide&nbsp;new', 'cuda_device', 'DisjointSlice']:
    print('code probe %-24s -> %d' % (probe, html.count(probe)))
# 正文图片位置
i = html.find('mmbiz.qpic.cn')
seg = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '|', html[max(0, i - 300):i + 120]))
print('around img   :', seg[-320:])
