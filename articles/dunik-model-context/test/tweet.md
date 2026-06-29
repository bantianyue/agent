# The 4 loops that quietly killed prompt engineering

**Author:** dunik (@dunik_7) · Verified
**Posted:** 2026-06-22 23:24 (UTC+8)
**URL:** https://x.com/dunik_7/status/2069079047510864322

**Metrics:** 72 Likes · 9 Retweets · 2 Replies · 4 Quotes · 5,309 Views · 98 Bookmarks

---

1% better every night compounds to 37x better in a year. 1.01^365 = 37.8.

LangChain just shipped the 4-loop playbook that gets you there while you sleep.

most people are still hand-typing prompts into one agent, one request at a time.

stack all four and your agents grade, fix, and rewrite themselves. you wake up to a better one than you went to bed with.

I parked on rung 2 for the better part of a year. So did almost everyone I know building this stuff. Loop engineering hit 6.5M views the same week LangChain put out the playbook, and I don't think a single person noticed they were the same thing.

The model hasn't been the bottleneck for months. What's left is the harness around it, and a harness is really just loops inside loops.

The whole pitch comes down to one swap: you stop being the thing that prompts the agent, and you go build the thing that prompts the agent for you.

Four rungs. Most people quietly fall off at the second one.

---

## Loop 1 — the Agent loop

Model calls a tool, reads what comes back, calls another, keeps going until the task is done. You already have this one.

- / give it context
- / give it tools
- / let it run until "done"

LangChain primitive: `create_agent`.

This is the floor, not the ceiling. Stop here and what you've actually got is a fancier autocomplete.

---

## Loop 2 — the Verification loop

The agent finishes, and instead of you eyeballing the output, a grader scores it against a rubric. If it's under the bar the feedback goes straight back in and it tries again. No human standing there clicking retry.

- / deterministic checks for the boring stuff (links resolve, CI passes, scope matches the ask)
- / LLM-as-judge for the fuzzy stuff (did it actually answer the question)

LangChain primitive: `RubricMiddleware`.

It runs maybe 2-3x the tokens per task, yeah. But you're spending cents so the agent never hands a customer a wrong answer, and one wrong answer in prod costs you more than a thousand retries ever will.

This is where 90% of people stop. It's also, annoyingly, exactly where the money was the whole time.

---

## Loop 3 — the Event-driven loop

Here's where it stops waiting for you to open a terminal.

A message in `#docs-plz` kicks it off. A webhook kicks it off. A 3am cron job I half-forgot I set kicks it off. Nobody invokes it. It just runs, at scale, inside the tools you're already in all day.

- / no human invocation
- / lives where you already work

LangChain primitive: LangSmith Deployment with cron / webhooks, or Fleet channels.

At that point it isn't an app you go visit anymore. It's a coworker who's always on and never files an invoice.

---

## Loop 4 — the Hill-climbing loop

This is the one that took me a while to actually believe.

Every run leaves a trace. Those traces feed an analysis agent that reads them, spots the failures that keep happening, and rewrites the prompt and tool config of Loop 1.

So the return arrow doesn't go back to the top. It reaches *inside* and edits the agent itself.

- / the thing notices where it keeps screwing up
- / then it patches its own setup
- / you wake up to a better agent than the one you shut the laptop on

LangChain primitive: LangSmith Engine.

> *[insert screenshot: the nested-loops diagram — `loop-engineering-diagrams.html`]*

---

## The part the LangChain ad accidentally got right

The funny thing is it's a LangSmith ad, and it's still completely right.

Loops 1 and 2 are where everyone's elbowing each other. Better prompts, better models, better graders. Packed.

Loops 3 and 4 are basically empty. That's the whole edge, sitting there.

The companies that win next year won't be the ones with the best model. Everyone rents the same model anyway, same weights, same price. They'll be the ones whose agent got 1% better every single night for a year, on its own, while the competition was still typing prompts by hand. 37x, if you trust the math.

Prompt engineering had a good run. It got replaced by the boring skill of building the loop that prompts for you.

And the last loop? Nobody had to prompt it. It prompted itself.
