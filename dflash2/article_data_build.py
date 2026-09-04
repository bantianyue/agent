# -*- coding: utf-8 -*-
"""DFlash 2 编译 build"""
import json, os, sys

DATA = {
 "title": "DFlash 2：继续并行起草——每次验证多出 20% 输出，代价只有 1% 延迟",
 "lead": [
  "推理是 agent 时代的瓶颈。agent 阅读、规划、调用工具，常常持续数小时或数天。它们消耗 token 的速率是聊天从未接近的。每一个 token 都需要对模型做一次完整前向。在 Inco AI，我们正在构建扩展到明天 token 经济学的推理栈。这篇文章是个预览。",
  "我们的团队一月份发布了 DFlash；它现在运行在 SGLang、vLLM、TensorRT-LLM 和 llama.cpp 中。NVIDIA 用它在 Blackwell GPU 上测到最高 15× 吞吐；Google 报告 TPU 上每秒 token 多 3×；CoreWeave 的生产 Kimi K2.7 Code 端点默认运行 DFlash。生态正在它之上构建：NVIDIA、Red Hat、Modal 都发布了 DFlash drafters；Meta、Poolside、Xiaomi、NVIDIA 用自己的模型发布了官方 drafters。在 Hugging Face 上，DFlash 模型下载超过 350 万次（截至 2026 年 8 月）。",
  "投机解码是现代推理栈的核心。小 draft 模型猜一块 token，目标模型一次前向验证整块。好猜把一次前向变成几个 token；坏猜只是被扔掉。多年以来，draft 本身保持自回归：一次一个 token。DFlash 让它也变一次前向：整块、每个位置、并行预测。",
  "DFlash 2 把并行起草再推进一步：**每次验证多出 20% 以上输出，代价约 1% 的循环延迟，且输出可证明不变**。跨基准增益 16-25%。随着今天发布的 Qwen3.8-27B drafter，SGLang 在 batch size 1 下以**自回归解码 2.7-3.4× 的吞吐**服务。独立预测每个位置在两方面留了余量：选对 token、把准确率保持到块尾。DFlash 2 在不放弃一次前向设计的前提下恢复两者。"
 ],
 "summary": [
  {
   "key": "核心",
   "body": "DFlash 2 = DFlash（一次性并行投机解码）+ 轻量路径选择器 + 两 tap 动态卷积。选择器从 top16 候选中选出连贯路径（+0.34-0.47 token）；卷积吸收块内局部依赖（后 2 tap 恢复 15L 大部分收益）。"
  },
  {
   "key": "数据",
   "body": "Qwen3.8-27B：DFlash 2 比 MTP +0.52、比 DSpark +1.18 mean 接受长度，2.7-3.4× 自回归吞吐。Muse Glimmer：比 DFlash +1.26、比 DSpark +1.22。总开销仅 1.3% 循环延迟。"
  },
  {
   "key": "洞见",
   "body": "正确的 token 早已在 DFlash 候选里（Recall@16 首位置 99.5%），缺的是选择而非预测——选择比预测便宜 40× 参数、16× 延迟。后缀衰减是局部问题（块内依赖），两 tap 卷积就能修复。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "立即运行",
   "paras": [
    "DFlash 2 已运行在主流入射引擎中：",
    "**SGLang**：安装 + 启动：",
    "**vLLM**：安装 + 启动：",
    "**llama.cpp**：编译 + 启动：",
    "下载并安装[带 DFlash 2 支持的预构建 oMLX](https://github.com/z-lab/omlx-fork/releases/download/0.6.2-dflash2/oMLX-0.6.2-zlab-dflash2-arm64-signed.dmg)。",
    "在 oMLX 中运行 Qwen3.8-27B + DFlash 2：① 打开 Model Downloader 下载 mlx-community/Qwen3.8-27B-4bit 和 incoai/Qwen3.8-27B-DFlash2；② 打开 Model Manager 编辑 Qwen3.8-27B-4bit，配置 DFlash：启用、Draft model 选 incoai/Qwen3.8-27B-DFlash2、Draft quantization 启用、Runtime block size=5、Verify mode=dflash；③ 保存并加载目标模型。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "SGLang 配置代码",
   "paras": [
    "__CODE__pip install -U \"sglang[all] @ git+https://github.com/sgl-project/sglang.git@refs/pull/35371/head#subdirectory=python\"\n\npython -m sglang.launch_server \\\n  --model-path Qwen/Qwen3.8-27B \\\n  --speculative-algorithm DFLASH \\\n  --speculative-draft-model-path incoai/Qwen3.8-27B-DFlash2 \\\n  --speculative-num-draft-tokens 8"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "vLLM 配置代码",
   "paras": [
    "__CODE__pip install -U \"vllm @ git+https://github.com/vllm-project/vllm.git@refs/pull/52816/head\"\n\nvllm serve Qwen/Qwen3.8-27B \\\n  --speculative-config '{\"method\": \"dflash\", \"model\": \"incoai/Qwen3.8-27B-DFlash2\", \"num_speculative_tokens\": 7}'"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "llama.cpp 配置代码",
   "paras": [
    "__CODE__git clone https://github.com/ggml-org/llama.cpp.git\ncd llama.cpp\ngit fetch origin pull/27342/head:pr-27342\ngit switch pr-27342\n\n# NVIDIA CUDA\ncmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_CUDA=ON\ncmake --build build -j\n\n# Apple Silicon\ncmake -B build -DCMAKE_BUILD_TYPE=Release -DGGML_METAL=ON\ncmake --build build -j\n\n./build/bin/llama-server \\\n  -hf ggml-org/Qwen3.8-27B-GGUF:Q4_K_M \\\n  -hfd incoai/Qwen3.8-27B-DFlash2-GGUF:Q4_K_M \\\n  --spec-type draft-dflash \\\n  --spec-draft-n-max 7"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "正确的 token 已经在那里了",
   "paras": [
    "DFlash 独立并行预测每个位置。每个选择单独看都合理。但没什么让它们组合在一起，不连贯的块在验证时被截短。最近的方法如 Domino 和 DSpark 用顺序 Markov 头改写每个位置的全词表分布来买连贯性。但这种昂贵的自回归修正真的必要吗？",
    "不需要。证据已经在 DFlash 自己的候选列表里。拿第一个位置：DFlash 的首选 85.4% 正确，但正确 token 在它 top16 候选里的概率是 99.5%。即使首选错了，正确 token 通常也在列表上。",
    "一个总是从 top16 选对的 oracle 会把接受长度从 4.27 提到 6.79。**那个差距是纯粹的选择余量。**我们只需要通过候选选出正确的路径。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig01.png",
      "caption": "图 1：选择器的一个周期——DFlash 单独时每位置保留首选，两个邻居选了同一个词、重复死在验证；DFlash 2 保留每位置 top 候选，选择器穿过它们画一条连贯路径，整块存活。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Table 1：Recall@1 与 Recall@16",
   "paras": [
    "表 1：每个 draft 位置的 Recall@1（首选多常正确）和 Recall@16（正确 token 在 top16 里的概率），以每个更早位置正确为条件。五层 Qwen3-4B DFlash 在 GSM8K 上。接受长度包含验证器的下一个 token。"
   ],
   "table": {
    "head": [
     "Metric",
     "0",
     "1",
     "2",
     "3",
     "4",
     "5",
     "6",
     "接受长度"
    ],
    "rows": [
     [
      "Recall@1",
      "85.4%",
      "80.3%",
      "79.4%",
      "78.3%",
      "77.5%",
      "75.9%",
      "72.9%",
      "4.27"
     ],
     [
      "Recall@16",
      "99.5%",
      "97.3%",
      "94.8%",
      "92.6%",
      "90.8%",
      "89.4%",
      "87.8%",
      "6.79"
     ]
    ]
   },
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "轻量路径选择器",
   "paras": [
    "连贯性大多是局部的：候选的契合主要取决于它前一个 token，所以给相邻对打分应该就够了。DFlash 2 在每位置保留 top16 候选，给每个相邻对打分：对前驱 a 和当前候选 b，S_t(a,b) = U_t(b) + ⟨A(a)⊙H(h_t), B(b)⟩。",
    "分数有两部分。第一部分 U_t(b) 是 DFlash 自己的 logit——drafter 单独有多喜欢 b。第二部分问 b 有多好地跟随 a：A 和 B 给每个 token 一个紧凑的 256 维嵌入，两个嵌入在上下文门 H(h_t) 下匹配，它决定匹配的哪些部分算数。本质上，这是对相邻候选的低秩双线性 attention。",
    "打分保持完全并行。每个位置的每个相邻对一次打完全部，没有额外 backbone 或 LM-head 前向。唯一顺序工作是最后在预计算分数上的行走：从最后一个已验证 token 开始，贪婪跟随每步最佳后继，采样从同一分数抽取，拒绝采样恢复精确的目标分布。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Table 2：路径选择的收益",
   "paras": [
    "表 2：仅路径选择（无卷积）的接受长度，五层 Qwen3-4B 在 GSM8K 上。开销相对纯 DFlash：加到 drafter 的参数、加到的 draft-verify 循环延迟。",
    "选择器把 DFlash 提升 **0.34** token（T=0）和 **0.47**（T=1）。它在两种设置下都击败 DSpark 修正，参数少约 40×、延迟开销低 16×。**选择比预测便宜。**而且还有空间：oracle 达到 6.79。成对打分是我们能想到的最简单的选择器，我们相信还有很多可探索。"
   ],
   "table": {
    "head": [
     "方法",
     "参数",
     "延迟",
     "T=0",
     "T=1"
    ],
    "rows": [
     [
      "DFlash",
      "—",
      "—",
      "4.27",
      "3.78"
     ],
     [
      "+ DSpark 修正",
      "+77.8M",
      "+9.6%",
      "4.49",
      "4.08"
     ],
     [
      "+ 路径选择（我们）",
      "+2.0M",
      "+0.6%",
      "4.61",
      "4.25"
     ]
    ]
   },
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "后缀衰减是局部问题",
   "paras": [
    "我们还注意到上面两个 recall 行都向块尾下降。甚至 oracle 也衰减：完美选择下准确率仍从首位置 99.5% 掉到最后 87.8%。没有选择器能修这个，因为候选本身在耗尽。我们称之为**后缀衰减**，它是 backbone 问题。",
    "一个嫌疑是容量：五层 backbone 可能太小、无法在块内保持依赖。如果对，深度应该在更后位置帮助最大。确实如此！3、5、15 层 DFlash 模型在首位置几乎相同，向块尾散开。但深度不分青红皂白：十个额外 attention 块到处加容量，甚至那些没多少可得的早期位置，抹掉了让 DFlash 有吸引力的效率。",
    "我们想要定向修复，而 DFlash 的 attention 显示了在哪。它有两份工作：读块前上下文、建模块内依赖。但它在第二个上花得越来越少：块的 attention 份额从**第 1 层的 30% 掉到第 5 层的 8%**，剩下的集中在缩小的几个头里。所以我们拆分工：专用模块接管块内工作，attention 继续读上下文。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 2：Qwen3-4B Recall@1 on GSM8K at T=0，以每个更早位置正确为条件。所有 drafter 同设置训练；卷积模型无选择器评估。其卷积加 3% 参数、0.7% 循环延迟；15L 的十个额外层加 15.2%。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "Table：Recall@1 各 drafter 对比",
   "paras": [
    "图 2 数据：各 drafter 的 Recall@1（T=0，以更早位置正确为条件）。"
   ],
   "table": {
    "head": [
     "Draft position",
     "0",
     "1",
     "2",
     "3",
     "4",
     "5",
     "6"
    ],
    "rows": [
     [
      "DFlash 3L",
      "85.21%",
      "79.26%",
      "77.18%",
      "75.75%",
      "73.96%",
      "70.4%",
      "64.97%"
     ],
     [
      "DFlash 5L",
      "85.39%",
      "80.31%",
      "79.39%",
      "78.27%",
      "77.39%",
      "76.03%",
      "72.86%"
     ],
     [
      "DFlash 15L（3×参数）",
      "86.42%",
      "81.61%",
      "80.68%",
      "80.34%",
      "80.59%",
      "79.66%",
      "78.73%"
     ],
     [
      "DFlash 5L+conv（+3%参数）",
      "85.83%",
      "80.94%",
      "79.98%",
      "79.68%",
      "79.73%",
      "79.43%",
      "77.61%"
     ]
    ]
   },
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Figure 3：块内 attention 热力图",
   "paras": [
    "图 3：五层 Qwen3-4B DFlash 中按头的块内 attention。亮格标记把更多 attention 花在 draft 块上的头；在后层块内质量收缩并集中在少数几个头里。",
    "数据表（每层×32 头 within-block attention %）："
   ],
   "table": {
    "head": [
     "Attention head",
     "1",
     "2",
     "3",
     "4",
     "5",
     "6",
     "7",
     "8",
     "9",
     "10",
     "11",
     "12",
     "13",
     "14",
     "15",
     "16",
     "17",
     "18",
     "19",
     "20",
     "21",
     "22",
     "23",
     "24",
     "25",
     "26",
     "27",
     "28",
     "29",
     "30",
     "31",
     "32"
    ],
    "rows": [
     [
      "Layer 1",
      "17.6%",
      "2.9%",
      "41.4%",
      "50.8%",
      "29.2%",
      "50.5%",
      "44.6%",
      "5.9%",
      "44.5%",
      "11.3%",
      "17.9%",
      "36.7%",
      "0.0%",
      "14.2%",
      "0.1%",
      "0.0%",
      "13.3%",
      "1.5%",
      "18.7%",
      "7.6%",
      "45.0%",
      "33.5%",
      "53.1%",
      "42.2%",
      "64.3%",
      "60.1%",
      "32.8%",
      "47.7%",
      "49.6%",
      "57.0%",
      "26.0%",
      "52.9%"
     ],
     [
      "Layer 2",
      "20.8%",
      "26.4%",
      "39.6%",
      "18.9%",
      "8.9%",
      "22.6%",
      "13.1%",
      "32.1%",
      "22.9%",
      "25.1%",
      "24.2%",
      "28.6%",
      "36.6%",
      "26.1%",
      "41.0%",
      "36.1%",
      "17.8%",
      "25.5%",
      "25.7%",
      "25.6%",
      "4.3%",
      "21.8%",
      "23.3%",
      "22.1%",
      "15.6%",
      "70.9%",
      "58.0%",
      "2.7%",
      "28.3%",
      "38.5%",
      "20.3%",
      "33.5%"
     ],
     [
      "Layer 3",
      "1.8%",
      "11.0%",
      "9.5%",
      "5.2%",
      "34.8%",
      "8.4%",
      "12.1%",
      "14.4%",
      "11.8%",
      "22.0%",
      "8.8%",
      "3.7%",
      "4.9%",
      "10.6%",
      "17.7%",
      "52.0%",
      "4.4%",
      "19.0%",
      "13.1%",
      "9.9%",
      "61.3%",
      "76.1%",
      "47.0%",
      "60.3%",
      "1.4%",
      "8.9%",
      "6.0%",
      "64.1%",
      "9.4%",
      "3.3%",
      "8.3%",
      "8.3%"
     ],
     [
      "Layer 4",
      "0.4%",
      "37.7%",
      "28.3%",
      "85.5%",
      "0.3%",
      "1.5%",
      "0.4%",
      "0.5%",
      "1.2%",
      "12.5%",
      "36.6%",
      "1.2%",
      "1.7%",
      "0.6%",
      "2.5%",
      "1.3%",
      "7.2%",
      "3.1%",
      "48.9%",
      "3.8%",
      "3.2%",
      "1.0%",
      "23.8%",
      "1.0%",
      "0.1%",
      "0.1%",
      "0.2%",
      "0.3%",
      "2.8%",
      "6.7%",
      "12.9%",
      "12.3%"
     ],
     [
      "Layer 5",
      "1.5%",
      "0.2%",
      "0.6%",
      "0.1%",
      "60.2%",
      "76.0%",
      "0.9%",
      "0.0%",
      "0.2%",
      "12.3%",
      "32.3%",
      "0.1%",
      "15.8%",
      "0.5%",
      "0.5%",
      "0.5%",
      "0.2%",
      "0.1%",
      "0.6%",
      "0.2%",
      "0.3%",
      "28.1%",
      "0.2%",
      "1.3%",
      "0.1%",
      "0.1%",
      "0.2%",
      "29.9%",
      "0.1%",
      "0.1%",
      "0.1%",
      "1.2%"
     ]
    ]
   },
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "轻量局部卷积",
   "paras": [
    "块内工作本来就是短程的：一块只跨 4 到 16 个 token，最紧的依赖在邻居之间。自然的算子是个短卷积：两个 tap，一个在当前位、一个回看一位，权重随内容适应。遵循 Canon Layers、Dynamic Short Convolutions 和 Convolution for Large Language Models，我们在每个 attention 和 feed-forward 子层前后插入这个两 tap 动态深度卷积：",
    "Conv_k(x)_t = k_{t,0}⊙x_t + k_{t,1}⊙x_{t-1}。",
    "每个系数组合一个学习的基础内核与一个从当前隐藏状态算出的微小修正；每 16 个通道共享一个修正。第一个位置读最后一个已验证 token 的表示，每个更后位置读其前驱的。信息跨块流动，而所有位置仍并行计算。",
    "卷积是块局部且无状态的，所以它无痛落入 DFlash，不改变 attention、LM 头或验证。",
    "只用 **16.5M 新增参数（3%）**，五层 DFlash + 卷积[接近 15 层 DFlash]，大幅减少后缀衰减。卷积给 draft-verify 循环延迟加 **0.7%**；十个 Transformer 层加 15.2%。第 4、5 层的平均块内 attention 也从 **9.4% 掉到 0.5%**，一致于卷积吸收局部工作、attention 回到读上下文。一个回看一位的内核恢复十个额外层买的大部分：后缀衰减大多是**局部**问题。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig03.png",
      "caption": "图 4：两 tap 动态卷积。一个放在每层 drafter 的每个 attention 和 MLP 子层前后。内部每个位置混合自己的表示与前驱的，第一个位置读最后一个已验证 token。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "组合起来：Qwen3.5-4B 完整对比",
   "paras": [
    "到目前为止，选择器和卷积是分开测的；下面的完整对比把它们放一起。我们自己按匹配设置训练 DFlash 和 DSpark drafters，而 MTP 随模型发布。",
    "表 3：Qwen3.5-4B 每请求平均接受长度。采样：thinking 启用、温度 1.0、top-p 0.95、top-k 20、presence penalty 1.5，带无损拒绝采样。",
    "DFlash 2 在每个基准领先。跨它们平均，比 DFlash 多 **1.05 token（21%）**、比 DSpark 多 0.48。升级保持便宜：选择器和卷积合计只给五层 DFlash draft-verify 循环延迟加 **1.3%**。",
    "在 MATH-500 上，[增益逐位置可见]：DFlash 2 稳在接近 86% 直到最后位置，每个基线在块尾低它 6 到 9 个点。"
   ],
   "table": {
    "head": [
     "数据集",
     "MTP",
     "DFlash",
     "DSpark",
     "DFlash 2"
    ],
    "rows": [
     [
      "GSM8K",
      "4.78",
      "4.99",
      "5.69",
      "6.20"
     ],
     [
      "MATH-500",
      "5.04",
      "5.42",
      "6.20",
      "6.76"
     ],
     [
      "HumanEval",
      "4.84",
      "5.43",
      "5.80",
      "6.28"
     ],
     [
      "MBPP",
      "4.16",
      "4.49",
      "4.96",
      "5.41"
     ],
     [
      "MT-Bench",
      "3.90",
      "4.26",
      "4.77",
      "5.20"
     ],
     [
      "均值",
      "4.54",
      "4.92",
      "5.49",
      "5.97"
     ]
    ]
   },
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Table：MATH-500 逐位置接受率",
   "paras": [
    "图 5 数据：Qwen3.5-4B conditional acceptance rate on MATH-500（与上面相同采样）。"
   ],
   "table": {
    "head": [
     "位置",
     "0",
     "1",
     "2",
     "3",
     "4",
     "5",
     "6",
     "7",
     "8",
     "9",
     "10",
     "11",
     "12",
     "13",
     "14"
    ],
    "rows": [
     [
      "MTP",
      "84.57%",
      "80.23%",
      "79%",
      "78.42%",
      "78.63%",
      "78.17%",
      "77.36%",
      "77.74%",
      "77.91%",
      "76.96%",
      "78.06%",
      "77.4%",
      "77.49%",
      "77.48%",
      "77.85%"
     ],
     [
      "DFlash",
      "88.35%",
      "77.7%",
      "77.8%",
      "79.45%",
      "80.3%",
      "81.12%",
      "81.22%",
      "81.07%",
      "81.29%",
      "80.28%",
      "80.64%",
      "80.29%",
      "79.56%",
      "78.77%",
      "77.48%"
     ],
     [
      "DSpark",
      "87.24%",
      "84.59%",
      "83.79%",
      "83.63%",
      "83.6%",
      "83.27%",
      "82.97%",
      "82.54%",
      "82.21%",
      "82.39%",
      "81.58%",
      "80.7%",
      "81.35%",
      "80.57%",
      "79.86%"
     ],
     [
      "DFlash 2",
      "88.3%",
      "85.3%",
      "84.98%",
      "84.88%",
      "85.41%",
      "85.3%",
      "85.36%",
      "85.13%",
      "85.95%",
      "85.99%",
      "86.41%",
      "86.46%",
      "86.43%",
      "86.02%",
      "86.48%"
     ]
    ]
   },
   "fig_after": {
    "0": [
     {
      "src": "fig04.png",
      "caption": "图 5：Qwen3.5-4B MATH-500 上的条件接受率——DFlash 2 保持接近 86% 直到最后位置，每个基线在块尾低 6-9 点。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "两个 drafter，今天发布",
   "paras": [
    "我们今天发布两个 DFlash 2 drafters：一个给 Qwen3.8-27B，一个给 Meta 的 Muse Glimmer。对 Qwen3.8-27B，我们对比模型原生的 MTP 路径和一个社区 DSpark drafter。",
    "表 4：Qwen3.8-27B 每请求平均接受长度，模型默认采样、块大小 8，对比其原生 MTP 路径和一个社区 DSpark drafter。",
    "对 Meta 的 Muse Glimmer，我们对比随模型发布的官方 DFlash drafter 和一个社区 DSpark drafter。",
    "表 5：Muse Glimmer 每请求平均接受长度，模型默认采样、块大小 16。DFlash 是 Meta 随模型发布的官方 drafter；DSpark 是社区 drafter。",
    "差距很大：在两个模型上，DFlash 2 平均比 DSpark 领先**一个多 token**。它也击败每个模型的官方 drafter——Qwen3.8-27B 的 MTP 和 Muse Glimmer 的 DFlash。那转化为 Qwen3.8-27B 上**自回归解码 2.7-3.4×** 的吞吐，Muse Glimmer 上 **3.1-4.6×**。模型卡按任务和并发拆解加速。"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Table 4：Qwen3.8-27B",
   "paras": [
    "表 4：Qwen3.8-27B per-request mean acceptance length, block size 8。"
   ],
   "table": {
    "head": [
     "数据集",
     "MTP",
     "DSpark",
     "DFlash 2"
    ],
    "rows": [
     [
      "GSM8K",
      "5.02",
      "4.36",
      "5.46"
     ],
     [
      "MATH-500",
      "4.72",
      "3.92",
      "5.28"
     ],
     [
      "HumanEval",
      "3.91",
      "3.30",
      "4.39"
     ],
     [
      "MBPP",
      "3.99",
      "3.51",
      "4.79"
     ],
     [
      "MT-Bench",
      "3.74",
      "3.01",
      "4.10"
     ],
     [
      "均值",
      "4.28",
      "3.62",
      "4.80"
     ]
    ]
   },
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "Table 5：Muse Glimmer",
   "paras": [
    "表 5：Muse Glimmer per-request mean acceptance length, block size 16。"
   ],
   "table": {
    "head": [
     "数据集",
     "DFlash",
     "DSpark",
     "DFlash 2"
    ],
    "rows": [
     [
      "GSM8K",
      "5.43",
      "5.45",
      "6.57"
     ],
     [
      "MATH-500",
      "5.39",
      "5.01",
      "6.56"
     ],
     [
      "HumanEval",
      "4.11",
      "4.33",
      "5.66"
     ],
     [
      "MBPP",
      "3.74",
      "4.02",
      "5.30"
     ],
     [
      "MT-Bench",
      "3.52",
      "3.59",
      "4.42"
     ],
     [
      "均值",
      "4.44",
      "4.48",
      "5.70"
     ]
    ]
   },
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "底线",
   "paras": [
    "agent 一个下午写出的东西是一个聊天机器人一个月写出的量，而解码位于那每个 token 之下。DFlash 2 以**接近自回归解码 3× 的速度**解码，**每个 token 约三分之一的计算**，输出相同。",
    "七个月内，DFlash 从我们的论文变成了行业标准，下载超 350 万次。在同一设计内，DFlash 2 每次前向多解码一个完整 token，免费。那只是服务栈的一个组件。推理远未到它的下限。",
    "在 Inco AI，我们正在构建端到端服务栈来持续压低那个下限。DFlash 2 是第一块。两个 drafters 今天在 Hugging Face 发布。",
    "如果你大规模服务 agent、想在自己的栈里评估 DFlash 2，或想为你运行的模型（包括自己的微调）要一个 drafter，写信给我们：contact@inco.ai。",
    "我们也在招人。如果你想帮忙构建这个栈，联系我们。",
    "**连接候选。继续并行起草。**"
   ],
   "fig_after": {}
  },
  {
   "type": "h2",
   "title": "引用",
   "paras": [
    "请这样引用这篇文章：",
    "__CODE__@misc{inco2026dflash2,\n  title = {{DFlash 2: Keep Drafting Parallel}},\n  author = {{Inco AI}},\n  year = {2026},\n  month = {August},\n  url = {https://inco.ai/blog/dflash2/}\n}"
   ],
   "fig_after": {}
  }
 ],
 "conclusion": [
  "DFlash 2 的核心洞察干净利落：投机解码的瓶颈不是「猜不出 token」，而是「猜对了却选不出」。DFlash 的候选列表里正确 token 在 top16 的概率高达 99.5%（首位置），缺的只是一个把连贯路径选出来的轻量选择器——256 维双线性打分、完全并行，代价仅 0.6% 延迟、2.0M 参数。",
  "第二个洞察是「后缀衰减是局部问题」：块内依赖本质短程，一个回看一位的两 tap 卷积（3% 参数、0.7% 延迟）就恢复了十层 Transformer（15.2% 开销）的大部分收益。选择比预测便宜 40 倍参数、16 倍延迟——这正是「把智能花在刀刃上」的又一个例证。"
 ],
 "reference_url": "https://inco.ai/blog/dflash2/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print(f"✅ 写入 article_data.json")