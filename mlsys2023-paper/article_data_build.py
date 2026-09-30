# -*- coding: utf-8 -*-
DATA = {
    "title": "PaLM推理优化实录:540B模型29ms/token、MFU 76%",
    "summary": [
        {"key": "核心观点", "body": "Google这篇MLSys 2023论文给出Transformer推理的工程原则：用解析模型选多维切分策略，配Looped CollectiveEinsum等底层优化，在TPU v4上用int8权重把PaLM 540B的生成延迟做到29ms/token、prefill的MFU做到76%。"},
        {"key": "关键数据", "body": "2D权重静止切分让通信随芯片数以1/√nchips下降；多查询注意力加按batch切分让KV缓存加载省nchips倍，上下文长度撑到32倍；64路张量并行仍有44% MFU，FasterTransformer的32路只能到33%。"},
        {"key": "方法创新", "body": "权重聚集布局在大batch/prefill时反转搬运方向：权重全量广播、激活静止，通信量从正比于BL降到正比于√BL；并行Transformer块把每层两次all-reduce砍成一次。"},
    ],
    "lead": [
        "把540B参数的模型跑起来做推理，难的不是算力，是访存和通信：每个token都要把全部参数从HBM搬一遍，KV缓存随batch和上下文膨胀，芯片一多通信就封顶。Google这篇论文把PaLM推理的每一笔账都算清楚了。",
        "核心方法是先建模再选型：解析地算出每种切分策略的通信量，按应用场景选1D、2D还是权重聚集；再用多查询注意力瘦身KV缓存、并行块砍通信。下面逐节拆开。",
    ],
    "sections": [
        {
            "type": "h2",
            "title": "推理成本的三个账本",
            "paras": [
                "推理成本记三笔账：延迟、吞吐、模型FLOPS利用率。延迟拆成prefill和decode：输入token在prefill一次性并行处理，输出token在decode逐个自回归生成；decode延迟也可按步计量。MFU是实测吞吐除以硬件峰值FLOPS下的理论最大吞吐。",
                "访存账：权重和KV缓存存在HBM里，每次前向都要搬进计算核心一次，小batch时搬权重主导，大batch加长序列时搬KV缓存主导。计算账：N参数解码器模型每token要2N次matmul FLOP。通信账：模型切到多芯片上就有芯片间通信，芯片越多通信占比越大。",
                "三个典型场景：要最低延迟就堆芯片、多维切分，小batch延迟低但MFU差、单token成本高；要长上下文，500B+模型多头注意力的KV缓存在batch 512、上下文2048时达3TB，是参数量的3倍，每个生成步都要搬一遍，计算核心基本空转；要离线高吞吐就拉大batch，MFU好看，单token成本低。",
                "64块TPU v4上，PaLM 540B用int8权重做到生成29ms/token，大batch处理输入token时MFU达76%，上下文2048。图1是8B、62B、540B三个模型在bf16和int8下的成本-延迟帕累托前沿：左图生成64个token的每token延迟，右图处理2048个输入token的时间，C是芯片数，B是batch大小。",
            ],
            "fig_after": {
                "3": [{"src": "fig01.png", "caption": "图1:PaLM模型的成本对延迟。上下文长度2048，每条线上的点是效率对延迟的帕累托前沿。C为芯片数，B为batch大小。左：生成64个token的每token延迟；右：处理2048个输入token的时间"}],
            },
        },
        {
            "type": "h2",
            "title": "切分符号与通信原语",
            "paras": [
                "论文基于TPU v4的3D torus拓扑X×Y×Z描述切分。记号BLExyz表示逻辑形状BLE的张量按最后一维E切成X×Y×Z份，每芯片分到[B, L, E/(X×Y×Z)]；某轴上复制则省略该轴。后缀partialsum-x表示已在芯片本地求和、还需沿x轴跨芯片求和。",
                "通信原语来自MPI：all-reduce(x)把partialsum张量沿x轴求和再广播；拆成两步就是reduce-scatter(x)和all-gather(x)：前者求和但结果按轴分片，后者广播拼接后输出变大X倍；all-to-all把分片从一个张量维度搬到另一个，比如BLHxQ变为BxLHQ。",
            ],
        },
        {
            "type": "h2",
            "title": "前馈层切分:从1D到2D再到权重聚集",
            "paras": [
                "最简单的1D权重静止：E×F权重矩阵沿E或F轴切到nchips块，每块权重固定在芯片上，激活在芯片间搬运。算连续两个matmul时有个经典技巧：第一个按输出轴切，第二个按输入轴切，中间不需要通信。但通信量恒定不随芯片数下降，芯片一多就封顶。",
                "2D权重静止把E×F矩阵沿E和F双轴切，每块近似正方形。E=1024、F=4096、64芯片时，E切4份、F切16份，每芯片存256×256。交替在两个轴上做激活聚合，每芯片永远有算自己权重块所需的激活分片，不再需要完整复制激活。通信量按O(1/√nchips)下降，加芯片就能继续降延迟。dff=4dmodel时，nchips>16后2D比1D省通信。",
                "细节上，2D布局权重为ExFyz，dmodel切X份、dff切Y×Z份。最优取X=0.5×√nchips、YZ=2×√nchips，总通信时间Tcomm=8BLE/(√nchips×带宽)，而1D是Tcomm=2BLE/带宽。",
                "batch再放大，输出激活可能比权重还大，这时反过来更划算：激活静止在芯片上，权重在芯片间搬运，这就是权重聚集。batch中等用X或XY聚集，大batch用XYZ全聚集，prefill和decode可以混用不同布局。最优聚集轴数N=√(BL·nchips/F)，总通信时间Tcomm=4E√(BLF)/(√nchips×带宽)，正比于√BL而非BL。图3显示batch以token计越大，最优布局越往权重聚集滑。",
            ],
            "fig_after": {
                "1": [{"src": "fig02.png", "caption": "图2:前馈层切分布局。(a)1D权重静止，(b)2D权重静止，(c)权重聚集。绿色为all-gather，红色为reduce-scatter，标注了每步的张量形状"}],
                "3": [{"src": "fig03.png", "caption": "图3:前馈层通信量随batch大小变化。batch以token计，X=Y=Z=4、dmodel=16384、dff=65536。低token数时2D权重静止最优，token数大了切到不同权重聚集布局"}],
            },
        },
        {
            "type": "h2",
            "title": "多查询注意力:KV缓存瘦身32倍",
            "paras": [
                "多头注意力可以照前馈层的方式切，把nheads当dff。但KV缓存的访存开销在大batch、长上下文下会压过一切。多查询注意力只给K、V留一个头，nheads个查询头共享，KV缓存直接小nheads倍，代价是少了一个可并行的轴。",
                "直接照搬多头那种按头切分，会把唯一的K、V头复制到每块芯片，省内存的效果全丢。论文的切法是按batch维B切Q、K、V：每芯片只加载1/nchips的KV缓存，访存时间同比例下降。代价是输入激活要用all-to-all重分片，但decode时Q、K、V每样本只有一个token，KV缓存却有2048个token，花小通信省大访存非常划算。prefill时Q有2048个token，K、V访存被摊薄，就不按batch切，仍用按头切。",
                "效果上，64芯片、batch 128时优化后的多查询布局支持43000的上下文长度，多头只有1320，基线多查询只有660，直接撑到32倍。8层540B、batch 256下，上下文拉长时优化布局的每token延迟远低于多头和基线布局，8192到32768的序列上注意力只占总运行时间的8%到31%。",
            ],
            "fig_after": {
                "0": [{"src": "fig04.png", "caption": "图4:多查询注意力按batch切分后KV缓存加载成本更低。上：多头对多查询的Q、K/V形状；下：(a)多头注意力按头切分，(b)多查询按头切分浪费了省内存的效果，(c)多查询按batch切分，每芯片只需一片K"}],
                "2": [{"src": "fig05.png", "caption": "图5:注意力层切分布局对比。(a)多头注意力按头切，(b)多查询注意力按batch切。标注了WQ/WK/WV投影后、softmax、WO投影的每步形状与通信原语"}],
            },
            "table": {
                "head": ["模型变体", "dhead", "最大上下文长度(batch=128)", "最大上下文长度(batch=512)"],
                "rows": [
                    ["多头", "128", "1320", "330"],
                    ["基线多查询", "256", "660", "165"],
                    ["优化多查询", "256", "<strong style=\"color:#1a7f5a;\">43,000</strong>", "<strong style=\"color:#1a7f5a;\">10,700</strong>"],
                ],
            },
        },
        {
            "type": "h2",
            "title": "并行块、底层优化与量化",
            "paras": [
                "PaLM用的并行Transformer块把注意力和前馈并行算再相加，好处有三：一是每层只有一个layernorm，小batch延迟低；二是前馈输入矩阵可与WQ融合、WK/WV互融、前馈输出与WO融合，大matmul跑得更满；三是每层少一次all-reduce，dff/nheads轴通信砍半。串行版decode每步延迟高14%。",
                "底层用Looped CollectiveEinsum让通信和计算重叠，把大部分reduce-scatter和all-gather的通信时间藏起来，比朴素的编译器切分调度快约1.4倍。reduce-scatter选在隐维度（E/F）而非batch/序列维上做，就是为了给CollectiveEinsum更多重叠机会。另有张量内存布局、top-k/top-p采样、log2底的Softmax/Swish、prefill增量处理等优化。",
                "量化用AQT库把16位权重转int8，质量无感，省权重加载的访存时间，低batch场景最受益，权重聚集布局的通信量也跟着降。batch 64下int8权重28.5ms/token，bf16要36.9ms；大batch下两者成本接近，因为瓶颈在计算而matmul仍是bf16。激活量化还没做，作者认为能进一步降大batch成本。",
            ],
            "fig_after": {
                "0": [{"src": "fig06.png", "caption": "图6:PaLM 540B在64芯片上做文本生成，2D与1D权重静止布局的每token延迟随芯片数变化。两者都趋向通信受限，2D因渐近扩展性更好而胜出"}],
                "2": [{"src": "fig07.png", "caption": "图7:PaLM 540B在64芯片上做prefill的MFU，序列长度2048，batch以token计。batch以token计越大，越该从2D权重静止切到权重聚集，大batch下MFU达76%"}],
            },
        },
        {
            "type": "h2",
            "title": "PaLM实测:29ms/token与76% MFU",
            "paras": [
                "方法跑在JAX/XLA/T5X上，最多256块TPU v4。每块275 TFLOPS bf16算力、32GiB HBM、1200GB/s带宽、270GB/s互连。540B的注意力头从48补到64以便在64+芯片上切分，多18B参数、花3% MFU，但切分效率赚回来更多。",
                "端到端看，低延迟场景用batch-1 prefill配batch 32到64 decode：prefill batch 1延迟最优，decode加到64对延迟几乎无影响、MFU却好得多，实际可用多采样或prefill/decode流水线实现。高吞吐场景切大batch并在prefill/decode间换布局，大batch下权重加载不重要就用bf16。成本按chip-seconds/token=nchips×时间/(BL)算，与运营成本成正比、与MFU成反比。",
                "表2是540B的四个典型配置：低延迟prefill 64芯片batch 1、0.29秒、MFU 43%；低延迟decode 64芯片batch 64、1.82秒、MFU 14%；高吞吐prefill 64芯片batch 512、85.2秒、MFU 76%；高吞吐decode 64芯片batch 512、6.0秒、MFU 33%。62B的配置见表3，芯片数减半，MFU相近，低batch延迟随模型规模亚线性增长，大致是平方根关系。",
                "一个直观的例子：跑在64块TPU v4上的PaLM 540B int8版，处理用户64个token、查1920个token的缓存对话历史、生成64个token回复，总共1.9秒。离线场景处理1984个输入token、生成64个输出token，整体FLOPS效率73%。",
            ],
            "fig_after": {
                "3": [{"src": "fig08.png", "caption": "图8:8层PaLM 540B在64芯片、batch 256下每生成token延迟对序列长度。虚线表示完整118层模型上，上下文超过512后多头或基线多查询的KV缓存装不进内存"}],
            },
            "table": {
                "head": ["", "低延迟Prefill", "低延迟Decode", "高吞吐Prefill", "高吞吐Decode"],
                "rows": [
                    ["芯片数", "64", "64", "64", "64"],
                    ["Batch", "1", "64", "512", "512"],
                    ["FFN布局", "WS 2D", "WS 2D", "WG XYZ", "WS 2D"],
                    ["注意力切分", "按头", "按batch", "按batch", "按batch"],
                    ["权重格式", "int8", "int8", "bfloat16", "bfloat16"],
                    ["MFU", "43%", "14%", "<strong style=\"color:#1a7f5a;\">76%</strong>", "33%"],
                    ["延迟", "0.29s", "1.82s", "85.2s", "6.0s"],
                ],
            },
        },
        {
            "type": "h2",
            "title": "对打FasterTransformer:64路并行不封顶",
            "paras": [
                "对比FasterTransformer基准，用16到32块A100 80GiB，，用MFU归一化芯片数和算力后比较。跑60个输入token、20个输出token的推理，PaLM 540B实现绝对延迟最优；Megatron 530B模型上除一个延迟目标外MFU全面最优。PaLM版比Megatron版MFU高最多10%，主要靠并行注意力/前馈层。",
                "FasterTransformer的32路张量并行最多33% MFU，16路反而有46%，说明张量并行过16路后通信封顶。而这套实现能扩展到64路张量并行仍有44% MFU，2D权重静止在TPU v4大互连域上的扩展性明显更好。",
            ],
            "fig_after": {
                "1": [{"src": "fig09.png", "caption": "图9:60个输入token、20个输出token推理的MFU对总延迟。Ours在64芯片上跑PaLM和Megatron模型，对比FasterTransformer的TP8/PP3、TP16、TP32三档"}],
            },
        },
    ],
    "conclusion": [
        "这篇论文的价值在于把推理优化变成了可计算的选择题：1D、2D、权重聚集三种布局的通信量都有解析式，按batch大小和阶段选型；多查询注意力加按batch切分把KV缓存这个最大包袱卸掉32倍；并行块和CollectiveEinsum把剩下的通信 latency 榨干。",
        "放到今天看，结论依然硬核：decode是访存 bound，堆芯片降延迟但MFU掉；prefill是计算 bound，大batch加权重聚集MFU冲到76%。PaLM 540B在64块TPU v4上29ms/token、1.9秒完成一轮对话，放在2023年是新的帕累托前沿。",
        "作者也留了口子：FLOP数和通信量最终会卡住稠密Transformer，稀疏MoE和自适应计算是下一步。今天回头看，这个判断相当准。",
    ],
    "reference_url": "https://proceedings.mlsys.org/paper_files/paper/2023/file/c4be71ab8d24cdfb45e3d06dbfca2780-Paper-mlsys2023.pdf",
}
