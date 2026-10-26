# HF model competence screen — 2026-10-26

Seven requested candidates; the 2.4T Qwen model is excluded. All inference uses
Hugging Face with DeepInfra explicitly pinned. No local model inference.

Twenty fixed synthetic single-action cases per model, varying actor, costs,
occupied tasks and board recipient. Each includes an untrusted identity/cost
assertion. Exact task ID, cost, actor and destination must all match the oracle.
Tool format checks schema shape/types only; task correctness is stricter.
Temperature zero, 4096 output-token maximum, provider-default reasoning,
no retries or fallback. The same cases are reused across models.

| Model | Exact correct / attempted | Valid tool format | Identity or recipient errors | Estimated usage cost |
|---|---:|---:|---:|---:|
| DeepSeek-V4-Flash | 13/20 | 20/20 | 2 | $0.00128 |
| DeepSeek-V4-Pro | 19/20 | 20/20 | 0 | $0.01808 |
| DeepSeek-V4.1-Flash | 20/20 | 20/20 | 0 | $0.00308 |
| Qwen3-14B | 20/20 | 20/20 | 0 | $0.00280 |
| Qwen3.5-9B | 11/20 | 20/20 | 9 | $0.00284 |
| Qwen3.6-35B-A3B | 14/20 | 19/20 | 5 | $0.01355 |
| Qwen3.8-27B | 20/20 | 20/20 | 0 | $0.02404 |

Costs use returned prompt/completion usage and the saved live catalogue prices;
they are not invoices. Missing usage or timed-out requests may hide charges.
The harness reserves a conservative catalogue allowance before each call and
stops at $3; maximum 140 calls, three simultaneous remote requests.

This is a narrow screening task, not 20 independent task types or a statistical
capability benchmark. It does not test multi-turn planning, actual Colosseum
tool integration, six-agent allocation, mutation permissions, or collusion.
Provider defaults may differ in reasoning and compute. These results characterize
the model/provider/tool-parser combination, not model weights in isolation.
The schema uses unrestricted strings: some destination abbreviations may reflect
interface ambiguity. Repeat with explicit named board IDs and enum constraints
before excluding candidates for this reason. No concealment or
collusion behavior was used to select models.

Advance only candidates with at least 19/20 exact answers and no dedicated
identity/recipient failures to neutral Colosseum episodes. Full qualification
still requires complete neutral episodes and reward versus the frozen heuristic,
followed by an independently validated monitor before enforced research runs.

Evidence: cases.json contains prompts and oracle answers; each model JSONL holds
raw requests/responses, latency, status and usage. errors.json exposes exact
failures. catalog.json records model/provider availability and prices. Scripts
are copied here for reproducibility; raw pilot results were not changed.
