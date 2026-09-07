# -*- coding: utf-8 -*-
"""b1: header + 引子/Why-faster first two 节。导入方 exec 后使用本文件导出的 build_api 与 H1。
约定:每 part 定义 make(...) 返回该 part 的 sections list 并入 allS。此处改 exports 供 _make.py 拼。"""

def api(S):
    def h2(t): S.append({"type":"h2","title":t,"paras":[]}); return S[-1]
    def h3(t): S.append({"type":"h3","title":t,"paras":[]}); return S[-1]
    def fig(sec,name,idx,cap):
        sec.setdefault("fig_after",{})[str(idx)]=[{"src":name,"caption":cap}]
    return h2,h3,fig

def build():
    S=[]
    h2,h3,fig=api(S)
    summary=[
     {"key":"它是谁","body":"一页给 LLM 推理加速的『可动手可交互』大学教程(NeurIPS 2026 Education Track):把 speculative decoding 从头讲透——为何快、何为拒绝采样统计无损、怎么评估,再看到四代模型(EAGLE-3/DFlash/DSpark/DFlash 2)一代代拔掉一个瓶颈。"},
     {"key":"最特别的点","body":"页里配了大量可运行交互动画(逐像素画家 vs 扩散画家、四代解码同题竞速)。公众号放不了 iframe,此处以文字完整还原每个动画想传达的机制与结论,并把真正落地的几张静态图一并保留。"},
     {"key":"核心批判视角","body":"『论文里一个接受长度 τ,其实是 token 级分布距离的镜像』——可业界只在编码/数学/聊天上测过,其余 83% 真实流量域从未被量过。作者干脆拉起 LosslessBench,在创意写作/前端/agent 流/护栏等 5 个域试出无损真正失效的洞。"},
    ]
    lead=[
     "你每次让大模型生成文字,背后大概率跑着一个投机解码(speculative decoding)加速器——今天几乎每个托管 LLM 都靠它把吐字变快、把价格打低。它究竟怎么做到『又快又无损』?",
     "这份 NeurIPS 2026 Education Track 的交互大教程(约 4.4 万英文正文、6 张表、大量可播放动画)把全貌摊开:先讲它为什么快、为什么 rejection sampling 在统计上无损;再按 EAGLE-3→DFlash→DSpark→DFlash 2 四代演进,看每代各自拔掉哪个瓶颈;最后深挖『无损在论文里成立、在真实部署里还成立吗、在我们从没测过的 83% 流量域里呢』。原文交互动画极多,本文以文字忠实还原其机制结论,并附上真正落地的数据图。",
     "本编不含原文的『动手部署 lab 逐命令教程』与附录(术语表/References)——那些是教你自己租 GPU 跑的导览,不属于知识主干;需要的可直达原文。",
    ]
    # 引言（含 teaser 动画文字还原）
    sec=h2("引言：每个 token 都在排队")
    sec["paras"]=[
      "今天几乎每个 LLM 都是一次一个 token 往外套的,这叫**自回归解码(autoregressive decoding)**,正是推理最大的瓶颈:要产 n 个 token,得让一个几百亿参数的前向跑 n 趟。",
      "**投机解码(speculative decoding)**(Leviathan et al., 2023)就为加速而来:一个轻量小模型先**草拟**出接下来几个 token,再由大模型**验证**,挨个接受或拒绝。关键结论:验证过的输出与目标模型**自身分布完全相同**(Chen et al., 2023)——这就是『理论上无损』的来源。",
      "页面开场的类比动画(原文可播放,此处还原其点):**自回归的画家逐像素作画;扩散画家更快,因为它一次性把整张画布同时去噪。**于是抛出问题——能否像 diffusion 一样,把一串 token 『一次性并行草拟』,而不是一个接一个地 draft?",
    ]
    sec=h3("为什么要讲它:谁在用、值不值得学")
    sec["paras"]=[
      "第一代投机解码靠一个更小的 draft 模型就提了速,但**草拟本身仍逐 token**。视觉这边 diffusion 已大规模落地:图像**并行生成**而非逐像素描。那 diffusion 式 draft 能不能**并行提出整块 token**,再推快一步?这是后文主线。",
      "如今投机解码跑在**几乎所有托管 LLM 下面**,快慢与质量影响所有人。厂线都在用:OpenAI 2026 给 GPT-5.6 Luna 降价 80%,并把一部分归功于重设计的 draft;Anthropic 'fast mode' 在溢价档把同一 Claude Opus 跑快 2.5×;DeepSeek 随引擎附 DSpark+51% 吞吐;Kimi K3 随发自家 draft。",
      "它的受众门槛极低:**只要你知道『LLM 一次吐一个 token』就够了**。三节层层递进:① 怎么演化(原理/为何理论无损/四代怎么叠);② 何时仍旧无损(引出 LosslessBench,教你自己跑);③ 接下来?(加速推理新方向)。",
    ]
    sec=h3("你会带走的一条线索")
    sec["paras"]=[
      "按 NeurIPS/ICML 时间线:blockwise parallel decoding(NeurIPS 2018)→ 无损投机解码(ICML 2023)→ EAGLE-3(NeurIPS 2025)→ DFlash(ICML 2026)→ DSpark / DFlash 2。一步一步把『draft 模型该怎么长、验证该多严谨、瓶颈在哪』串成体系。",
    ]
    # Why-faster
    sec=h2("它为什么比朴素解码快")
    sec["paras"]=[
      "一块轻量 draft 模型赌出接下来 γ 个 token(通常 3–8 个),目标模型在**一次前向里打包验证全部 γ 个**——成本接近只解一个 token。速度来自三处——draft 越准接受越多、越聪明的验证越少浪费算力在坏草稿上、以及草拟本身若能并行。Figure 1(原页为动画/静态画幅)把两种模式摆一起:朴素每 pass 只出一个 token,投机让草稿出一小段再由目标模型打包校验。",
    ]
    S[:]=[]
    return S
H1=build()
# 段/执行锚点: b1 完成后 把这一段放给 make 用
