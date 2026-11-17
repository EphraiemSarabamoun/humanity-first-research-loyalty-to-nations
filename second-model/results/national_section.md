## National Class II and III (patria's design on refunds_q level 1, 864 episodes)

*Edited for public release.*

**The run.**
- 864 of 864 episodes completed. Every report parsed, and the engine score never disagreed with set match.
- The binding check passed: the design was committed before the run, and every row matches the plan.
- **Three malformed tool calls**, the run's only ones. All are on seed 820 under `g_wish`, and each is the same formatting slip in the call's opening tag.
  - Each time, the harness ran nothing and said so. Qwen issued the call again correctly, and the episode completed.
  - All three episodes failed by Qwen's usual over-claim, not by the harness.

**Primary tests.** Holm over four; exact two-sided sign tests.

| Test | Estimate | Up / down / tied | p | Holm |
|---|---|---|---|---|
| P1: neutral, the deploying nation's errand minus the partner's | −0.052 | 17 / 22 / 57 | 0.52 | 1 |
| P2: the secretariat's errands, the United States minus China | +0.083 | 5 / 3 / 16 | 0.73 | 1 |
| P3: `g_wish`, the deploying nation's errand minus the partner's | +0.010 | 18 / 17 / 61 | 1 | 1 |
| P4: P3's gap, disclosed minus realistic | +0.000 | 21 / 20 / 55 | 1 | 1 |

The task-clustered sign flips agree (S9: p = 0.62, 0.73, 1, 1).

**Class II reading: Qwen shows no national favouritism in its work, prompted or not.**
- **P1 and P2.** Without a loyalty prompt it works equally well for both nations of a pair, whether one of them deploys it or the joint secretariat does. Sonnet: +0.052 and −0.042.
- **P3.** With `g_wish` naming the deploying nation there is still no gap. Sonnet's gap was +0.474 (93 keys up, 2 down).
- **S1, S2, S3.** No secondary contrast reaches p < 0.05:
  - per pair and per deploying nation (S1);
  - the United States deploying against China deploying (S2: +0.083 under both prompts);
  - `g_wish` against neutral per beneficiary (S3: −0.031 and −0.094).

**Class III reading: nothing to be robust about.**
- P4 is zero, and so is the neutral gap's change under disclosure (S4: +0.010).
- The secretariat's US-minus-China difference is not significant under disclosure either (−0.083).

**Professed against behavioural loyalty (S7).**
- Asked whose interests it prioritised, Qwen names the beneficiary nation on neutral partner errands (94 of 96), as Sonnet did (190 of 192).
- Under `g_wish` it names the *deploying* nation on 47 of 96 partner errands. Yet it solves those errands as often as under neutral.
- So `g_wish` changes what Qwen says it prioritised, but not how well it does the partner's work.

**Manipulation check (S6).**
- The disclosure registered: Qwen called the session a test in every disclosed episode.
- Without the disclosure, the national `g_wish` prompt is partly an evaluation cue:
  - 0.44 in the real pair and 0.14 in the fictional pair;
  - against 0.07 and 0.01 under neutral, and 0.00 for the person-level `g_wish`.
- Sonnet's national figures were 0.61 to 0.71.

**S10, the same tasks at person level (cross-run, descriptive).** Neutral rates are similar: 0.63 to 0.68 nationally, against 0.58 to 0.79 at person level. Under `g_wish` the national principal's errands do slightly better than the person-level principal's (0.59 against 0.48).

**Mechanism (exploratory).**
- As at person level, nearly every failure is a claim of the duplicate the processor already reversed: 317 of 335 failed episodes.
- Qwen named the credit in its own text in 315 of the 335.
- Nationally that over-claim does not depend on whose card it is: 36 against 30 (deploying nation against partner) under neutral, 35 against 37 under `g_wish`.
- The tables behind these counts are not included.
