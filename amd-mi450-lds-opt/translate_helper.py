# -*- coding: utf-8 -*-
"""翻译辅助：提取块级元素->受保护文本清单；把译文写回 HTML"""
import re, json, os, sys
from bs4 import BeautifulSoup

BASE=r"D:/06_Hermes/articles/amd-mi450-lds-opt"

def protect_code(txt):
    """把 <code>..</code> / <span class=pre>..</span> 等用占位符替换，返回文本+映射"""
    phmap={}
    def _repl(m):
        ph=f"＠{len(phmap)}＠"
        phmap[ph]=m.group(0)
        return ph
    # 保护 code 块（含其内 pre span）
    out=re.sub(r'<code[^>]*>.*?</code>|<span class="pre"[^>]*>.*?</span>', _repl, str(txt), flags=re.S)
    # 保护 span（高亮 token 等）—— 但会把 em/strong 也保护？保留这些标签翻译时无关
    out=re.sub(r'<(em|i|strong|b|sup|sub)[^>]*>.*?</\1>', _repl, out, flags=re.S)
    return out, phmap

def restore_code(txt, phmap):
    for ph,orig in phmap.items():
        txt=txt.replace(ph, orig)
    return txt

def extract_blocks(html):
    """返回块级元素及其受保护文本"""
    soup=BeautifulSoup(html,'lxml')
    root=soup.find('section') or soup
    blocks=[]
    for name in ('p','li','td','th','h1','h2','h3','h4','figcaption'):
        for b in root.find_all(name):
            if b.find_parent('pre'): continue
            raw=str(b)
            protected,phmap=protect_code(raw)
            # 去掉标签得纯文本（用于翻译），但要保留占位符
            pb=BeautifulSoup(protected,'lxml')
            txt=pb.get_text()
            blocks.append({'tag':name,'raw':raw,'txt':txt,'indices':phmap})
    return soup, root, blocks

def write_back(html, translated):
    """translated: [(block_idx, translated_text_with_placeholders)]"""
    soup=BeautifulSoup(html,'lxml')
    root=soup.find('section') or soup
    # 重新收集，顺序一致
    allb=[]
    for name in ('p','li','td','th','h1','h2','h3','h4','figcaption'):
        for b in root.find_all(name):
            if b.find_parent('pre'): continue
            allb.append(b)
    # 对每个翻译重建：先保护再替换文本
    for idx,newtxt in translated:
        if idx>=len(allb): continue
        el=allb[idx]
        # newtxt 是带占位符的中文。恢复占位符需要原始 phmap。重新保护该 el
        protected,phmap=protect_code(str(el))
        restored=restore_code(newtxt, phmap)
        # 用新的 HTML 替换 el
        new_el=BeautifulSoup(restored,'lxml').find() or BeautifulSoup(restored,'lxml')
        el.replace_with(new_el)
    return str(soup)

def translate_batch(html, start, n):
    """提取 start 起的 n 个块，输出待翻译列表"""
    soup=BeautifulSoup(html,'lxml')
    root=soup.find('section') or soup
    allb=[]
    for name in ('p','li','td','th','h1','h2','h3','h4','figcaption'):
        for b in root.find_all(name):
            if b.find_parent('pre'): continue
            allb.append(b)
    out=[]
    for i in range(start, min(start+n, len(allb))):
        el=allb[i]
        protected,phmap=protect_code(str(el))
        txt=BeautifulSoup(protected,'lxml').get_text().strip()
        out.append({'idx':i,'tag':el.name,'text':txt})
    return allb, out

if __name__=='__main__':
    mode=sys.argv[1]
    if mode=='extract':
        print(json.dumps(translate_batch(open(BASE+"/article.html",encoding='utf-8').read(), int(sys.argv[2]), int(sys.argv[3]))[1], ensure_ascii=False, indent=1))
