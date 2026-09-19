# -*- coding: utf-8 -*-
import json

d = json.load(open("article_data.json", encoding="utf-8"))
REPL = [
 ("计算低效问题\u2014\u2014这是训练中的常见配置", "计算低效问题，而这是训练中的常见配置"),
 ("将推测解码\u2014\u2014加速 LLM（大语言模型）推理的常用技术\u2014\u2014改造用于", "将推测解码（加速 LLM（大语言模型）推理的常用技术）改造用于"),
 ("比生成它们更快\u2014\u2014尽管使用的是同一个模型\u2014\u2014因为验证可以并行处理", "比生成它们更快（尽管使用的是同一个模型），因为验证可以并行处理"),
 ("草稿器从 token 6 重新开始\u2014\u2014因为验证会给出正确的第 5 个 token", "草稿器从 token 6 重新开始，因为验证会给出正确的第 5 个 token"),
 ("显著更多的 GPU\u2014\u2014不仅要承载多个 draft model，还要验证它们的输出", "显著更多的 GPU：不仅要承载多个 draft model，还要验证它们的输出"),
 ("确定最优 placement\u2014\u2014即分别将多少 worker 分配给草稿生成与验证\u2014\u2014以最小化", "确定最优 placement，即分别将多少 worker 分配给草稿与验证，以最小化"),
 ("为解耦执行建模性能\u2014\u2014token 生成速度（TGS）", "为解耦执行建模性能，即 token 生成速度（TGS）"),
 ("对三种示例 draft 方法\u2014\u2014n-gram、0.5B 与 1.5B 模型草稿生成，先查询", "对三种示例 draft 方法（n-gram、0.5B 与 1.5B 模型草稿），先查询"),
 ("该原语将服务实例\u2014\u2014要么是草稿器，要么是验证器\u2014\u2014部署到特定 worker", "该原语将服务实例（要么是草稿器，要么是验证器）部署到特定 worker"),
 ("新验证器需要一份 KVCache\u2014\u2014LLM（大语言模型）计算的中间结果\u2014\u2014来加速计算", "新验证器需要一份 KVCache（LLM（大语言模型）计算的中间结果）来加速计算"),
 ("实现了 SpecActor\u2014\u2014veRL 是当前最先进的后训练框架", "实现了 SpecActor。veRL 是当前最先进的后训练框架"),
 ("使用 DAPO 训练 Qwen2.5-32B\u2014\u2014DAPO 是 AI 学术界与工业界的热门算法\u2014\u2014每步 batch size", "使用 DAPO 训练 Qwen2.5-32B（DAPO 是 AI 学术界与工业界的热门算法），每步 batch size"),
 ("采样温度设为 1.0\u2014\u2014这是后训练中的常见设置\u2014\u2014但该设置会对推测解码产生负面影响", "采样温度设为 1.0（这是后训练中的常见设置），但该设置会对推测解码产生负面影响"),
 ("端到端训练时间与 rollout 时间\u2014\u2014训练时间是算法开发者最关键的指标", "端到端训练时间与 rollout 时间，其中训练时间是算法开发者最关键的指标"),
 ("Qwen2.5-1.5B\u2014\u2014以及一个 n-gram 草稿器", "Qwen2.5-1.5B，以及一个 n-gram 草稿器"),
 ("per-step batch size 为 256\u2014\u2014受 GPU 显存限制而略小", "per-step batch size 为 256，受 GPU 显存限制而略小"),
 ("这与相反。", "这与依赖训练侧改动的方案相反。"),
 ("0.5B 草稿生成 model", "0.5B 草稿模型"),
 ("1.5B 草稿生成 model", "1.5B 草稿模型"),
 ("选择单一草稿生成方法", "选择单一草稿方法"),
 ("其他草稿生成方法（如 EAGLE）", "其他草稿生成方式（如 EAGLE）"),
 ("利用 profiled 接受率", "利用已做性能分析的接受率"),
 ("这些方法已 profiling 的接受率", "这些方法已做性能分析的接受率"),
 ("草稿器  ", "草稿器 "),
]

def walk(o):
    if isinstance(o, str):
        for a, b in REPL:
            o = o.replace(a, b)
        return o
    if isinstance(o, list): return [walk(x) for x in o]
    if isinstance(o, dict): return {k: walk(v) for k, v in o.items()}
    return o

d = walk(d)
json.dump(d, open("article_data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
s = json.dumps(d, ensure_ascii=False)
print("remaining ——:", s.count("\u2014\u2014"), "single —:", s.count("\u2014") - s.count("\u2014\u2014") * 2)
