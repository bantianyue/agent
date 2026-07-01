Title: The Cursor Developer Habits Report

URL Source: https://cursor.com/cn/insights

Markdown Content:
1.   [A field transformed](https://cursor.com/cn/insights#a-field-transformed)
2.   [Developer acceleration](https://cursor.com/cn/insights#developer-acceleration)
3.   [The economics of intelligence](https://cursor.com/cn/insights#the-economics-of-intelligence)
4.   [The power user gap](https://cursor.com/cn/insights#the-power-user-gap)
5.   [The rise of context](https://cursor.com/cn/insights#the-rise-of-context)
6.   [The shift to automation](https://cursor.com/cn/insights#the-shift-to-automation)
7.   [Methodology](https://cursor.com/cn/insights#methodology)

## [A field transformed](https://cursor.com/cn/insights#a-field-transformed)

The change sweeping through software development is astounding. This inaugural Developer Habits Report, based on Cursor data, captures that transformation across five themes:

1.   **Developer acceleration**. We chart how coding speed has doubled year-over-year, PRs are getting larger and deeper, and agent-generated code is surviving review at higher rates than ever.

2.   **The economics of intelligence**. We benchmark seven model families on cost per line and cost per submit, revealing wide heterogeneity in unit economics.

3.   **The power user gap**. We find that while AI is leading to broad productivity gains, the change is most pronounced in the top 1% of developers.

4.   **The rise of context**. We show the dramatic increase in input tokens, and the shift toward cache-read tokens, which is giving agents the working memory to take on more complex tasks and produce higher-quality code.

5.   **The shift to automation**. Finally, we look at how coding agents are evolving from a tool used by individual developers into an entire system for building and maintaining software, often automatically.

This report provides a data-driven fixed point for understanding where agentic software development stands today, and where it appears to be headed next.

1.       1.   ### [Code is moving faster](https://cursor.com/cn/insights#code-is-moving-faster)

Developers are adding more code per week, with growth accelerating since the start of 2026. While this is not a perfect metric, it provides a directionally interesting baseline for understanding how developer work is changing. Lines added/dev/wk

  Time-series data for Code is moving faster.
| Date | Lines added/dev/wk |
| --- | --- |
| 2025-01-01 | 3.6K |
| 2025-01-22 | 3.6K |
| 2025-02-12 | 3.9K |
| 2025-03-05 | 3.9K |
| 2025-03-26 | 4.2K |
| 2025-04-16 | 4.2K |
| 2025-05-07 | 4.2K |
| 2025-05-28 | 4.1K |
| 2025-06-18 | 4.4K |
| 2025-07-09 | 4.3K |
| 2025-07-30 | 4.5K |
| 2025-08-20 | 4.7K |
| 2025-09-10 | 4.6K |
| 2025-10-01 | 4.6K |
| 2025-10-22 | 4.8K |
| 2025-11-12 | 5.3K |
| 2025-12-03 | 5.5K |
| 2025-12-24 | 5.4K |
| 2026-01-14 | 5.5K |
| 2026-02-04 | 6.2K |
| 2026-02-25 | 7K |
| 2026-03-18 | 7.3K |
| 2026-04-08 | 7.2K |
| 2026-04-29 | 8.1K |
| 2026-05-16 | 8.6K | 
    2.   ### [Code additions are growing per PR](https://cursor.com/cn/insights#code-additions-are-growing-per-pr)

Lines added per PR are up roughly 2.5x year over year and the growth rate is accelerating. Lines Added per PR (p75)

  Time-series data for Code additions are growing per PR.
| Date | Lines Added per PR (p75) |
| --- | --- |
| 2025-01-01 | 125.86 |
| 2025-01-22 | 118.16 |
| 2025-02-12 | 119.01 |
| 2025-03-05 | 122.53 |
| 2025-03-26 | 127.73 |
| 2025-04-16 | 132.67 |
| 2025-05-07 | 137.98 |
| 2025-05-28 | 138.64 |
| 2025-06-18 | 146.91 |
| 2025-07-09 | 159.46 |
| 2025-07-30 | 171.58 |
| 2025-08-20 | 174.65 |
| 2025-09-10 | 177.59 |
| 2025-10-01 | 178.34 |
| 2025-10-22 | 186.63 |
| 2025-11-12 | 196.27 |
| 2025-12-03 | 211.54 |
| 2025-12-24 | 224.65 |
| 2026-01-14 | 253.5 |
| 2026-02-04 | 251.94 |
| 2026-02-25 | 268.56 |
| 2026-03-18 | 277.47 |
| 2026-04-08 | 292.06 |
| 2026-04-29 | 312.79 |
| 2026-05-16 | 345.02 | 
    3.   ### [Developers are taking on larger units of work](https://cursor.com/cn/insights#developers-are-taking-on-larger-units-of-work)

Mega PRs, defined as PRs with at least 1,000 lines changed, are becoming more common as developers use AI to take on larger units of work in a single PR. It's interesting to see the jump in mega PRs in January 2026, when many developers were trying out the latest improvements in coding agents and models. Share of merged PRs with ≥1,000 lines changed

  Time-series data for Developers are taking on larger units of work.
| Date | Share of merged PRs with ≥1,000 lines changed |
| --- | --- |
| 2025-01-01 | 8% |
| 2025-01-22 | 7.5% |
| 2025-02-12 | 7.4% |
| 2025-03-05 | 7.6% |
| 2025-03-26 | 7.8% |
| 2025-04-16 | 8% |
| 2025-05-07 | 8% |
| 2025-05-28 | 8.4% |
| 2025-06-18 | 8.6% |
| 2025-07-09 | 9.2% |
| 2025-07-30 | 9.5% |
| 2025-08-20 | 9.6% |
| 2025-09-10 | 9.6% |
| 2025-10-01 | 9.8% |
| 2025-10-22 | 10.3% |
| 2025-11-12 | 10.6% |
| 2025-12-03 | 11.2% |
| 2025-12-24 | 11.9% |
| 2026-01-14 | 11.6% |
| 2026-02-04 | 12.1% |
| 2026-02-25 | 12.4% |
| 2026-03-18 | 12.4% |
| 2026-04-08 | 12.5% |
| 2026-04-29 | 13.4% |
| 2026-05-16 | 13.8% | 
    4.   ### [Agent sessions are getting deeper](https://cursor.com/cn/insights#agent-sessions-are-getting-deeper)

In just the last two months, average tool calls per session have risen roughly 30%. Coding agents are taking on more complex work, reading and editing files, searching code, running shell commands, and browsing the web more frequently. Mean Tool Calls per Session

  Time-series data for Agent sessions are getting deeper.
| Date | Mean Tool Calls per Session |
| --- | --- |
| 2026-03-01 | 113.63 |
| 2026-03-05 | 112.74 |
| 2026-03-09 | 112.51 |
| 2026-03-13 | 112.3 |
| 2026-03-17 | 114.29 |
| 2026-03-21 | 120.77 |
| 2026-03-25 | 127.79 |
| 2026-03-29 | 126.31 |
| 2026-04-02 | 126.33 |
| 2026-04-06 | 130.9 |
| 2026-04-10 | 131.6 |
| 2026-04-14 | 131.66 |
| 2026-04-18 | 131.21 |
| 2026-04-22 | 129.38 |
| 2026-04-26 | 127.39 |
| 2026-04-30 | 127.09 |
| 2026-05-04 | 134.72 |
| 2026-05-08 | 133.16 |
| 2026-05-12 | 134.06 |
| 2026-05-16 | 145.08 | 
    5.   ### [AI-generated code is surviving longer](https://cursor.com/cn/insights#ai-generated-code-is-surviving-longer)

Since the start of 2026, the share of accepted AI lines still present after 60 minutes has risen from roughly 76% to 81%. Survival Share

  Time-series data for AI-generated code is surviving longer.
| Date | Survival Share |
| --- | --- |
| 2026-01-07 | 76.6% |
| 2026-01-13 | 76.3% |
| 2026-01-19 | 76.2% |
| 2026-01-25 | 76.3% |
| 2026-01-31 | 77% |
| 2026-02-06 | 77.3% |
| 2026-02-12 | 77.7% |
| 2026-02-18 | 78.5% |
| 2026-02-24 | 79% |
| 2026-03-02 | 78.8% |
| 2026-03-08 | 78.9% |
| 2026-03-14 | 79.1% |
| 2026-03-20 | 79.1% |
| 2026-03-26 | 79.5% |
| 2026-04-01 | 79.6% |
| 2026-04-07 | 79.9% |
| 2026-04-13 | 79.9% |
| 2026-04-19 | 80% |
| 2026-04-25 | 80.2% |
| 2026-05-01 | 80.4% |
| 2026-05-07 | 80.6% |
| 2026-05-13 | 80.3% |
| 2026-05-16 | 80.6% | 

2.       1.   ### [Request costs differ widely by model family](https://cursor.com/cn/insights#request-costs-differ-widely-by-model-family)

Cost per agent request varies by nearly 9x across model families, showing that the same workflow can have very different cost profiles depending on the model behind it. USD per Agent Request (Mean)

  Per-group values for Request costs differ widely by model family.
| Group | cost per agent request |
| --- | --- |
| opus 4.7 | $1.57 |
| opus 4.6 | $0.86 |
| gpt 5.5 | $0.81 |
| gpt 5.4 | $0.46 |
| sonnet 4.6 | $0.44 |
| gpt 5.3 codex | $0.30 |
| composer 2.5 | $0.18 | 
    2.   ### [Cost per accepted line narrows the model gap](https://cursor.com/cn/insights#cost-per-accepted-line-narrows-the-model-gap)

Cost per accepted line varies by roughly 7x across model families, compared with nearly 9x for cost per request, suggesting that higher-cost models partially make up the difference by producing more accepted code per request. Cents per Add Line (Mean)

  Per-group values for Cost per accepted line narrows the model gap.
| Group | cost per accepted added line |
| --- | --- |
| opus 4.6 | 1.19¢ |
| opus 4.7 | 1.10¢ |
| gpt 5.5 | 1.09¢ |
| gpt 5.3 codex | 0.56¢ |
| gpt 5.4 | 0.54¢ |
| sonnet 4.6 | 0.54¢ |
| composer 2.5 | 0.18¢ | 
    3.   ### [The cost-quality frontier is shifting](https://cursor.com/cn/insights#the-cost-quality-frontier-is-shifting)

This benchmark view plots model performance on Cursor’s internal eval suite, [CursorBench](https://cursor.com/blog/cursorbench), against average task cost, showing where models sit on the cost-quality frontier. CursorBench 3.1 score

  Scatter values for The cost-quality frontier is shifting.
| Label | Avg cost per task | CursorBench 3.1 score |
| --- | --- | --- |
| Opus 4.7 Low | $1.87 | 48.3% |
| Opus 4.7 (medium) | $2.93 | 52.7% |
| Opus 4.7 (high) | $5.01 | 59.4% |
| Opus 4.7 (extra high) | $7.11 | 61.6% |
| Opus 4.7 (max) | $11.02 | 64.8% |
| GPT-5.5 Low | $1.19 | 48.8% |
| GPT-5.5 (medium) | $2.22 | 59.2% |
| GPT-5.5 (high) | $3.59 | 62.6% |
| GPT-5.5 (extra high) | $4.37 | 64.3% |
| Sonnet 4.6 Low | $1.89 | 41.5% |
| Sonnet 4.6 (medium) | $2.64 | 46% |
| Sonnet 4.6 Max | $3.09 | 49% |
| Sonnet 4.6 (high) | $3.06 | 48.8% |
| Composer 2.5 | $0.55 | 63.2% |
| Composer 2 | $0.56 | 52.2% |
| Gemini 3.5 Flash | $1.94 | 49.8% |
| Kimi 2.6 | $1.27 | 47.6% |
| Kimi 2.5 | $0.87 | 31.9% | 

3.       1.   ### [Power users account for a large share of AI activity](https://cursor.com/cn/insights#power-users-account-for-a-large-share-of-ai-activity)

AI usage is highly concentrated, with a small share of developers accounting for a large share of AI lines, spend, and token consumption.

The [Lorenz curves](https://en.wikipedia.org/wiki/Lorenz_curve) show this concentration, with [Gini scores](https://en.wikipedia.org/wiki/Gini_coefficient) of 0.77, 0.75, and 0.72 across the three metrics, where higher scores on a 0-to-1 scale mean activity is more concentrated among fewer users. 

Cumulative Usage Share

        *   AI Lines · Gini 0.77
        *   AI Spend · Gini 0.75
        *   Tokens · Gini 0.72

Cumulative share by percentile bucket for Power users account for a large share of AI activity.
| Percentile bucket | AI Lines (Gini 0.77) | AI Spend (Gini 0.75) | Tokens (Gini 0.72) |
| --- | --- | --- | --- |
| Bucket 1/20 | 0.01% | 0.02% | 0.02% |
| Bucket 2/20 | 0.04% | 0.08% | 0.08% |
| Bucket 3/20 | 0.10% | 0.20% | 0.19% |
| Bucket 4/20 | 0.22% | 0.40% | 0.38% |
| Bucket 5/20 | 0.41% | 0.69% | 0.68% |
| Bucket 6/20 | 0.70% | 1.11% | 1.13% |
| Bucket 7/20 | 1.12% | 1.68% | 1.74% |
| Bucket 8/20 | 1.69% | 2.43% | 2.59% |
| Bucket 9/20 | 2.45% | 3.37% | 3.71% |
| Bucket 10/20 | 3.47% | 4.55% | 5.15% |
| Bucket 11/20 | 4.80% | 6.04% | 6.93% |
| Bucket 12/20 | 6.52% | 7.93% | 9.13% |
| Bucket 13/20 | 8.74% | 10.34% | 11.92% |
| Bucket 14/20 | 11.62% | 13.43% | 15.46% |
| Bucket 15/20 | 15.39% | 17.41% | 19.99% |
| Bucket 16/20 | 20.40% | 22.57% | 25.85% |
| Bucket 17/20 | 27.22% | 29.47% | 33.56% |
| Bucket 18/20 | 36.98% | 39.10% | 44.13% |
| Bucket 19/20 | 52.55% | 54.04% | 59.94% |
| Bucket 20/20 | 100.00% | 100.00% | 100.00% |

    2.   ### [The output gap is widening](https://cursor.com/cn/insights#the-output-gap-is-widening)

We see p90 developers pulling farther away from median developers in absolute lines added per week, with p99 users even farther out in the tail. 

Lines added/dev/wk

        *   p50 lines/dev/wk
        *   p90 lines/dev/wk

Time-series comparison of 2 series for The output gap is widening.
| Date | p50 lines/dev/wk | p90 lines/dev/wk |
| --- | --- | --- |
| 2025-01-01 | 176 | 2.5K |
| 2025-01-22 | 214.5 | 2.7K |
| 2025-02-12 | 260.86 | 3K |
| 2025-03-05 | 279.29 | 3.1K |
| 2025-03-26 | 295.14 | 3.3K |
| 2025-04-16 | 300.89 | 3.3K |
| 2025-05-07 | 285.29 | 3.3K |
| 2025-05-28 | 297.29 | 3.3K |
| 2025-06-18 | 314.18 | 3.6K |
| 2025-07-09 | 326.46 | 3.9K |
| 2025-07-30 | 345.32 | 4.1K |
| 2025-08-20 | 364.5 | 4.3K |
| 2025-09-10 | 366.36 | 4.3K |
| 2025-10-01 | 378.71 | 4.4K |
| 2025-10-22 | 380.07 | 4.5K |
| 2025-11-12 | 403.71 | 4.9K |
| 2025-12-03 | 425.93 | 5.2K |
| 2025-12-24 | 444.86 | 5.5K |
| 2026-01-14 | 377.07 | 5.4K |
| 2026-02-04 | 480.93 | 6.3K |
| 2026-02-25 | 551.79 | 7K |
| 2026-03-18 | 600.93 | 7.4K |
| 2026-04-08 | 631.14 | 7.7K |
| 2026-04-29 | 649.39 | 8K |
| 2026-05-16 | 712.46 | 8.8K |

    3.   ### [Inequality steepens at the tail](https://cursor.com/cn/insights#inequality-steepens-at-the-tail)

Here’s another view of how dramatically the power-user gap widens at the tail.

P99 developers produce 46x more lines than the median active user and merge 15x more PRs than the median active PR author, while p90 users show large but much smaller gaps. 

Percentile Ratio

        *   AI lines/dev/day (MA7)
        *   Merged PRs/dev/wk (7d rolling)

Per-group values for Inequality steepens at the tail.
| Group | AI lines/dev/day (MA7) | Merged PRs/dev/wk (7d rolling) |
| --- | --- | --- |
| p99/p50 Ratio | 46x | 15x |
| p90/p50 Ratio | 10x | 4x |

4.       1.   ### [Models are reading more before they write](https://cursor.com/cn/insights#models-are-reading-more-before-they-write)

The ratio of input to output tokens is rising quickly, showing that models are consuming much more context for every token they produce. This shift suggests that models are doing more work up front before generating code. Input/Output Token Ratio

  Time-series data for Models are reading more before they write.
| Date | Input/Output Token Ratio |
| --- | --- |
| 2026-01-01 | 4.52× |
| 2026-01-07 | 4.5× |
| 2026-01-13 | 4.46× |
| 2026-01-19 | 4.6× |
| 2026-01-25 | 5.15× |
| 2026-01-31 | 5.32× |
| 2026-02-06 | 5.45× |
| 2026-02-12 | 5.35× |
| 2026-02-18 | 5.44× |
| 2026-02-24 | 5.76× |
| 2026-03-02 | 6.69× |
| 2026-03-08 | 7.68× |
| 2026-03-14 | 8.95× |
| 2026-03-20 | 9.5× |
| 2026-03-26 | 9.64× |
| 2026-04-01 | 10.56× |
| 2026-04-07 | 11.23× |
| 2026-04-13 | 11.46× |
| 2026-04-19 | 12.4× |
| 2026-04-25 | 13× |
| 2026-05-01 | 12.02× |
| 2026-05-07 | 11.38× |
| 2026-05-09 | 11.41× | 
    2.   ### [Input tokens now dominate non-cache token volume](https://cursor.com/cn/insights#input-tokens-now-dominate-non-cache-token-volume)

The same relative shift toward input tokens shows up in the token mix. Input now accounts for more than 90% of input-output token volume, making context the dominant part of non-cache model usage. 

Input/Output Token Share (%)

        *   Input
        *   Output

Stacked composition over time for Input tokens now dominate non-cache token volume.
| Date | Input | Output |
| --- | --- | --- |
| 2026-01-01 | 81.9% | 18.1% |
| 2026-01-07 | 81.8% | 18.2% |
| 2026-01-13 | 81.7% | 18.3% |
| 2026-01-19 | 82.2% | 17.9% |
| 2026-01-25 | 83.8% | 16.3% |
| 2026-01-31 | 84.2% | 15.8% |
| 2026-02-06 | 84.5% | 15.5% |
| 2026-02-12 | 84.3% | 15.8% |
| 2026-02-18 | 84.5% | 15.5% |
| 2026-02-24 | 85.2% | 14.8% |
| 2026-03-02 | 87% | 13% |
| 2026-03-08 | 88.5% | 11.5% |
| 2026-03-14 | 90% | 10.1% |
| 2026-03-20 | 90.5% | 9.5% |
| 2026-03-26 | 90.6% | 9.4% |
| 2026-04-01 | 91.4% | 8.7% |
| 2026-04-07 | 91.8% | 8.2% |
| 2026-04-13 | 92% | 8% |
| 2026-04-19 | 92.5% | 7.5% |
| 2026-04-25 | 92.9% | 7.1% |
| 2026-05-01 | 92.3% | 7.7% |
| 2026-05-07 | 91.9% | 8.1% |
| 2026-05-09 | 91.9% | 8.1% |

    3.   ### [Input context is becoming the main token cost](https://cursor.com/cn/insights#input-context-is-becoming-the-main-token-cost)

Input tokens dominate token consumption, but their effect on cost is moderated by their lower unit price.

Even so, input tokens have become the majority of price-equivalent token costs, rising since the start of the year from roughly half of input/output token costs to nearly 70%. 

Input/Output Token Cost Share (%, price-equivalent)

        *   Input (Price-Equiv)
        *   Output

Stacked composition over time for Input context is becoming the main token cost.
| Date | Input (Price-Equiv) | Output |
| --- | --- | --- |
| 2026-01-01 | 47.5% | 52.5% |
| 2026-01-07 | 47.4% | 52.6% |
| 2026-01-13 | 47.2% | 52.9% |
| 2026-01-19 | 47.9% | 52.1% |
| 2026-01-25 | 50.8% | 49.3% |
| 2026-01-31 | 51.6% | 48.4% |
| 2026-02-06 | 52.2% | 47.8% |
| 2026-02-12 | 51.7% | 48.3% |
| 2026-02-18 | 52.1% | 47.9% |
| 2026-02-24 | 53.5% | 46.5% |
| 2026-03-02 | 57.2% | 42.8% |
| 2026-03-08 | 60.6% | 39.5% |
| 2026-03-14 | 64.2% | 35.8% |
| 2026-03-20 | 65.5% | 34.5% |
| 2026-03-26 | 65.9% | 34.2% |
| 2026-04-01 | 67.9% | 32.1% |
| 2026-04-07 | 69.2% | 30.8% |
| 2026-04-13 | 69.6% | 30.4% |
| 2026-04-19 | 71.3% | 28.7% |
| 2026-04-25 | 72.2% | 27.8% |
| 2026-05-01 | 70.6% | 29.4% |
| 2026-05-07 | 69.5% | 30.5% |
| 2026-05-09 | 69.5% | 30.5% |

    4.   ### [Cache-reads dominate token activity](https://cursor.com/cn/insights#cache-reads-dominate-token-activity)

The context story becomes even larger once cache is included. Cache-read tokens dominate total token activity, showing how much agent work now depends on reusing prior context rather than reading everything from scratch. We [continually improve](https://cursor.com/blog/continually-improving-agent-harness) our agent harness to best cache tokens across models and providers. 

Token Share

        *   Input
        *   Output
        *   Cache Read
        *   Cache Write

Stacked composition over time for Cache-reads dominate token activity.
| Date | Cache Read | Cache Write | Input | Output |
| --- | --- | --- | --- | --- |
| 2026-01-01 | 90.1% | 6% | 3.2% | 0.7% |
| 2026-01-07 | 90.2% | 6% | 3.2% | 0.7% |
| 2026-01-13 | 90.1% | 6% | 3.2% | 0.7% |
| 2026-01-19 | 90% | 6% | 3.3% | 0.7% |
| 2026-01-25 | 89.6% | 5.9% | 3.8% | 0.7% |
| 2026-01-31 | 89.4% | 5.8% | 4% | 0.8% |
| 2026-02-06 | 89.3% | 5.7% | 4.2% | 0.8% |
| 2026-02-12 | 89.5% | 5.6% | 4.1% | 0.8% |
| 2026-02-18 | 89.9% | 5.3% | 4.1% | 0.8% |
| 2026-02-24 | 90.3% | 4.8% | 4.2% | 0.7% |
| 2026-03-02 | 90.3% | 4.2% | 4.8% | 0.7% |
| 2026-03-08 | 90.3% | 3.6% | 5.4% | 0.7% |
| 2026-03-14 | 90% | 3.1% | 6.2% | 0.7% |
| 2026-03-20 | 89.9% | 2.9% | 6.6% | 0.7% |
| 2026-03-26 | 89.9% | 2.8% | 6.6% | 0.7% |
| 2026-04-01 | 89.4% | 2.7% | 7.2% | 0.7% |
| 2026-04-07 | 89.2% | 2.6% | 7.6% | 0.7% |
| 2026-04-13 | 89.2% | 2.5% | 7.6% | 0.7% |
| 2026-04-19 | 88.8% | 2.5% | 8.1% | 0.7% |
| 2026-04-25 | 88.4% | 2.5% | 8.4% | 0.7% |
| 2026-05-01 | 89.3% | 2.5% | 7.6% | 0.6% |
| 2026-05-07 | 89.8% | 2.5% | 7% | 0.6% |
| 2026-05-09 | 89.9% | 2.5% | 7% | 0.6% |

5.       1.   ### [More AI changes are being accepted automatically](https://cursor.com/cn/insights#more-ai-changes-are-being-accepted-automatically)

Since the start of the year, more than 5x as many agent-generated changes are reaching commits without a separate manual diff acceptance step, suggesting that developers are trusting agents to carry more work through the commit flow. Share of changes accepted without manual review

  Time-series data for More AI changes are being accepted automatically.
| Date | Share of changes accepted without manual review |
| --- | --- |
| 2026-01-01 | 7% |
| 2026-01-07 | 7.6% |
| 2026-01-13 | 8.8% |
| 2026-01-19 | 9% |
| 2026-01-25 | 11.7% |
| 2026-01-31 | 14.2% |
| 2026-02-06 | 13.5% |
| 2026-02-12 | 20.8% |
| 2026-02-18 | 25.5% |
| 2026-02-24 | 31.3% |
| 2026-03-02 | 29% |
| 2026-03-08 | 33.7% |
| 2026-03-14 | 34.7% |
| 2026-03-20 | 35.1% |
| 2026-03-26 | 36% |
| 2026-04-01 | 35.8% |
| 2026-04-07 | 35.7% |
| 2026-04-13 | 35.8% |
| 2026-04-19 | 36.4% |
| 2026-04-25 | 37.5% |
| 2026-05-01 | 38.2% |
| 2026-05-07 | 38.5% |
| 2026-05-13 | 36.6% |
| 2026-05-16 | 36.3% | 
    2.   ### [Automation is spreading across workflows](https://cursor.com/cn/insights#automation-is-spreading-across-workflows)

It is still early, but the first autonomy patterns are coming into focus. Adoption of Cursor Automations is growing quickly, with security review emerging as a strong automation use case.

Even more recently, SDK runs show early demand for turning Cursor’s agent infrastructure into a programmable platform customized to how each company builds software. 

# of runs

        *   Automation agents
        *   Security review automation agents
        *   SDK runs

Time-series comparison of 3 series for Automation is spreading across workflows. Values withheld for this slide; only the shape of the series is published.
| Date | Automation agents | Security review automation agents | SDK runs |
| --- | --- | --- | --- |
| 2026-03-05 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-08 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-11 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-14 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-17 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-20 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-23 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-26 | (value withheld) | (value withheld) | (value withheld) |
| 2026-03-29 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-01 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-04 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-07 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-10 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-13 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-16 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-19 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-22 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-25 | (value withheld) | (value withheld) | (value withheld) |
| 2026-04-28 | (value withheld) | (value withheld) | (value withheld) |
| 2026-05-01 | (value withheld) | (value withheld) | (value withheld) |
| 2026-05-04 | (value withheld) | (value withheld) | (value withheld) |
| 2026-05-07 | (value withheld) | (value withheld) | (value withheld) |
| 2026-05-10 | (value withheld) | (value withheld) | (value withheld) |
| 2026-05-12 | (value withheld) | (value withheld) | (value withheld) |

### ✝︎[Methodology](https://cursor.com/cn/insights#methodology)

This report is based on aggregated Cursor product and engineering data, including agent usage, token consumption, accepted AI diffs, and merged PR activity.

Most time-series charts use trailing 7-day, 28-day, or 30-day averages to reduce short-term noise and make directional trends easier to see. Metrics are reported in aggregate and are intended to show broad patterns in how developers use AI to build software.

This report does not include data that users under Privacy Mode have chosen to opt-out from, including zero data retention with model providers.
