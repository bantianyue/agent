import json
j=json.load(open('what-is-a-gpu-kernel-intro/article_data.json',encoding='utf-8'))
print('TITLE',j.get('title'))
print('LEAD')
for x in j.get('lead') or []: print('  ',x)
print('SUMMARY')
for x in j.get('summary') or []: print('  [',x.get('key'),']',x.get('body'))
for i,sec in enumerate(j['sections']):
    print('== sec%d %s'%(i,sec.get('title')))
    for pi,pa in enumerate(sec['paras']): print('  p%d: %s'%(pi,pa))
print('CONCL')
for c in j.get('conclusion') or []: print('  ',c)
