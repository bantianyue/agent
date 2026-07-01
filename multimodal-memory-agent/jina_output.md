Title: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions

URL Source: https://arxiv.org/html/2602.07624v1

Published Time: Tue, 10 Feb 2026 01:42:27 GMT

Markdown Content:
Binxiao Xu Jiayi Chen Mengyu Dai Cenyang Wu Haodong Li Bohan Zeng Yunliu Xie Hao Liang Ming Lu Wentao Zhang

###### Abstract

This work addresses the challenge of personalized question answering in long-term human-machine interactions: when conversational history spans weeks or months and exceeds the context window, existing personalization mechanisms struggle to continuously absorb and leverage users’ incremental concepts, aliases, and preferences. Current personalized multimodal models are predominantly static—concepts are fixed at initialization and cannot evolve during interactions. We propose M 2 A, an agentic dual-layer hybrid memory system that maintains personalized multimodal information through online updates. The system employs two collaborative agents: ChatAgent manages user interactions and autonomously decides when to query or update memory, while MemoryManager breaks down memory requests from ChatAgent into detailed operations on the dual-layer memory bank, which couples a RawMessageStore (immutable conversation log) with a SemanticMemoryStore (high-level observations), providing memories at different granularities. In addition, we develop a reusable data synthesis pipeline that injects concept-grounded sessions from Yo’LLaVA and MC-LLaVA into LoCoMo long conversations while preserving temporal coherence. Experiments show that M 2 A significantly outperforms baselines, demonstrating that transforming personalization from one-shot configuration to a co-evolving memory mechanism provides a viable path for high-quality individualized responses in long-term multimodal interactions. The code is available at [https://github.com/Little-Fridge/M2A](https://github.com/Little-Fridge/M2A).

Machine Learning, ICML

## 1 Introduction

Large vision-language models (VLMs) have achieved strong performance on multimodal instruction following, visual question answering, and open-ended dialogue(Li et al., [2024a](https://arxiv.org/html/2602.07624v1#bib.bib1 "Llava-onevision: easy visual task transfer"); Chen et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib7 "Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling"); Wang et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib3 "Qwen2-vl: enhancing vision-language model’s perception of the world at any resolution"); Li et al., [2024b](https://arxiv.org/html/2602.07624v1#bib.bib2 "Llava-next-interleave: tackling multi-image, video, and 3d in large multimodal models")). However, these models are primarily trained for generic, “anonymous” users and lack mechanisms to explicitly capture individual concepts, naming conventions, or stylistic preferences. Consequently, their responses are often broadly acceptable but insufficiently personalized(Hao et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib9 "RAP: retrieval-augmented personalization for multimodal large language models")).

Existing personalization methods fall into two categories. The first internalizes user-provided concept images into model representations, enabling recognition of personalized visual entities within LLaVA-like architectures (e.g., Yo’LLaVA, MC-LLaVA)(Nguyen et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib22 "Yo’llava: your personalized language and vision assistant"); An et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib10 "Mc-llava: multi-concept personalized vision-language model")). The second adopts retrieval-augmented paradigms (e.g., RAP), storing user-related information externally and dynamically retrieving it at inference time for better scalability(Hao et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib9 "RAP: retrieval-augmented personalization for multimodal large language models")). Despite their differences, most approaches assume personalization is static. In practice, personalization is incremental: users continually refine concepts with new attributes, aliases, and preferences, which static systems cannot effectively absorb.

Meanwhile, long-term conversations quickly exceed context windows, requiring external memory and selective retrieval(Maharana et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib13 "Evaluating very long-term conversational memory of llm agents"); Packer et al., [2023](https://arxiv.org/html/2602.07624v1#bib.bib14 "MemGPT: towards llms as operating systems."); Zhong et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib19 "Memorybank: enhancing large language models with long-term memory"); Luo et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib4 "Llm as dataset analyst: subpopulation structure discovery with large language model")). However, existing memory systems largely focus on text, offering limited support for multimodal concepts, fine-grained updates, or editable memory structures specifically designed for human-machine interactions. Addressing these limitations requires a unified framework for editable multimodal personalization.

![Image 1: Refer to caption](https://arxiv.org/html/2602.07624v1/x1.png)

Figure 1: M 2 A enables incremental personalization with an editable multimodal memory. Unlike Yo’LLaVA and RAP-LLaVA, which keep initial concept tokens or text only profiles without write-back, M 2 A updates a unified memory bank during interaction and queries it at generation time, yielding recommendations aligned with evolving preferences across long, multi session dialogs.

We formalize long-term personalized interaction as a Partially Observable Markov Decision Process (POMDP)(Kaelbling et al., [1998](https://arxiv.org/html/2602.07624v1#bib.bib42 "Planning and acting in partially observable stochastic domains")), where the user’s latent state u evolves over time and is approximated by an explicit belief state M_{t}. Based on this formulation, we propose M 2 A, an agentic framework with dual-layer hybrid memory. The system comprises two cooperating agents: (i) ChatAgent, which manages dialogue through a ReAct-style workflow (Query → Generate → Update) and decides when to access or modify memory; and (ii) MemoryManager, which holds exclusive read-write access and performs iterative, reasoning-driven retrieval and updates. Memory is organized into a lower _Raw Message Store_ that preserves complete conversational logs and an upper _Semantic Memory Store_ that maintains high-level semantic observations. Each semantic entry links to raw-message evidence via evidence_ids, enabling evidence-linked progressive narrowing from coarse semantic retrieval to fine-grained context. A tri-path retrieval strategy combining dense text vectors, BM25(Robertson and Zaragoza, [2009](https://arxiv.org/html/2602.07624v1#bib.bib41 "The probabilistic relevance framework: bm25 and beyond")) sparse retrieval, and cross-modal image embeddings with Reciprocal Rank Fusion(Cormack et al., [2009](https://arxiv.org/html/2602.07624v1#bib.bib38 "Reciprocal rank fusion outperforms condorcet and individual rank learning methods")) further improves robustness.

Our contributions are summarized as follows:

1.   1.Agentic online personalized memory. We introduce M 2 A, an agentic multimodal memory framework that supports incremental concept updates during interaction. 
2.   2.Dual-layer hybrid memory with evidence linking. We propose a two-tier memory architecture with progressive narrowing for efficient and precise retrieval. 
3.   3.Scalable multimodal data synthesis. We design a pipeline that injects multimodal sub-sessions into long conversations for training and evaluation. 

![Image 2: Refer to caption](https://arxiv.org/html/2602.07624v1/x2.png)

Figure 2: Overview of the M^{2}A framework. M^{2}A employs a multi-agent architecture consisting of a ChatAgent for user interaction and a MemoryManager for autonomous memory operations. The system leverages a Dual-Layer Hybrid Memory bank, linking high-level semantic observations in the Semantic Store to immutable conversational logs in the Raw Message Store via evidence IDs. 

## 2 Related Work

#### Personalized multimodal models.

Recent vision-language models combine strong visual encoders with large language backbones(Li et al., [2024a](https://arxiv.org/html/2602.07624v1#bib.bib1 "Llava-onevision: easy visual task transfer"); Chen et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib7 "Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling"); Wang et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib3 "Qwen2-vl: enhancing vision-language model’s perception of the world at any resolution"); Li et al., [2024b](https://arxiv.org/html/2602.07624v1#bib.bib2 "Llava-next-interleave: tackling multi-image, video, and 3d in large multimodal models")), but largely overlook user-specific concepts. Existing personalization methods follow two paradigms.

Concept internalization compresses user-provided concept images into embeddings injected into LLaVA-style models, enabling recognition of personalized visual entities at inference. Yo’LLaVA(Nguyen et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib22 "Yo’llava: your personalized language and vision assistant")) targets single concepts, while MC-LLaVA(An et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib10 "Mc-llava: multi-concept personalized vision-language model")) and MyVLM(Alaluf et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib12 "Myvlm: personalizing vlms for user-specific queries")) extend to multi-concept or few-shot settings. Yo’Chameleon(Nguyen et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib6 "Yo’chameleon: personalized vision and language generation")) and UniCTokens(An et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib5 "UniCTokens: boosting personalized understanding and generation via unified concept tokens")) utilize this paradigm in the area of both personalized understanding and generation. Online-PVLM(Bai et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib47 "Online-pvlm: advancing personalized vlms with online concept learning")) introduces hyperbolic representations to enable online concept learning at test time without training, allowing incremental addition of new concepts during interaction. However, these approaches cannot flexibly update or refine existing concepts based on conversational feedback—once a concept is initialized (either through training or test-time encoding), its representation remains fixed. This limits their ability of online adaptation, refinement, or evolution of user’s personalized knowledge.

Retrieval-augmented personalization instead stores user profiles, aliases, and concept descriptions externally and retrieves them during inference. RAP(Hao et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib9 "RAP: retrieval-augmented personalization for multimodal large language models")) exemplifies this paradigm for multimodal language models, while Personalization Toolkit(Seifi et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib48 "Personalization toolkit: training free personalization of large vision language models")) leverages pre-trained vision foundation models with visual prompting and retrieval to achieve training-free personalization. Such methods scale better by keeping the base model fixed, but typically assume a static concept set and lack mechanisms for online refinement of existing knowledge.

Our work builds on the retrieval-augmented paradigm while introducing agentic memory updates, allowing the system to autonomously decide when and how to modify personalized knowledge during interaction. Unlike concept internalization methods (including online learning variants) that encode concepts into fixed representations, or passive retrieval systems that merely store and retrieve static information, M2A maintains editable, persistent memory that accumulates, refines, and even corrects user-specific knowledge across multi-session conversations through explicit update operations.

#### Long-context memory and agentic memory management.

As conversations exceed context windows, external memory becomes essential. LoCoMo shows that long dialogues require selectively reintroducing early utterances to maintain temporal consistency(Maharana et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib13 "Evaluating very long-term conversational memory of llm agents")). Early systems adopt passive retrieval, storing conversation history externally and retrieving relevant segments at inference time (e.g., LongMem, MemLong, UniMem, HMT)(Wang et al., [2023](https://arxiv.org/html/2602.07624v1#bib.bib15 "Augmenting language models with long-term memory"); Liu et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib16 "Memlong: memory-augmented retrieval for long text modeling")). While effective, these methods rely on fixed retrieval strategies.

Agentic memory introduces dynamic control over memory operations. MemGPT frames memory access as agent actions(Packer et al., [2023](https://arxiv.org/html/2602.07624v1#bib.bib14 "MemGPT: towards llms as operating systems.")), while MemoryBank, Mem0, and A-MEM extend this idea with long-term persistence and editable memories(Zhong et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib19 "Memorybank: enhancing large language models with long-term memory"); Xu et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib30 "A-mem: agentic memory for llm agents")). Despite their flexibility, existing systems are mostly text-based, rely on single-pass retrieval, and operate at a single memory granularity. We address these limitations with a dual-layer hybrid memory that supports multimodal concepts and iterative reasoning-driven retrieval from semantic summaries to raw conversational evidence.

Additional related work on multimodal generation and editing is discussed in Appendix[A](https://arxiv.org/html/2602.07624v1#A1 "Appendix A Additional Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions").

## 3 Problem Formulation

We formalize long-term personalized interaction as a Partially Observable Markov Decision Process (POMDP), defined as the tuple (\mathcal{U},\mathcal{A},\mathcal{T},\Omega,\mathcal{O}).

#### Latent user state.

Let \mathcal{U} denote the latent state space of user profiles. At each interaction round t, the user is in a hidden state u_{t}\in\mathcal{U} that contains their private concepts (e.g., specific pet name “Bobo”), visual preferences (e.g., “likes blue toys”), and interaction styles evolving over time. The system cannot directly observe u_{t} and can only infer it through user queries and feedback.

#### Transitions and observations.

*   •State transition\mathcal{T}: As the dialogue progresses, the user’s latent state evolves according to transition probability P(u_{t+1}|u_{t},a_{t}). For example, when a user introduces new conceptual entities (“my dog is named Bobo”) or corrects previous preferences (“she actually prefers quiet toys”) during interaction, the latent state u_{t} undergoes incremental updates. 
*   •Observation\Omega: At round t, the system receives a multimodal observation x_{t}\in\Omega (the user’s input query, potentially containing text and images). This observation is an instantiation of intent conditioned on the current latent state, following probability distribution x_{t}\sim\mathcal{O}(x|u_{t}). 

#### Belief state as memory bank.

Due to the unobservability of u_{t}, the agent must maintain a belief state M_{t} based on the historical observation sequence H_{t}=\{x_{1},a_{1},\dots,x_{t},a_{t}\}. In our framework, M_{t} is instantiated as a multimodal memory bank, whose goal is to approximate the posterior distribution of latent state u_{t}:

M_{t}\approx P(u_{t}|H_{t})(1)

At each interaction round, the evolution mechanism of the memory bank is:

1.   1.Action execution: The system takes action a_{t}\in\mathcal{A} (generates response) based on current observation x_{t} and belief state M_{t-1}: a_{t}\sim\pi(a|x_{t},M_{t-1}). 
2.   2.Belief update: The system updates memory through MemoryManager based on new observation x_{t}, system action a_{t}, and historical memory M_{t-1}: M_{t}=f_{update}(M_{t-1},x_{t},a_{t}). 

In M 2 A, the belief state M_{t} is instantiated through dual-layer hybrid memory: the lower RawMessageStore saves complete observation history \{x_{1},\dots,x_{t}\}, while the upper SemanticAssociationStore stores high-level inferences about latent state u_{t} (semantic observations). The collaboration mechanism between ChatAgent and MemoryManager implements the f_{update} function: ChatAgent decides when to trigger updates, MemoryManager decides how to update (which memories to add, delete, or modify). The retrieval process corresponds to extracting information most relevant to the current query x_{t} from M_{t-1} to support action generation a_{t} in a timely manner.

![Image 3: Refer to caption](https://arxiv.org/html/2602.07624v1/x3.png)

Figure 3: Overview of the proposed dataset construction pipeline. We first organize source images into semantic Concept Groups. Then, a unified One-Call Generation strategy produces concept-grounded dialogues and QA pairs. Finally, these generated sub-narratives are seamlessly interpolated into the original LoCoMo sessions to create the final hybrid dialog.

## 4 M 2 A: Multimodal Memory Agent

### 4.1 Framework Overview

Figure[2](https://arxiv.org/html/2602.07624v1#S1.F2 "Figure 2 ‣ 1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions") illustrates M 2 A’s overall architecture. M 2 A adopts a distributed collaboration architecture centered on MemoryManager, decoupling user interaction from memory management. The system consists of three main components:

1.   1.ChatAgent (User Interaction Agent). Serving as the system’s front-end interface, ChatAgent conducts natural language conversations with users. The key feature is autonomous decision-making capability: in each conversational turn, ChatAgent autonomously determines whether to query or update long-term memory through a three-stage ReAct(Yao et al., [2023](https://arxiv.org/html/2602.07624v1#bib.bib37 "ReAct: synergizing reasoning and acting in language models")) workflow, rather than passively executing fixed procedures. 
2.   2.MemoryManager (Memory Management Agent). As the system’s back-end core, MemoryManager is the only entity with read-write access to the memory bank. It executes iterative reasoning-driven retrieval and update operations: after receiving instructions from ChatAgent, it progressively narrows the retrieval scope through multi-round reasoning (from semantic memory to raw messages), or analyzes existing memories to decide how to update (create, delete, modify). 
3.   3.Dual-Layer Hybrid Memory. The system maintains two storage tiers: the lower RawMessageStore (raw message log) and the upper SemanticMemoryStore (semantic memory repository). The two layers are linked via evidence_ids, enabling progressive narrowing from coarse to fine granularity. 

### 4.2 Dual-Layer Hybrid Memory

To address noise interference from long contexts and difficulties in cross-modal retrieval, we design a layered storage structure balancing retrospective accuracy with inference efficiency overall.

#### Layer 1: Raw Message Store.

This is the memory’s foundation, serving as an append-only database that stores raw conversational messages in chronological order.

#### Layer 2: Semantic Memory Store.

The upper layer stores high-level knowledge extracted and refined by MemoryManager. To address the challenge of images not being recalled by pure text queries, we introduce a visual captioning mechanism to incorporate visual content into searchable text. Each semantic entry e can be represented as:

e=\{c_{text},c_{caption},c_{image},ptr\}(2)

where c_{text} represents the textual semantic description (e.g., “User’s dog Bobo is a Corgi who likes blue toys”); c_{caption} contains automatically generated captions for associated images using a vision-language model; c_{image} is a image associated with this semantic entry; and ptr=\{[s_{1},e_{1}],[s_{2},e_{2}],\ldots\} contains evidence_ids linking to supporting raw message ranges in Layer 1. To speed up retrivial, we generate the following index vectors for each semantic entry: v_{text}^{dense}\in\mathbb{R}^{d} is the dense text embedding computed from the concatenation of c_{text} and c_{caption} using a sentence encoder(Reimers and Gurevych, [2019](https://arxiv.org/html/2602.07624v1#bib.bib35 "Sentence-bert: sentence embeddings using siamese bert-networks"))E_{T}^{dense}; v_{text}^{sparse} denotes the BM25 sparse representation for keyword matching; v_{img}\in\mathbb{R}^{d^{\prime}} represents the visual embedding generated from associated images using a cross-modal encoder(Zhai et al., [2023](https://arxiv.org/html/2602.07624v1#bib.bib36 "Sigmoid loss for language image pre-training"))E_{I}.

#### Tri-path hybrid retrieval.

Given user query q (possibly text or text+image), retrieval score S(q,e) is computed through three parallel paths:

\displaystyle S_{dense}(q,e)\displaystyle=\text{sim}(E_{T}^{dense}(q_{text}),v_{text}^{dense})(3)
\displaystyle S_{sparse}(q,e)\displaystyle=\text{BM25}(q_{text},v_{text}^{sparse})(4)
\displaystyle S_{visual}(q,e)\displaystyle=\text{sim}(E_{I}(q_{img}),v_{img})(5)

Path 1 (Dense text semantic): Computes cosine similarity between the query’s dense text embedding and each entry’s v_{text}^{dense}, capturing semantic relationships.

Path 2 (Sparse keyword): Applies BM25 scoring between query text and v_{text}^{sparse}, capturing exact keyword matches crucial for names, dates, and specific terms.

Path 3 (Cross-modal): When q_{img} is provided, computes similarity between the query image embedding and v_{img}; otherwise uses cross-modal text-to-image similarity between q_{text} and v_{img}, enabling text queries to retrieve image-centric memories.

Finally, results from the three paths are fused via Reciprocal Rank Fusion (RRF):

S_{RRF}(q,e)=\sum_{path\in\{dense,sparse,visual\}}\frac{1}{k+rank_{path}(e)}(6)

where k=60 is a hyperparameter and rank_{path}(e) is the rank of entry e in that path’s results.

Cross-modal alignment: Since we generate c_{caption} during storage, even when users search for images using only text (q_{img} is empty), q_{text} can recall corresponding image memories through high similarity with c_{caption}. This enables queries like “my Corgi photo” to return stored dog photos even if the semantic entry doesn’t explicitly contain “Corgi” text description.

### 4.3 Agentic Collaboration

The system implements memory operations through the collaboration of two specialized agents, each with distinct responsibilities and capabilities.

#### ChatAgent workflow.

ChatAgent processes each user message through three sequential stages inspired by ReAct:

Query Stage: Upon receiving a user message, ChatAgent first determines whether querying long-term memory is necessary. This decision considers whether the query references past events, people, or concepts not present in recent conversation context. If needed, ChatAgent queries memory, providing both the query and a snippet of recent conversation context. The agent may iterate this process, refining queries based on retrieved results, until sufficient information is gathered or a maximum iteration limit N is reached. This iterative querying enables progressive information gathering and disambiguation in practice.

Generate Stage: With all the retrieved memory context and the current conversation history, ChatAgent generates a response to the user. The memory context is then naturally incorporated into the generation process through the language model’s context window.

Update Stage: After generating the response, ChatAgent analyzes the conversation content to determine whether new information should be persisted. If updates are warranted, ChatAgent invokes MemoryManager to update memory.

#### MemoryManager operations.

MemoryManager handles two types of requests from ChatAgent:

Query operation: Upon receiving a query request with accompanying conversation context, MemoryManager performs iterative reasoning-driven retrieval. It begins by searching the semantic memory bank using the tri-path hybrid retrieval mechanism. For promising candidates, it examines their evidence_ids and may retrieve specific raw conversational segments for detailed context. This progressive narrowing from semantic to episodic memory enables MemoryManager to provide increasingly refined context. The agent may iterate this process (up to N rounds), alternating between semantic search and raw message examination, until confident in having gathered sufficient relevant information for downstream answering.

Update operation: When receiving an update request, MemoryManager determines whether the current interaction introduces new, outdated, or conflicting information that should be reflected in long-term memory. Building on the same retrieval and reasoning mechanisms used in the query operation, it first inspects existing semantic memories related to the new content. Based on this comparison, MemoryManager may add new semantic entries, remove obsolete ones, or replace existing memories to maintain consistency. Throughout this process, the agent can re-query the memory store as needed to verify the effects of its actions and to avoid redundancy or contradiction. In essence, the update operation extends the query operation with write access to the semantic memory store, enabling dynamic and self-consistent memory maintenance.

#### Motivation for agent collaboration.

The two-agent architecture provides several advantages over a single-agent design: First, it isolates memory management complexity from user interaction, preventing ChatAgent’s conversation context from being overwhelmed by raw memory retrieval results. Second, MemoryManager can maintain its own reasoning context across operations without interfering with ChatAgent’s dialogue context. Third, when memory operations require conversation context, ChatAgent provides only a concise recent snippet rather than full history, while MemoryManager can access older context through the memory bank itself when needed. This separation of concerns enables both agents to specialize in their respective tasks while collaborating effectively.

### 4.4 Multimodal Chat Dataset Construction

Building upon the LoCoMo framework(Maharana et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib13 "Evaluating very long-term conversational memory of llm agents")), we construct a concept-grounded multimodal chat corpus to address the limitation where images primarily serve as background context. As illustrated in [Figure 3](https://arxiv.org/html/2602.07624v1#S3.F3 "In Belief state as memory bank. ‣ 3 Problem Formulation ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), our approach transforms visual inputs into essential narrative drivers through a four-stage pipeline:

1.   1.Concept Grouping: Instead of isolated images, we sample semantically distinct Concept Groups (e.g., specific objects or entities) to simulate realistic discussions. 
2.   2.Unified Multimodal Generation: We employ a “One-Call” generation strategy using large language models. This method simultaneously generates multi-session dialogues and corresponding reasoning QA pairs, ensuring strict consistency between the visual evidence, the narrative flow, and the ground-truth answers. 
3.   3.Temporal Interpolation: To maintain the temporal integrity of the original long-context conversations, generated sessions are inserted into specific time intervals of the host dialogue using strict timestamp interpolation. 
4.   4.Hybrid QA Injection: The final evaluation set combines the newly generated reasoning questions (covering multi-hop, temporal, and open-domain types) with VQA samples explicitly injected into the dialogue stream. 

For comprehensive implementation details, including prompt constraints, QA category distributions, and hyperparameter settings, please refer to Appendix[C](https://arxiv.org/html/2602.07624v1#A3 "Appendix C Dataset Construction Details ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions").

Table 1: Experimental results on LoCoMo dataset. The best results are highlighted in bold, and the second-best results are underlined. Models are evaluated on LLM-as-a-Judge with evaluation model Qwen3-VL-32B(Q), GPT-4o(G) and their average(Avg). 

## 5 Experiment

### 5.1 Experimental Setup

#### Datasets.

We evaluate on our enhanced LoCoMo dataset constructed via the pipeline described in [Section 4.4](https://arxiv.org/html/2602.07624v1#S4.SS4 "4.4 Multimodal Chat Dataset Construction ‣ 4 M2A: Multimodal Memory Agent ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). The dataset consists of 10 long conversations averaging 621 turns and approximately 10k tokens each, with 214 images injected throughout the dialogues. The original LoCoMo questions are categorized into Single-Hop, Multi-Hop, Temporal, and Open Domain. Following prior work(Yan et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib40 "Memory-r1: enhancing large language model agents to manage and utilize memories via reinforcement learning")), we exclude the Adversarial category due to missing ground-truth answers.

We further augment the benchmark with a new category, Visual-Centric questions, which are designed to fully leverage the injected visual information. These questions specifically test the model’s ability to recall and reason over visual content introduced during concept sessions. The Visual-Centric questions can be further divided into five subtypes: four of them are directly aligned with the original LoCoMo categories (Single-Hop, Multi-Hop, Temporal, and Open Domain) but require visual grounding, while the remaining subtype is adapted from the original QA pairs of YolLaVA.

#### Baselines.

We compare against three representative systems: LoCoMo(Maharana et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib13 "Evaluating very long-term conversational memory of llm agents")): a RAG system with single-layer semantic vector storage and single-pass retrieval before generation. Below we will refer this system as RAG. Mem0(Chhikara et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib33 "Mem0: building production-ready ai agents with scalable long-term memory")): A general memory layer supporting cross-session knowledge persistence but with text-only support. A-MEM(Xu et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib30 "A-mem: agentic memory for llm agents")): An agentic memory system supporting editing operations but handling only text modality.

#### Evaluation metrics.

Prior work typically uses F1 or BLEU-1 scores for evaluation. However, we argue these metrics are inadequate for open-ended generation tasks where answers may be semantically equivalent but lexically different (e.g., “last week” vs. specific dates). Instead, we employ LLM-as-a-judge evaluation using two independent judges: Qwen3-VL-32B(Yang et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib31 "Qwen3 technical report")) (denoted as Q) and GPT-4o(Hurst et al., [2024](https://arxiv.org/html/2602.07624v1#bib.bib32 "Gpt-4o system card")) (denoted as G). Each judge assigns a binary correctness score by comparing generated answers to ground-truth references considering semantic equivalence. We report Q, G, and their average (Avg) as our primary metrics.

#### Implementation details.

All local models are served using vLLM(Kwon et al., [2023](https://arxiv.org/html/2602.07624v1#bib.bib34 "Efficient memory management for large language model serving with pagedattention")) for efficient inference. For GPT-4o/GPT-4o-mini API calls, we use the official structured output API. Text embeddings for all methods use all-MiniLM-L6-v2(Reimers and Gurevych, [2019](https://arxiv.org/html/2602.07624v1#bib.bib35 "Sentence-bert: sentence embeddings using siamese bert-networks")) (consistent with A-MEM). Image embeddings and cross-modal retrieval employ SigLIP-Base-Patch16-384(Zhai et al., [2023](https://arxiv.org/html/2602.07624v1#bib.bib36 "Sigmoid loss for language image pre-training")). For the tri-path retrieval, we retrieve top-10 candidates from each path and fuse using RRF with k=60. Semantic memories are managed with Milvus(Wang et al., [2021](https://arxiv.org/html/2602.07624v1#bib.bib39 "Milvus: a purpose-built vector data management system")).

### 5.2 Main Results

[Table 1](https://arxiv.org/html/2602.07624v1#S4.T1 "In 4.4 Multimodal Chat Dataset Construction ‣ 4 M2A: Multimodal Memory Agent ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions") reports experimental results across different question categories and base models. Overall, M 2 A consistently outperforms all baselines across the majority of settings, demonstrating robust advantages in long-context and multimodal memory reasoning.

On GPT-4o-mini, M 2 A achieves an average accuracy of 44.64%, substantially surpassing RAG (33.27%), Mem0 (34.73%), and A-MEM (36.26%). The gains are most pronounced on Single-Hop questions, where M 2 A improves from 44.71% (best baseline) to 56.48%, highlighting the effectiveness of evidence-linked progressive narrowing for retrieving fine-grained and contextually relevant information. On the newly introduced Visual-Centric questions, M 2 A reaches 43.27% accuracy, significantly outperforming RAG (30.69%), which validates the benefits of maintaining multimodal memory representations with image captions and cross-modal hybrid retrieval.

Similar trends are observed on open-source models. On Qwen3-VL-8B, M 2 A achieves 54.69% average accuracy, compared to 43.95% for the strongest baseline. On GLM-4.6V-Flash, the performance gap narrows slightly (56.48% vs. 47.46%), yet M 2 A consistently maintains a clear advantage across questions of all categories.

[Figure 4](https://arxiv.org/html/2602.07624v1#S5.F4 "In 5.2 Main Results ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions") further presents a fine-grained breakdown of results on Visual-Centric questions for GPT-4o-mini and Qwen3-VL-8B. Across all subcategories, M 2 A demonstrates superior performance, underscoring its strong capability in multimodal information recall and reasoning.

Notably, despite being an agentic memory system, A-MEM underperforms Pure RAG on several categories. We attribute this behavior to A-MEM’s text-only design and single-layer memory structure, which are insufficient for modeling multimodal concepts and supporting fine-grained temporal retrieval in our visually enriched benchmark.

![Image 4: Refer to caption](https://arxiv.org/html/2602.07624v1/x4.png)

Figure 4: Detailed results on Visual-Centric questions.

Table 2: Comparison of M 2 A and its variation on Qwen3-VL-8B.

### 5.3 Ablation Study

To understand the contribution of each component, we conduct systematic ablations on the Qwen3VL-8B model. [Table 2](https://arxiv.org/html/2602.07624v1#S5.T2 "In 5.2 Main Results ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions") presents results averaged across all question categories.

#### Effect of dual-layer memory.

Removing the RawMessageStore and relying solely on SemanticMemoryStore (“w/o Dual-layer”) degrades performance by 13.31 percentage points. This validates our hypothesis that semantic summaries alone may lack crucial details or suffer from information loss during abstraction. The evidence-linked design enables MemoryManager to verify and augment semantic memories with precise raw context when needed.

#### Effect of iterative retrieval.

Constraining MemoryManager to single-pass retrieval without iterative reasoning (“w/o Iterative”) reduces accuracy by 16.02 points. This demonstrates the value of progressive narrowing—the ability to examine initial semantic results, identify promising candidates through their linked raw messages, and iteratively refine the search. Single-pass retrieval often either misses relevant context or retrieves too broadly.

#### Effect of tri-path retrieval.

Using only dense text embeddings without sparse BM25 or cross-modal image retrieval (“w/o Tri-path”) drops performance by 4.10 points. This results proves that the tri-path retrieval approach provides robustness: dense embeddings capture semantic similarity, BM25 handles exact entity matches, and cross-modal retrieval enables text-to-image queries. Removing any path weakens overall recall quality.

![Image 5: Refer to caption](https://arxiv.org/html/2602.07624v1/x5.png)

Figure 5: Detailed results on Visual-Centric questions.

#### Effect of context window length.

We study the impact of the amount of recent conversational context provided to MemoryManager when ChatAgent triggers memory queries or updates. Specifically, we vary the number of recent turns passed along with each request to the MemoryManager. As shown in [Figure 5](https://arxiv.org/html/2602.07624v1#S5.F5 "In Effect of tri-path retrieval. ‣ 5.3 Ablation Study ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), providing no contextual history severely degrades performance across all models, indicating that MemoryManager cannot reliably update or retrieve effective memories based solely on the current turn and ChatAgent’s high-level update suggestions.

Notably, supplying only a small amount of recent context (e.g., 5 turns) already leads to substantial performance gains, enabling MemoryManager to better infer user intent and anchor updates to the appropriate conversational state. Increasing the context window further yields only marginal improvements. Overall, these results suggest that a short recent context window is sufficient for effective memory operations, while longer contexts provide limited additional benefits and primarily incur extra computational overhead.

## 6 Conclusion

We presented M 2 A, an agentic multimodal memory system addressing the challenge of incremental personalization in long-term human-machine interactions. Through dual-layer hybrid memory with evidence linking, M 2 A enables progressive narrowing from semantic summaries to fine-grained conversational context. The collaboration between ChatAgent and MemoryManager implements autonomous, reasoning-driven memory operations that adapt dynamically to conversation context. Tri-path cross-modal hybrid retrieval combining dense text embeddings, BM25 sparse retrieval, and cross-modal image embeddings provides robust recall across semantic, lexical, and visual cues. Experimental results demonstrate substantial improvements over existing methods, particularly on temporally complex and visual-centric questions. This work shows that transforming personalization from static configuration to co-evolving memory provides a viable path toward more adaptive and individualized AI systems.

## Impact Statement

This paper presents work advancing long-term personalized interaction in AI systems. There are many potential societal consequences of our work, none of which we feel must be specifically highlighted here.

## References

*   Y. Alaluf, E. Richardson, S. Tulyakov, K. Aberman, and D. Cohen-Or (2024)Myvlm: personalizing vlms for user-specific queries. In European Conference on Computer Vision,  pp.73–91. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p2.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   R. An, S. Yang, M. Lu, R. Zhang, K. Zeng, Y. Luo, J. Cao, H. Liang, Y. Chen, Q. She, et al. (2024)Mc-llava: multi-concept personalized vision-language model. arXiv preprint arXiv:2411.11706. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p2.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p2.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   R. An, S. Yang, R. Zhang, Z. Shen, M. Lu, G. Dai, H. Liang, Z. Guo, S. Yan, Y. Luo, et al. (2025)UniCTokens: boosting personalized understanding and generation via unified concept tokens. arXiv preprint arXiv:2505.14671. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p2.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   H. Bai, R. Wang, Z. Du, Y. Zhao, F. Zhang, H. Chen, X. Zhu, B. Zheng, and X. Zhao (2025)Online-pvlm: advancing personalized vlms with online concept learning. arXiv preprint arXiv:2511.20056. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p2.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   Z. Chen, W. Wang, Y. Cao, Y. Liu, Z. Gao, E. Cui, J. Zhu, S. Ye, H. Tian, Z. Liu, et al. (2024)Expanding performance boundaries of open-source multimodal models with model, data, and test-time scaling. arXiv preprint arXiv:2412.05271. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p1.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p1.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   P. Chhikara, D. Khant, S. Aryan, T. Singh, and D. Yadav (2025)Mem0: building production-ready ai agents with scalable long-term memory. arXiv preprint arXiv:2504.19413. Cited by: [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px2.p1.1 "Baselines. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   G. V. Cormack, C. L. Clarke, and S. Buettcher (2009)Reciprocal rank fusion outperforms condorcet and individual rank learning methods. In Proceedings of the 32nd international ACM SIGIR conference on Research and development in information retrieval,  pp.758–759. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p4.3 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   H. Hao, J. Han, C. Li, Y. Li, and X. Yue (2025)RAP: retrieval-augmented personalization for multimodal large language models. In Proceedings of the Computer Vision and Pattern Recognition Conference,  pp.14538–14548. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p1.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§1](https://arxiv.org/html/2602.07624v1#S1.p2.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p3.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   A. Hurst, A. Lerer, A. P. Goucher, A. Perelman, A. Ramesh, A. Clark, A. Ostrow, A. Welihinda, A. Hayes, A. Radford, et al. (2024)Gpt-4o system card. arXiv preprint arXiv:2410.21276. Cited by: [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px3.p1.1 "Evaluation metrics. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   L. P. Kaelbling, M. L. Littman, and A. R. Cassandra (1998)Planning and acting in partially observable stochastic domains. Artificial intelligence 101 (1-2),  pp.99–134. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p4.3 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   W. Kwon, Z. Li, S. Zhuang, Y. Sheng, L. Zheng, C. H. Yu, J. Gonzalez, H. Zhang, and I. Stoica (2023)Efficient memory management for large language model serving with pagedattention. In Proceedings of the 29th symposium on operating systems principles,  pp.611–626. Cited by: [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px4.p1.1 "Implementation details. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   B. Li, Y. Zhang, D. Guo, R. Zhang, F. Li, H. Zhang, K. Zhang, P. Zhang, Y. Li, Z. Liu, et al. (2024a)Llava-onevision: easy visual task transfer. arXiv preprint arXiv:2408.03326. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p1.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p1.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   F. Li, R. Zhang, H. Zhang, Y. Zhang, B. Li, W. Li, Z. Ma, and C. Li (2024b)Llava-next-interleave: tackling multi-image, video, and 3d in large multimodal models. arXiv preprint arXiv:2407.07895. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p1.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p1.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   W. Liu, Z. Tang, J. Li, K. Chen, and M. Zhang (2024)Memlong: memory-augmented retrieval for long text modeling. arXiv preprint arXiv:2408.16967. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px2.p1.1 "Long-context memory and agentic memory management. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   Y. Luo, R. An, B. Zou, Y. Tang, J. Liu, and S. Zhang (2024)Llm as dataset analyst: subpopulation structure discovery with large language model. In European Conference on Computer Vision,  pp.235–252. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p3.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   A. Maharana, D. Lee, S. Tulyakov, M. Bansal, F. Barbieri, and Y. Fang (2024)Evaluating very long-term conversational memory of llm agents. arXiv preprint arXiv:2402.17753. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p3.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px2.p1.1 "Long-context memory and agentic memory management. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§4.4](https://arxiv.org/html/2602.07624v1#S4.SS4.p1.1 "4.4 Multimodal Chat Dataset Construction ‣ 4 M2A: Multimodal Memory Agent ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px2.p1.1 "Baselines. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   T. Nguyen, H. Liu, Y. Li, M. Cai, U. Ojha, and Y. J. Lee (2024)Yo’llava: your personalized language and vision assistant. Advances in Neural Information Processing Systems 37,  pp.40913–40951. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p2.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p2.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   T. Nguyen, K. K. Singh, J. Shi, T. Bui, Y. J. Lee, and Y. Li (2025)Yo’chameleon: personalized vision and language generation. In Proceedings of the Computer Vision and Pattern Recognition Conference,  pp.14438–14448. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p2.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   C. Packer, V. Fang, S. Patil, K. Lin, S. Wooders, and J. Gonzalez (2023)MemGPT: towards llms as operating systems.. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p3.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px2.p2.1 "Long-context memory and agentic memory management. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   N. Reimers and I. Gurevych (2019)Sentence-bert: sentence embeddings using siamese bert-networks. arXiv preprint arXiv:1908.10084. Cited by: [§4.2](https://arxiv.org/html/2602.07624v1#S4.SS2.SSS0.Px2.p2.11 "Layer 2: Semantic Memory Store. ‣ 4.2 Dual-Layer Hybrid Memory ‣ 4 M2A: Multimodal Memory Agent ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px4.p1.1 "Implementation details. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   S. Robertson and H. Zaragoza (2009)The probabilistic relevance framework: bm25 and beyond. Foundations and Trends in Information Retrieval 3,  pp.333–389. External Links: [Document](https://dx.doi.org/10.1561/1500000019)Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p4.3 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   S. Seifi, V. Dorovatas, D. Olmeda Reino, and R. Aljundi (2025)Personalization toolkit: training free personalization of large vision language models. arXiv preprint arXiv:2502.02452. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p3.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   D. Song, J. Zeng, M. Liu, X. Li, and A. Liu (2023)Fashion customization: image generation based on editing clue. IEEE Transactions on Circuits and Systems for Video Technology 34 (6),  pp.4434–4444. Cited by: [Appendix A](https://arxiv.org/html/2602.07624v1#A1.SS0.SSS0.Px2.p1.1 "Multimodal editing and enhancement. ‣ Appendix A Additional Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   D. Song, J. Zhou, J. Zeng, H. Tian, B. Zheng, R. Kang, and A. Liu (2025)MEF-gd: multimodal enhancement and fusion network for garment designer. IEEE Transactions on Circuits and Systems for Video Technology. Cited by: [Appendix A](https://arxiv.org/html/2602.07624v1#A1.SS0.SSS0.Px2.p1.1 "Multimodal editing and enhancement. ‣ Appendix A Additional Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   J. Wang, X. Yi, R. Guo, H. Jin, P. Xu, S. Li, X. Wang, X. Guo, C. Li, X. Xu, et al. (2021)Milvus: a purpose-built vector data management system. In Proceedings of the 2021 international conference on management of data,  pp.2614–2627. Cited by: [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px4.p1.1 "Implementation details. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   P. Wang, S. Bai, S. Tan, S. Wang, Z. Fan, J. Bai, K. Chen, X. Liu, J. Wang, W. Ge, et al. (2024)Qwen2-vl: enhancing vision-language model’s perception of the world at any resolution. arXiv preprint arXiv:2409.12191. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p1.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px1.p1.1 "Personalized multimodal models. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   W. Wang, L. Dong, H. Cheng, X. Liu, X. Yan, J. Gao, and F. Wei (2023)Augmenting language models with long-term memory. Advances in Neural Information Processing Systems 36,  pp.74530–74543. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px2.p1.1 "Long-context memory and agentic memory management. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   W. Xu, Z. Liang, K. Mei, H. Gao, J. Tan, and Y. Zhang (2025)A-mem: agentic memory for llm agents. arXiv preprint arXiv:2502.12110. Cited by: [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px2.p2.1 "Long-context memory and agentic memory management. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px2.p1.1 "Baselines. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   S. Yan, X. Yang, Z. Huang, E. Nie, Z. Ding, Z. Li, X. Ma, K. Kersting, J. Z. Pan, H. Schütze, et al. (2025)Memory-r1: enhancing large language model agents to manage and utilize memories via reinforcement learning. arXiv preprint arXiv:2508.19828. Cited by: [§D.3](https://arxiv.org/html/2602.07624v1#A4.SS3.p1.1 "D.3 LLM-as-a-Judge Prompts ‣ Appendix D System Prompts ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px1.p1.1 "Datasets. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   A. Yang, A. Li, B. Yang, B. Zhang, B. Hui, B. Zheng, B. Yu, C. Gao, C. Huang, C. Lv, C. Zheng, D. Liu, F. Zhou, F. Huang, F. Hu, H. Ge, H. Wei, H. Lin, J. Tang, J. Yang, J. Tu, J. Zhang, J. Yang, J. Yang, J. Zhou, J. Zhou, J. Lin, K. Dang, K. Bao, K. Yang, L. Yu, L. Deng, M. Li, M. Xue, M. Li, P. Zhang, P. Wang, Q. Zhu, R. Men, R. Gao, S. Liu, S. Luo, T. Li, T. Tang, W. Yin, X. Ren, X. Wang, X. Zhang, X. Ren, Y. Fan, Y. Su, Y. Zhang, Y. Zhang, Y. Wan, Y. Liu, Z. Wang, Z. Cui, Z. Zhang, Z. Zhou, and Z. Qiu (2025)Qwen3 technical report. External Links: 2505.09388, [Link](https://arxiv.org/abs/2505.09388)Cited by: [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px3.p1.1 "Evaluation metrics. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   S. Yao, J. Zhao, D. Yu, N. Du, I. Shafran, K. Narasimhan, and Y. Cao (2023)ReAct: synergizing reasoning and acting in language models. In International Conference on Learning Representations (ICLR), Cited by: [item 1](https://arxiv.org/html/2602.07624v1#S4.I1.i1.p1.1 "In 4.1 Framework Overview ‣ 4 M2A: Multimodal Memory Agent ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   J. Zeng, D. Song, W. Nie, H. Tian, T. Wang, and A. Liu (2024)Cat-dm: controllable accelerated virtual try-on with diffusion model. In Proceedings of the IEEE/CVF conference on computer vision and pattern recognition,  pp.8372–8382. Cited by: [Appendix A](https://arxiv.org/html/2602.07624v1#A1.SS0.SSS0.Px1.p1.1 "Controllable generation with user constraints. ‣ Appendix A Additional Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   X. Zhai, B. Mustafa, A. Kolesnikov, and L. Beyer (2023)Sigmoid loss for language image pre-training. In Proceedings of the IEEE/CVF international conference on computer vision,  pp.11975–11986. Cited by: [§4.2](https://arxiv.org/html/2602.07624v1#S4.SS2.SSS0.Px2.p2.11 "Layer 2: Semantic Memory Store. ‣ 4.2 Dual-Layer Hybrid Memory ‣ 4 M2A: Multimodal Memory Agent ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§5.1](https://arxiv.org/html/2602.07624v1#S5.SS1.SSS0.Px4.p1.1 "Implementation details. ‣ 5.1 Experimental Setup ‣ 5 Experiment ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   N. Zhang, Y. Li, D. Du, Z. Chong, Z. Sun, J. Zeng, Y. Dai, Z. Xie, H. Zhu, and X. Han (2025)Robust-mvton: learning cross-pose feature alignment and fusion for robust multi-view virtual try-on. In Proceedings of the Computer Vision and Pattern Recognition Conference,  pp.16029–16039. Cited by: [Appendix A](https://arxiv.org/html/2602.07624v1#A1.SS0.SSS0.Px3.p1.1 "Cross-view consistency and alignment. ‣ Appendix A Additional Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 
*   W. Zhong, L. Guo, Q. Gao, H. Ye, and Y. Wang (2024)Memorybank: enhancing large language models with long-term memory. In Proceedings of the AAAI Conference on Artificial Intelligence, Vol. 38,  pp.19724–19731. Cited by: [§1](https://arxiv.org/html/2602.07624v1#S1.p3.1 "1 Introduction ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"), [§2](https://arxiv.org/html/2602.07624v1#S2.SS0.SSS0.Px2.p2.1 "Long-context memory and agentic memory management. ‣ 2 Related Work ‣ M2A: Multimodal Memory Agent with Dual-Layer Hybrid Memory for Long-Term Personalized Interactions"). 

## Appendix A Additional Related Work

Beyond memory-centric personalization approaches, there exists a complementary research direction on controllable multimodal generation and editing systems. While our work focuses on personalization through memory and retrieval, these systems explore personalization through conditional generation, offering an alternative perspective on user-specific multimodal systems.

#### Controllable generation with user constraints.

Diffusion-based generative models have enabled fine-grained control over visual synthesis under user-specified constraints. Zeng et al. ([2024](https://arxiv.org/html/2602.07624v1#bib.bib43 "Cat-dm: controllable accelerated virtual try-on with diffusion model")) propose Cat-DM, a controllable accelerated virtual try-on system that leverages diffusion models to render garments according to user-defined constraints while maintaining synthesis efficiency. This demonstrates how generative priors can be conditioned on user inputs to produce personalized visual outputs. Such conditional generation paradigms represent an orthogonal approach to personalization: rather than retrieving and reasoning over stored user information, these systems directly encode user preferences into generation controls.

#### Multimodal editing and enhancement.

Image editing techniques that integrate multimodal signals provide another avenue for user-driven customization. Song et al. ([2023](https://arxiv.org/html/2602.07624v1#bib.bib44 "Fashion customization: image generation based on editing clue")) explore fashion customization through image generation based on editing cues, enabling users to modify garment appearance and style through natural specifications. Building on this direction, Song et al. ([2025](https://arxiv.org/html/2602.07624v1#bib.bib45 "MEF-gd: multimodal enhancement and fusion network for garment designer")) introduce MEF-GD, a multimodal enhancement and fusion network for garment design that integrates diverse modalities to improve synthesis quality and support richer semantic controls. These works highlight the role of multimodal fusion in enabling more expressive user control over generated content.

#### Cross-view consistency and alignment.

Maintaining consistency across different views or poses presents additional challenges for personalized visual systems. Zhang et al. ([2025](https://arxiv.org/html/2602.07624v1#bib.bib46 "Robust-mvton: learning cross-pose feature alignment and fusion for robust multi-view virtual try-on")) present Robust-MVTON, which learns cross-pose feature alignment and fusion to achieve robust multi-view virtual try-on results across varied user poses and viewpoints. This work emphasizes the importance of robust feature alignment when personalizing visual content under geometric variations.

While these generation-based systems differ from our memory-centric approach, both paradigms ultimately aim to create user-specific experiences in multimodal contexts. Generation-based methods encode personalization directly into model outputs through conditional controls, whereas memory-based methods (including ours) maintain explicit user representations that guide response generation through retrieval. These approaches can be viewed as complementary: generation-based systems excel at producing novel personalized visual content, while memory-based systems excel at maintaining consistency and reasoning over accumulated user knowledge across extended interactions. Future work might explore hybrid approaches that combine editable long-term memory with controllable generation capabilities.

## Appendix B Detailed Baselines Introduction

### B.1 A-MEM

We use the A-MEM baseline. The system initializes the AgenticMemorySystem from the original A-MEM codebase with a sentence embedding model (all-MiniLM-L6-v2) and connects the LLM to a local vLLM endpoint via the API. Each conversation turn is converted into a structured memory note that includes the timestamp, speaker name, and message content. If images are present, the system first performs image captioning with the same vision-language model and appends a concise natural-language image summary to the memory note. During question answering, it retrieves top-k related memories (default k=10) and constructs the final prompt from the retrieved context. This implements an agentic memory read/write pipeline while keeping the base model fixed.

### B.2 Mem0

We use the legacy Mem0 implementation with an in-memory Qdrant vector store and a embedding model (all-MiniLM-L6-v2). Similar to A-MEM, each dialog turn is ingested into memory with optional image captioning; captions are appended to the text as a system note so that vision signals are converted into searchable text. At inference, it retrieves a fixed number of memories (default k=10), builds a retrieval-augmented prompt, and generates the answer with the vLLM-backed model.

### B.3 RAG

This is a single-pass retrieval setup without explicit memory editing. All conversation turns are embedded with a sentence-transformer model and stored as dense vectors. At query time, we compute cosine similarity (dot product on normalized embeddings) between the question and all stored turns, select the top-k contexts (default k=5), and concatenate them into the prompt. Image paths from retrieved turns are passed through the model as additional visual inputs. This provides a pure retrieval-augmented baseline without long-term memory updates.

## Appendix C Dataset Construction Details

This section details the pipeline implemented to construct the concept-grounded multimodal dataset. The process is governed by strict constraints to ensure high-quality visual grounding and temporal coherence.

#### Step 1: Concept Grouping and Sampling.

For each target conversation, we sample a concept group \mathcal{G}=\{c_{1},...,c_{k}\} where the group size k is uniformly sampled from [3,4]. For each concept c_{i}, we retrieve a subset of m\in[2,3] images from the source dataset to ensure visual consistency across different dialogue turns.

#### Step 2: One-Call Generation Strategy.

We utilize GPT-4 to generate the dialogue and QA pairs in a single API call to maximize coherence. The generation is constrained by the following hyperparameters:

*   •Session Structure: The model generates N_{sess}\in[5,6] distinct sessions. Each session consists of T_{turns}\in[5,15] dialogue turns. 
*   •Visual Grounding: The first message of the sequence is forced to explicitly reference all concepts in \mathcal{G} using angle-bracket notation (e.g., <concept_name>) to establish the entities. 

#### Step 3: QA Taxonomy and Distribution.

To balance the difficulty of the benchmark, we enforce a strict distribution ratio of 2:3:1:4 for the generated QA categories. For a typical set of 20 generated questions, the distribution is:

*   •Type 6 (Multi-Hop): 20% (4 questions). Requires reasoning across multiple dialogue turns. 
*   •Type 7 (Temporal): 30% (6 questions). Involves understanding the timeline of events. 
*   •Type 8 (Open-Domain): 10% (2 questions). Requires external knowledge grounded in the image. 
*   •Type 9 (Single-Hop): 40% (8 questions). Direct information retrieval. 

Additionally, we inject Type 5 (Visual Retrieval) questions by matching images appearing in the dialogue with existing VQA datasets.

#### Step 4: Temporal Interpolation.

To insert the generated sessions into a host conversation without disrupting its timeline, we perform linear time interpolation. Let the insertion point in the host conversation be between timestamps t_{start} and t_{end}. We generate timestamps \tau_{j} for the j-th generated session (j\in\{1,...,N_{sess}\}) using:

\tau_{j}=t_{start}+\frac{j}{N_{sess}+1}\times(t_{end}-t_{start})(7)

This ensures that t_{start}<\tau_{1}<...<\tau_{N_{sess}}<t_{end}, preserving the strictly increasing temporal order of the merged conversation.

## Appendix D System Prompts

### D.1 ChatAgent Prompts

### D.2 MemoryManager Prompts

### D.3 LLM-as-a-Judge Prompts

We adapt the same LLM-as-a-Judge Prompts from Memory-R1(Yan et al., [2025](https://arxiv.org/html/2602.07624v1#bib.bib40 "Memory-r1: enhancing large language model agents to manage and utilize memories via reinforcement learning")):
