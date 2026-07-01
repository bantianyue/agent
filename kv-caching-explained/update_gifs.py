import json, urllib.request, os, re

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
appid = env.get('WECHAT_APP_ID', '')
secret = env.get('WECHAT_APP_SECRET', '')

url = f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={appid}&secret={secret}'
req = urllib.request.Request(url)
with urllib.request.urlopen(req, timeout=10) as resp:
    data = json.loads(resp.read())
    token = data.get('access_token', '')

draft_id = open('draft.id').read().strip()

get_url = f'https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}'
get_body = json.dumps({'media_id': draft_id}).encode()
get_req = urllib.request.Request(get_url, data=get_body, method='POST')
get_req.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(get_req, timeout=15) as resp:
    draft_data = json.loads(resp.read())

item = draft_data['news_item'][0]
content_html = item.get('content', '')

img_urls = re.findall(r'<img[^>]+src="(https://mmbiz\.qpic\.cn[^"]+)"', content_html)
print(f'Found {len(img_urls)} image URLs')

# Order: [0]=img3 Part1-GIF1, [1]=img4 Part1-GIF2, [2]=img5 Part2-GIF1,
#        [3]=img6 Part2-GIF2, [4]=img7.png Part3-static, [5]=img8 Part4-GIF,
#        [6]=img9 Part7-GIF
gif_urls = [
    'http://mmbiz.qpic.cn/sz_mmbiz_gif/MJRkdzPjdxQAX5Nt2ms0BHOD27FM6l1uLJEtlZK6wIAdHvlRF80ibIWzMVlibIkkTRibHWy0aDGKR71kfuYx0eibbvV96ib7N1TlnBsYj8FmpShA/0?wx_fmt=gif',
    'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxQ9n4j0aWLF0l4vovejGm50jHZ6xbYG74PkgmsUlIfbSbcHcYCR8N97By8fyDywmvXqJ2QTOPhQpiaogOPKrTMZ3qkAjicUic1KVQ/0?wx_fmt=gif',
    'http://mmbiz.qpic.cn/sz_mmbiz_gif/MJRkdzPjdxSYzL3p9iaiaBVp5ibsiclJ8c0Y18Ora0xNk8GIUic0QnEjanUxibWtcro3yrxhBsY826WKdhUhY348TlaiakQD00HHgBeMnFOCPlFFcw/0?wx_fmt=gif',
    'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxRibdQAooczHVW8UdN2ib8Q7ZAYUhJicBCzojnQU7TmR4bV7zElibq1SibcIOs90n46yia1AnYiapzHY69UcmoVpMJvaoEicicoMRDibQzHY/0?wx_fmt=gif',
    None,  # img7.png static
    'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxTbWY9iaPdq1H0JzdeyoGCNEiaCdxS63hdcRzAZKVNfwLbFu0icWjS9uTmKwtqBqKPLC6GpLJUiaFWBDquLFCRxlviaKBYVVf7Ezobc/0?wx_fmt=gif',
    'http://mmbiz.qpic.cn/mmbiz_gif/MJRkdzPjdxSq29icNPREHSXkUY0Tc5ricDoYYkkwNHwXRsTsbZK5aDxSLib4EFAiawsxEIE38vZcu2w731BTjTiaic43m5RzBB71aaQWCIsIjtXxk/0?wx_fmt=gif',
]

for i, old_url in enumerate(img_urls):
    if gif_urls[i] is not None:
        content_html = content_html.replace(old_url, gif_urls[i])
        print(f'  [{i}] Replaced with GIF')
    else:
        print(f'  [{i}] Kept static')

update_url = f'https://api.weixin.qq.com/cgi-bin/draft/update?access_token={token}'
update_payload = {
    "media_id": draft_id,
    "index": 0,
    "articles": {
        "title": item['title'],
        "content": content_html,
        "thumb_media_id": item.get('thumb_media_id', ''),
    }
}

update_body = json.dumps(update_payload, ensure_ascii=False).encode('utf-8')
update_req = urllib.request.Request(update_url, data=update_body, method='POST')
update_req.add_header('Content-Type', 'application/json; charset=utf-8')

try:
    with urllib.request.urlopen(update_req, timeout=15) as resp:
        result = json.loads(resp.read())
        print(f'\nUpdate result: {json.dumps(result, ensure_ascii=False)}')
except Exception as e:
    print(f'\nError: {e}')
