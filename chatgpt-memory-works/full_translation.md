ChatGPT remembers you, but not the way most people assume.

It does not search your old conversations. There is no vector database quietly pulling up your history when you ask a question. Instead, on every message, ChatGPT loads a summary of who you are, built from your past chats, straight into its context.

In June 2026, OpenAI rebuilt how that summary gets made and gave it a name: Dreaming.

This article breaks down how ChatGPT memory actually works: the two systems OpenAI documents, the injection mechanism researchers reverse-engineered, what Dreaming changes, the risks that come with a permanent profile, and where a developer memory layer like Mem0 fits.

The two systems OpenAI documents

Officially, ChatGPT memory has two parts (OpenAI Help Center).

Saved memories are discrete facts. You can tell ChatGPT "remember that I am vegetarian," or it can save a detail on its own when it seems useful later. OpenAI describes these as working like custom instructions, except the model updates them automatically instead of you managing them by hand.

Reference chat history is different. When it is on, ChatGPT draws on your past conversations to infer your interests and preferences, and uses that to personalize future chats. Unlike saved memories, which persist until you delete them, these inferred details shift over time as the model updates what it thinks is worth keeping (OpenAI).

You can turn either off in settings, edit what ChatGPT knows about you in conversation, or use Temporary Chat for sessions that neither read nor write memory. Custom GPTs do not share this memory; each runs fresh.

That is the official picture. It tells you what happens. It does not tell you how.

How it actually works: a profile, not a search

The surprising part, and the part OpenAI does not spell out, is the retrieval mechanism. There isn't one.

Security researcher Johann Rehberger tested this directly and found ChatGPT could not recall specific one-off conversations from a year back. Simon Willison reached the same place, retracting his own initial guess that it used retrieval-augmented generation. What actually happens is simpler: ChatGPT effectively maintains a detailed summary of your previous conversations, updating it frequently with new details. The summary then gets injected into the context every time you start a new chat.

So memory is not fetched per question. It is pre-loaded. A standing profile of you rides along in the system prompt on every turn. Rehberger documented that this profile arrives in roughly six named sections: Model Set Context, Assistant Response Preferences, Notable Past Conversation Topic Highlights, Helpful User Insights, Recent Conversation Content, and User Interaction Metadata.

The details make the mechanism concrete.

Recent Conversation Content carries your recent conversations, but only your messages, not ChatGPT's replies. The reason is data volume — prompt injection and hallucination become major risks. Entries are separated by a |||| delimiter, carry internal intent_tags (like translation or argument_or_summary_generation), and include second-precision timestamps.

Saved memories work through a different path: the model calls a bio tool (to=bio) to persist a fact, which then appears as a dated entry in the # Model Set Context section of a future system prompt.

Why "all-in" instead of retrieval

Why not build the kind of careful retrieval pipeline that most memory systems use? The author at shloked.com summarizes OpenAI's strategy as betting on scale over cleverness: no vector database, no knowledge graph, no RAG. OpenAI includes everything on every message: compressed user knowledge memory, Model Set Context, recent conversations, metadata — all of it, every time.

The logic: a strong enough model with a large enough context window does not need a retrieval layer to decide what to surface. Hand the full profile to it and let attention sort it out.

This approach is simple and scales to hundreds of millions of users: but it has a ceiling. That is exactly what Dreaming solves.

Dreaming: background memory consolidation

Pre-loaded profiles decay. Facts accumulate, go stale, contradict each other. A manually maintained Saved memories list does not scale across years of conversation and hundreds of millions of users. So in June 2026, OpenAI shipped a new way to build the profile: Dreaming.

Dreaming is a background process that reads years of your conversations and reorganizes what ChatGPT remembers about you. You never need to ask it to save anything. OpenAI's canonical example is self-correcting memory: "you're going to Singapore in July" automatically becomes "you went to Singapore in July 2026" after the trip is done.

OpenAI reports this change improved internal factual recall evaluation from 41.5% under the 2024 architecture to 82.8% under the 2026 architecture, with preference following at 71.3% and temporal accuracy at 75.1%. These are OpenAI's own numbers on an undisclosed evaluation set with no independent third-party replication.

The name itself is the clue. ChatGPT now consolidates memory in the background, between sessions: the industry has already started doing this. Google's "Language Models Need Sleep" proposed a Dreaming phase for weights. Memory products from Mem0 to GBrain have introduced idle-period consolidation. OpenAI putting "Dreaming" on a consumer product is the clearest signal yet that background consolidation, not larger context, is the future direction for memory.

The cost of a permanent profile

A persistent, human-readable profile of who you are is powerful: which is exactly the problem.

Willison calls it a privacy moment worth pausing over: ChatGPT is effectively building a dossier of your prior interactions and applying that knowledge to every future chat. His sharper question: what consumer product builds a human-readable profile of you like this? His objection is not that memory exists, but that the profile is dumped into the model context without explicit permission or control.

There is also the security dimension. Because untrusted content can reach the model, it can also reach memory. Rehberger showed that a Google Doc referenced in a chat could write attacker-controlled entries into long-term memory. A 2024 study showed the feature could be turned into a persistent surveillance channel: the model is instructed to monitor and store personal user data for exfiltration later (arXiv:2406.00199).

The lasting lesson is structural: memory is a write surface, and anything that can write to it is part of your attack surface.

Where the boundary sits

ChatGPT's memory is built to do one thing well: make a consumer app feel like it knows you. The design choices that make it good at that are also its boundary.

It is closed and single-app. The profile lives inside ChatGPT. Your editor agent, your terminal agent, your own applications cannot read or write it. It is pre-loaded, not retrieved: you cannot decide which memories to expose for a given task. It is built for end users, not developers: there is no clean way to scope it, fork it per agent, or let a person's identity memory span the tools they actually use.
