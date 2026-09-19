import json
import os
import re
import subprocess
import sys

mid = open('draft.id', encoding='utf-8').read().strip()
ts = "C:/Users/twfehh7/.codex/skills/baoyu-post-to-wechat/scripts/wechat-api.ts"
env = dict(os.environ)
env['PYTHONIOENCODING'] = 'utf-8'
out = subprocess.run(
    ['npx', '-y', 'tsx', ts, 'draft/get', '--media-id', mid],
    capture_output=True, text=True, encoding='utf-8', errors='replace', env=env,
)
txt = (out.stdout or '') + (out.stderr or '')
print(txt[:600])
try:
    data = json.loads(out.stdout)
    content = json.dumps(data, ensure_ascii=False)
except Exception:
    content = txt
print('WECHATIMGPH_ placeholders:', content.count('WECHATIMGPH_'))
print('mmbiz imgs:', len(re.findall(r'mmbiz\.qpic\.cn', content)))
print('preview-table:', content.count('preview-table'))
print('strong:', content.count('strong'))
