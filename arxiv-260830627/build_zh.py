# -*- coding: utf-8 -*-
"""构建 REER-PT 论文中文编译版（4图全保留）"""
import os, re
base=r"D:/06_Hermes/articles/arxiv-260830627"
OUT=[]
def add(s): OUT.append(s)
def img(n,cap=None):
    add(f'<img src="figs/figure{n:02d}.png" style="max-width:100%;margin:8px 0;border-radius:6px;"/>')
    if cap: add(f'<p style="font-size:12px;color:#777;text-align:center;margin:0 0 10px;line-height:1.5;">{cap}</p>')
def para(t): add(f'<p style="font-size:15px;line-height:1.9;color:#333;margin:10px 0;text-align:justify;">{t}</p>')
def h1(t): add(f'<h1 style="font-weight:bold;font-size:24px;color:#111;margin:16px 0 6px;line-height:1.4;">{t}</h1>')
def h2(t): add(f'<h2 style="font-weight:bold;font-size:19px;color:#0a7d91;margin:24px 0 10px;padding-bottom:6px;border-bottom:2px solid #e0f0f0;">{t}</h2>')
def h3(t): add(f'<h3 style="font-weight:bold;font-size:16px;color:#111;margin:16px 0 6px;">{t}</h3>')

add('<section style="background:#ffffff;font-family:-apple-system,BlinkMacSystemFont,\'Helvetica Neue\',\'PingFang SC\',\'Microsoft YaHei\',sans-serif;max-width:100%;box-sizing:border-box;">')
h1('🧠 REER-PT：给预训练数据"注入推理"——用困惑度引导的数据增强新范式')
add('<p style="font-size:13px;color:#888;margin:0 0 16px;">🗂️ 论文解读 · arXiv:2608.30627 · 北京大学 × ByteDance Seed · 2026-08-31</p>')

h2('核心问题：高质量训练数据已成瓶颈')
para('大语言模型的能力主要来自在海量文本上的 next-token（下一个词元）预测。但随着算力持续提升，<strong>高质量训练数据正成为越来越重要的瓶颈</strong>。传统的预训练只教会模型"文本后面跟的是什么"，却几乎不解释"为什么会这样续写"——那层连接上下文与续写的中间推理，是隐式地缺位的。')

para('有人尝试用思维链（CoT）数据补足推理信号，但多数 CoT 数据集来自人工整理的问答对，规模和领域覆盖都有限。相比之下，预训练语料本身横跨各种主题、文风与篇章形式。<strong>如果能直接从语料中合成推理注释</strong>，就能以可扩展的方式为无数领域补充推理信号，而无需为每个领域单独设计任务。')

para('现有"推理感知预训练"研究存在两个现实难题：一是<strong>稠密或在线推理生成在语料规模下代价高昂</strong>；二是<strong>流畅的模型生成注释未必有用</strong>——它可能冗余、与上下文关联弱，或与实际困难点无关。同时，高损失 token 并不总是推理机会，有些是因为引入了任意名字、日期、标识符或外部事实而难以预测。因此有效的语料增强，既要判断"哪里需要推理"，也要判断"提出的注释能否让续写更好预测"。')

h2('方法：REER-PT 框架（三步流水线）')
para('<strong>REER-PT（Reverse-Engineered Reasoning for Pre-Training）</strong>把反向工程推理（REER）从"问答响应"扩展到"文档续写"。核心思想：对预训练原始文档，<strong>找出难以预测、但仍能从上下文推断的续写位置，插入一条简洁的、读书笔记风格的推理注释</strong>，重建上下文到续写之间缺失的衔接。这条注释不透露目标内容，但能让原本高困惑度的续写变得更好预测。')
img(1,'图 1：REER-PT 增强示意图。给高困惑度的续写插入一条简洁推理注释，使隐式过渡显式化，降低其预测困惑度。')
para('整个过程<b>离线</b>完成，源文本完全保留，因此增强后的语料仍可直接用标准 next-token 预测训练，无需在线推理 rollout。')

h3('① 插入位置选择')
para('先把每个文档切分为句子，用句子级困惑度给候选位置排序，困惑度越高说明过渡越难预测。但高困惑度不保证续写能从上下文推断——有些句子引入的是任意名字/标识符/外部事实。因此注释模型会做"上下文可推断性检查"，过滤掉无法由上下文支撑的位置。<strong>最终留下的位置，既难预测、又在上下文上可推断</strong>。')
img(2,'图 2：REER-PT 流水线全貌。按句子级困惑度给候选位置排序，用上下文可推断性过滤，用续写困惑度生成并精修注释，最后插入源文档。')

h3('② 注释生成与精修')
para('对每个选中位置，注释模型先生成多条<strong>读书笔记风格</strong>的初始注释（第三人称/无人称叙述，摘要上下文相关信息、点明缺失的衔接、说明续写为何顺理成章，同时不措辞复述续写内容）。精修前，先过滤掉超长（正常每条约 500-1000 词）或<strong>存在目标泄漏</strong>的注释——目标泄漏指注释直接重复或复述了续写里的词/事实，那会通过"提前剧透"而非"讲清衔接"来降低困惑度，是无效的。')
para('随后按 REER 原则，<strong>以观察续写的困惑度作为优化信号</strong>：如果注释抓住了从上下文到续写的有用依赖，那么以它为条件应该能降低续写的困惑度。作者把注释切分成多段，逐段用模型改写候选、取续写困惑度最低者；全部轨迹完成后，选中整体困惑度最低的注释。若它比"无注释基线"困惑度还高，就丢弃该位置不插入。')
para('每条被接受的注释用专门的边界标记 &lt;annotation_begin&gt;/&lt;annotation_end&gt; 括起来，插在其目标续写之前。所有源 token 原样不动、顺序不变，增强语料在预训练前一次性固定。')

h3('③ 定量设计')
para('作者用困惑度模型提供逐 token 概率来选位置、评估注释；注释模型负责可推断性检查和生成改写。可用目标模型自身做困惑度模型（on-policy），也可用独立的困惑度模型（off-policy）。对 1000 token 的文档约选 K=⌊T/1000⌋ 个插入位置。')

h2('实验结果')
h3('困惑度分析')
para('在全局与局部两个尺度上，每一次对比都带来正面的困惑度下降。全局上，优化后的注释使完整增强数据的困惑度相对无注释<strong>降低 7.285</strong>、原始 token 困惑度降低 1.031；与初始注释相比，困惑度引导的精修又进一步降低 0.488（完整数据）和 0.422（原始 token）。局部上，优化注释使被选续写的困惑度相对无注释降低 4.235、相对初始注释降低 1.385。<strong>综合困惑度下降区间为 0.42 到 7.29。</strong>')
img(3,'图 3：不同注释条件与评估范围下的困惑度分布。优化后的分布整体左移，说明增强使预测更顺畅。')
para('与此同时，文本内部的 13-gram 自重复率和注释到源文档的精确重合率都很低：注释自重复率均值 0.203%（源文档为 0.615%），注释与源文本的精确 13-gram 重合率仅 <strong>0.051%</strong>——说明几乎没有逐字抄写。')

h2('预训练对比实验')
para('作者用 23B-token 源语料 + 500B 通用语料组成原始混合；REER-PT 把源语料替换为其 42B-token 增强版。从零各训练一个 <strong>680M 参数</strong>模型（相同架构/tokenizer/优化器配置），分别作为 raw baseline 和 augmented-data 模型。')
img(4,'图 4：训练动态对比。左/中分别为原始训练损失与梯度范数，右为 100B token 后的 EMA 平滑损失。增强模型在训练后期一般达到更低的损失。')
para('<strong>训练动态</strong>：两模型梯度范数轨迹相似，但增强数据模型在训练后期普遍达到更低训练损失。')
para('<strong>基准成绩</strong>：在知识、通用推理、STEM 推理类目均有正面提升。BBH 与 GPQA-Diamond 各提升 <strong>+2.07</strong> 个百分点，MATH +1.50、OlympiadBench +1.49、DROP +1.40、MMLU-Pro +0.90，其余 C-Eval/SuperGPQA/Chinese SimpleQA/ZebraLogic 等小幅 +0.36~0.60。')
para('<strong>代码类目回落</strong>：三个代码基准全部下降——MBPP+ −2.65、HumanEval+ −1.83、LiveCodeBench −1.79。案例分析显示，向代码文档插入自然语言注释会打乱局部程序结构，促使模型把解释性文本与可执行代码混在一起，从而在要求简洁、语法严谨代码的基准上失分。这为未来针对代码文档设计专用推理注释格式留出了空间。')

h2('局限与展望')
para('实验仅用 680M 模型和单一预训练配方，更大规模下的行为未知；数据构建依赖困惑度模型与注释模型这两个选择；当前读书笔记式格式主要针对自然语言文档，在代码中会破坏结构。<strong>未来工作</strong>应研究更大规模训练、注释密度、不同 PPL/注释模型的组合，并开发面向代码等专门领域的结构感知注释格式，识别哪些隐式依赖最受益于显式推理注释。')

h2('一句话总结')
para('<strong>REER-PT 用"困惑度引导 + 反向工程推理"给预训练数据稀疏地注入简洁推理注释：不改标准训练目标、不采在线滚动，就能在知识/推理基准上带来最高 2.07 个百分点的提升，同时几乎不引入重复或抄袭。短板是代码类任务回落——自然语言注释会打乱程序结构。</strong>')

add('<div style="margin-top:26px;padding:14px;background:#f5f0eb;border-radius:6px;font-size:13px;color:#555;line-height:1.7;">'
    '<strong>📌 论文信息</strong><br>REER-PT: Reverse-Engineered Reasoning for Perplexity-Guided Pre-training Data Augmentation<br>'
    '作者：Haoran Que 等（北京大学 × ByteDance Seed）· arXiv:2608.30627 · 2026-08-31<br>'
    '本文为论文解读编译，4 张原图全保留。链接：https://arxiv.org/pdf/2608.30627</div>')
add('</section>')
html=''.join(OUT)
open(base+"/article_zh.html","w",encoding="utf-8").write(html)
zh=len(re.findall(r'[\u4e00-\u9fff]',html))
nfig=len(re.findall(r'figure\d+\.png',html))
print(f"✅ len:{len(html)} 中文:{zh} 图:{nfig}/4")
