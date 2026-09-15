# -*- coding: utf-8 -*-
"""content*.txt (S# / H# / T / L / F / B / X) → article_data.json"""
import os
import re
import json

from tables import TABLES

D = os.path.dirname(os.path.abspath(__file__))

BULLET = ('<span style="color:#0F4C81;font-size:7px;line-height:1;'
          'vertical-align:middle;">●</span>&nbsp;')


def parse():
    sections = []
    cur = None
    code_lang = None
    code_lines = []
    files = sorted(f for f in os.listdir(D) if re.fullmatch(r'content\d+\.txt', f))
    for fn in files:
        for raw in open(os.path.join(D, fn), encoding='utf-8'):
            line = raw.rstrip('\n').rstrip('\r')
            if code_lang is not None:
                if line.strip() == 'X-END':
                    cur['paras'].append('__CODE__' + code_lang + '::' + '\n'.join(code_lines))
                    code_lang = None
                    code_lines = []
                else:
                    code_lines.append(line)
                continue
            if not line.strip():
                continue
            if line.startswith('X '):
                code_lang = line[2:].strip()
                code_lines = []
            elif line.startswith('S# '):
                cur = {'type': 'h2', 'title': line[3:].strip(), 'paras': [], 'fig_after': {}}
                sections.append(cur)
            elif line.startswith('H# '):
                cur = {'type': 'h3', 'title': line[3:].strip(), 'paras': [], 'fig_after': {}}
                sections.append(cur)
            elif line.startswith('T '):
                cur['paras'].append(line[2:].strip())
            elif line.startswith('L '):
                cur['paras'].append(BULLET + line[2:].strip())
            elif line.startswith('F '):
                src, _, cap = line[2:].strip().partition('|')
                idx = max(0, len(cur['paras']) - 1)
                cur['fig_after'].setdefault(str(idx), []).append(
                    {'src': src.strip(), 'caption': cap.strip()})
            elif line.startswith('B '):
                cur['table'] = TABLES[line[2:].strip()]
            else:
                raise SystemExit('无法识别的行: ' + line[:60])
    if code_lang is not None:
        raise SystemExit('代码块未闭合')
    return sections


def resequence(sections):
    """图不得连排：相邻两图之间插入承接段，并重算 fig_after 下标。"""
    for s in sections:
        fa = s.get('fig_after') or {}
        seq = []
        for i, p in enumerate(s['paras']):
            seq.append(('T', p))
            for g in fa.get(str(i), []):
                seq.append(('F', g))
        out = []
        prev = None
        for k, v in seq:
            if k == 'F' and prev == 'F':
                out.append(('T', '（承接上图）'))
            out.append((k, v))
            prev = k
        paras, nfa, idx = [], {}, -1
        for k, v in out:
            if k == 'T':
                paras.append(v)
                idx = len(paras) - 1
            else:
                nfa.setdefault(str(idx), []).append(v)
        s['paras'] = paras
        s['fig_after'] = nfa
    return sections


SUMMARY = [
    {'key': '核心机制', 'body': '草稿模型一次猜出多个 token，目标模型用一次前向并行验证，拒绝采样保证输出分布与目标模型完全一致。'},
    {'key': '关键数据', 'body': '8B 通用对话 EAGLE 601 tok/s（1.43x）、代码任务 Suffix 534 tok/s（1.45x）；70B 两个场景 EAGLE-3 分别拿到 1.57x 与 1.60x。'},
    {'key': '选型结论', 'body': '小模型属于计算受限，低开销的 Suffix 更划算；70B 属于显存带宽受限，为 EAGLE-3 投入配置成本能换回最高吞吐。'},
]

LEAD = [
    '大模型推理最慢的地方不在算力，而在顺序：每生成一个 token 都要跑一次完整前向计算，输出越长，等待越久。',
    '推测解码换了一条路：让一个小而快的草稿模型先连续猜出几个 token，再让目标模型用一次前向把它们全部验证完，串行的等待就变成了并行的检查。',
    'vLLM 里已经内置了多种推测解码实现。这篇文章把 N-Gram Matching、Suffix Decoding、EAGLE 与 EAGLE-3 放在 Llama-3.1-8B 与 Llama-3.3-70B 上实测了一遍，数据集覆盖通用对话与代码智能体两类负载，并给出各自的吞吐、时延与加速比。',
]

CONCLUSION = [
    '**推测解码不是新算法，却是当前性价比最高的推理加速手段之一**：改动只发生在解码环节，模型权重不动、输出分布不变，只要接受率够高，省下的时间就直接变成吞吐。',
    '机制上分成两条线。一条是 EAGLE、MLP Speculator 这类学出来的预测器，用草稿头或小幅 MLP 换更高的预测准确率，代价是需要训练或加载检查点；另一条是 N-Gram、Suffix Decoding 这类零权重启发式，用文本重复度换速度，代价是可以忽略的显存与训练成本。',
    '最有说服力的证据是同一个方法在两档模型上的排名翻转：8B 的代码任务里 Suffix 的 534 tok/s 压过了 EAGLE-3 的 379 tok/s，而 70B 的两个场景都由 EAGLE-3 拿下 1.57x 与 1.60x。小模型是计算受限，草稿侧的额外开销会直接吃掉收益；70B 是显存带宽受限，预测得越准等于越少搬运权重，收益被成倍放大。',
    '对做 LLM 服务的人来说，可操作的路径很清楚：先用零成本的 Suffix Decoding 摸一摸自己负载上的天花板，再决定是否为 EAGLE-3 付出配置与调优成本。与其争论哪种方法更强，不如先弄清自己的瓶颈到底在计算还是显存带宽。',
]


def main():
    sections = resequence(parse())
    # 越界断言
    for s in sections:
        for k in s.get('fig_after', {}):
            assert int(k) < len(s['paras']), 'fig_after 越界: %s key=%s paras=%d' % (
                s['title'], k, len(s['paras']))
    data = {
        'title': 'vLLM 推测解码完整指南：四种加速方法的实测对比',
        'summary': SUMMARY,
        'lead': LEAD,
        'sections': sections,
        'conclusion': CONCLUSION,
        'reference_url': 'https://jarvislabs.ai/blog/speculative-decoding-vllm-faster-llm-inference',
    }
    out = os.path.join(D, 'article_data.json')
    with open(out, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    nparas = sum(len(s['paras']) for s in sections)
    nfigs = sum(len(v) for s in sections for v in (s.get('fig_after') or {}).values())
    ntabs = sum(1 for s in sections if s.get('table'))
    ncode = sum(1 for s in sections for p in s['paras'] if p.startswith('__CODE__'))
    nbul = sum(1 for s in sections for p in s['paras'] if 'font-size:7px' in p)
    print('sections=%d paras=%d figs=%d tables=%d codes=%d bullets=%d chars=%d' % (
        len(sections), nparas, nfigs, ntabs, ncode, nbul,
        sum(len(p) for s in sections for p in s['paras'])))


if __name__ == '__main__':
    main()
