# Dockerless: Environment-Free Program Verifier for Coding Agents

## 摘要

Program verifiers play a central role in training coding agents, including selecting trajectories for supervised fine-tuning (SFT) and providing rewards for reinforcement learning (RL). Standard execution-based verification requires running unit tests inside per-repository environments such as Docker images, incurring substantial environment setup costs. We propose Dockerless, an environment-free agentic patch verifier that evaluates generated code patches without executing them. Rather than simply matching candidate patches to references, Dockerless judges patch correctness using evidence gathered through agentic repository exploration. On a verifier evaluation benchmark, Dockerless outperforms the strongest open-source verifier by 14.3 AUC points. Using Dockerless as both the SFT trajectory filter and the RL reward enables a fully environment-free post-training pipeline. The resulting model reaches 62.0%, 50.0%, and 35.2% resolve rate on SWE-bench Verified, Multilingual, and Pro, respectively. It surpasses the Qwen3.5-9B baseline by 2.4, 8.7, and 2.9 points, matching environment-based post-training.

## 1 引言

Program verifiers play a critical role in training automated coding agents. Whether curating high-quality trajectories for SFT or providing rewards for RL, verifiers determine whether the agent rollouts successfully resolve issues. Currently, the gold standard for this correctness feedback relies on executing test cases inside isolated, per-repository environments.

However, execution-based verification imposes substantial engineering overhead. Setting up these environments requires building custom Docker images, resolving per-repository dependencies, identifying relevant tests, and writing test-execution scripts and result parsers. Even advanced automated pipelines still succeed on only a limited share of candidate repositories. More fundamentally, many real-world repositories, especially private, enterprise, or legacy codebases, lack reproducible environments or comprehensive test suites altogether, making execution-based verification unreliable or infeasible.

To reduce setup costs, recent work executes agent rollouts from a single shared base image rather than per-repository Docker containers. Yet, the verifier remains a critical bottleneck. Existing environment-free verifiers score patches using only surface-level information, without ever inspecting the repository. Such shallow approaches are insufficient for complex SWE tasks, where determining functional equivalence requires deep repository context.

To close this gap, we propose Dockerless, an environment-free agentic verifier that actively explores the repository to judge patch correctness. Rather than blindly matching textual diffs, Dockerless grounds its verification in the actual codebase. Given an issue description, a reference patch, and a candidate patch, Dockerless first derives several verification questions from the issue and the reference patch. It then dispatches dedicated sub-agents to gather repository evidence for each question. Finally, it aggregates the collected evidence into a correctness score indicating whether the candidate patch correctly resolves the issue.

We train Dockerless via rejection sampling on 3.7K issues from SWE-Gym and Multi-SWE-RL, retaining only question-answer-judge trajectories whose final verdict matches the ground-truth test outcome.

Ultimately, Dockerless unlocks a fully environment-free post-training pipeline: rollout collection, SFT data filtering, and RL reward computation can all run on a minimal base image with zero per-repository setup. As a standalone verifier, Dockerless outperforms the strongest open-source baseline by 14.3 AUC points on a verifier evaluation benchmark. For SFT, training on the top 25% of trajectories filtered by Dockerless (4K out of 16K) surpasses training on the full environment-free pool by 1.8, 6.4, and 3.4 points on SWE-bench Verified, Multilingual, and Pro, respectively. For RL, using Dockerless as an environment-free reward outperforms RL with the DeepSWE Verifier by 1.4, 2.7, and 1.1 points on the same three benchmarks. End-to-end, our fully environment-free post-training pipeline produces a model that reaches 62.0%, 50.0%, and 35.2% resolve rate, improving over the Qwen3.5-9B baseline by 2.4, 8.7, and 2.9 points. By matching the performance of standard environment-based post-training, Dockerless establishes environment-free post-training as a scalable and viable path for the vast long tail of real-world repositories.

Contributions:
- Dockerless, an environment-free agentic verifier that scores patches by actively exploring the repository with parallel sub-agents
- By providing reliable correctness feedback, Dockerless enables a fully environment-free post-training pipeline for SFT trajectory filtering and RL rewards
- Empirically, Dockerless outperforms the strongest open-source verifier by 14.3 AUC points, while the resulting fully environment-free post-training pipeline achieves performance comparable to standard environment-based post-training

## 2 方法论

### 2.1 问题设定

Given an issue x and a candidate patch y, a verifier assigns a correctness score r(x,y) ∈ [0,1] indicating whether y resolves x.

In standard SWE post-training (environment-based setting), candidate patches are verified by executing held-out tests inside a repository-specific environment (E_x). E_x consists of a Docker image with pinned dependencies, a curated unit-test suite, and a working test runner. This produces a binary correctness signal. However, building these environments is prohibitively expensive, and many real-world codebases lack reproducible environments or usable test suites.

To make post-training scalable, we consider the environment-free (env-free) setting in which agents run in a single minimal base image without repository-specific dependencies, test runners, or access to E_x. This setting is already practical on the agent side: frontier models under the OpenHands scaffold retain much of their performance after removing the per-repository environment, with resolve-rate drops of 3.0–13.9 points. Thus, env-free rollouts can be collected at scale; the remaining bottleneck is verification. Our goal is to train an environment-free verifier r_φ(x,y) that can replace r_env for both SFT trajectory filtering and RL reward computation.

### 2.2 Dockerless 架构

The verifier operates in two stages. First, given an issue x and a reference patch y_ref, the model proposes a small set of verification questions {Q_1, ..., Q_K}. These questions ask, for example, where in the repository the fix should take effect, what the patched code is supposed to do, what tests or assertions would confirm correctness, and whether other parts of the repository could break. Answering these questions grounds the verifier's eventual judgment in repository exploration rather than in surface-level comparison between the candidate and the reference patch. For each question, a sub-agent then explores the repository through read-only shell tools (e.g., find, grep, rg) and returns a short evidence-backed answer A_k. The K sub-agents run in parallel for efficiency.

After all sub-agents return their answers, Dockerless aggregates the collected evidence to judge whether the candidate patch y resolves the issue x. Given (x, y_ref, y, {(Q_k, A_k)}), the verdict model outputs a binary token in {0,1}, where 1 denotes a correct patch. At inference time, we convert the logits of the two verdict tokens into a continuous score via softmax.

### 2.3 Dockerless 训练

We train the verifier r_φ via rejection sampling on execution-labeled candidate patches. Each example is a tuple (x, y_ref, y, r*), where r* ∈ {0,1} is the ground-truth verdict obtained by running the held-out unit tests on the candidate patch.

To construct training trajectories τ for the question-answer-judge, an agent powered with a teacher model explores the repository until making a judgment verdict r̂ ∈ {0,1} for each example. We then reject-sample these trajectories, keeping only those whose r̂ matches the execution label r*. The retained examples form D_rej. This keeps the training signal consistent end-to-end, and the verifier learns how to reason step-by-step and conclude the final verdict rather than from lucky matches. We additionally cap the negative-to-positive sample ratio at ρ to mitigate class imbalance.

The verifier is then trained with the standard next-token cross-entropy over the full output sequence. A single backbone is shared across question generation, sub-agent exploration, and the final judging stage, jointly trained under the same loss.

### 2.4 无环境 Post-Training

Environment-free RFT. Rejection-sampling fine-tuning (RFT) curates SFT data by keeping only the high-quality rollouts whose final patches pass per-repository unit tests. We instead start from an agent, collect a large pool of rollouts in a minimal Linux image without instantiating per-repository environments, and use Dockerless as the rejection signal. We score each rollout's final patch with Dockerless and form D_RFT by keeping the top-K rollouts globally ranked by r_φ. We then fine-tune the model on D_RFT with the standard SFT objective, yielding the SFT model.

Environment-free RL. We further use Dockerless as the reward model for RL on top of the SFT model. During RL, rollouts are collected in the same minimal Linux image used for env-free RFT. For each rollout on issue x, let y_i denote its final patch. We score y_i with Dockerless and use r_φ(x, y_i) as the reward. We then optimize the model with GRPO. For each group of G rollouts on issue x, we form group-normalized advantages and use them in the standard GRPO objective. To improve reward stability, we compute each reward by averaging M independent Dockerless evaluations of the same final patch.

## 3 实验设置

Benchmarks. For agent resolve rate, we evaluate on SWE-bench Verified, SWE-bench Multilingual, and SWE-bench Pro. For evaluating the verifier itself, we construct a balanced trajectory-level verifier evaluation benchmark of 776 samples (500 from SWE-bench Verified and 276 from Multi-SWE-bench Flash).

Evaluation protocol. We use OpenHands as the default agent scaffold with a maximum of 150 turns. For env-based evaluation, the agent runs inside the original per-repository Docker image. For env-free evaluation, the agent runs in a minimal Ubuntu 22.04 LTS image with only the repository checkout at the base commit. The main paper reports env-based evaluation; env-free numbers are deferred to Appendix B. We report resolve rate for issue resolution and AUC for verifier evaluation.

Baselines. For agent performance, we compare against SWE-Gym-7B, SWE-Dev-7B, SWE-Lego-8B, and the base model Qwen3.5-9B. For verifier evaluation, we compare Dockerless against four frontier LLMs used zero-shot as judges (DeepSeek-V3.2, Kimi-K2.5, GLM-5, GPT-5.4) and four trained verifiers: SWE-Gym Verifier, R2E-Gym Verifier, OpenHands Critic, and DeepSWE Verifier.

Implementation details. We use Qwen3.5-9B as the backbone for both Dockerless and the downstream post-training. Dockerless is trained on rejection-sampled trajectories from 3.7K execution-labeled issues, and uses K=2-4 verification questions. For downstream post-training, we use SWE-Rebench-v2.

## 4 结果

### 4.1 主要结果

Fully environment-free post-training reaches strongest open-source performance. Starting from Qwen3.5-9B, our fully environment-free post-training pipeline produces Dockerless-RL-9B, which reaches 62.0, 50.0, and 35.2 resolve rate on SWE-bench Verified, Multilingual, and Pro, respectively. This improves over the base model by +2.4, +8.7, and +2.9 points and over SWE-Lego-8B by +20.8, +31.0, and +19.1 points.

Env-free SFT matches env-based SFT. Dockerless-SFT-9B achieves comparable performance to the env-based baseline (60.6 vs 60.0 on Verified, 47.7 vs 48.3 on Multilingual, and 35.3 vs 33.9 on Pro).

Env-free RL approaches env-based RL. Dockerless-RL-9B achieves performance close to Test-Execution RL (62.0 vs 62.4 on Verified, 50.0 vs 51.3 on Multilingual, and 35.2 vs 35.7 on Pro), while outperforming DeepSWE-Verifier RL by +1.4, +2.7, and +1.1 points.

### 4.2 验证器评估

Dockerless reaches 81.0 AUC on SWE-bench Verified and 72.1 AUC on Multi-SWE-bench Flash, outperforming every baseline in both splits. Compared with the strongest trained open-source verifier (DeepSWE Verifier), Dockerless improves AUC by 14.3 points on Verified and 9.2 points on Multi-SWE-bench Flash; compared with the strongest frontier LLM judge (GLM-5), it improves by 5.1 and 8.2 points.

### 4.3 SFT 数据筛选器效果

Dockerless achieves effective trajectory filtering. Training on all env-free trajectories (All 16K) does not improve over the base model. Dockerless 4K substantially outperforms Random 4K on all three benchmarks (60.6 vs 58.2 on Verified, 47.7 vs 44.3 on Multilingual, and 35.3 vs 32.0 on Pro). Env-free RFT matches env-based trajectory collection: Dockerless 4K matches Env-based 4K across the three benchmarks.

### 4.4 验证问题数量的影响

Dockerless performance improves as K increases from 0 to 4, rising from 78.3 AUC to 81.0 AUC at K=4. Beyond four questions, performance fluctuates rather than improving monotonically (79.6 at K=6, 80.3 at K=8). We therefore let Dockerless generate 2-4 verification questions at inference time.

### 4.5 延迟分析

Agent rollouts dominate the wall-clock cost, taking 2308s on average, whereas reward evaluation adds only 41-180s. Although Dockerless requires more reward-evaluation time than the other verifier rewards, it still accounts for only 7.2% of the total per-rollout time. The end-to-end latency distribution shows the same pattern.

### 4.6 案例研究

A representative case on a matplotlib offsetText color issue: the candidate patch passes execution (r_env=1.0) but rewrites the fix as an inline conditional rather than the helper-variable refactor. Text similarity returns 0.468, DeepSWE Verifier assigns 0.035, but Dockerless scores the patch 0.996, in agreement with the execution result. The case illustrates how Q&A evidence can support a correct judgment even when the candidate patch differs substantially from the reference patch in surface form.

## 5 相关工作

### 5.1 软件工程 Agent

LLMs have evolved from generating simple code snippets to real-world software engineering tasks. SWE agents are typically post-trained with a two-stage SFT-then-RL recipe. A complementary line builds env-free rollout pipelines that share a single base image, but they still constrain the agent during rollout. Dockerless instead lets the agent issue any shell command in a minimal Linux image and receive real tool feedback, replacing both the RFT-stage filter and the RL reward source with a single env-free agentic verifier.

### 5.2 SWE Agent 验证器

Previous work trains LM verifiers that score a patch from a fixed prompt, ranging from execution-trained classifiers to rubric-supervised or RL-distilled variants. None of these call tools or inspect the repository at scoring time. Dockerless instead places the agent at SWE patch outcome scoring itself, actively exploring the repository through real tool calls before issuing a verdict.

## 6 结论

We propose Dockerless, an agentic verifier that scores patches by actively exploring the repository, requiring no per-repository environment. We show that Dockerless can serve as both the trajectory filter for SFT and the reward signal for RL, yielding a fully environment-free post-training pipeline for coding agents. Dockerless outperforms prior open-source verifiers, and the resulting model matches the performance of its environment-based counterpart while requiring zero per-repository setup. We believe that agentic, evidence-grounded verification provides a new perspective on reward modeling for code, and opens a scalable path toward post-training on the long tail of real-world repositories without reproducible execution environments.
