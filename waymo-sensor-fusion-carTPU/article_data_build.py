# -*- coding: utf-8 -*-
"""Waymo Sensor Fusion Processor (carTPU) 编译 build"""
import json

DATA = {
 "title": "Waymo Hot Chips 2026：传感器融合处理器 carTPU 深度解析",
 "lead": [
  "Waymo 在 Hot Chips 2026 展示了它的传感器融合处理器——围绕自动驾驶车辆中央计算打造的专用硅。ServeTheHome 现场报道全文。",
  "核心故事：Waymo 不再用现成的自动驾驶加速器，而是围绕自己的传感器融合模型协同设计、掌控从首个像素到 embedding 输出的完整路径，目前已在第六代车辆量产车队运行。"
 ],
 "summary": [
  {
   "key": "规格与自研思路",
   "body": "45×45mm FCBGA、208mm² N5 工艺、LPDDR5x 273GB/s、PCIe Gen5 x8、<75W。自己设计 carTPU/ISP/codec/MIPI，GPU/互连/内存/PCIe 用第三方，明文无 DSP。"
  },
  {
   "key": "架构与软件",
   "body": "160 TOPS INT8 / 80 TFLOPS FP16：控制 PE（双核 RISC-V）+ carTPU 阵列（16 PE+2 core），camera/radar/fusion 三 backbone。compiler-first：AOT 编译 mega-kernel 分片进 SRAM，确定性数据流。"
  },
  {
   "key": "管线与定位",
   "body": "相机：MIPI→HDR ISP→时间去噪→自研 demosaic→patch extraction；雷达/激光：共享 MIPI + GPU 处理 FFT cubes + 以太旁路。定位为自动驾驶规模化首个专用 ASIC。"
  }
 ],
 "sections": [
  {
   "type": "h2",
   "title": "车辆系统视角与自研动机",
   "paras": [
    "Waymo 从车辆系统视图开场：计算居中，周围是激光雷达、相机、雷达、麦克风传感器阵列——这正是传感器融合处理器必须聚合车内每条流的位置。",
    "今天的焦点是 Waymo foundation-model 栈里的传感器融合编码器。相机、激光雷达、雷达的 embedding 都落在该编码器上，这个阶段就是这颗硅为运行而造的。驾驶 VLM 更用于高延迟容忍任务。",
    "Waymo 想要围绕自家传感器融合模型协同设计、自研传感器处理，从首个像素进来到 embedding 输出、低 batch 下测延迟。keynote 里还提到：车辆能在凤凰城夏日阳光下有液冷，但是 60°C 的液体——与数据中心非常不同。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig02.png",
      "caption": "图 1：Waymo 车辆系统视图——计算居中，聚合 lidar/相机/雷达/麦克风流。"
     }
    ],
    "1": [
     {
      "src": "fig03.png",
      "caption": "图 2：聚焦 foundation-model 栈里的传感器融合编码器。"
     }
    ],
    "2": [
     {
      "src": "fig04.png",
      "caption": "图 3：自研传感器处理设计目标——协同设计、低延迟（首个像素到 embedding）。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "头号规格与子系统分工",
   "paras": [
    "头号规格在此类中算紧凑：45×45mm FCBGA 封装、N5 工艺 208mm² 硅、封装内 LPDDR5x（273GB/s）、PCIe Gen5 x8 主机接口、25G 以太、TDP 低于 75W。",
    "主要子系统在 Waymo 设计和成熟第三方 IP 间拆分。Waymo 自研块处理 carTPU、ISP、codec、MIPI ingest 路径和 scratchpad 内存；两块 GPU、片上互连、内存、PCIe 和以太控制器、PHY、安全启动、外设来自第三方。值得注意的是 Waymo 没有 DSP——部分因为所需编程技能。",
    "一条演进时间线解释为何 Waymo 自研：从 2013 年深度卷积网络、经 transformer 和大数据集，到 2024 年驱动感知/规划/世界建模的 foundation-model 栈。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig05.png",
      "caption": "图 4：关键规格——45mm 封装、N5、LPDDR5x 273GB/s、<75W。"
     }
    ],
    "1": [
     {
      "src": "fig06.png",
      "caption": "图 5：子系统分工——Waymo 设计 vs 第三方 IP。"
     }
    ],
    "2": [
     {
      "src": "fig08.png",
      "caption": "图 6：演进时间线——2013 深度卷积到 2024 foundation-model 栈。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "算力与架构",
   "paras": [
    "计算吞吐靠整数和更高精度。Waymo 报 160 TOPS（INT8×INT8）和 80 TFLOPS（FP16），64MB 片上 SRAM、8MB register file、160GB/s 外部内存带宽。Waymo 说聚焦更高精度以保真度。",
    "架构总览：控制块 + 核心 carTPU 阵列。每个控制 PE 场带双核 RISC-V CPU（向量扩展），核心阵列打包 16 个处理单元和 2 内核。",
    "Waymo 的 carTPU 核心拆到三个 backbone：camera、radar、fusion。fusion 路径延迟关键，camera 和 radar backbone 跑最大并发。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig09.png",
      "caption": "图 7：算力——160 TOPS INT8 / 80 TFLOPS FP16 / SRAM/寄存器/外带。"
     }
    ],
    "1": [
     {
      "src": "fig10.png",
      "caption": "图 8：架构总览——控制块 + carTPU 阵列。"
     }
    ],
    "2": [
     {
      "src": "fig11.png",
      "caption": "图 9：carTPU 核心三 backbone——camera/radar/fusion。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "数据流与硬件设计原则",
   "paras": [
    "数据流原则保持硬件精简。Waymo 依赖带静态 shape 的确定性 mega-instructions，约一千个周期单线程执行、无缓存无分支；FIFO 和带信号量的内存处理跨计算和 DMA 线程的排序与背压。",
    "每个处理单元保持高度分库的 2MB SRAM——按 activations 和 context 保持驻留以喂 GEMV 来设计。Ring 和 mesh DMA 把权重流式与跨 PE 集合分开，4× 计算切片每周期维持 INT8 GEMV、带稀疏 gather/scatter 融合。",
    "灵活的 GEMV 路径随每个计算原语塑形。Waymo 为最大空间利用率变换操作——这对在差异很大的层形状里保持张量核忙碌很关键。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig12.png",
      "caption": "图 10：数据流——确定性 mega-instructions、静态 shape、无缓存/分支。"
     }
    ],
    "1": [
     {
      "src": "fig13.png",
      "caption": "图 11：处理单元——分库 2MB SRAM、Ring/mesh DMA、INT8 GEMV。"
     }
    ],
    "2": [
     {
      "src": "fig14.png",
      "caption": "图 12：灵活 GEMV 路径为各计算原语塑形。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "软件：compiler-first",
   "paras": [
    "软件遵循 compiler-first 哲学。AOT 编译为整个模型构建 mega-kernel 并分片适配 SRAM，让编译器管理分区、全局内存流量、竞争条件和数值精度。",
    "Waymo 主张这里已达成性能比原始 TOPS 更重要。该图把持续优化画为相对初始延迟的加速比，显示协同设计和实测效率胜过账面吞吐。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig15.png",
      "caption": "图 13：compiler-first——AOT 编译 mega-kernel 分片进 SRAM。"
     }
    ],
    "1": [
     {
      "src": "fig16.png",
      "caption": "图 14：已达成性能——持续优化 vs 初始延迟、实测效率胜过账面 TOPS。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "相机管线",
   "paras": [
    "相机管线工作从 MIPI ingest 开始。原始传感器数据移进 DRAM，同时构建灰度对齐金字塔供后续融合用，同一阶段做传感器错误处理。",
    "HDR ISP 扩展该路径。原始帧从 RGB 转 YUV 带去时间噪，然后 still-frame 图像 codec 写 YUV 金字塔回 DRAM。",
    "流水线保持相机流移动：MIPI ingest 输出推进、ISP 尽可能前进，YUV 金字塔以子帧延迟生成——大约比传感器读出晚几百行图像。",
    "相机路径随后是 patch extraction。该阶段从 YUV 金字塔拉任意缩放的兴趣区、转颜色空间、应用合成 HDR 曝光，让模型只看它们需要的窗口。",
    "流程视图把 ISP 块串起来。原始传感器流经图像信号处理进 RGB，再到金字塔生成、内联有损 codec 在到达 DRAM 前压缩。Waymo 很大一部分似乎在自研。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig18.png",
      "caption": "图 15：MIPI ingest——原始数据进 DRAM + 灰度对齐金字塔。"
     }
    ],
    "1": [
     {
      "src": "fig19.png",
      "caption": "图 16：HDR ISP——RGB→YUV、时间去噪、codec 写金字塔。"
     }
    ],
    "2": [
     {
      "src": "fig20.png",
      "caption": "图 17：流水线——YUV 金字塔以子帧延迟生成。"
     }
    ],
    "3": [
     {
      "src": "fig21.png",
      "caption": "图 18：patch extraction——从金字塔拉兴趣区、合成 HDR 曝光。"
     }
    ],
    "4": [
     {
      "src": "fig22.png",
      "caption": "图 19：ISP 流程——原始流→ISP→RGB→金字塔→内联有损 codec。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "ISP 自研细节",
   "paras": [
    "时间去噪把单帧结果与多帧处理对比。多帧时间去噪用延迟换更干净图像，对夜间和低对比场景的下游融合重要。",
    "Waymo 不用标准图像信号处理器块、而自研 demosaic。传统 demosaic 会引入 zipper 和颜色伪影，自研版本保颜色精度和边缘细节。",
    "HDR 感知针对棘手真实场景。夜间远光灯眩光和出隧道瞬间正是自动驾驶车必须读对的场景，两者都推高动态范围需求。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig23.png",
      "caption": "图 20：时间去噪——单帧 vs 多帧。"
     }
    ],
    "1": [
     {
      "src": "fig24.png",
      "caption": "图 21：自研 demosaic——保住颜色精度和边缘细节。"
     }
    ],
    "2": [
     {
      "src": "fig25.png",
      "caption": "图 22：HDR 感知——应对远光灯眩光和隧道转场。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "雷达与激光雷达处理",
   "paras": [
    "雷达和激光共享同一入口前端：MIPI ingest 移原始数据进 DRAM 并应用传感器错误处理，再深入处理。",
    "GPU 阶段处理重传感器数学：点云处理、FFT cube 波形处理、GPGPU 编程模型跑在 GPU 上，与 carTPU 推理核分开。",
    "一些雷达/激光数据走以太直连主机，从 GPU 和 carTPU 卸载流量，让传感器数学和模型推理不争同一带宽。",
    "典型雷达处理基于多维 FFT——range、Doppler、azimuth 投影从该阶段出来，喂给后与相机数据融合的点/特征表示。",
    "示例激光投影展示管线产生的表示：透视图和顶视图、加上 range/intensity/elongation 图，给出可融合输出形态的观感。"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig26.png",
      "caption": "图 23：雷达/激光共享 MIPI 入口前端。"
     }
    ],
    "1": [
     {
      "src": "fig27.png",
      "caption": "图 24：GPU 处理重传感器数学——FFT cube、点云、GPGPU。"
     }
    ],
    "2": [
     {
      "src": "fig28.png",
      "caption": "图 25：以太旁路——传感器数学与推理不争带宽。"
     }
    ],
    "3": [
     {
      "src": "fig29.png",
      "caption": "图 26：典型雷达处理——多维 FFT 的 range/Doppler/azimuth 投影。"
     }
    ],
    "4": [
     {
      "src": "fig32.png",
      "caption": "图 27：示例激光投影——perspective/top-down/range/intensity/elongation。"
     }
    ]
   }
  },
  {
   "type": "h2",
   "title": "结语与定位",
   "paras": [
    "Waymo 以把 carTPU 定位为首个规模化自动驾驶专用 ASIC 收尾（第六代车辆可体验），并称这是 Waymo 用的其中一颗芯片。",
    "**ServeTheHome 看法**：Waymo 已超越现成自动驾驶加速器，转向围绕自家融合模型协同设计的硅。该处理器让公司掌控从传感器到 embedding 的完整路径，且据 Waymo 已在量产车队运行。（作者表示：这场演讲很快，大概有不少遗漏。）"
   ],
   "fig_after": {
    "0": [
     {
      "src": "fig34.png",
      "caption": "图 28：Waymo carTPU 定位——首个规模化自动驾驶专用 ASIC。"
     }
    ]
   }
  }
 ],
 "conclusion": [
  "Waymo 这颗传感器融合处理器讲清楚了「为自动驾驶自研硅」的完整故事：45mm 封装/N5/208mm²/<75W TDP 的紧凑规格里，自研 carTPU/ISP/codec/MIPI（无 DSP），第三方 GPU/互连/内存；160 TOPS INT8/80 TFLOPS FP16，控制 PE（双核 RISC-V）+16 PE 阵列跑 camera/radar/fusion 三 backbone。",
  "设计哲学值得圈点：确定性 mega-instructions（无缓存无分支）+ compiler-first 的 mega-kernel 分片进 SRAM；相机从 MIPI→HDR ISP→时间去噪→自研 demosaic→patch extraction，雷达/激光共享 MIPI + GPU 跑 FFT cubes + 以太旁路。定位为首个规模化自动驾驶专用 ASIC、第六代车上运行——这是 Waymo 从 sensor 到 embedding 全程自控的路标。"
 ],
 "reference_url": "https://www.servethehome.com/waymo-sensor-fusion-processor-at-hot-chips-2026/"
}

with open("article_data.json", "w", encoding="utf-8") as f:
    json.dump(DATA, f, ensure_ascii=False, indent=1)
print("✅ 写入 article_data.json")
