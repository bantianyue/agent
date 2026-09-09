✅ 完成 (north-mini-code-megakernel)
- 源: Cohere 官方博客《Inside the megakernel serving engine for North Mini Code》(46k/22min; 图11)
- 主题(亲自读全): 以 decode megakernel(单常驻kernel+task list+计数barrier)服务 North Mini Code, 目标解码内存带宽极限
- 体验数字: H100 SoL≈470tok/s; vLLM185(39%); megakernel bs1=292=62%SoL(=1.58x); 端到端 AIME1.41x/GPQA1.25x/MMLU-Pro1.33x/SciCode1.37x/LiveCodeBench1.28x; 无精度损失; 真实路由batch8 1.32x vs uniform1.14x
- 机制要点(正文): ABI(12warf/3warpgroup + 32-int task descriptor + counting barrier) 缝16 opcode单CUDA文件; 红利=省launch/全栅barrier+消波次量化+去伪依赖+权重预取; 调度 round-robin+调好波序(bs1: tuned291/interleaved282/attn-first236)+局部work stealing; 服务= Python控制面暂挂 decode + C++独占decode(park/resume)
- 已知限制(正文): 无 prefill/decode 混合; max batch 8 为配置限制; MK 纯 decode
- 配图: 官方真实图4张 cdn.sanity PNG (decode吞吐/波次量化示意/并行transformer层/跨batch-上下文); 封面=官方 abstract hero(源码512上限)
- preflight ALL PASS; push media=TIqnnVEu6Oy3-wtKttGa0QgtEVQo8I7ZSJYzv_RCTgCp-IrpcGZxaAR6Y90n2Xbe; verify body 4/4; arbiter(queue jid_20260909_175046_87917b) done
source: https://cohere.com/blog/megakernels
