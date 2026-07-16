# 使用 NVIDIA TensorRT 多设备推理支持，跨多 GPU 扩展 AI 推理

## NVIDIA NCCL：分布式推理的传输层

NVIDIA 集合通信库 (NCCL) 提供高性能的多 GPU 和多节点集合操作，支撑着数千 GPU 上的大规模模型训练。NCCL 自动为给定拓扑选择最优传输方式，将 NVIDIA NVLink、NVSwitch、PCIe 和 InfiniBand 抽象在统一接口之后。通过与 NCCL 直接集成，TensorRT 在运行多设备推理时继承了这种传输优化。

新的多设备特性覆盖了完整的 NVIDIA NCCL 分布式集合操作集：AllReduce、Broadcast、Reduce、AllGather、ReduceScatter、AlltoAll、Gather 和 Scatter。

## 分布式推理的并行策略

分布式推理可以通过几种并行策略来实现，每种策略在内存节省、计算扩展和通信开销之间有不同的权衡。最常见的策略是张量并行和上下文并行。

### 张量并行

在张量并行中，单层权重被分区到多个 GPU 上。每个 GPU 计算该层矩阵乘法的分片，然后通过集合操作合并部分结果以产生完整输出。这减少了每设备的内存权重，使其在单层权重超过单 GPU 内存时成为自然（且通常是唯一）的选择，与输入序列长度或批量大小无关。

在一个 Transformer 块中，列并行投影（如 QKV 和 MLP 上投影）与行并行投影（注意力输出和 MLP 下投影）配对，使得每个块只需要一次 AllReduce，通信开销保持有界。

### 上下文并行

在上下文并行中，输入序列沿序列维度被分区到多个 GPU 上。每个 GPU 仅处理序列的一个切片，而集合操作在需要时使全局序列可用，例如在注意力计算期间。上下文并行对于长序列工作负载特别有效，因为注意力的二次缩放与序列长度成正比，使其成为计算和内存的主要消耗者。

它也是扩散和 DiT 模型的特别自然的选择，因为其双向注意力规避了因果掩码引起的负载不均衡问题。

NVIDIA TensorRT 11.0 引入了各种并行化策略所需的 `IDistCollectiveLayer` 原语支持。本文的其余部分聚焦于上下文并行，它直接解决了现代生成式媒体流水线中的主要成本：长序列注意力。

#### 生成式媒体中的上下文并行

基于扩散的图像和视频生成流水线将其计算和内存预算的很大一部分花在处理长 token 序列的注意力块上。一幅高分辨率图像潜变量或一段多帧视频剪辑可以在每个块中产生数万个 token 的序列，而注意力与序列长度呈二次缩放。

#### AllGather KV

上下文并行将序列分区到多个 GPU 上。每个 rank 处理与其序列分区对应的查询 (Q) 切片。实现上下文并行的一种直接方法是 AllGather KV 方法，其中 rank 通过 AllGather 集合交换其键 (K) 和值 (V) 分片，然后计算局部注意力，使每个 rank 能够关注完整序列。结果是每个 rank 的注意力输出覆盖完整序列，代价是每个注意力块增加一次集合操作，而局部 Q × Kᵀ 矩阵乘法随 rank 数量成比例缩小。

对于视频和高分辨率图像扩散，这种权衡在去噪步骤中有利地累积。每步的通信开销仍然受序列维度 AllGather 的限制，而计算和内存的节省适用于每一步的每个注意力层。

#### Ring Attention

上下文并行可以通过多种方式实现，每种方式都有不同的权衡。

AllGather KV 方法的一个潜在改进是 Ring Attention，其中通信和计算被重叠。这使得每个 GPU 可以同时处理其局部 Q，同时 K 和 V 以环形拓扑持续流过。Ring Attention 还减少了内存占用：使用在线 softmax，完整尺寸的 K 和 V 张量无需在任何 GPU 上实例化。

#### DeepSpeed Ulysses

对于长上下文（数万 token），另一种上下文并行实现方法是 DeepSpeed Ulysses。它首先沿序列维度将单个样本分区到参与 GPU 上。在注意力计算之前，它对分区后的 Q、K 和 V 使用 all-to-all 通信集合。

这确保每个 GPU 接收完整的序列长度，但仅针对注意力头的一个非重叠子集，使它们能够并行计算注意力。最后，第二个 all-to-all 通信收集各注意力头的结果，同时沿序列维度重新分区。

## 基准测试：C++ 上下文并行媒体生成

以下基准测试评估了面向 C++ 生产部署的媒体生成工作负载的多设备 TensorRT 推理。使用了两个代表性的生成式 AI 流水线：基于 NVIDIA Cosmos 3 的视频生成流水线和基于 FLUX.1 的图像生成流水线。

这些流水线首先在 PyTorch 中实现，然后通过 Torch-TensorRT 转换出框架，生成适合部署在 C++ 推理应用中的 NVIDIA TensorRT 引擎。这种工作流使开发人员能够保留 PyTorch 作为模型开发环境，同时在生产系统中部署优化的 TensorRT 引擎。

基准测试比较了不同上下文并行策略（AllGather KV、Ring Attention 和 Ulysses）的端到端延迟。所有结果均在单节点 8 GPU 上采集。

### NVIDIA Cosmos 3 视频生成

NVIDIA Cosmos 模型平台是一个世界基础模型平台，Cosmos3-Nano 模型能够基于多模态输入（包括文本、图像和视频）生成图像、视频、音频等格式。基于基准测试，当扩散模型具有极长上下文长度（数万输入 token 量级）时，Ulysses 是明显的胜者。

### FLUX.1 图像生成

Black Forest Labs 的 FLUX.1-dev 模型可以根据文本描述生成图像。基准测试使用提示词"a beautiful photograph of Mt. Fuji during cherry blossom"。基于基准测试，Ulysses 策略在图像生成中同样胜出，但值得注意的是 Ring Attention 在 4 GPU 上扩展也很好。

## TensorRT 多设备功能入门

TensorRT 支持多设备推理，使单一网络能够通过集成的分布式通信原语在多个 GPU 上执行。核心工作流与单设备 TensorRT 类似。区别在于网络现在可以包含分布式通信层。

本指南假设相同的网络部署在所有 GPU rank 上，但这不是严格的要求，理论上每个 rank 可以运行不同的模型。

TensorRT 仓库中提供了一个可运行示例。

### 使用入门步骤

1. **创建多设备推理网络**：通过网络级别的 `IDistCollectiveLayer` 实现跨 GPU 通信。可以直接使用 `INetworkDefinition::addDistCollective` 将集合操作添加到 TensorRT 网络中。

2. **构建引擎**：使用构建器配置序列化网络。

3. **创建执行上下文**：通过 `createInferRuntime` 创建运行时。

4. **绑定 IO 张量**：获取引擎的输入/输出张量名称，分配 GPU 内存，设置张量地址和形状。

5. **设置通信器并执行推理**：`context->setCommunicator(comm)` 然后 `context->enqueueV3(stream)`。注意：NCCL 通信器必须在使用它的执行上下文的生命周期内保持有效。

6. **启动推理**：使用 OpenMPI 在 8 GPU 上运行应用程序。每个 rank 选择其本地 CUDA 设备，初始化 NCCL，创建自己的 TensorRT 引擎和执行上下文，并附加 NCCL 通信器。
