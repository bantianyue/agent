# -*- coding: utf-8 -*-
import os, glob
root=r"D:/06_Hermes/articles"
dps=[d for d in os.listdir(root) if os.path.isdir(os.path.join(root,d))]
def has_success(d):
    hits=glob.glob(os.path.join(d,'logs','push-draft*.log'))
    if not hits: return False
    for h in sorted(hits,key=os.path.getmtime):
        try:t=open(h,encoding='utf8',errors='ignore').read()
        except OSError: continue
        if '推送成功' in t: return True
    return False
flagged=[]
for d in dps:
    dp=os.path.join(root,d)
    if not os.path.exists(os.path.join(dp,'article_data.json')) and not os.path.exists(os.path.join(dp,'article.html')):
        continue
    if not has_success(dp):
        flagged.append(d)
print("dirs with work but no verified push-success:", len(flagged))
for d in sorted(flagged):
    dp=os.path.join(root,d)
    has_html=os.path.exists(os.path.join(dp,'article.html'))
    has_did=os.path.exists(os.path.join(dp,'draft.id'))
    print("  ", d, "| html?",has_html,"| draft.id?",has_did)
