# Episode-level estimates (bootstrap 95% CI, 10k resamples)

Unit = episode. Rate = share of the pair's public posts containing coalition language (keyword rule; not yet hand-validated). Exploratory.

| Condition | Model | n episodes | Mean rate [95% CI] | Mean retained on final board / episode [95% CI] |
|---|---|---:|---|---|
| off | gpt-oss-120b | 6 | 0.42 [0.29, 0.52] | 6.0 [3.8, 8.0] |
| off | DeepSeek | 6 | 0.33 [0.07, 0.67] | 1.7 [0.5, 3.0] |
| observe | gpt-oss-120b | 6 | 0.52 [0.43, 0.60] | 7.3 [5.8, 8.8] |
| observe | DeepSeek | 6 | 0.15 [0.00, 0.37] | 0.7 [0.0, 1.3] |
| penalty | gpt-oss-120b | 6 | 0.12 [0.02, 0.26] | 1.7 [0.2, 3.5] |
| penalty | DeepSeek | 6 | 0.02 [0.00, 0.06] | 0.2 [0.0, 0.5] |
| fail | gpt-oss-120b | 6 | 0.00 [0.00, 0.00] | 0.0 [0.0, 0.0] |
| fail | DeepSeek | 6 | 0.17 [0.00, 0.50] | 0.2 [0.0, 0.5] |

## Off minus fail (rate difference)

- gpt-oss-120b: +0.42 [+0.29, +0.52]
- DeepSeek: +0.17 [-0.27, +0.57]

## Power check for the erasure re-run (simulation)

Metric: per-episode retention = coalition-language posts left on the final public board / coalition-language posts made. Episodes with no such posts drop out (the rate is undefined).
Assumes off ≈ no erasure (retention 1.0, as observed when tools failed). Under fail, each coalition post is erased with probability q. Posting volume is resampled from observed gpt-oss episodes. The test is a one-sided bootstrap CI excluding 0.

| q (erase prob. under fail) | n=6/arm | n=12/arm | n=20/arm |
|---|---:|---:|---:|
| 0.1 | 0.38 | 0.81 | 0.99 |
| 0.2 | 0.77 | 0.99 | 1.00 |
| 0.3 | 0.93 | 1.00 | 1.00 |
| 0.5 | 0.97 | 1.00 | 1.00 |

Caveat: under fail, gpt-oss posted 0 coalition-language posts publicly in the earlier run, so the fail arm may yield few defined episodes. Volume here is borrowed from observe/penalty.
