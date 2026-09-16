import json
j=json.load(open('what-is-a-gpu-kernel-intro/article_data.json',encoding='utf-8'))
print('keys',list(j.keys()))
print('TITLE',j.get('title'))
print('LEAD:',j.get('lead'))
print('SUMMARY:')
for s in j.get('summary') or []: print('  -',s.get('key'),':',s.get('body','')[:120])
for i,sec in enumerate(j['sections']):
    print('== sec%d %s (type=%s)'%(i,sec.get('title'),sec.get('type')))
    for pi,pa in enumerate(sec['paras']):
        print('  p%d: %s'%(pi,pa[:150]))
print('CONCLUSION:')
for c in j.get('conclusion') or []: print('  -',c[:120])
