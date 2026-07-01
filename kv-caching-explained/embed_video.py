import json, urllib.request, os, re
from urllib.parse import quote

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
print(f'Draft ID: {draft_id[:40]}...')

# Get draft content
get_url = f'https://api.weixin.qq.com/cgi-bin/draft/get?access_token={token}'
get_body = json.dumps({"media_id": draft_id}).encode()
get_req = urllib.request.Request(get_url, data=get_body, method='POST')
get_req.add_header('Content-Type', 'application/json')

with urllib.request.urlopen(get_req, timeout=15) as resp:
    draft_data = json.loads(resp.read())
    ut = draft_data.get("update_time", "")
    print(f'Got draft: update_time={ut}')

item = draft_data['news_item'][0]
content_html = item.get('content', '')

# Find the first image URL
img_urls = re.findall(r'<img[^>]+src="(https://mmbiz\.qpic\.cn[^"]+)"', content_html)
first_img_url = img_urls[0]
print(f'First image URL: {first_img_url[:80]}...')

# Build video iframe
cover_url = "http://mmbiz.qpic.cn/mmbiz_jpg/MJRkdzPjdxRGdDgvWPOnPTwqRpfuicZmZJzHPEXWibcssQmAhnCTA3aWBicQ3BiarILIbqh8d5NE6iadMdZCLHZdgfdmiafT3UkLyEwAPTT9OkicCo/0?wx_fmt=jpeg"
cover_encoded = quote(cover_url, safe='')

video_iframe = f'''<section style="text-align: center;margin-left: 8px;margin-right: 8px;" nodeleaf="">
  <iframe class="video_iframe rich_pages"
    data-src="https://mp.weixin.qq.com/mp/readtemplate?t=pages/video_player_tmpl&action=mpvideo&auto=0&vid=apiv_4557370031474425862"
    data-mpvid="apiv_4557370031474425862"
    data-vidtype="2"
    data-cover="{cover_encoded}"
    data-ratio="1.7777777777777777"
    data-w="1920">
  </iframe>
</section>'''

# Replace the first image with video iframe
content_html = content_html.replace(f'<img src="{first_img_url}"', video_iframe, 1)

# Update draft
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
        print(f'Update result: {json.dumps(result, ensure_ascii=False)}')
except urllib.error.HTTPError as e:
    print(f'HTTP Error: {e.code}')
    print(e.read().decode()[:500])
except Exception as e:
    print(f'Error: {e}')
