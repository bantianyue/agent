#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""build_gen.py — jev-101-what-you-can-build

来源: https://x.com/manish_fp/status/2101325394532266139
X Article: Jev 101: what it is, and what you can build with it (manish_fp)

结构真相源: fxtwitter Draft.js blocks（79 块：47 段正文 / 14 个 header-two /
6 段 blockquote / 3 个有序项 / 1 段代码 / 1 条分隔线）。
图序真相源: CDP 渲染 DOM 文档流（1 张 hero 封面 + 7 张正文图，均为 900 宽）。
原文正文图无 caption，按规矩保留空图注槽，不自行补写。
hero 图（1200x480）只做封面来源，不进正文。
代码块原文照录不翻译。
"""

import json
import os

D = os.path.dirname(os.path.abspath(__file__))

sections = []
cur = None
code_lang = None
code_buf = []


def _flush_code():
    global code_lang, code_buf
    if code_lang is not None:
        cur['paras'].append('__CODE__' + code_lang + '::' + '\n'.join(code_buf))
        code_lang, code_buf = None, []


for raw in open(os.path.join(D, 'content.txt'), encoding='utf-8'):
    line = raw.rstrip('\n')
    if code_lang is not None:
        if line.strip() == 'C#END':
            _flush_code()
        else:
            code_buf.append(line)
        continue
    if not line.strip():
        continue
    if line.startswith('S# '):
        cur = {'type': 'h2', 'title': line[3:].strip(), 'paras': [], 'fig_after': {}}
        sections.append(cur)
    elif line.startswith('S3 '):
        cur = {'type': 'h3', 'title': line[3:].strip(), 'paras': [], 'fig_after': {}}
        sections.append(cur)
    elif line.startswith('T '):
        cur['paras'].append(line[2:].strip())
    elif line.startswith('F '):
        sp = line[2:].strip().split('|', 1)
        idx = len(cur['paras']) - 1
        if idx < 0:
            cur['paras'].append('')
            idx = 0
        cur.setdefault('fig_after', {}).setdefault(str(idx), []).append(
            {'src': sp[0].strip(), 'caption': sp[1].strip() if len(sp) > 1 else ''})
    elif line.startswith('C# '):
        code_lang = line[3:].strip()
        code_buf = []
    else:
        raise SystemExit('UNKNOWN LINE: ' + line[:60])

# 去连排：同一节内两图紧邻时中间插入承接段
for s in sections:
    fa = s.get('fig_after', {})
    seq = []
    for i, p in enumerate(s['paras']):
        seq.append(('T', p))
        if str(i) in fa:
            seq += [('F', g) for g in fa[str(i)]]
    out = []
    prev = None
    for k, v in seq:
        if k == 'F' and prev == 'F':
            out.append(('T', '(承接上图)'))
        out.append((k, v))
        prev = k
    np_ = []
    nfa = {}
    idx = -1
    for k, v in out:
        if k == 'T':
            np_.append(v)
            idx = len(np_) - 1
        else:
            nfa.setdefault(str(idx), []).append(v)
    s['paras'] = np_
    s['fig_after'] = nfa

DATA = {
    'title': 'Jev 是什么：从三种输出形式到四种落地模式',

    'summary': [
        {'key': '核心定位',
         'body': 'Jev 不生成文字，只做选择、打分和是非判断；答案自带类型与置信度，同一次调用里的多个问题并行评估。'},
        {'key': '数字口径',
         'body': '输入每百万 token 0.042 美元、输出不计费；提速倍数看基线怎么选，循环里的单次判断约 7 倍，同等条件约 25 倍。'},
        {'key': '真正改变架构',
         'body': '置信度把升级策略变成配置文件里的一个数字，输出免费让逐块、逐行的判断第一次变得付得起。'},
    ],

    'lead': [
        'Jev 是 TypeSafe AI 的 System One 模型：输入一段状态，输出一个带类型的判断，一个字都不写。它的输入价格是每百万 token 0.042 美元，输出不计费，速度比现有模型快 40 到 100 倍。',
        '下面把它的三种输出格式、那些宣传数字该怎么读、置信度为什么才是真正的产品，以及四种已经有人在生产里跑起来的模式，依次说清楚。',
    ],

    'sections': sections,

    'conclusion': [
        '**Jev 真正的产品不是那个标签，而是那个置信度。**分类器只给你一个答案，信不信由你自己扛；Jev 同时给出一个校准过的数字，告诉你允不允许照着它行事。低于 0.3 到 0.5 就停下来找人，这一条把升级策略从系统提示词里的一段话，变成了配置文件里的一个数字。',
        '它还顺手改掉了一个结构性错误：过去整个技术栈里最便宜的那个决定，一直由最贵的东西来做。把路由、压缩、执行前审查这些判断挪到 System One 上，等于让最便宜的决定交给最便宜的东西，而输出不计费让逐块、逐行、逐键的判断第一次变得付得起。',
        '对正在搭智能体的人，起步点很小：找一个现在靠慢调用或者脆弱正则撑着的判断，用代码构造好候选，让 Jev 只负责选。真正要花时间的是选项集和问题措辞，API 调用本身是琐碎的。至于宣传里那句「不会幻觉」，记住它做不到的恰恰是这一点：它不会输出非法类型，但完全可以输出一个合法却错误的值。',
    ],

    'reference_url': 'https://x.com/manish_fp/status/2101325394532266139',
}

out_path = os.path.join(D, 'article_data.json')
with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nfig = 0
bad = []
for si, s in enumerate(sections):
    for k in (s.get('fig_after') or {}):
        if int(k) >= len(s['paras']):
            bad.append((si, k, len(s['paras'])))
    nfig += sum(len(v) for v in (s.get('fig_after') or {}).values())

print('写入 {}'.format(out_path))
print('sections={} paras={} figs={} chars={}'.format(
    len(sections), sum(len(s['paras']) for s in sections), nfig,
    len(json.dumps(DATA, ensure_ascii=False))))
assert not bad, 'fig_after 越界: %s' % bad
print('fig_after 无越界 OK')
