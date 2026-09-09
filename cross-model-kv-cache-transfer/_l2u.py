# -*- coding: utf-8 -*-
import re, json, copy

def _inner_clean_once(s):
    sc = {'S':'S','T':'T','C':'C','O':'O'}
    sc_u = {'S':'\U0001d4ae','T':'\U0001d4af','C':'\U0001d49e','O':'\U0001d4aa'}
    def rep(m):
        body = m.group(1)
        if m.group(0).startswith('\\mathbb'):
            return {'R':'ℝ','Z':'ℤ','Q':'ℚ','N':'ℕ','C':'ℂ','T':'𝕋'}.get(body, body)
        if m.group(0).startswith('\\mathcal'):
            return sc_u.get(body, body)
        return body  # mathbf/bm/text/mathrm -> content
    s = re.sub(r'\\(?:mathbf|bm|text|mathrm|mathbb|mathcal)\{([^}]*)\}', rep, s)
    s = re.sub(r'\\hat\{([^}]{1,3})\}', lambda m: m.group(1)+'\u0302', s)
    s = re.sub(r'\\bar\{([^}]{1,3})\}', lambda m: m.group(1)+'\u0304', s)
    return s

def convert(s):
    prev=None
    while prev!=s:
        prev=s; s=_inner_clean_once(s)
    for k,v in {'\\approx':'≈','\\times':'×','\\cdot':'·','\\top':'⊤','\\prime':'′',
         '\\dots':'…','\\ldots':'…','\\to':'→','\\rightarrow':'→','\\in':'∈','\\subseteq':'⊆',
         '\\geq':'≥','\\leq':'≤','\\sum':'∑','\\prod':'∏','\\|':'‖','\\approxeq':'≈',
         '\\Delta':'Δ','\\alpha':'α','\\beta':'β','\\gamma':'γ','\\theta':'θ','\\Theta':'Θ',
         '\\lambda':'λ','\\mu':'μ','\\sigma':'σ','\\phi':'φ','\\omega':'ω','\\epsilon':'ε',
         '\\infty':'∞','\\nabla':'∇','\\ell':'ℓ','\\neq':'≠','\\ne':'≠','\\colon':':',
         '\\tau':'τ','\\leftrightarrow':'↔','\\mapsto':'↦','\\coloneqq':'≔','\\coloneq':'≔',
         '\\sim':'~','\\simeq':'≃','\\propto':'∝','\\langle':'⟨','\\rangle':'⟩'}.items():
        s=s.replace(k,v)
    s=s.replace('\\left','').replace('\\right','').replace('\\Big','').replace('\\big','')
    # remaining bare one-letter macros fallback to the letter (rm, etc.)
    s=re.sub(r'\\[a-zA-Z]+', lambda m: m.group(0)[1], s)
    s=s.replace('\\(','').replace('\\)','')
    def sup(m):
        inner=m.group(1)
        if re.search(r'[a-zA-Z]{2,}', inner): return '^'+inner
        sm={'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹',
            '-':'⁻','+':'⁺','l':'ˡ','h':'ʰ','t':'ᵗ','s':'ˢ','i':'ⁱ','N':'ᴺ','T':'ᵀ','d':'ᵈ','o':'ᵒ',
            'r':'ʳ','k':'ᵏ','m':'ᵐ','n':'ⁿ','j':'ʲ','x':'ˣ','′':'′','p':'ᵖ','b':'ᵇ','c':'ᶜ','e':'ᵉ',
            'v':'ᵛ','w':'ʷ','K':'ᵏ','L':'ᴸ','S':'ˢ','R':'ᴿ','a':'ᵃ','g':'ᵍ','u':'ᵘ','f':'ᶠ','(':'(',')':')',',':',','=':'⁼','<':'<','>':'>','.':'.'}
        return ''.join(sm.get(ch,ch) for ch in inner)
    # resolve nested braces by processing from innermost repeatedly on sup/sub
    s=re.sub(r'\^\{([^}]{0,20})\}', sup, s)
    s=re.sub(r'_\{([^}]{0,20})\}', lambda m: '_'+m.group(1), s)
    s=re.sub(r'\^([0-9])', lambda m: {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}[m.group(1)], s)
    s=re.sub(r'\{([0-9])\}', lambda m: {'0':'⁰','1':'¹','2':'²','3':'³','4':'⁴','5':'⁵','6':'⁶','7':'⁷','8':'⁸','9':'⁹'}.get(m.group(1),m.group(1)), s)
    return s

if __name__=='__main__':
    d=json.load(open('article_data.json',encoding='utf-8'))
    nd=copy.deepcopy(d)
    for s in nd['sections']:
        s['paras']=[convert(p) for p in s.get('paras',[])]
        for k,fl in (s.get('fig_after') or {}).items():
            for f in fl: f['caption']=convert(f['caption'])
    nd['lead']=[convert(p) for p in nd['lead']]
    nd['conclusion']=[convert(p) for p in nd['conclusion']]
    for it in nd['summary']: it['body']=convert(it['body'])
    json.dump(nd, open('article_data.json','w',encoding='utf-8'), ensure_ascii=False, indent=2)
    blob=json.dumps(nd,ensure_ascii=False)
    print('converted OK')
    print('residual \\cmd:', re.findall(r'\\[a-zA-Z]+\{', blob)[:10])
    print('residual ^{ :', blob.count('^{'), '_{ :', blob.count('_{'))
