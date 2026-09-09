#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""article_data_build.py — LMSYS: Fast JSON Decoding with Compressed FSM"""

import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DEMO = {"src": "demo.gif", "caption": "图1：SGLang 与 Outlines + vLLM 的 JSON 解码对比。"}
SCHEMA_FIG = {"src": "json_schema.png", "caption": "图2：遵循 JSON Schema 的约束生成示例。"}
METHOD1_FIG = {"src": "method1.png", "caption": "图3：基于 FSM 与 logits 掩码的约束解码。第一次约束解码只允许 age；第二次解码时，由于正则要求数字，0 和 1 都被允许，但 LLM 采样 1 的概率更高。"}
METHOD2_FIG = {"src": "method2.png", "caption": "图4：Guidance 中的交织式 JSON 解码。"}
COMPARE_FIG = {"src": "compare.png", "caption": "图5：压缩 FSM 跳跃式解码与普通解码的对比。"}
RESULT_FIG = {"src": "result.png", "caption": "图6：基准测试结果。"}
LLAVA_FIG = {"src": "llava_demo.gif", "caption": "图7：使用 SGLang 与 LLaVA 从图像中提取结构化信息。"}

DATA = {
    "summary": [
        {"key": "核心思路", "body": "把正则 FSM 中确定性的连续转移压缩成单一路径，一次 prefill 多个 token，而不是逐 token 约束解码。"},
        {"key": "实测收益", "body": "相对 guidance + llama.cpp、outlines + vLLM，延迟最多降低 2 倍、吞吐最多提升 2.5 倍，甚至快过普通解码。"},
        {"key": "落地状态", "body": "基于压缩 FSM 的跳跃式解码已集成到 SGLang，兼容任意正则与 JSON/YAML schema。"},
    ],
    "sections": [
        {
            "type": "",
            "title": "",
            "paras": [
                "让 LLM 稳定输出符合特定 schema 的 JSON 或 YAML，是许多应用的关键需求。这里介绍一种显著加速此类约束解码的优化方案：它基于压缩有限状态机，兼容任意正则表达式，因此可适配任意 JSON 或 YAML schema。与 guidance + llama.cpp、outlines + vLLM 等既有系统相比，该方法可以把延迟最多降低 2 倍、吞吐最多提升 2.5 倍，甚至让约束解码比普通解码更快，现已在 SGLang 中开放试用。",
            ],
            "fig_after": {
                "0": [DEMO],
            },
        },
        {
            "type": "h2",
            "title": "背景",
            "paras": [
                "JSON 是最重要的数据交换格式之一。让 LLM 始终输出合法 JSON，输出就能被稳定地结构化解析。OpenAI 正是看到了这一点，推出 JSON mode 来约束模型总是返回合法 JSON 对象；不过很多场景需要更细粒度的控制，确保生成的 JSON 对象符合特定 schema，例如下图中的约束生成示例。",
                "对本地 LLM 而言，目前引导模型生成符合 schema 的 JSON 对象，主要有两类方法。",
            ],
            "fig_after": {
                "0": [SCHEMA_FIG],
            },
        },
        {
            "type": "h3",
            "title": "方法一：基于有限状态机（FSM）",
            "paras": [
                "把 JSON schema 转成正则表达式，再基于正则构造有限状态机 FSM。解码时对 FSM 的每个状态计算允许的转移，找出可接受的下一批 token；跟踪当前状态并用 logit bias 过滤掉非法 token。这一方法的细节可参考 outlines 论文。",
                "FSM 方法用通用正则表达低层规则，可覆盖多种语法，例如 JSON schema、IP 地址和邮箱。",
                "局限在于：FSM 在 token 级构造，每步只能让状态前进一个 token，也就是一次只能解码一个 token，导致解码速度慢。",
            ],
            "fig_after": {
                "0": [METHOD1_FIG],
            },
        },
        {
            "type": "h3",
            "title": "方法二：交织式解码",
            "paras": [
                "另一种思路不把整个 JSON schema 转成一个正则，而是采用交织式解码：把 schema 拆成若干部分，每部分要么是分块 prefill，要么是约束解码段，由推理系统交替执行。分块 prefill 一次前向就能处理多个 token，因此比逐 token 解码更快。",
                "Guidance 为交织式解码提供了一套语法规则，后端使用 llama.cpp。",
                "它的局限一是需要自定义语法，通用性和表达力不如单独的正则表达式。",
                "局限二是 decode 段与分块 prefill 段可能相互冲突，分词边界很难妥善处理。",
                "局限三是解释器与后端之间频繁通信，会带来额外开销。",
            ],
            "fig_after": {
                "1": [METHOD2_FIG],
            },
        },
        {
            "type": "h2",
            "title": "新方法：压缩有限状态机上的跳跃式解码",
            "paras": [
                "跳跃式解码（jump-forward decoding）把两类方法的优点结合起来，算法基础是压缩有限状态机。",
                "在被 schema 正则引导的解码过程中，走到特定节点时，往往能预测后面一定会出现的字符串。",
                "以解码刚开始为例，根据正则就能预判接下来会出现的字符串是：",
                "__CODE__json::{\n  \"name\":",
                "这段固定前缀之后，才轮到真正需要解码的部分。",
                "另一个例子：在填写角色的 house 属性时，LLM 一旦输出 G，就能确定下一个字符串是 ryffindor，从而一次补全为 Gryffindor。",
                "这正是跳跃式解码的加速原理：检查给定正则的 FSM，找出所有单一转移边，把连续的边压缩成单一路径。与其逐 token 解码这些路径，不如直接 prefill（扩展）它们，一路跳到下一个分叉点。",
                "SGLang 的 RadixAttention 机制让跳跃式解码的实现非常简单：执行一次跳跃时，直接终止当前请求并排入一个新请求，RadixAttention 和运行时高效的 extend 原语会自动复用前面 token 的 KV cache，避免重复计算。",
            ],
            "fig_after": {
                "6": [COMPARE_FIG],
            },
        },
        {
            "type": "h3",
            "title": "处理分词边界",
            "paras": [
                "实现约束解码时，字符与 token 之间的映射关系很复杂，分词边界始终是个棘手问题。",
                "LLM 解码时可能更愿意把多个字符合并成一个 token（概率更高）。例如在 JSON 解码语境下输出 Hello 时，模型可能输出这样的 token 序列：",
                "__CODE__\" He llo \",",
                "与其单独解码末尾的引号，模型更倾向于把引号与后面的逗号拼成一个出现频率更高的 token「\",」。这种效应可能引发奇怪行为：如果正则设为「[\\w\\d\\s]*」（不含末尾的「\",」），模型想用「\",」收尾却不被允许，就可能陷入无休止解码。",
                "此外，跳跃式解码时，对跳过的部分采用不同的分词策略，会影响后续 token 的 logit 分布；直接把分词后的跳跃段追加到当前 token 序列，可能得到意外结果。",
                "针对这些问题，作者提出以下对策：",
                "一是在跳跃阶段实现重新分词机制：以字符串而非 token 的形式追加内容，再对整个文本重新分词。这能解决大部分分词问题，计算开销仅增加约 4%。",
                "二是尽量用一条完整正则引导整个解码过程，而不是拼接多条正则。这样 FSM 和 LLM 都清楚完整解码路径，能最大限度减少边界问题。",
            ],
        },
        {
            "type": "h2",
            "title": "基准测试",
            "paras": [
                "跳跃式解码在两个任务上做了评测：",
                "任务一是根据简短 prompt 生成角色的 JSON 数据。",
                "任务二是从长文档中提取城市信息，并以 JSON 格式输出。",
                "测试使用 llama-7B、NVIDIA A10 GPU（24GB），对比 vllm v0.2.7、guidance v0.1.0、outlines v0.2.5 与 llama.cpp v0.2.38（Python binding）。下图展示各系统在最大支持 batch size 下的吞吐，以及 batch size 为 1 时的延迟：",
                "结果显示，采用该解码算法的 SGLang 显著优于其他系统，延迟最多降低 2 倍、吞吐最多提升 2.5 倍。在角色生成任务中，即使是不带跳跃式解码的 SGLang，吞吐也高于 Outlines + vLLM，作者推测这与 Outlines 自身存在额外开销有关。",
            ],
            "fig_after": {
                "3": [RESULT_FIG],
            },
        },
        {
            "type": "h2",
            "title": "落地用例",
            "paras": [
                "Boson.ai 已试用该功能约两周，并把它投入生产场景，因为它能保证响应稳定，同时解码吞吐更高。",
                "另一位用户则借助视觉语言模型 LLaVA，用该功能从图像中提取结构化信息。",
                "目前该功能已在 SGLang 中开放试用，benchmark 代码也已公开。压缩 FSM 的实现建立在 outlines 开源 FSM 实现之上，感谢 outlines 的贡献。",
            ],
            "fig_after": {
                "1": [LLAVA_FIG],
            },
        },
    ],
    "conclusion": [
        "**约束解码的瓶颈不在模型本身，而在把每一步都限制在一个 token 上。** 把 FSM 中已经确定的路径一次性 prefill 掉，本质是让「已知部分」不再逐个 token 去猜，约束带来的安全性与解码速度从对立变成兼得。",
        "对做本地推理与结构化输出的开发者，这里的启发在于：JSON schema 这类硬约束不一定只是负担，把它前移到 FSM 结构里，反而能变成可以跳过的已知路径。当约束解码能比普通解码更快，「格式安全」就不再是牺牲吞吐换来的选项，而会成为默认配置。",
    ],
    "reference_url": "https://www.lmsys.org/blog/2024-02-05-compressed-fsm/",
    "title": "压缩有限状态机：让本地 LLM 的 JSON 约束解码提速两倍",
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"OK wrote {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA['sections'])} sections)")
