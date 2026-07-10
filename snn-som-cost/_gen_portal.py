#!/usr/bin/env python3
"""Generate 传送门 block from published_articles.json: 4 related + 4 diverse.
Reusable substitute for the missing add-portal.py. Selects by keyword score,
excludes current article URL, dedups, respects .portal_history.json, applies
display-width truncation (<=81 units: hanzi=1, halfwidth=0.5).
"""
import json, os, re, unicodedata, sys

ARTICLES = "D:/06_Hermes/articles"
PORTAL_JSON = os.path.join(ARTICLES, "published_articles.json")
HISTORY = os.path.join(ARTICLES, ".portal_history.json")

KW = ['GPU','并行','NVLink','CUDA','推理','Tensor','延迟','kernel','吞吐',
      '流水线','B200','H200','Hopper','Blackwell','TP','张量','GEMM','算力','显存','AllReduce']

def width(s):
    return sum(1.0 if unicodedata.east_asian_width(c) in ('W','F') else 0.5 for c in s)

def truncate(s, cap=81):
    out=''; w=0.0
    for c in s:
        cw = 1.0 if unicodedata.east_asian_width(c) in ('W','F') else 0.5
        if w + cw > cap:
            out += '…'; break
        out += c; w += cw
    return out

def score(e):
    t = e.get('title','').lower()
    return sum(1 for k in KW if k.lower() in t)

def load_history():
    if os.path.exists(HISTORY):
        try: return set(json.load(open(HISTORY,encoding='utf-8')))
        except: return set()
    return set()

def save_history(used):
    h = load_history(); h |= set(used)
    json.dump(sorted(h), open(HISTORY,'w',encoding='utf-8'), ensure_ascii=False, indent=1)

def main():
    cur_url = sys.argv[1] if len(sys.argv)>1 else None
    d = json.load(open(PORTAL_JSON,encoding='utf-8'))
    hist = load_history()
    # exclude current + history
    cand = [e for e in d if e.get('url') and e['url']!=cur_url]
    related = sorted([e for e in cand if score(e)>=1], key=score, reverse=True)
    diverse = [e for e in cand if score(e)==0]
    chosen = []
    seen=set()
    for e in related:
        if e['url'] in hist or e['url'] in seen: continue
        chosen.append(e); seen.add(e['url'])
        if len(chosen)>=4: break
    for e in diverse:
        if e['url'] in hist or e['url'] in seen: continue
        chosen.append(e); seen.add(e['url'])
        if len(chosen)>=8: break
    # fallback if still <8
    for e in cand:
        if len(chosen)>=8: break
        if e['url'] in seen: continue
        chosen.append(e); seen.add(e['url'])
    save_history([e['url'] for e in chosen])

    lines = ['<span style="font-size:14px;color:#888888;font-family:\'Courier New\',monospace;">【传送门】<br>']
    for e in chosen:
        title = truncate(e['title'])
        lines.append(f'<a class="normal_text_link mp_article_text_link" href="{e["url"]}" target="_blank" data-linktype="2">{title}</a><br>')
    lines.append('</span>')
    print('\n'.join(lines))
    # verify widths
    bad=[e['title'] for e in chosen if width(truncate(e['title']))>81]
    if bad: print('WARN width>81:', bad, file=sys.stderr)

if __name__=='__main__':
    main()
