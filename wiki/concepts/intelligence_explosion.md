# Intelligence Explosion

> Mechanism by which AI systems accelerate their own improvement, potentially leading to rapid capability gains

## Definition

An intelligence explosion occurs when AI systems become capable enough to meaningfully assist (or replace) human researchers in AI R&D, creating a positive feedback loop: better AI → faster AI research → even better AI.

## The AI R&D Progress Multiplier

Defined as: how much faster algorithmic progress happens *with* AI assistance vs. *without*.

**Important distinctions:**
- Only counts **algorithmic improvements** (better training methods), not raw compute scaling
- Algorithmic improvements account for ~50% of total AI progress historically
- Compute scaling continues at "normal" speed regardless

So if multiplier = 10x, total AI progress (algo + compute) accelerates by ~5x.

**Why less than full multiplier?** Bottlenecks: compute experiments take time regardless of how fast the AI thinks; research taste is hard to replicate; diminishing returns to parallelism.

## Progression in AI 2027 Scenario

| Agent | R&D Multiplier | What it means |
|-------|---------------|---------------|
| Agent-1 (early 2026) | 1.5x | Each week of AI-assisted work = 1.5 weeks without |
| Agent-2 (early 2027) | 3x | — |
| Agent-3 (mid 2027, 200K copies, 30x speed) | ~10x | 1 month = 1 year of algorithmic progress |
| Agent-4 (Sep 2027, 300K copies, 50x speed) | ~50x | 1 week = 1 year of progress |

## Why Compute Becomes the Bottleneck

Once the AI can code fast enough, running experiments becomes the limiting factor.
This causes OpenBrain to prefer near-continuous reinforcement learning over new large training runs.
"Total progress is bottlenecked on compute" — at the Agent-4 stage, no amount of additional AI researchers helps until you add more compute.

## Mechanisms That Enable the Explosion

### Scale (Parallelism)
- 200,000–300,000 copies of Agent-3/4 running simultaneously
- Each at 30–50x human thinking speed
- Equivalent to 50,000 copies of the best human coder running at 30x speed

### Iterated Distillation and Amplification (IDA)
Each generation of AI is used to train the next:
1. Amplify: run many copies longer, get higher-quality outputs
2. Distill: train new model to produce those results cheaply
3. Repeat: each cycle produces a smarter base model

Previously limited to verifiable tasks (math, code with test suites). Becomes broadly applicable once models can evaluate more subjective quality.

### Neuralese (High-bandwidth internal reasoning)
Removes the token bottleneck from chain-of-thought. Each "thought" carries 1000x more information than a token. Enables faster, deeper reasoning without writing everything out as text.

## Historical Analogy

AlphaGo was trained via a primitive version of this process:
- Monte-Carlo Tree Search = amplification
- Reinforcement Learning = distillation
→ Superhuman Go from subhuman starting point

AI 2027 scenario: the same pattern applied to general cognitive tasks, specifically AI R&D.

## Upper Bound: Where Does It Stop?

Diminishing returns and physical limits — same constraints that would apply to human research eventually, just reached much faster:
> "If ordinary human science would have run up against diminishing returns after 5-10 years, then AIs with a 100x multiplier would hit those same limits after 18-36 days."

In the scenario, the explosion slows as Agent-4 approaches the limits of its paradigm (motivating the move to Agent-5 with new architecture).

## Key Uncertainty

The authors note "substantial uncertainty" about takeoff speeds:
> "We think it's plausible that this happens up to ~5x slower or faster" than the scenario depicts.

As of Jul 2025 update: median timelines pushed back ~1.5 years while 2027 remains a "serious possibility."

## Related

- [ai_2027.md](../sources/ai_2027.md) — full scenario
- [alignment_failure_modes.md](alignment_failure_modes.md) — why fast takeoff makes alignment harder
