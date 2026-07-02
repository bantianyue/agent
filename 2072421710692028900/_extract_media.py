import subprocess, json, sys, re

result = subprocess.run(
    ['twitter', 'article', '2072421710692028900', '--json'],
    capture_output=True, text=True,
    env={'HTTP_PROXY': 'http://127.0.0.1:7890', 'HTTPS_PROXY': 'http://127.0.0.1:7890'}
)
data = json.loads(result.stdout)
d = data['data'][0]

# Check media-related fields
for k in d:
    if any(x in k.lower() for x in ['media', 'image', 'photo']):
        val = d[k]
        if val:
            print(f'{k}: {json.dumps(val, indent=2, default=str)[:800]}')

print('---ALL KEYS WITH "media"---')
for k in sorted(d.keys()):
    if 'media' in k.lower() or 'image' in k.lower() or 'photo' in k.lower():
        print(f'{k}: {type(d[k]).__name__} = {str(d[k])[:200]}')
