# -*- coding: utf-8 -*-
"""Hot Chips 2026 全文编译 —— 手动完整 build"""
import json, os, sys, re
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
t=json.load(open(os.path.join(_article_dir,"_trans.json"),encoding="utf-8"))
tr={int(k):v for k,v in t.items()}
def P(i): return tr[i]
def fig(src,caption): return {"src":src,"caption":caption}

DATA = {
  "title":"Hot Chips 2026 全景拆解：内存六路破困、CPU 五种答案，机架取代芯片",
  "summary":[
    {"key":"内存","body":"内存日 6 家公司给 6 条路线：基底 die 算逻辑、计算叠 DRAM、HBF 叠闪存、库内 PIM、RISC-V 近内存。距量产 2-4 年，难解当下短缺。"},
    {"key":"CPU","body":"主机 CPU 定位五家各异：NVIDIA 要极低延迟、Intel 走 256 核吞吐、Arm/Fujitsu 拥抱生态与低成本、IBM 双 ISA 求软件存活。"},
    {"key":"GPU与系统","body":"机架取代芯片成产品：Rubin 抢 token 速度（解码高交互端 30×）、AMD 拼每 MW、Spectrum-X 用多平面与 CPO；ASIC 靠大 SRAM+低跳拓扑收敛。"},
  ],
  "lead":[
    "Hot Chips 是斯坦福三天芯片会议，架构师在此公布最新设计——从内存、CPU、GPU、网络到定制加速器。**它直接给出最重要公司的路线图，决定组件需求，今年内存尤为突出**。本篇把三份日报按主题整合成完整分析。",
    "一线视角的全中文编译：**6 条缓解内存带宽的方案、5 个对主机 CPU 的答案、机架级吞吐-交互曲线取代单芯规格成为记分牌**。25 张关键图表全部还原。",
  ],
  "sections":[
    {"type":"h2","title":"这份全景能读到什么","paras":[P(0),P(1),P(2)]},

    # ========== 内存 ==========
    {"type":"h2","title":"内存日：六条破解同一瓶颈的路线","paras":[P(11)]},
    {"type":"h3","title":"HBM 基础：高并行怎么来的","paras":[P(13),P(14)],
      "fig_after":{1:[fig("fig01.jpg","图1 · HBM 上千条走线并行，代价是面积与散热")]}},
    {"type":"h3","title":"HBM 的代价与演进","paras":[P(15),P(16)],
      "fig_after":{0:[fig("fig02.jpg","图2 · HBM 规格随时间演进")]}},
    {"type":"h3","title":"三星定制 HBM：把计算搬上基底 die","paras":[P(18),P(19),P(20),P(21),P(22)],
      "fig_after":{2:[fig("fig03.jpg","图3 · 三星 HBM 基底 die 走向计算 + zHBM(2030+) 混合键合")]}},
    {"type":"h3","title":"SK 海力士 HBM 封装","paras":[P(25)],
      "fig_after":{0:[fig("fig04.jpg","图4 · 键合技术从 MR-MUF 走向 TC-NCF(实际用)")]}},
    {"type":"p","paras":[P(26)]},
    {"type":"h3","title":"d-Matrix 3D DRAM：算力直接叠内存","paras":[P(28),P(29)],
      "fig_after":{1:[fig("fig05.jpg","图5 · 逻辑叠 DRAM，无滩头限制的垂直带宽")]}},
    {"type":"p","paras":[P(30),P(31)]},
    {"type":"h3","title":"高带宽闪存 HBF：系统的现实检验","paras":[P(33)],
      "fig_after":{0:[fig("fig06.jpg","图6 · HBF 同成本 8-16 倍 HBM 容量，但带宽受限")]}},
    {"type":"p","paras":[P(34),P(35),P(36),P(37)]},
    {"type":"h3","title":"三星 LPDDR5X-PIM：库内一小块计算","paras":[P(39)],
      "fig_after":{0:[fig("fig07.jpg","图7 · 每个 DRAM 库旁小逻辑块，8 倍内部带宽")]}},
    {"type":"p","paras":[P(40),P(41)]},
    {"type":"h3","title":"XCENA MX1：CXL 上 3,072 个 RISC-V 核","paras":[P(43),P(44),P(45)],
      "fig_after":{1:[fig("fig08.jpg","图8 · MX1 近内存 RISC-V 核心做数据缩减；KV attention 百K 上下文提速 3.35×")]}},
    {"type":"p","paras":[P(46)]},
    {"type":"h3","title":"内存日结论","paras":[P(48),P(49)]},

    # ========== CPU ==========
    {"type":"h2","title":"CPU 日：主机处理器之争","paras":[P(51)]},
    {"type":"h3","title":"IBM Z / LinuxONE：双 ISA 求生","paras":[P(53)],
      "fig_after":{0:[fig("fig09.jpg","图9 · 双 ISA 核同时跑 z/Architecture 与 Arm v9.3，扩软件生态")]}},
    {"type":"p","paras":[P(54)]},
    {"type":"h3","title":"Intel Wildcat Lake：客户端上的 UCIe","paras":[P(56)],
      "fig_after":{0:[fig("fig10.jpg","图10 · 廉价有机封装上的 UCIe 互连（首个主流客户端）")]}},
    {"type":"p","paras":[P(57)]},
    {"type":"h3","title":"NVIDIA Vera：极速单线程的赌注","paras":[P(59),P(60)],
      "fig_after":{1:[fig("fig11.jpg","图11 · 空间多线程×88 核 Olympus，求低延迟确定性")]}},
    {"type":"p","paras":[P(61),P(62)]},
    {"type":"h3","title":"富士通 MONAKA：让 5nm 以下不值钱的工艺退出","paras":[P(64)],
      "fig_after":{0:[fig("fig12.jpg","图12 · 144 核，<30% 硅片用领先工艺省成本")]}},
    {"type":"p","paras":[P(65)]},
    {"type":"h3","title":"Arm AGI：Arm 首次自己做芯片","paras":[P(67)],
      "fig_after":{0:[fig("fig13.jpg","图13 · Arm 自家成品 CPU，Meta 为主客户")]}},
    {"type":"p","paras":[P(68)]},
    {"type":"h3","title":"Intel Diamond Rapids：规格面几乎顶格","paras":[P(70),P(71),P(72)],
      "fig_after":{1:[fig("fig14.jpg","图14 · 1.28GB 末级缓存 / 256 核 / 全 Intel 自造")]}},
    {"type":"p","paras":[P(73)]},
    {"type":"h3","title":"CPU 日结论：主机 CPU 到底是什么，没有共识","paras":[P(75)]},

    # ========== GPU ==========
    {"type":"h2","title":"GPU：机架取代芯片成为产品","paras":[P(77)]},
    {"type":"h3","title":"NVIDIA Rubin：专抢 token 速度","paras":[P(79)],
      "fig_after":{0:[fig("fig15.jpg","图15 · 高交互端每 MW 吞吐大幅提升（30× 战略核心）")]}},
    {"type":"p","paras":[P(80),P(81),P(82)]},
    {"type":"p","title":"NVLink 是护城河：大扩展域撑起专家并行","paras":[P(83)],
      "fig_after":{0:[fig("fig16.jpg","图16 · NVLink 扩展域规模 = 经济效益")]}},
    {"type":"p","paras":[P(84)]},
    {"type":"h3","title":"AMD MI400 与 Helios：72-GPU 机架硬刚","paras":[P(86)],
      "fig_after":{0:[fig("fig17.jpg","图17 · Helios：内存 31TB vs 21TB、横扩 43 vs 28.8 TB/s")]}},
    {"type":"p","paras":[P(87),P(88),P(89),P(90),P(91)]},
    {"type":"h3","title":"Intel Crescent Island：没有 HBM 的数据中心 GPU","paras":[P(93)],
      "fig_after":{0:[fig("fig18.jpg","图18 · 350W / 512GB LPDDR5X / 风冷 / PCIe 纵向扩展")]}},
    {"type":"p","paras":[P(94)]},
    {"type":"h3","title":"GPU 日结论","paras":[P(96),P(97)]},

    # ========== 网络 ==========
    {"type":"h2","title":"网络：一台体系里已没有单一网络","paras":[P(99)]},
    {"type":"h3","title":"Broadcom Thor Ultra：商用阵营开场","paras":[P(101)],
      "fig_after":{0:[fig("fig19.jpg","图19 · 800G NIC / PCIe Gen6 / 5nm / 40-42W")]}},
    {"type":"p","paras":[P(102)]},
    {"type":"h3","title":"NVIDIA BlueField-4：向内扩展","paras":[P(104)],
      "fig_after":{0:[fig("fig20.jpg","图20 · Grace CPU + ConnectX-9 NIC 的 AI DPU")]}},
    {"type":"p","paras":[P(105),P(106)]},
    {"type":"h3","title":"NVIDIA Spectrum-X：多平面拓扑","paras":[P(108),P(109),P(110)],
      "fig_after":{2:[fig("fig21.jpg","图21 · 多平面网络：故障保留 90% 带宽、交换机减 1.7×")]}},
    {"type":"p","paras":[P(111)]},
    {"type":"h3","title":"网络日结论","paras":[P(113),P(114)]},

    # ========== ASIC ==========
    {"type":"h2","title":"ASIC：挑战者的共同诊断","paras":[P(116)]},
    {"type":"h3","title":"Cerebras CS-4 / CS-6：旗舰晶圆押注带宽","paras":[P(118),P(119)],
      "fig_after":{1:[fig("fig22.jpg","图22 · 3 片 WSE-3 Turbo：750 PFLOPS / 132GB SRAM / 129.6 PB/s")]}},
    {"type":"p","paras":[P(120),P(121)]},
    {"type":"h3","title":"SambaNova SN50：decode 专用专家","paras":[P(123)],
      "fig_after":{0:[fig("fig23.jpg","图23 · 432MB 片上 SRAM + 64GB HBM 的解码专家")]}},
    {"type":"p","paras":[P(124)]},
    {"type":"h3","title":"Google TPU v8：终于分训练与推理","paras":[P(126),P(127),P(128)],
      "fig_after":{2:[fig("fig24.jpg","图24 · 8i 大量 SRAM+BW；BoardFly 每 pod 1,152 芯片≤7 跳")]}},
    {"type":"p","paras":[P(129)]},
    {"type":"h3","title":"OpenAI Jalapeño：9 个月流片才是重点","paras":[P(131),P(132),P(133),P(134)],
      "fig_after":{2:[fig("fig25.jpg","图25 · 128 颗棋盘 1PB/s；9 个月极小团队流片 + AI 芯片")]}},
    {"type":"p","paras":[P(135)]},
    {"type":"h3","title":"ASIC 日结论","paras":[P(137)]},

    # ========== 会议要点 ==========
    {"type":"h2","title":"四个结论：Hot Chips 2026 的信号","paras":[P(139)]},
    {"type":"h3","title":"资本主义正在逼近内存加价","paras":[P(141),P(142)]},
    {"type":"h3","title":"解聚正在吞噬推理","paras":[P(144),P(145),P(146)]},
    {"type":"h3","title":"AI 正进军芯片设计本身","paras":[P(148),P(149)]},
    {"type":"h3","title":"前沿制程只留给逻辑","paras":[P(151),P(152)]},
  ],
  "conclusion":[
    "Hot Chips 2026 拼出三个更大的信号：**内存短缺靠资本与创新缓解、推理被拆成专用阶段各自优化、AI 亲自入场设计芯片**。GPU 时代「单芯规格决定一切」的旧规则，已让位给机架级系统与吞吐交互曲线。",
    "对中国芯片圈最有分量的是 Diamond Rapids 的全自给路径、Fujitsu 与 Intel 对成本生态的现实主义，以及 OpenAI 把芯片设计压进 9 个月的实验——竞争门槛正从人才转向工具。",
  ],
  "reference_url":"https://x.com/jasonschips/status/2095084434185924625",
}

out_path = os.path.join(_article_dir,"article_data.json")
with open(out_path,"w",encoding="utf-8") as f: json.dump(DATA,f,ensure_ascii=False,indent=2)

# 图引用校验
refd=[]
for s in DATA["sections"]:
    for v in (s.get("fig_after") or {}).values():
        for fi in v: refd.append(fi["src"])
have={f for f in os.listdir(_article_dir) if f.startswith("fig") and f.endswith(".jpg")}
used=set(refd)
print(f"sections={len(DATA['sections'])} paras={sum(len(s.get('paras',[])) for s in DATA['sections'])}")
print(f"figs_ref={len(refd)} unique={len(used)} have_on_disk={len(have)}")
miss=have-used; extra=used-have
print("fig 未引用:", sorted(miss) if miss else "无")
