4-bit floating point encodes each value in just sixteen levels. Until recently usable only for storage; with NVIDIA's NVFP4 format and Blackwell hardware, now supports full lifecycle of large models. The core difficulty: four bits afford only fifteen distinct magnitudes. NVFP4 addresses this with fine-grained, two-level scaling. NVFP4 gives Blackwell Tensor Cores a practical 4-bit path.

E2M1 has 1 sign, 2 exponent, 1 mantissa: 15 values {0, ±0.5, ±1, ±1.5, ±2, ±3, ±4, ±6}. A 4-bit code picks which mark; scale decides where the ruler is placed. MXFP4 gives every 32 values its own power-of-two scale (E8M0 exponent). The catch: power-of-two dial is coarse. NVFP4 achieves ~88% lower quantization error than MXFP4.

NVFP4 uses two-level scaling: element-level (4-bit E2M1), block-level (FP8 E4M3 scale per 16 values), per-tensor (FP32 scale). Total cost ~4.5 bits/value vs MXFP4's ~4.25.

LLMs: Up to 4× throughput ceiling over BF16. ~1.9× faster pretraining than FP8 (Llama-3.1 405B), up to ~3× peak inference throughput. DeepSeek-R1 PTQ to NVFP4: within ~1% of FP8 (MMLU-Pro 85→84, GPQA 81→80). MXFP4 needed 36% more tokens. Ships in TensorRT-LLM and TensorRT Model Optimizer. Used in DeepSeek-V4 (1.6T MoE) and OpenAI GPT-OSS (120B on single 80GB GPU).

Video generation (LongLive-2.0): 5B model, 45.7 FPS at 720p. Training: 2.1× faster than BF16. DMD in 4-bit drops memory from 70.5GB to 49.0GB per GPU. Inference: W4A4 +NVFP4 KV cache drops memory from 36.4GB to 19.4GB, throughput 24.8→32.0 FPS.

KV Cache: NVFP4 cuts footprint ~50% versus FP8, <1% accuracy loss. Hardware: dequantizes along native FP4→FP8 datapath, overhead <2%.

Attention: FlashAttention-2 (FP16), FA3 (FP8 on Hopper), SageAttention (INT8), SageAttention2 (INT4), SageAttention3 (NVFP4 on Blackwell). Challenge: softmax map P in [0,1] wastes 4-bit range. Solution: stretch each row by per-token FP32 factor. Result: 1038 TOPS, ~5× FA2, 2.4–3× end-to-end video diffusion. Cosine similarity 93.3%→99.5%.

Key lesson: FP4 works only when format, kernels, cache, and attention are co-designed. Open problems: better scales, KV-cache dequant efficiency, FP4 attention quality, QAT vs PTQ gap.
