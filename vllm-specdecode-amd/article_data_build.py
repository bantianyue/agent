#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""由 _build_gen.py 生成的 article_data_build.py（勿手改）"""
import json, os, sys

_article_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()

DATA = {
  "title": "在 AMD GPU 上探索 vLLM 的投机解码（Speculative Decoding）",
  "summary": [
    {
      "key": "核心机制",
      "body": "保留原模型作 target，前面加更快的 draft 阶段提出候选 token，由 target 在一次前向里验证；接受判定从左到右，遇到第一个被拒 token 即停止。"
    },
    {
      "key": "五种方法",
      "body": "按「用哪些 target 信息 + 串行还是并行起草」分为三类：native MTP、独立 MTP drafter（Gemma 4 MTP）、专用 target-conditioned 网络（EAGLE-3 自回归、DFlash 并行块、DSpark 并行加轻量顺序修正）。"
    },
    {
      "key": "实测与调参",
      "body": "AMD MI300X/MI355X + ROCm 上吞吐比随模型、方法、负载差异很大：gemma-4-26B-A4B 的 DFlash 最高 2.87×，也有配置低于基线；num_speculative_tokens 必须按负载扫描（常见峰值 N=4 到 7）。"
    }
  ],
  "lead": [
    "投机解码（speculative decoding）让 vLLM 在单次 target model 前向中验证多个 draft token。实验中，它对输出 token 吞吐的影响随 drafting 方法和 proposal 长度而变化，同时也取决于模型系列、draft checkpoint、workload 与接受行为。"
  ],
  "sections": [
    {
      "type": "h2",
      "title": "引言",
      "paras": [
        "LLM（大语言模型）支持广泛的应用，但大规模服务需要精细优化。标准自回归解码是多数 LLM 服务系统采用的基线：模型生成一个 token，将其追加到序列，再用更新后的序列生成下一个 token。该过程简单可靠，但由于输出 token 必须严格按从左到右的顺序产生，服务循环每次仍只推进一个已提交 token。",
        "投机解码（投机解码）[1] 在此基线上引入 draft-and-verify 机制。轻量级 draft 组件提出候选未来 token，target model 在候选被提交前对其验证。当多个 draft token 被接受时，系统可在单次 target-model 验证步骤中提交多个输出 token，同时保持 target model 的输出行为不变。",
        "以下说明投机解码在 vLLM 中的工作方式，并给出测试环境中的测量结果。先回顾自回归解码基线与 draft-and-verify 流程，再考察五种投机 drafting 方法：native MTP、Gemma 4 MTP、EAGLE-3、DFlash 和 DSpark。这些方法的差异在于 draft 组件如何从 target model 获取信息，以及候选 token 是串行、自回归、并行还是混合方式生成。最后给出在本环境中启用所测方法的方式、基于 ROCm™ 开放软件平台在 AMD Instinct™ MI300X 和 MI355X GPU 上的实验测量结果，并讨论实际调优与可观测性方面的注意事项。"
      ]
    },
    {
      "type": "h2",
      "title": "自回归解码基线",
      "paras": [
        "在标准的自回归解码中，每个 decode step 产生并提交一个新 token。例如，生成四个输出 token 需要四个顺序执行的 decode step：",
        "每一步之后，生成的 token 会追加到序列中，并成为下一步输入的一部分。这使解码循环简单直接，但也要求每个输出 token 都对应一次模型 decode step。在长序列生成过程中，这种逐 token 循环会成为延迟的主要来源，并限制服务吞吐。",
        "因此，投机解码背后的关键问题是：",
        "能否在保持原始模型输出行为不变的同时，减少每次只推进一个 token 的生成次数？",
        "投机解码通过将提案与验证分离来解决这一问题。draft 组件先提出若干候选的未来 token。原始模型作为 target model，随后在这些候选 token 被提交前对其进行验证。"
      ],
      "fig_after": {
        "0": [
          {
            "src": "fig01.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h2",
      "title": "投机解码的核心思想",
      "paras": [
        "投机解码不会替换原始模型。它将原始模型保留为 target model，由后者负责最终输出，并在其前面加入一个更快的 proposal 阶段。",
        "该过程包含两部分：",
        "Draft：提出若干个候选的未来 token。",
        "Verify：使用 target model 校验这些候选。",
        "在每轮 投机解码 中（见下图），一个轻量的 draft 组件提出一个或多个未来 token。这些 token 仅为候选，不会被立即提交。随后 target model 在一次验证 pass 中评估候选 token 序列。",
        "验证从左到右进行。每个 draft token 使用 target model 在对应位置的结果进行校验。被接受的 token 提交到输出序列。当某个 draft token 被拒绝时，同一提案中后续的候选不再被接受。",
        "如果某个 draft token 被拒绝，则由 target model 给出下一个 token。其余 draft token 被丢弃，生成从更新后的序列继续。",
        "从概念上讲，标准自回归解码的推进方式如下：",
        "投机解码则允许多个候选位置被一并评估：",
        "当多个候选被接受时，这可以减少 target model 的解码轮数。当 draft 组件产生的 token 被 target model 接受时，一次 target model 验证步骤即可提交多个输出 token。当某个提案被拒绝时，由 target 侧的结果决定生成如何继续。"
      ],
      "fig_after": {
        "7": [
          {
            "src": "fig02.png",
            "caption": ""
          }
        ],
        "8": [
          {
            "src": "fig03.png",
            "caption": ""
          }
        ],
        "9": [
          {
            "src": "fig04.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h3",
      "title": "一个简单的接受/拒绝示例",
      "paras": [
        "下图给出了一个投机解码轮次的示例。绿色框是验证通过的 draft token，红色框标记第一个被拒绝的 draft token，灰色框是随后被丢弃的 draft token。输出中的蓝色 token 来自 target model，而非 draft 提议。",
        "假设当前 prompt 为：",
        "draft 组件提议若干未来 token：",
        "target model 从左到右验证 draft token：",
        "前两个 draft token sunny 和 and 被接受。在第三个位置，draft 提议 warm，但 target model 选择 clear。其余候选 outside 因位于第一个被拒绝位置之后而被丢弃。",
        "因此，下一轮解码从以下内容继续："
      ],
      "fig_after": {
        "0": [
          {
            "src": "fig05.png",
            "caption": ""
          }
        ],
        "1": [
          {
            "src": "fig06.png",
            "caption": ""
          }
        ],
        "2": [
          {
            "src": "fig07.png",
            "caption": ""
          }
        ],
        "3": [
          {
            "src": "fig08.png",
            "caption": ""
          }
        ],
        "5": [
          {
            "src": "fig09.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h2",
      "title": "五种起草方法如何工作",
      "paras": [
        "所有 投机解码方法遵循相同的整体 draft-and-verify 流程，但在 draft 组件的设计方式及其与 target model 的协作方式上存在差异。",
        "主要差异在于：",
        "从 target model 获取的信息类型。",
        "这些信息如何融入 drafting 过程。",
        "候选 token 是按顺序生成还是并行生成。",
        "基于这些差异，可将 drafting 方法归为三大类：native MTP 模块、独立 MTP drafter、专用的 target-conditioned draft 网络。",
        "Native MTP 模块：直接内建于 target 模型架构中；使用模型原生的辅助预测路径；按顺序生成候选 token。",
        "独立 MTP drafter：使用与特定 target 模型配对的独立 checkpoint；推理时使用 target 模型的激活值和共享的 KV cache 信息；按顺序生成候选 token。",
        "专用的 target-conditioned draft 网络：使用针对特定 target 模型训练的独立 speculator 模型，包括 EAGLE-3、DFlash 和 DSpark。EAGLE-3 基于 target 模型的 hidden states 自回归地 draft，DFlash 基于 target 模型的 hidden states 并行 draft 块，DSpark 则增加轻量的因果校正和基于置信度的前缀选择。",
        "这些分类描述的是 draft 组件的架构，而非 target 模型系列。一个 target 模型可以支持 native MTP，同时也可拥有单独训练的 EAGLE-3、DFlash 或 DSpark draft 模型。",
        "draft 组件并非完全独立运行。根据方法不同，draft 组件可能接收：",
        "来自 target 模型的 hidden representation。",
        "来自若干选定 target 层的 hidden states。",
        "target 模型的 KV cache。",
        "由多个 target 模型表示组合生成的特征。",
        "以下各节说明每种方法如何使用这些信息，以及如何生成候选 token。"
      ]
    },
    {
      "type": "h3",
      "title": "Native MTP",
      "paras": [
        "Multi-Token Prediction（多 token 预测），即 MTP，指一类模型原生机制，用于预测紧邻下一个 token 之后的 token。在 vLLM 中，当 target 模型包含兼容的辅助预测组件时，即可使用原生 MTP[2]。MTP 的具体架构因模型系列而异，但每种实现都提供一条辅助路径来提议未来的 token。",
        "在第一个投机步骤中，MTP 组件将 target 模型的隐藏表示与当前 token 的信息结合，预测出第一个 draft token。在后续步骤中，新生成的 draft token 与上一步 MTP 产生的隐藏状态用于预测下一个候选 token。提议出配置数量的候选 token 后，target 模型在一次验证中统一评估它们。",
        "许多原生 MTP 实现遵循相似的模式。来自 target 模型或上一步 MTP 预测的隐藏表示，与偏移输入 token 或最新 draft token 的 embedding 相结合：",
        "这两个输入承担不同职责：(1) hidden representation 携带前序序列的信息；(2) token embedding 标识 draft 继续生成的最后一个 token。在常见实现中，二者沿 hidden 维度拼接，经过变换后进入辅助预测层。",
        "物理 MTP 层数与配置的投机长度是两个独立概念。当 num_speculative_tokens 超过 checkpoint 直接提供的预测深度时，vLLM 可以通过额外的 forward pass 复用 MTP 路径。因此取值更大意味着在验证前提出更多候选，但也会引入更多串行 draft 工作。",
        "原生 MTP 与 target model 架构紧密绑定。在许多实现中，MTP 路径的部分组件与 target model 共享，这使额外的显存开销相对可控。但生成多个 speculative token 仍需在验证前串行 draft。"
      ],
      "fig_after": {
        "1": [
          {
            "src": "fig10.png",
            "caption": ""
          }
        ],
        "2": [
          {
            "src": "fig11.png",
            "caption": ""
          }
        ],
        "4": [
          {
            "src": "fig12.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h3",
      "title": "Gemma 4 MTP",
      "paras": [
        "Gemma 4 使用单独打包的 MTP draft 组件，与特定 target model 配对 [3]。该 draft 组件虽有独立 checkpoint，但在推理过程中仍与 target model 紧密连接。",
        "draft 组件使用 target model 产生的 activation，并共享 target model 的 KV cache。由此可复用 target 已计算好的上下文信息，无需独立处理已接受的 prefix。",
        "与 native MTP 相同，draft 组件的层数与配置的 speculative length 相互独立。当请求多个候选 token 时，draft 组件按顺序依次生成："
      ],
      "fig_after": {
        "0": [
          {
            "src": "fig13.png",
            "caption": ""
          }
        ],
        "2": [
          {
            "src": "fig14.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h3",
      "title": "EAGLE-3",
      "paras": [
        "EAGLE-3 使用针对特定 target model 训练的专用 draft 网络。draft 组件拥有自身的执行路径，但仍紧密依赖于 target model 产生的信息作为条件 [4]。",
        "在 target model 前向传播过程中，EAGLE-3 记录 target Transformer 三个阶段的 hidden states：接近开头、中间附近和接近结尾。它们是同一 accepted sequence 在 target model 不同处理阶段上的上下文表示。",
        "三个 hidden states 被拼接并投影为单一的 fused target feature。该融合表示随后与采样所得 token 的 embedding 结合，再进入 EAGLE-3 draft decoder。",
        "这两类输入承担不同的作用：",
        "融合后的 target 特征利用 target model 前向传播中多个阶段的信息，对已接受的序列进行汇总。",
        "采样得到的 token embedding 标识出 drafting 继续的起始 token。",
        "EAGLE-3 以自回归方式生成 draft token。对于第一个 draft token，它使用由已接受序列计算得到的融合 target 特征，并结合采样 token 的 embedding。生成一个 draft token 后，其 embedding 被送入下一个 drafting 阶段。",
        "由于 target model 尚未处理后续的投机位置，这些位置上的 target model 隐状态不可用。因此 EAGLE-3 在延续 draft 序列时使用前一个 draft 组件的输出。",
        "这种顺序反馈使后续 draft token 直接依赖于所提议序列中更早的 drafted token。然而，生成更多投机 token 也意味着在验证之前需要更多顺序 drafting 工作。"
      ],
      "fig_after": {
        "1": [
          {
            "src": "fig15.png",
            "caption": ""
          }
        ],
        "2": [
          {
            "src": "fig16.png",
            "caption": ""
          }
        ],
        "7": [
          {
            "src": "fig17.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h3",
      "title": "DFlash",
      "paras": [
        "DFlash 使用为特定 target 模型训练的专用 draft 网络。与顺序生成候选 token 的 MTP 和 EAGLE-3 不同，DFlash 并行预测整个未来位置块 [5]。",
        "DFlash 以 anchor token 开始每个 draft block。anchor 是由 target 模型生成或确认的已知 token，因此 DFlash 无需预测它。它只是为后续被掩码的位置提供一个已知的起始点。在后续解码轮次中，这通常是上一轮验证过程返回的额外 target token。",
        "anchor 占据 block 的第一个位置，其余位置被掩码并并行预测：",
        "draft block 以已确认的 anchor token 开始，后跟被掩码的位置：",
        "其中，anchor 是已知的 target-model token，而被 mask 的位置由 DFlash 预测。",
        "单次 DFlash 前向传播即可同时预测所有被 mask 的位置：",
        "与 EAGLE-3 相同，DFlash 首先将 target model 多个层的 hidden states 融合为一个表示。",
        "主要区别在于该融合表示的使用方式。EAGLE-3 在自回归 draft network 的输入端将其与采样 token 的 embedding 拼接。DFlash 则把融合后的 target 上下文转换为额外的 Key 和 Value 表示，供 draft network 的每一层使用。",
        "因此，来自被 mask 的 draft 位置的 Query 可以同时关注：",
        "由 target model 导出的 Key 和 Value 表示。",
        "Key 和 Value 表示由 draft block 自身产生。",
        "因此 target model 的上下文在整个 draft network 中始终可用，而不是仅在其输入端注入一次。",
        "draft block 生成后，target model 在一次验证 pass 中评估所有候选 token。接受判定按从左到右的顺序应用：token 依次被接受并提交，直到出现第一次拒绝，其余候选全部丢弃。",
        "此时，target model 的 token 替换第一个被拒绝的 draft token，其余 draft token 被丢弃。",
        "DFlash 的一个典型特征是：所有 masked 位置在一次 draft-network 前向传播中一并预测。",
        "这与串行 draft 不同：",
        "由于所有被 mask 的位置是一次性共同预测的，同一次前向中靠后的位置并不以靠前位置的采样输出为条件。这移除了自回归 draft 所使用的逐 token 反馈。因此，靠后位置的有效性取决于训练好的 checkpoint 与具体 workload，在使用更长的 draft block 时尤为如此。"
      ],
      "fig_after": {
        "3": [
          {
            "src": "fig18.png",
            "caption": ""
          }
        ],
        "5": [
          {
            "src": "fig19.png",
            "caption": ""
          }
        ],
        "6": [
          {
            "src": "fig20.png",
            "caption": ""
          }
        ],
        "8": [
          {
            "src": "fig21.png",
            "caption": ""
          }
        ],
        "12": [
          {
            "src": "fig22.png",
            "caption": ""
          }
        ],
        "14": [
          {
            "src": "fig23.png",
            "caption": ""
          }
        ],
        "15": [
          {
            "src": "fig24.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h3",
      "title": "DSpark",
      "paras": [
        "DSpark 在并行 draft 基础上扩展了两个额外机制：",
        "一个轻量级 sequential head，在 draft block 内引入 token 之间的依赖关系。",
        "基于置信度选择提交给 target model 验证的前缀。",
        "DSpark 使用改造后的 DFlash 模型作为其并行 backbone [6]。该 backbone 在一次 forward pass 中为所有位置执行主要的 draft 计算，为每个 draft 位置生成一个 hidden state 和一组 base logits。因此它继承了 DFlash 一节所述的 target-context conditioning。",
        "完全并行的 draft 组件在预测每个位置时，不会先看到同一 block 中更早位置已选出的 token。当存在多种合理续写时，这会产生不一致的组合。例如，\"of course\" 和 \"no problem\" 都可能合理，但独立地按位置预测可能产生 \"of problem.\"",
        "DSpark 在并行 backbone 之后接一个轻量级 sequential head 来解决这一问题。backbone 仍然一次性计算所有位置的 base logits。sequential head 随后从左到右选择 token，利用此前已选出的 draft token 信息调整每个位置。",
        "DSpark 采用轻量级 Markov head，在已选出的 draft token 之间引入依赖关系。对每个位置，Markov head 使用紧邻其前一个已选 token 产生一个小 bias。该 bias 用于调整并行 backbone 输出的 base logits：",
        "主 draft 网络在一次 forward pass 中同时处理所有候选位置。之后，仅由轻量级 Markov head 从左到右运行，利用此前已选出的 draft token 调整每个位置。",
        "由此，同一 block 内后续的 draft token 可以依赖于已经选出的 token，而无需为每个位置重新运行完整的 draft 网络。",
        "DSpark 的设计还包含一个 confidence head（置信度头），可为 target model 的验证选择更短的 draft prefix。该功能在本次实验所用的 vLLM 路径中未启用，因此基准测试结果只反映并行 draft network 与轻量级 Markov 校正。",
        "target model 在一次 verification pass 中评估提议序列，draft token 从左到右依次提交，直到出现首次拒绝。"
      ],
      "fig_after": {
        "3": [
          {
            "src": "fig25.png",
            "caption": ""
          }
        ],
        "6": [
          {
            "src": "fig26.png",
            "caption": ""
          }
        ],
        "7": [
          {
            "src": "fig27.png",
            "caption": ""
          }
        ]
      }
    },
    {
      "type": "h3",
      "title": "五种方法对比",
      "paras": [
        "下图以并排视图直观呈现五种 drafting 方法：draft 组件长什么样、使用哪些 target model 信息，以及候选 token 是串行还是并行生成。图下方的表格以紧凑形式重述同一对比。在这五种方法中，target model 仍以一次 verification pass 评估提议序列，接受判定从左到右依次应用，直到第一个被拒绝的 draft token。"
      ],
      "fig_after": {
        "0": [
          {
            "src": "fig28.png",
            "caption": ""
          }
        ]
      },
      "table": {
        "head": [
          "方法",
          "draft 组件",
          "使用的目标模型信息",
          "draft token 如何生成"
        ],
        "rows": [
          [
            "Native MTP",
            "模型原生的辅助 MTP 路径",
            "目标模型或先前 MTP 的隐藏表示，与当前draft token 信息结合",
            "通过重复使用 MTP 路径顺序生成"
          ],
          [
            "Gemma 4 MTP",
            "与目标模型配对的独立 MTP draft 组件",
            "目标模型激活值和共享的目标 KV cache",
            "通过配对的 MTP 组件顺序生成"
          ],
          [
            "EAGLE-3",
            "专用自回归draft 网络",
            "在目标模型前向传播的开头附近、中间附近和结尾附近捕获的隐藏状态，融合为一个表示",
            "顺序生成，每个draft token 都会影响下一个"
          ],
          [
            "DFlash",
            "专用并行draft 网络",
            "融合后的目标模型隐藏状态作为额外的 Key 和 Value 信息提供给每个draft 层",
            "所有候选位置在一次并行前向传播中一起预测"
          ],
          [
            "DSpark",
            "DFlash 风格的并行draft 网络，带轻量级 Markov head",
            "并行draft 网络使用的相同目标条件信息",
            "一次并行前向传播，随后对 token 选择进行轻量级顺序调整"
          ]
        ]
      }
    },
    {
      "type": "h2",
      "title": "在 vLLM 中启用投机解码",
      "paras": [
        "在 vLLM 中，投机解码（投机解码）通过 --speculative-config 配置。主要差异在于 method 名称、是否需要单独的 draft checkpoint，以及请求的候选 token 数量。当前 vLLM 支持 mtp、eagle3、dflash 和 dspark 作为 method 取值。",
        "对于原生 MTP，draft 组件随 target 模型一同提供，因此省略 model 字段：",
        "__CODE__bash::vllm serve <target-model> \\\n  --speculative-config '{\n    \"method\": \"mtp\",\n    \"num_speculative_tokens\": <N>\n  }'",
        "对于 Gemma 4 MTP、EAGLE-3、DFlash 和 DSpark，model 字段通常指向针对 target 模型训练的 checkpoint：",
        "__CODE__bash::vllm serve <target-model> \\\n  --speculative-config '{\n    \"method\": \"<method>\",\n    \"model\": \"<matching-draft-checkpoint>\",\n    \"num_speculative_tokens\": <N>\n  }'",
        "Gemma 4 assistant checkpoint 走 MTP 路径，尽管它们是通过 model 字段提供的。vLLM 将 assistant 组件连接到 target 模型，并允许其共享 target 的 KV cache。",
        "启用某个方法前，请确认：",
        "已安装的 vLLM 版本支持该方法与模型架构。",
        "draft checkpoint 与 target 模型及方法兼容。",
        "num_speculative_tokens 与该 checkpoint 兼容。",
        "模型卡支持目标硬件与推理后端。"
      ],
      "table": {
        "head": [
          "方法",
          "独立draft checkpoint",
          "典型配置"
        ],
        "rows": [
          [
            "Native MTP",
            "否",
            "\"method\": \"mtp\" \"num_speculative_tokens\": <N>"
          ],
          [
            "Gemma 4 MTP",
            "是",
            "\"method\": \"mtp\" \"model\": \"<matching-assistant>\" \"num_speculative_tokens\": <N>"
          ],
          [
            "EAGLE-3",
            "是",
            "\"method\": \"eagle3\" \"model\": \"<matching-speculator>\" \"num_speculative_tokens\": <N>"
          ],
          [
            "DFlash",
            "是",
            "\"method\": \"dflash\" \"model\": \"<matching-speculator>\" \"num_speculative_tokens\": <N>"
          ],
          [
            "DSpark",
            "是",
            "\"method\": \"dspark\" \"model\": \"<matching-speculator>\" \"num_speculative_tokens\": <N>"
          ]
        ]
      }
    },
    {
      "type": "h3",
      "title": "显存考量",
      "paras": [
        "Native MTP 不加载单独的 draft checkpoint，并且可能与 target model 共享 embedding table 或 output head 等组件。Gemma 4 MTP、EAGLE-3、DFlash 和 DSpark 会加载额外的 draft 权重，因此需要预留足够的 GPU 显存余量。实际开销取决于 draft 组件大小、数值精度、tensor-parallel 配置以及运行时缓冲区。"
      ]
    },
    {
      "type": "h2",
      "title": "预训练 draft 模型去哪找",
      "paras": [
        "目前已有多个组织在 Hugging Face 上发布预训练 draft 模型。Google 为 Gemma 4 提供 MTP assistant，Z-Lab 维护了一系列 DFlash checkpoint。Red Hat AI 提供覆盖 EAGLE-3、DFlash 和 DSpark 的 draft 模型，DeepSeek 的 DeepSpec 集合为这三种方法提供匹配的 checkpoint。LightSeek 专注于面向 Kimi 的基于 EAGLE 的 draft 模型，Inferact 则发布面向 MiniMax 和 Kimi 的 draft 模型。"
      ],
      "table": {
        "head": [
          "draft 模型发布方",
          "方法",
          "代表性模型与目标模型"
        ],
        "rows": [
          [
            "Google",
            "Gemma 4 MTP",
            "用于 Gemma 4 E2B、E4B、12B、26B-A4B 和 31B 目标模型的 Assistant 检查点。[7]"
          ],
          [
            "LightSeek Foundation",
            "EAGLE-3 和 EAGLE-3.1",
            "用于 Kimi-K2.5、Kimi-K2.6 和 Kimi-K2.7-Coder 的基于 EAGLE 的draft 模型，包括标准版和 MLA 变体。[8]"
          ],
          [
            "Red Hat AI",
            "EAGLE-3、DFlash 和 DSpark",
            "涵盖 Llama、Qwen、Gemma、GPT-OSS、GLM、Nemotron 和 Mistral 等目标模型系列的集合。常见后缀包括 -speculator.eagle3、-speculator.dflash 和 -speculator.dspark。[9]"
          ],
          [
            "Z-Lab",
            "DFlash",
            "适用于 Qwen3、Qwen3.5、Qwen3.6、Gemma 4、Kimi、MiniMax、GPT-OSS 和 Llama 等目标的 DFlash 检查点。检查点名称通常遵循 <target>-DFlash 模式。[10]"
          ],
          [
            "DeepSeek AI",
            "EAGLE-3、DFlash 和 DSpark",
            "DeepSpec 集合为 Qwen3-4B、Qwen3-8B 和 Qwen3-14B 以及 Gemma 4 12B 提供了这三种方法的版本。示例包括 eagle3_qwen3_8b_ttt7、dflash_qwen3_8b_block7 和 dspark_qwen3_8b_block7。[11]"
          ],
          [
            "Inferact",
            "EAGLE-3 和 DSpark",
            "draft 模型，包括 Inferact/MiniMax-M3-EAGLE3、其 GQA 变体以及 Inferact/Kimi-K3-DSpark。[12]"
          ]
        ]
      }
    },
    {
      "type": "h2",
      "title": "实验设置与主要观测",
      "paras": [
        "启用 投机解码 后，实际问题是额外的 drafting 工作能否提升端到端服务性能。候选 token 不必在每个位置都正确，因为 target model 会在提交前对其评估。因此性能取决于有多少候选 token 被接受，以及节省的 target-model 解码工作是否超过 drafting 与验证的成本。",
        "我们使用基于任务的基准测试而非随机 token 序列来评估模型质量与服务性能。接受行为取决于实际模型输出的结构和可预测性，因此基于任务的 prompt 能更真实地反映实际性能。",
        "主要性能指标如下：",
        "输出 token 吞吐，以及相对非投机基线的加速比。",
        "平均接受长度与 draft token 接受率（在可获取的情况下）。",
        "相对非投机基线的模型质量。"
      ]
    },
    {
      "type": "h3",
      "title": "模型与实验覆盖",
      "paras": [
        "实验覆盖五个投机起草（speculative drafting）方法，涉及多个 target 模型系列。对勾表示该 target-方法组合已有基准测试结果；短横线表示该组合未纳入当前实验。",
        "该表汇总了实验中包含的 target-method 组合，并展示了 投机解码在不同模型、负载和 proposal 长度下的表现。由于模型架构、激活参数量、draft 组件规模、负载以及服务条件都会影响性能，每项结果应结合其测试配置来解读。"
      ],
      "table": {
        "head": [
          "目标模型",
          "Native MTP",
          "Gemma 4 MTP",
          "EAGLE-3",
          "DFlash",
          "DSpark"
        ],
        "rows": [
          [
            "google/gemma-4-26B-A4B-it",
            "-",
            "✓ Google",
            "✓ Red Hat AI",
            "✓ Z-Lab",
            "-"
          ],
          [
            "google/gemma-4-31B-it",
            "-",
            "✓ Google",
            "✓ Red Hat AI",
            "✓ Z-Lab",
            "✓ Red Hat AI"
          ],
          [
            "Qwen/Qwen3-8B",
            "-",
            "-",
            "✓ Red Hat AI",
            "✓ Z-Lab",
            "✓ DeepSeek"
          ],
          [
            "Qwen/Qwen3.5-27B",
            "✓ 内建",
            "-",
            "-",
            "✓ Z-Lab",
            "-"
          ],
          [
            "Qwen/Qwen3.5-122B-A10B",
            "✓ 内建",
            "-",
            "-",
            "✓ Z-Lab",
            "-"
          ],
          [
            "Qwen/Qwen3.6-27B",
            "✓ 内建",
            "-",
            "-",
            "✓ Z-Lab",
            "-"
          ],
          [
            "Qwen/Qwen3.6-35B-A3B",
            "✓ 内建",
            "-",
            "-",
            "✓ Z-Lab",
            "-"
          ],
          [
            "moonshotai/Kimi-K2.5",
            "-",
            "-",
            "✓ LightSeek",
            "✓ Z-Lab",
            "-"
          ],
          [
            "MiniMaxAI/MiniMax-M3-MXFP8",
            "-",
            "-",
            "✓ Inferact",
            "-",
            "-"
          ]
        ]
      }
    },
    {
      "type": "h3",
      "title": "吞吐测量",
      "paras": [
        "吞吐方面，我们以标准自回归基线为参照测量每秒生成的 token 数，并扫描 speculative token 数量，以研究投机深度对端到端服务吞吐的影响。"
      ]
    },
    {
      "type": "h3",
      "title": "主要观测",
      "paras": [
        "测量结果随 target 模型、draft 方法、负载和 proposal 长度而变化。",
        "对于 gemma-4-26B-A4B-it，在测试扫描范围内测得的最高吞吐比分别为：Gemma 4 MTP 在 GSM8K 和 MBPP 上达到 2.74× 和 2.62×，DFlash 在 MATH500 和 HumanEval 上达到 2.87× 和 2.79×。EAGLE-3 在四个数据集上的测量结果为 2.11× 至 2.27×。",
        "对于 gemma-4-31B-it，Gemma 4 MTP 在 GSM8K 上达到 2.00×，在 MBPP 上达到 1.99×；DFlash 在 MATH500 上达到 2.34×，在 HumanEval 上达到 2.05×。EAGLE-3 与 DSpark 在四个评测数据集上也均高于基线。与最大实测吞吐对应的 proposal length 随 workload 而变化。",
        "对于 Qwen3-8B，DSpark 的结果从 MATH500 上的 1.15× 到 GSM8K 上的 1.63×。DFlash 的结果范围为 1.08× 至 1.27×。EAGLE-3 在 GSM8K、HumanEval 和 MBPP 上高于基线，而在 MATH500 上的最大实测值仍低于基线。",
        "对于 Qwen3.5-27B、Qwen3.5-122B-A10B 和 Qwen3.6-27B，在测试范围内测得的最大 native-MTP 值均高于对应的最大 DFlash 值。该组中最高倍率为 Qwen3.5-122B-A10B 在 MATH500 上的 2.20×。与最大实测吞吐对应的 native-MTP proposal length 为 N=4 至 N=7，取决于模型与数据集。",
        "对于 Qwen3.6-35B-A3B，DFlash 的结果范围为 1.77× 至 2.06×，最大值在四个数据集上均出现在 N=7。Native-MTP 的结果范围为 1.28× 至 1.49×，最大值出现在 N=6。与 Qwen3.6-27B 的结果差异表明，同一系列内不同模型的表现可能不同。",
        "对于 MiniMax-M3-MXFP8，EAGLE-3 在 N=4 时于 HumanEval 上达到 2.09×。对于 Kimi-K2.5，EAGLE-3 最高达到 2.33×，DFlash 最高达到 2.68×。在测试范围内，EAGLE-3 的最大值通常出现在 N=4，而 DFlash 的最大值出现在 N=7。",
        "在各项实验中，与最大实测吞吐对应的 proposal length 并非常量。对于串行方法，吞吐通常随 N 的前几个取值上升后进入平台期。对于 DFlash 与 DSpark，N=7 常位于较高吞吐的设置之列，而更大的取值并未持续提升吞吐。",
        "这些观察结果反映了本研究所使用的硬件、软件、target model、draft checkpoint、workload 以及 sweep 设置。"
      ]
    },
    {
      "type": "h2",
      "title": "调参考虑",
      "paras": [
        "投机解码 应被视为一种运行时优化，而非对所有 workload 都同样有效的固定设置。与最高吞吐对应的 num_speculative_tokens 取值取决于有多少 proposed token 被接受，以及所避免的 target-model decode 工作量是否超过 drafting 与 verification 的开销。",
        "因此可观测性很重要。model-card 推荐配置或示例配置可作为起点，但最终设置应基于代表性 workload 和端到端测量来确定。有用的信号包括吞吐、平均接受长度、整体接受率以及逐位置接受率。",
        "更大的 proposal window 为系统提供了在一次 verification pass 中提交多个 token 的更多机会。然而，在较靠后的 draft 位置上接受率可能下降。此时，额外的候选贡献甚微，却仍增加 drafting 与 verification 的工作量，导致吞吐趋于平缓甚至回退。"
      ]
    },
    {
      "type": "h3",
      "title": "从受支持的配置入手",
      "paras": [
        "对于原生 MTP，N=1 是保守的起点，因为它引入的额外串行 draft 工作量最少：",
        "__CODE__json::{\"method\": \"mtp\", \"num_speculative_tokens\": 1}",
        "在确认正确性与稳定性后，再扫描更大的取值，如 2、3、4、5、6、7。",
        "在测量中，最大实测吞吐对应的原生 MTP 设置随 target model 与 workload 而变化。对于 Qwen3.5-27B，最大实测吞吐在 GSM8K 和 MATH500 上出现在 N=5，在 HumanEval 和 MBPP 上出现在 N=4，在 MT-Bench 上出现在 N=3。对于 Qwen3.5-122B-A10B，在所列举的四个推理与代码数据集上，最大实测吞吐出现在 N=7。",
        "Qwen3.6 的测量结果同样表明，同一系列内的不同模型，该设置也会发生变化。对于 Qwen3.6-27B，最大实测值出现在 N=4 或 N=5，而所测试的 Qwen3.6-35B-A3B 配置的吞吐随 N 持续提升，直至 N=6。",
        "对于 Gemma 4 MTP 和 EAGLE-3，增大 N 同样会增加串行 draft 工作量。因此，即使 checkpoint 提供了推荐配置，做一次短扫描仍有必要。在 Gemma 4 和 EAGLE-3 实验中，实测吞吐通常在 N 的前几个取值上持续上升，随后趋于平台。",
        "对于 DFlash，先从 draft checkpoint 推荐或支持的 proposal length 入手。许多 DFlash checkpoint 都采用固定 block size 训练。例如，当：",
        "__CODE__python::block_size = 16",
        "最大 proposal length 通常为：",
        "__CODE__python::num_speculative_tokens = 15",
        "因为第一个位置是已确认的 anchor token，其余 15 个位置为 draft 候选。",
        "这是支持的最大 proposal length，不一定是吞吐最高的设置。实践中，测试较小的值很有用，例如：",
        "__CODE__text::N = 3, 7, 11, 15",
        "在 DFlash 实验中，N=7 经常处于吞吐较高的设置之列。对某些工作负载，实测吞吐最大值出现在 N=11。",
        "对 DSpark，num_speculative_tokens 设定每一轮投机所生成的候选 token 数量。在 vLLM 实验中，配置的完整 proposal 会全部提交给 target model 验证，因此 N=3 与 N=7 之类的取值应通过端到端吞吐进行对比。"
      ]
    },
    {
      "type": "h3",
      "title": "监控接受行为",
      "paras": [
        "需要监控的相关信号包括：",
        "在调整 proposal 长度时，逐位置 acceptance 尤为有用。若前几个位置频繁被接受，而后续位置的贡献很小，则降低 num_speculative_tokens 可避免无谓的 draft 工作，从而提升吞吐。",
        "接受率指标应与吞吐一起解读。当 draft 生成开销较低时，某方法即使接受率更低，其吞吐仍可能高于基线。反之，当 draft 组件带来额外开销时，高接受率并不必然对应更高吞吐。"
      ],
      "table": {
        "head": [
          "信号",
          "说明"
        ],
        "rows": [
          [
            "吞吐量",
            "相对于非投机基线，端到端服务性能如何变化"
          ],
          [
            "平均接受长度",
            "平均每轮推测提交多少draft token"
          ],
          [
            "总体接受率",
            "提出的draft token 中被接受的比例是多少"
          ],
          [
            "各位置接受率",
            "提议中较后位置是否仍然有用"
          ]
        ]
      }
    },
    {
      "type": "h3",
      "title": "让扫描匹配工作负载",
      "paras": [
        "不同工作负载会产生不同的接受模式。",
        "在 GSM8K 与 MATH500 的测量中，在测试的 sweep 范围内，中等或更长的 proposal 长度往往对应更高的实测吞吐。对于 Qwen3.5-122B-A10B 上的原生 MTP，实测吞吐随 N 增长至 N=7。对于 DFlash，较高的实测值常出现在 N=7 或 N=11。",
        "对于 HumanEval 与 MBPP，中等 proposal 长度往往属于吞吐较高的配置。代码包含可预测的局部结构，但格式、标识符与实现选择可能导致原本合理的续写发生偏离。"
      ]
    },
    {
      "type": "h3",
      "title": "调参工作流示例",
      "paras": [
        "从该 checkpoint 支持或推荐的配置开始。",
        "使用具有代表性的 prompt 和生成设置进行基准测试。",
        "记录吞吐、平均接受长度和接受率。",
        "扫描若干更小与更大的提议长度。",
        "根据与目标工作负载最相关的指标选择配置。在这些实验中，端到端服务吞吐是首要选择指标。",
        "所选配置不一定拥有最长的 proposal、最高的接受率或最大的平均接受长度。选择时应权衡 drafting cost、验证成本、接受 token 数以及与目标工作负载最相关的指标。"
      ]
    },
    {
      "type": "h2",
      "title": "为新 target 模型训练 speculator",
      "paras": [
        "本指南不深入涵盖 speculator 训练。以下工作流总结了 vLLM Speculators 与 DeepSpec 资源 [13]、[14]、[15] 中的实践要点。",
        "典型工作流如下：",
        "准备具有代表性的 prompt。",
        "使用 target 模型生成响应。",
        "选择 hidden state 生成模式。",
        "收集所需的 target 模型 hidden states。",
        "训练 speculator。",
        "测试接受率与服务吞吐。"
      ]
    },
    {
      "type": "h3",
      "title": "准备有代表性的 prompt",
      "paras": [
        "从反映预期工作负载的 prompt 入手，例如 chat、数学、代码生成、工具调用或多语言任务。另留一组 prompt 专用于评估。",
        "用于训练的响应应由 speculator 将要支持的那个确切 target model 生成。tokenizer、chat template、thinking mode 与生成配置也应与目标部署一致。vLLM 文档强调，把 target model 的 tokenizer 或 chat template 套用到已有响应上，并不能让数据变成 target-specific；响应本身必须来自 target model。"
      ]
    },
    {
      "type": "h3",
      "title": "如何获取 hidden states",
      "paras": [
        "speculator 在训练期间从 target model 接收内部 hidden states。vLLM Speculators workflow 支持三种提供 hidden states 的方式：",
        "所选模式改变 hidden states 的来源；其余训练流程基本一致。"
      ],
      "table": {
        "head": [
          "训练模式",
          "工作方式",
          "主要考虑"
        ],
        "rows": [
          [
            "在线",
            "需要时由运行中的 vLLM 服务器生成隐藏状态，随后丢弃",
            "避免大型磁盘缓存，但同时需要为目标推理和训练提供资源"
          ],
          [
            "离线",
            "在训练开始前生成并存储隐藏状态",
            "之后释放所有 GPU 用于训练，但需要大量存储"
          ],
          [
            "混合",
            "在第一个 epoch 期间生成并缓存隐藏状态，然后复用",
            "只需承担一次生成成本，无需单独的预处理阶段"
          ]
        ]
      }
    },
    {
      "type": "h3",
      "title": "收集 target 模型信息",
      "paras": [
        "vLLM server 可运行 target model，并暴露所选 drafting 方法所需层的 hidden states。选择自定义 target layers 时，speculator 训练配置中也必须使用相同的层选择。",
        "采集的信息取决于方法：",
        "EAGLE-3 使用所选 target model 层的 hidden states 进行自回归 drafting。[4]",
        "DFlash 使用 target 模型的特征训练一个网络，并行预测未来多个位置的 token。[16]",
        "DSpark 在 DFlash 风格的 draft 网络上增加了轻量的顺序头和置信度头。[6]",
        "MTP 训练微调的是 target 模型自身的 MTP 组件，因此要求 target 模型本身已包含兼容的 MTP 层。[13]"
      ]
    },
    {
      "type": "h3",
      "title": "训练与测试 speculator",
      "paras": [
        "speculator 配置必须与 target 模型的 hidden size、词表、tokenizer 以及选定的 target 层保持一致。此外还需选定各方法特有的设置，例如 draft 网络深度、block size、序列长度和学习率。",
        "训练完成后，检查 checkpoint，并将其与 target 模型一同部署到 vLLM 中提供服务。仅凭训练 loss 不足以判断结果；关键指标是 accepted length、acceptance rate、draft 延迟、GPU 显存占用以及端到端服务吞吐。vLLM Speculators 教程涵盖了从数据准备、hidden state 提取到 checkpoint 测试与部署的完整流程。",
        "当某一特定工作负载的 acceptance 偏低时，可调整 prompt 混合比例或训练配置并重复该流程。核心原则是使用 speculator 预期支持的同一 target 模型、生成模式与代表性工作负载。"
      ]
    },
    {
      "type": "h2",
      "title": "总结",
      "paras": [
        "投机解码在 vLLM 中作为 draft-and-verify 方案用于 LLM（大语言模型）服务。draft 组件提出候选的未来 token，target 模型在提交任何 token 之前对该提案进行评估。",
        "共考察五种 draft 方法：native MTP、Gemma 4 MTP、EAGLE-3、DFlash 和 DSpark。它们的主要差异在于如何使用 target 模型的信息，以及候选 token 是串行生成、并行生成，还是通过并行预测与轻量级串行校正相结合的方式生成。",
        "实验覆盖选定的 Gemma、Qwen、MiniMax 和 Kimi 模型，运行于 AMD Instinct™ MI300X 和 MI355X GPU，使用 ROCm™ 软件平台。实测吞吐随 target 模型、draft checkpoint、工作负载、proposal 长度和服务配置的不同而变化。",
        "在所测试的配置中，部分设置带来较小变化，或吞吐低于非投机解码基线，而若干模型-工作负载组合的吞吐比超过 2×。观测范围高端示例包括 gemma-4-26B-A4B-it 上 DFlash 的 2.87×、同一 target 上 Gemma 4 MTP 的 2.83×，以及 Kimi-K2.5 上 DFlash 的 2.68×。",
        "Proposal 长度也是重要的实验变量。增加 num_speculative_tokens 在前几个设置下有时能提升吞吐，而更大的取值可能导致吞吐持平或下降。checkpoint 推荐值可作为起点，但在选择部署配置时，仍需针对代表性负载进行测量并参考 acceptance 指标。"
      ]
    },
    {
      "type": "h2",
      "title": "未来工作",
      "paras": [
        "后续基准测试可纳入非学习类方法，例如 n-gram speculation 与 suffix decoding，尤其适用于代码编辑、Agentic（智能体原生）循环等存在重复 token 模式的负载。",
        "在并发度、prompt 与输出长度、batch size 以及采样设置上进行更广泛的评测，也有助于揭示 投机解码在不同服务条件下的表现。",
        "另一个有价值的方向是研究 speculator 训练数据如何影响代码、数学、对话、多语言 prompt、工具调用和结构化输出等场景下的 acceptance。这可为针对特定负载选择或训练 draft checkpoint 提供更明确的指导。",
        "最后，对 draft 生成、target 验证、KV cache 行为、graph 执行和调度进行更深入的 profiling（性能分析），有助于解释不同 target 模型与负载之间观察到的性能差异。"
      ]
    },
    {
      "type": "h2",
      "title": "实验环境与配置",
      "paras": [
        "测量在 AMD Instinct™ MI300X 和 MI355X 平台上使用以下配置运行。",
        "Hardware 1：8× AMD Instinct™ MI300X GPU（gfx942），搭配 2× AMD EPYC™ 9654 96-Core Processor。",
        "Hardware 2：8× AMD Instinct™ MI355X GPU（gfx950），搭配 2× AMD EPYC™ 9575F 64-Core processor。MiniMax-M3-MXFP8 实验使用该平台。",
        "Ubuntu 22.04.5 LTS、ROCm/HIP runtime 7.2.53211、vLLM 0.23.1rc1.dev1120+g0f0f28b53、PyTorch 2.11.0+gitd0c8b1f、Transformers 5.13.1、Python 3.12.13。",
        "服务器制造商可能会采用不同的配置，从而产生不同的结果。性能可能因配置、软件、vLLM 版本以及是否使用最新驱动程序和优化而有所不同。"
      ]
    }
  ],
  "conclusion": [
    "**① 加速来自一次 target 前向提交多个 token，而不是放宽判定标准。** 原模型始终是 target，draft 只提候选，验证从左到右进行，遇到第一个被拒 token 就停止并丢弃后续候选，输出行为与不投机时一致。",
    "**② 五种方法的分野在两点：draft 拿到哪些 target 信息，以及候选是串行还是并行起草。** native MTP 内建在模型里、Gemma 4 MTP 独立打包但共享 target 的 KV cache、EAGLE-3 融合三层 hidden states 自回归起草，DFlash 用 anchor 加 mask 一次并行预测整块，DSpark 再补一个轻量 Markov 头补回位置间的依赖。",
    "**③ 部署上没有万能配置，调参要看接受行为。** 实测吞吐比从低于基线到 2.87× 都有，同一系列的不同模型（Qwen3.6-27B 与 35B-A3B）最优 N 都不一样；先跑通 checkpoint 支持的配置，再用逐位置接受率把 N 收到峰值，通常落在 4 到 7。",
    "投机解码本质是用额外显存和 draft 计算，换每次 target 前向的产出 token 数。在 AMD Instinct + ROCm 上它已经跑通，真正决定收益的是把 N 和 draft checkpoint 压到目标工作负载的接受模式上，而不是照抄一个推荐值。"
  ],
  "reference_url": "https://vllm.ai/blog/2026-08-23-speculative-decoding-amd-gpus"
}

out_path = os.path.join(_article_dir, "article_data.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=2)
print(f"✅ 写入 {out_path} ({len(json.dumps(DATA, ensure_ascii=False))} chars, {len(DATA.get('sections', []))} sections)")
