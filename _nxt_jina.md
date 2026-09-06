Title: Next-Latent Prediction Transformers

URL Source: https://jaydenteoh.github.io/blog/2026/nextlat/

Published Time: 2026-05-25

Markdown Content:
[← back to all posts](https://jaydenteoh.github.io/blog)

## Next-Latent Prediction Transformers Learn Compact World Models

Jayden Teoh Manan Tomar Kwangjun Ahn Edward S. Hu Tim Pearce Pratyusha Sharma Akshay Krishnamurthy Riashat Islam Alex Lamb John Langford

Microsoft Research

Preprint, 2025

**TL;DR:**

We introduce **Next-Latent Prediction (NextLat)**, a simple auxiliary objective that augments next-token training with self-supervised predictions in the latent space. NextLat has three main benefits:

1.   **Representation Learning**: it encourages transformers to form compact belief states for reasoning and planning.
2.   **Better Data Efficiency**: predicting in latent space provides denser learning signal than predicting one-hot tokens.
3.   **Faster Inference**: it enables variable-length self-speculative decoding, allowing up to 3.3× faster inference.

![Image 1: Transformers are trained to predict the next token. What if transformers also learn to predict their own next hidden state?](https://jaydenteoh.github.io/blog/assets/2026-05-25-nextlat/nextlat_viz.gif)

Transformers are trained to predict the next token. What if transformers also learn to predict their own next hidden state?

On this page Contents:[Introduction](https://jaydenteoh.github.io/blog/2026/nextlat/#intro)[Method](https://jaydenteoh.github.io/blog/2026/nextlat/#method)[Motivation](https://jaydenteoh.github.io/blog/2026/nextlat/#motivation)[The Bitter Lesson](https://jaydenteoh.github.io/blog/2026/nextlat/#bitter-lesson)[Experiments](https://jaydenteoh.github.io/blog/2026/nextlat/#experiments)[Speculative Decoding](https://jaydenteoh.github.io/blog/2026/nextlat/#speculative-decoding)
## Introduction

In this blog, I question two dominant components of sequence modeling today:

1.   **The transformer architecture**
2.   **Next-token prediction**

I then show how Next-Latent Prediction (NextLat) can address issues with each of these components.

## Method

I'll describe our method in a high-level manner to set up the context for the subsequent sections. **NextLat** extends standard next-token training with a self-supervised auxiliary objective in the latent space. Specifically, we teach the transformer to encode tokens $X_{1 : t}$ into latent representations/hidden states $\mathbf{h}_{t}$ such that it can:

1.   predict the _next token_$X_{t + 1}$,
2.   predict _its own next hidden state_$\mathbf{h}_{t + 1}$ given the next token $X_{t + 1}$.

Our training objective combines standard next-token cross-entropy with a latent-prediction regression loss There are other components to the loss, but they are not immediately relevant — see the paper for the full objective.:

$$
\mathcal{L}_{\text{next}-\text{h}} = \parallel \left(\hat{\mathbf{h}}\right)_{t + 1} - s g \left[\right. \mathbf{h}_{t + 1} \left]\right. \parallel_{2}^{2}
$$

where $\left(\hat{\mathbf{h}}\right)_{t + 1}$ is the predicted next hidden state, and $s g$ is the stop-gradient operator.

Importantly, this objective retains the transformer's parallel training efficiency. At inference, the transformer decodes autoregressively as usual — there is no architectural change.

## Motivation

## the issue with transformers

Transformers replaced recurrence with a memory that grows with sequence length and self-attention that enables ad-hoc lookups over past tokens. Consequently, they lack an inherent incentive to compress history into compact latent summaries, and often learn solutions that generalize poorly[Anil et al. (2022)Exploring Length Generalization in Large Language Models NeurIPS 2022](https://arxiv.org/abs/2207.04901)[Dziri et al. (2023)Faith and Fate: Limits of Transformers on Compositionality NeurIPS 2023](https://openreview.net/forum?id=Fkckkr3ya8)[Liu et al. (2023)Transformers Learn Shortcuts to Automata ICLR 2023](https://openreview.net/forum?id=De4FYqjFueZ)[Wu et al. (2024)Reasoning or Reciting? Exploring the Capabilities and Limitations of Language Models Through Counterfactual Tasks NAACL 2024](https://aclanthology.org/2024.naacl-long.102/).

### > how does NextLat fix this?

NextLat forces each latent state to store all information about the history necessary to predict the next hidden state.

NextLat ensures existence of a mapping from current latent state to the next latent state to the next next latent state... and so on.

$$
\mathbf{h}_{t} & \rightarrow_{\text{decode}\textrm{ }\text{token}}^{p_{\theta}} X_{t + 1} \rightarrow_{\text{update}\textrm{ }\text{state}}^{p_{\psi}} \mathbf{h}_{t + 1} \rightarrow_{\text{decode}\textrm{ }\text{token}}^{p_{\theta}} X_{t + 2} \rightarrow_{\text{update}\textrm{ }\text{state}}^{p_{\psi}} \mathbf{h}_{t + 2} \textrm{ }\textrm{ } \hdots \textrm{ }\textrm{ } \overset{p_{\theta}}{\rightarrow} X_{T}
$$

For these maps to exist, and be learned, $\mathbf{h}_{t}$ must optimize toward a _belief state_—a compressed summary of the history necessary to predict the future.

Intuitively, this teaches the model to form a compact latent summary at every step. This prevents it from learning shortcut shortcuts that depend on lazy self-attention lookups over past tokens!

## the issue with next-token prediction

Firstly, next-token prediction _does not_ have an inherent incentive to learn belief states (see [Hu et al. (2025)The Belief State Transformer ICLR 2025](https://arxiv.org/abs/2410.23506)).

Secondly, next-token prediction is inherently _myopic_. It is biased towards learning short-term dependencies in the data. For example, on _Path-Star_[Bachmann et al. (2024)The Pitfalls of Next-Token Prediction ICML 2024](https://proceedings.mlr.press/v235/bachmann24a.html), a simple lookahead planning task, next-token predictors are unable to solve it .

### > how does NextLat fix this?

Compression and planning are two sides of the same coin. To compress history into compact belief states, NextLat must anticipate which information from the past will matter downstream. Therefore, NextLat teaches the model to capture long-term dependencies and perform lookahead planning.

Later in the "Experiments" section, we show that NextLat is the only method capable of solving Path-Star!

## connections to recurrent neural networks

Algorithmic reasoning requires capabilities most naturally understood through recurrent models of computation, like the Turing machine. However, recurrent neural networks (RNNs) are not parallelizable during training, which has led transformers to become the dominant architecture for sequence modeling.

### > NextLat introduces a recurrent inductive bias without recurrence

NextLat introduces a _recurrent inductive bias_ in transformers without the sequential training bottleneck. By teaching the model to compress history into belief state at every time step, NextLat effectively encourages the model to learn the underlying recurrent latent dynamics of the data, rather than exploit surface-level token patterns.

In fact, _NextLat can be viewed as a method for training RNNs without recurrence_ (see [Akarsh Kumar and Phillip Isola (2026)Pretraining Recurrent Networks without Recurrence arXiv 2026](https://arxiv.org/abs/2410.23506)). We demonstrate this interesting connection in the "Experiments" section, where NextLat solves state-tracking tasks that are inexpressible for transformers, but solvable by RNNs.

## What about "The Bitter Lesson"?

New methods of learning like NextLat can often repulse religious adherents to [The Bitter Lesson](http://www.incompleteideas.net/IncIdeas/BitterLesson.html). At first glance, adding yet another auxiliary objective to the well-established next-token prediction objective may seem like another attempt to inject human inductive bias, and another departure from the simple recipe of _"scale the model, scale the data, scale the compute"_.

![Image 2: Richard Sutton's yearly reminder on The Bitter Lesson.](https://jaydenteoh.github.io/blog/assets/2026-05-25-nextlat/bitter_lesson.png)

Richard Sutton's yearly reminder on The Bitter Lesson.

But NextLat is not in contention with The Bitter Lesson. In fact, I would argue that it is a direct application of the lesson from two viewpoints:

1.   **NextLat brings us closer toward _self-supervised learning_ rather than human supervised learning.**
2.   **NextLat improves _data efficiency_ by extracting more learning signal from each training sequence**

## 1. self-supervised learning

Self-supervised learning (SSL) is the ultimate realization of "The Bitter Lesson". Rather than relying on human-provided labels, SSL methods learn to generates its own learning signals from the structure of raw unlabeled inputs.

Next-token prediction is useful for bootstrapping the model with a core basis of human knowledge by leveraging the vast amount of human-written text on the internet. But then the model remains bounded by the way humans articulate and represent information. Human language and web text are riddled with useless syntax and inconsistencies. Here is an example:

Recipe says: add 2 tbsp sugar, stir unt ill dissolved, then put in the fridge for 30 mins lol

Human-written text tokenized by the GPT-2 tokenizer.

Next-token prediction has to work double time to model misspellings like "untill" (which gets tokenized differently from "until") and abbreviations like "tbsp". However, the underlying latent transition in semantics is clean: **mix ingredients → dissolve sugar → refrigerate**.

So the Bitter Lesson-pilled argument for NextLat is simple: if raw sequences contain more learnable structure than next-token prediction alone extracts, then NextLat helps direct more learning capacity towards the underlying latent transition (i.e., predicting in latent space), rather than focusing on superfluous syntax.

## 2. data efficiency and richer gradient signals

At the current rate, we will run out of web-text data for training models by 2028[Villalobos et al. (2024)Will we run out of data? Limits of LLM scaling based on human-generated data arXiv:2211.04325](https://arxiv.org/abs/2211.04325). There is a growing need for methods that can extract richer gradient signals from datasets, allowing efficient learning from less data.

Prior methods propose to extract richer gradient signals by predicting more tokens every step[Gloeckle et al. (2024)Better & faster large language models via multi-token prediction arXiv:2404.19737](https://arxiv.org/abs/2404.19737)[Ahn et al. (2025)Efficient joint prediction of multiple future tokens arXiv:2503.21801](https://arxiv.org/abs/2503.21801)[Hu et al. (2025)The belief state transformer ICLR 2025](https://arxiv.org/abs/2410.23506)[Shao et al. (2025)Beyond Next Token Prediction: Patch-Level Training for Large Language Models ICLR 2025](https://openreview.net/forum?id=dDpB23VbVa). However, these methods predict in token space, so the learning signal is sparse and only tied to the next one-hot token, or multiple tokens. In contrast, NextLat predicts in the latent space. This difference sets apart the richness of the learning signal it provides.

Firstly, NextLat is trained to predict the next hidden state $\mathbf{h}_{t + 1}$, which itself parameterizes the _entire distribution_ over the next-next token $X_{t + 2}$. This shifts supervision from individual token targets to distribution-level alignment. Secondly, $\mathbf{h}_{t + 1}$ is also trained to predict the next-next hidden state $\mathbf{h}_{t + 2}$. This recursive latent dynamics, where every latent is predictive of the next, means that

$\mathbf{h}_{t}$ predicts $\mathbf{h}_{t + 1}$ which predicts $\mathbf{h}_{t + 2}$ which predicts $\mathbf{h}_{t + 3}$ which predicts...

Therefore, $\mathbf{h}_{t + 1}$ encodes information about $\mathbf{h}_{t + 2}$, $\mathbf{h}_{t + 3}$, $\mathbf{h}_{t + 4}$, $\ldots$

Predicting $\mathbf{h}_{t + 1}$ therefore provides learning signal about the future, not just the immediate next token.

As a result, next-latent supervision not only provides learning signals that are dense in the vocabulary distribution, but also provides information about all future tokens.

## Experiments

We show that NextLat improves over next-token prediction, multi-token prediction, and other token-prediction baselines across benchmarks in world modeling, reasoning, planning, and language modeling.

![Image 3: World modeling](https://jaydenteoh.github.io/blog/assets/2026-05-25-nextlat/manhattan_population_webby.gif)

We train the models on Manhattan taxi ride sequences. NextLat learns a world model that is not only more compact, but also more consistent with the real world!

## Variable-length self-speculative decoding

Once the model has learned to predict its own next latent state, we get a free inference-time bonus: the lightweight latent dynamics model (i.e., the next-latent prediction head) can be _recursively_ rolled out to predict future tokens entirely in latent space, without invoking the main transformer. This enables _variable-length self-speculative decoding_.

![Image 4: Self-speculative decoding with NextLat enables longer drafts and faster inference.](https://jaydenteoh.github.io/blog/assets/2026-05-25-nextlat/spec_decoding_cover.png)

Self-speculative decoding with NextLat enables longer drafts and faster inference.

In our experiments, NextLat trained with only next-latent prediction ($d = 1$) can still draft long token sequences up to 10 tokens long, achieving up to **3.3× faster inference** on language modeling benchmarks.

![Image 5: NextLat enables variable-length self-speculative decoding.](https://jaydenteoh.github.io/blog/assets/2026-05-25-nextlat/combined_spec_decoding.gif)

NextLat enables variable-length self-speculative decoding.

Multi-token prediction (MTP) has become the standard for open-source language model pretraining[Liu et al. (2024)Deepseek-v3 technical report arXiv:2412.19437](https://arxiv.org/abs/2412.19437)[Qwen Team (2025)Qwen3-Next: Towards Ultimate Training & Inference Efficiency Qwen Blog](https://qwen.ai/blog?id=4074cca80393150c248e508aa62983f9cb7d27cd)[NVIDIA (2025)NVIDIA Nemotron 3: Efficient and Open Intelligence White Paper](https://arxiv.org/abs/2512.20856)[Xiaomi MiMo Core Team et al. (2026)MiMo-V2-Flash Technical Report arXiv:2601.02780](https://arxiv.org/abs/2601.02780)[Google (2026)Accelerating Gemma 4: faster inference with multi-token prediction drafters Google Blog](https://blog.google/innovation-and-ai/technology/developers-tools/multi-token-prediction-gemma-4/). However, MTP is typically limited to the fixed speculative horizon it was trained on. Unlike MTP, NextLat allows for longer flexible-length drafts. This means that NextLat can achieve much faster inference than MTP!

## Conclusion

NextLat is a simple modification to the training objective, but it has surprisingly far-reaching benefits for representation learning, data efficiency, and inference speed. We hope that our work will inspire future pretraining research.

## BibTeX

If you find this work useful, please cite:

```
@misc{teoh2026nextlatentpredictiontransformerslearn,
title    = {Next-Latent Prediction Transformers Learn Compact World Models},
author   = {Jayden Teoh and Manan Tomar and Kwangjun Ahn and Edward S. Hu and
            Tim Pearce and Pratyusha Sharma and Akshay Krishnamurthy and
            Riashat Islam and Alex Lamb and John Langford},
year     = {2026},
eprint   = {2511.05963},
archivePrefix = {arXiv},
primaryClass  = {cs.LG},
url      = {https://arxiv.org/abs/2511.05963},
}
```
