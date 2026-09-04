# -*- coding: utf-8 -*-
"""Custom Base Die HBM 标准模板 build（原文100%保留·全中文）"""
import json, os, sys
_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
tr=json.load(open(os.path.join(_article_dir,"_translations.json"),encoding="utf-8"))

DATA = {
  "title": "🔧 定制 Base Die 如何驱动 HBM 带宽：谁才是受益者",
  "summary": [
    {"key":"趋势","body":"HBM 性能与堆叠高度脱钩，容量被当成需要绕开的问题，业界正转向用「定制 Base Die」而非堆更多层来突破带宽。"},
    {"key":"瓶颈","body":"内存厂推通道速度力不从心：三星 HBM3e 认证难、SK Hynix HBM4 致 Rubin 延迟、美光基底节点选择落后。"},
    {"key":"转折","body":"NVIDIA 推出定制 NVHBM——内存控制器移入定制基die，带宽比 HBM4e 高 30%、功耗降 15%；受益者是掌握电路设计的 NVIDIA/Broadcom/AMD/Marvell。"},
  ],
  "lead": [
    "一个显著趋势是 **HBM 性能与堆叠高度正在脱钩**：过去一个月 Rubin Ultra 把 HBM 从 12 层降至 8 层的报道表明，业界已把容量当作「要绕开的问题」而不是要堆高的目标。真正的瓶颈在带宽，而答案藏在定制 Base Die（基die/基础晶圆）。",
    "本文为 X 博主 Vikram Sekar 的同题长文，**7 张原图全收录**。",
  ],
  "sections": [
    {"type":"h2","title":"HBM 带宽的艰难之路","paras":[
      tr["0"],
      tr["1"],
      tr["3"],
    ],"fig_after":{2:[{"src":"fig01.png","caption":"图1：来源——三星，Hot Chips 2026"}]}},
    {"type":"h3","title":"内存厂商在 HBM 高速 PHY 上节节受挫","paras":[
      tr["6"],
      "· " + tr["7"],
      "· " + tr["8"],
      "· " + tr["9"],
      tr["10"],
    ],"fig_after":{3:[{"src":"fig02.jpg","caption":"图2：全球 HBM 市场份额（Counterpoint Research）"}]}},
    {"type":"h3","title":"HBM4 市场到达的均衡","paras":[
      tr["12"],
    ]},
    {"type":"h2","title":"PHY 设计：GDDR 与 HBM 对比","paras":[
      tr["14"],
      "· " + tr["15"],
      "· " + tr["16"],
      tr["17"],
    ],"fig_after":{3:[{"src":"fig03.png","caption":"图3：Rambus 提供的 GDDR6 与 HBM2 设计对比表"}]}},
    {"type":"h3","title":"HBM 与 XPU 协同的严苛环境","paras":[
      tr["19"],
    ]},
    {"type":"h2","title":"NVHBM：业余时代结束","paras":[
      tr["21"],
      "> " + tr["22"],
      tr["23"],
      tr["24"],
    ],"fig_after":{3:[{"src":"fig04.png","caption":"图4：NVIDIA 定制 NVHBM 示意图"}]}},
    {"type":"h3","title":"NVHBM 的性能声明","paras":[
      tr["26"],
    ],"fig_after":{0:[{"src":"fig05.png","caption":"图5：NVIDIA 技术博客性能对比"}]}},
    {"type":"h3","title":"带宽提升与电路设计研究","paras":[
      tr["29"],
      tr["31"],
    ],"fig_after":{1:[{"src":"fig06.jpg","caption":"图6：NVIDIA 在《固态电路杂志》发表的高速 die-to-die 接口研究"}]}},
    {"type":"h3","title":"谁才是真正的受益者","paras":[
      tr["33"],
    ],"fig_after":{0:[{"src":"fig07.jpg","caption":"图7：定制 Base Die——掌握在电路设计公司手中"}]}},
  ],
  "conclusion": [
    "HBM 的下一场竞争已从「谁堆更高层」转向「谁来设计决定带宽与功耗的 Base Die」。内存厂在高速 PHY 上的集体乏力，恰恰给了 NVIDIA 借助定制 NVHBM「打进内存行业」的窗口。",
    "数字很说明问题：**30% 更高带宽、每引脚超 20 Gbps、功耗降 15%**。当内存控制器从 XPU 移入定制基die、PHY 在两处都缩小，真正的受益者浮现——不是堆叠的记忆体厂，而是掌握全球顶尖电路设计能力的 NVIDIA、Broadcom、AMD 与 Marvell。",
  ],
  "reference_url": "https://x.com/vikramskr/status/2094749612498440653",
  "reference_extra": "完整版含价值拆分与 DRAM 堆叠对比，见原文 Substack：viksnewsletter.com/p/hot-chips-2026-tuning-into（付费）",
}

out_path = os.path.join(_article_dir, "article_data.json")
os.makedirs(_article_dir, exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
toti=sum(len(s['paras']) for s in DATA['sections'])
figs=sum(len(v) for s in DATA['sections'] for v in s.get('fig_after',{}).values() if isinstance(v,list))
print(f"✅ {len(DATA['sections'])} sections, {toti} paras, {figs} 图")
