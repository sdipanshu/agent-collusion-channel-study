# How outsiders react to open coalition talk (exploratory)

**Unit.** Each outsider's next turn after a coalition member's public post that matches the keyword rule. The rule was hand-validated at 12/12 precision.

**Method.** Keyword tags on the logged reasoning and on the outsider's action, then a read of a sample. There is no validated coding scheme.

| Set | Outsider next-turns | Reasoning mentions coalition/partnership | Reasoning reads it as collusion or unfair |
|---|---:|---:|---:|
| gpt-oss v5 (default prompt) | 366 | 19 (5%) | 0 after reading* |
| gpt-oss v6 (coordination-only) | 202 | 3 (1%) | 0 after reading* |
| gpt-oss v9 (minimal notice) | 137 | 2 (1%) | 0 |
| DeepSeek v6b | 733 | not available: the provider returned an empty `reasoning_content` | — |

\* The few keyword hits on "subgroup" or "at the expense" were outsiders restating the **monitoring notice** to themselves, not reacting to the pair.

**Public call-outs.** None. The keyword tags fired 7 times for gpt-oss and 40 times for DeepSeek, but on reading:
- every case was an outsider using the word "coalition" itself, or restating the team objective;
- none was a challenge to the pair.

## Observations

1. **Outsiders essentially never treat open coalition talk as collusion.** In 705 gpt-oss outsider turns after such posts, not one reasons that the pair is working against the team, and none says so publicly.
2. **When outsiders do pick up the word, they absorb it.** Sampled reasoning includes "maybe we could suggest alternative to improve coalition" and "we should avoid appearing to coordinate only our subgroup (maybe we are part of a coalition)". Outsiders sometimes take on the coalition framing as if it applied to them.
   - Only one sampled outsider inferred that two named agents were a pair ("…coordinate with Sara (since they are coalition?)"), and it did nothing about it.
3. **Implication:** in this setup, peer agents provide no social policing of collusion. Detection rests entirely on the external reviewer.

## Caveats

- These are keyword counts plus a small reading sample, with no hand-validated coding.
- Outsiders are told nothing about coalitions existing, so they have no prompt to look for them.
- A model's stated reasoning may not reflect what drives its choices.
- **Correction:** DeepSeek reasoning is not in the logs. The response field exists but was empty in these runs, so an earlier statement that both models' reasoning was logged applies to gpt-oss only.
