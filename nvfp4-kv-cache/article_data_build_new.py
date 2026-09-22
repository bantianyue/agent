#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""nvfp4-kv-cache 文章 build（命令式 builder，fig_after 显式挂图）

2026-09-22 复盘生成：按 SKILL v2.4.6 文风四条（禁第一人称 / 逐句精简 / 禁重复 / 删「它」）
+ 标题排版新规（标题中英之间不加空格、标点一律半角）重写全文。
"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

S = []
def h2(t):
    S.append({"type": "h2", "title": t, "paras": [], "fig_after": {}})
    return S[-1]

def h3(t):
    S.append({"type": "h3", "title": t, "paras": [], "fig_after": {}})
    return S[-1]

def fig(sec, name, caption, idx=-1):
    i = idx if idx >= 0 else max(0, len(sec["paras"]) - 1)
    assert i < len(sec["paras"]), 'fig_after key out of range: %s vs %d paras' % (i, len(sec["paras"]))
    sec.setdefault("fig_after", {}).setdefault(str(i), []).append({"src": name, "caption": caption})

BULLET = '<span style="color:#0F4C81;font-size:7px;line-height:1;vertical-align:middle;">●</span>&nbsp;'
def code(s):
    return '<code style="background:#f3f4f5;padding:2px 5px;border-radius:3px;color:#0F4C81;">' + s + '</code>'

# ── 1. 为什么要给 KV cache 上 4 bit ──
s1 = h2('为什么要给KV cache上4 bit')
s1["paras"] += [
    'KV cache是现代LLM推理系统的基础组件。智能体会话里多轮对话的上下文以key和value的形式缓存在GPU显存中，供后续解码步骤复用：每生成一个新token，新的query都要attend到相关的历史KV。上下文窗口越大，KV cache的存储与读取对显存容量和带宽的压力就越大。',
    '缓解这种压力有两条互补的路：扩大缓存可用的存储，或者减少每个token存储的数据量。',
    'GPU显存给活跃KV数据提供快速访问，容量却有限。服务大量用户或长会话时，无法让所有会话的缓存一直常驻。分层KV缓存HiCache把缓存层级扩展到主机内存和分布式存储，在GPU之外保留更多上下文。',
    'KV cache量化从另一侧解决问题：用FP8而不是BF16存K/V，数据占用大约减半，解码要读的字节数随之减少，KV读取成为带宽瓶颈时能直接转化为性能。代价是数值精度，低位宽带来量化误差，误差必须小到不破坏有用的模型行为。FP8 KV缓存已广泛使用，压到4 bit难得多，因为量化误差更大。',
    'NVIDIA随Blackwell架构引入了NVFP4数据格式。把4 bit E2M1数值与两级缩放结合：每16个值一个FP8 block scale，再加一个FP32张量级scale。相比单一全局scale，这种结构对动态范围的控制更细，有助于压低量化误差；Blackwell硬件也为这一格式提供了原生支持，计算效率与灵活性都适合KV cache量化。',
]
fig(s1, 'fig01.gif', '图1:NVFP4逐块与逐张量两级缩放的量化策略', 4)

# ── 2. SGLang 中的 NVFP4 KV 实现 ──
s2 = h2('SGLang中的NVFP4 KV实现')
s2["paras"] += [
    '实现把SGLang的分页KV cache系统接到三条注意力路径上：初始prefill、分块prefill或extend、decode。SGLang负责管理缓存及其辅助缓冲区，每条路径的数据流各不相同。',
]
fig(s2, 'fig02.png', '图2:SGLang中的NVFP4 KV cache实现', 0)

s2a = h3('路径1:初始prefill')
s2a["paras"] += [
    '初始prefill处理没有缓存前缀的prompt。经过QKV投影和位置编码后，注意力直接作用于当前prompt的BF16 Q与FP8 K/V；同一份K/V同时从FP8量化为NVFP4，写入持久缓存，供后续extend和decode步骤使用。',
    '这条路径里，量化后的NVFP4 KV数据写入缓存，但注意力消费的是量化前的FP8 KV，阶段内不从KV cache读任何数据。',
]

s2b = h3('路径2:分块prefill与extend')
s2b["paras"] += [
    '分块prefill一次只处理prompt的一部分，extend则是向已有上下文追加新token。两者都面对两个K/V来源：缓存前缀和当前分块。',
    '对缓存前缀，SGLang取出相关NVFP4条目，反量化后填充FP8工作区；一对K/V工作区缓冲区跨层共享，避免每层都分配一整份FP8工作区。',
    '当前分块走另一条路：KV数据在QKV投影后拷入FP8工作区，注意力像初始prefill一样作用于工作区里的KV；这份KV同样被量化存入NVFP4缓存，供后续步骤使用。',
]

s2c = h3('路径3:decode')
s2c["paras"] += [
    'decode阶段，注意力kernel直接从NVFP4 KV cache读数据，在kernel内部即时反量化为FP8再参与后续计算，不需要单独的反量化操作。',
    '与prefill不同，decode时query序列长度很短，KV序列长度往往大得多，注意力性能完全受显存读取限制。把反量化放进kernel，省掉了单独反量化操作读写整个KV cache的额外显存往返，性能提升可观。',
]

# ── 3. decode attention kernel ──
s3 = h2('NVFP4 KV decode attention kernel')
s3["paras"] += [
    '当前SM120上的实现消费BF16 query和NVFP4 KV，矩阵乘法在BF16上进行。',
    'kernel先把打包的K/V tile和对应的E4M3 block scale载入共享内存，再在寄存器中解包并缩放：用 ' + code('cvt.rn.bf16x2.e2m1x2') + ' 把成对的E2M1值转成BF16，E4M3 block scale也转型为BF16，打包乘法指令把缩放因子作用到成对的值上；随后注意力矩阵乘法作用于反量化后的K/V，全局K/V scale通过注意力BMM的缩放参数传入。',
]
fig(s3, 'fig03.png', '图3:NVFP4 KV attention decode kernel设计', 1)
s3["paras"] += [
    '每16个NVFP4值占8字节打包数据加1字节block scale元数据，对比FP8的16字节，即(8+1)/16=0.5625：同样的K/V数量，打包数据加block scale只需FP8约56%的存储，这里不计入少量全局scale元数据和池或工作区开销。这正是降低GPU显存读取流量、提升decode效率的空间。',
]

# ── 4. 精度 ──
s4 = h2('精度:大模型几乎无损,小模型按任务看')
s4["paras"] += [
    '精度对比在Qwen3.5-397B-A17B和Qwen3.8-27B上做，基准覆盖GSM8K、GPQA-Diamond、AIME 2025，以及只在Qwen3.8-27B上跑的SWE-bench。两组配置使用相同的FP8模型权重；SGLang里用 ' + code('--kv-cache-dtype nvfp4') + ' 选择NVFP4 KV存储。',
    'GSM8K评测一次，预留8个样本做few-shot提示后共1,311道计分题；GPQA-Diamond和AIME因任务方差较大各评测两轮，下图汇报两轮汇总的准确率。',
    'Qwen3.5-397B-A17B上的差异很小。NVFP4在GSM8K上少对了一道题，差距约0.08个百分点；GPQA-Diamond和AIME 2025的答对题数完全一致。',
]
fig(s4, 'fig04.png', '图4:Qwen3.5-397B-A17B精度基准', 2)
s4["paras"] += [
    'Qwen3.8-27B则表现出任务相关的差异。NVFP4在GSM8K上比FP8低0.31个百分点，GPQA-Diamond低1.01个百分点；AIME 2025在thinking/xhigh模式下与FP8持平，都是98.33%。SWE-bench Verified上NVFP4解决500题中的381题(76.20%)，FP8为389题(77.80%)，差1.60个百分点。',
]
fig(s4, 'fig05.png', '图5:Qwen3.8-27B精度基准', 3)
s4["paras"] += [
    '这次测量里更大模型更不敏感，但两个模型加一小撮任务还不足以确立模型大小与量化容忍度之间的一般关系。结果对NVFP4 KV缓存是正向信号，部署前仍需按任务验证。',
]

# ── 5. 性能 ──
s5 = h2('性能:decode提速,prefill持平')
s5["paras"] += [
    '性能测试在单张NVIDIA RTX PRO 6000 Blackwell Server Edition GPU上跑Qwen3.8-27B，输入长度固定为32,768、163,840和1,048,576 token，每个请求固定输出1,024 token。两组配置使用相同的FP8权重，固定长度测试关闭了radix caching。',
    '1M负载是纯性能实验，用了显式的上下文长度覆盖，模型原生上下文上限是262,144 token。1M时NVFP4的static-memory fraction取0.75，给临时prefill工作区留空间，FP8为0.90；更短的上下文长度下两者都用0.90。',
    '对照点分两组：一组固定实际并发比性能，一组放开并发看容量收益。',
]

s5a = h3('同并发decode:iso-concurrency')
s5a["paras"] += [
    'iso-concurrency测试让FP8与NVFP4 KV在相同的实际decode并发下对比。调度器在32K、160K和1M下都稳定在44、10、1个decode常驻请求。',
]
fig(s5a, 'fig06.png', '图6:Qwen3.8-27B同并发decode性能', 0)
s5a["paras"] += [
    'NVFP4 KV在这些负载下把峰值batch decode吞吐提升约26%到30%。峰值batch大小一致，结果与KV读取流量减少、解码变快的推断一致。',
]

s5b = h3('容量驱动decode:iso-capacity')
s5b["paras"] += [
    'iso-capacity测试把并发继续往上加，用满NVFP4能多驻留的请求。这里的同容量指同一块GPU上容量驱动的对比，两种KV格式可用的KV token槽位数不同。',
    '32K时实际并发从FP8的44提高到NVFP4的70，160K从10到15，1M从1到2；峰值batch decode吞吐分别提升37.37%、57.75%和78.46%。',
]
fig(s5b, 'fig07.png', '图7:Qwen3.8-27B同容量decode性能', 1)
s5b["paras"] += [
    '这些收益来自更紧凑的KV读取加上更大的batch。更高的并发能把注意力之外的矩阵乘法也喂饱。图8的Pareto曲线进一步展示NVFP4 KV的优势：相近并发下，NVFP4 KV的输出吞吐和交互性都更高，同时还能服务更高的并发，把输出吞吐再往上推。',
]
fig(s5b, 'fig08.png', '图8:Qwen3.8-27B 32K/1K ISL/OSL的Pareto曲线', 2)

s5c = h3('prefill性能')
s5c["paras"] += [
    'decode阶段KV cache读取是主要瓶颈，prefill阶段则是计算受限。这套方案只改了KV数据类型，计算数据类型不变，prefill注意力本身没有性能收益。同并发下NVFP4的平均首token延迟(TTFT)只增加了0.20%到0.40%，轻微变慢主要来自KV量化或反量化的开销。',
]
fig(s5c, 'fig09.png', '图9:以TTFT衡量的Qwen3.8-27B prefill性能', 0)
s5c["paras"] += [
    '容量驱动负载下，平均TTFT反而下降0.74%到10.72%。TTFT包含准入、prefill和排队，这部分改善不能只归功于prefill计算变快：更大的常驻缓存让更多请求无需等其他请求释放KV槽位就能推进，例如1M时NVFP4能同时容纳两个完整请求，FP8只能容纳一个。',
    '上面的decode吞吐收益也不应读成端到端加速比。prompt很长时，即使decode明显变快，prefill仍可能主导总耗时。',
]

# ── 6. 智能体负载 ──
s6 = h2('智能体负载:省下来的显存变成缓存命中率')
s6["paras"] += [
    '智能体负载比固定输入输出的基准复杂：多轮之间交替extend和decode，历史里常带工具输出和中间推理，动辄几十万token。KV cache的价值取决于下一轮到来时还有多少历史可用。',
    '需要的前缀一旦从所有可用缓存层级中被逐出，服务端就得重算。对几十万token的上下文，这会明显拉高首token延迟，还占用本可服务新请求的资源。',
    'NVFP4创造了把更多工作集留在GPU上的机会。打包数据的计算给出约1.78倍于FP8的理想容量比，未计工作区等显存开销，实际可用容量取决于负载与服务配置。让更多前缀常驻，能在内存压力本会触发逐出的场景下减少重复prefill。',
    '收益取决于负载的复用模式和服务配置。分层缓存与KV量化可以互补：一个扩展缓存层级，一个压缩层级里内容的大小。',
    'AgentX测试在8卡NVIDIA RTX 6000D节点上以TP8并行跑Qwen3.5-397B-A17B，NVFP4与FP8 KV各扫一遍1到16的并发，基准窗口1,200秒。',
    '结果显示，低并发(C <= 8)时NVFP4 KV与FP8 KV表现相当；并发超过12后，FP8 KV的吞吐和交互性急剧下滑，NVFP4 KV的吞吐仍在上升。',
]
fig(s6, 'fig10.png', '图10:Qwen3.5-397B-A17B上的AgentX性能', 5)
s6["paras"] += [
    '输入token缓存命中率分析给出了证据：高并发下FP8 KV的缓存命中率远低于NVFP4 KV。',
]
fig(s6, 'fig11.png', '图11:Qwen3.5-397B-A17B的AgentX输入token缓存命中率分析', 6)

# ── 7. 限制与进行中的工作 ──
s7 = h2('限制与进行中的工作')
s7["paras"] += [
    'SGLang当前的NVFP4 KV支持仍处于实验阶段，团队在持续改进，现状与进展如下：',
    BULLET + '**GPU架构支持：**目前支持SM12x与SM100/SM103，更多架构的适配在推进中。',
    BULLET + '**模型支持：**支持GQA模型和Sparse MLA模型，正在适配更多类型，例如Sparse GQA。',
    BULLET + '**精度改进：**实验没有使用NVFP4的每张量FP32全局scale，为简单起见取1.0；合适的校准可能减少数值上溢与下溢，进一步收窄NVFP4与FP8 KV的精度差距。团队也在试验朴素NVFP4 KV之外的更多4 bit配方，某些模型上可能进一步提升精度。',
]

DATA = {
    "title": 'SGLang上线NVFP4 KV Cache:decode吞吐最高提升78%',
    "summary": [
        {"key": "是什么", "body": "SGLang、Qwen与NVIDIA把KV cache从FP8压到4 bit NVFP4，K/V存储与读取量约为FP8的56%。"},
        {"key": "关键数据", "body": "Qwen3.8-27B同并发decode吞吐提升26%到30%，容量驱动下最高提升78.46%，prefill几乎不受影响。"},
        {"key": "智能体收益", "body": "AgentX上FP8 KV在并发12后吞吐骤降，NVFP4 KV靠更高的缓存命中率持续扩展。"},
    ],
    "lead": [
        'SGLang、Qwen与NVIDIA联合把KV cache从FP8压到4 bit的NVFP4，K/V读取量降到FP8的约56%，同并发decode吞吐提升26%到30%，容量驱动下最高提升78.46%。',
    ],
    "sections": S,
    "conclusion": [
        '**省下的显存同时换来两样东西：更快的decode和更多常驻请求，这是NVFP4 KV cache最值得记住的地方。**',
        '打包数据加block scale只要FP8约56%的存储，带宽受限的长上下文decode提速26%到30%，容量驱动下最高78.46%；把反量化放进decode kernel，省掉整块KV cache的显存往返，是这轮收益的直接来源。',
        '对做LLM serving的人，AgentX那组数据更关键：高并发下FP8的缓存命中率崩塌、NVFP4仍在持续扩展，4 bit KV的真正红利在智能体负载里，显存省下来变成了prefix命中率，而不是单次decode快的那一点。实验未启用FP32全局scale，校准之后精度差距还有收窄空间，任务级验证仍是上线前的必做项。',
    ],
    "reference_url": 'https://www.lmsys.org/blog/2026-09-16-nvfp4-kv-cache',
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)

nfigs = sum(len(v) for s in S for v in s["fig_after"].values())
nparas = sum(len(s["paras"]) for s in S)
print("sections=%d paras=%d figs=%d -> %s" % (len(S), nparas, nfigs, out_path))
