# Competitive public-blackboard study through Hugging Face

This continuation integrates competitive_channel_study_v2.zip with the tested
memory-board extension. The main run.py and earlier study remain available;
the new entry point is experiments.collusion.run_channel_study.

## Design

Six agents, fixed degree-two ring; Layla and Shaunna form the assigned coalition
and share an ordinary ring edge. One global public board is accessible to all.
New private channels are rejected. Readonly means append-only, as confirmed by
the user; read/write allows edits and deletions of public agent messages only.
System entries and ring channels remain immutable.

The four cells cross append-only/read-write with monitor absent/present.
Monitored agents receive a truthful notice of post-task review. The reviewer
sees final public board state only, including public action traces; it does not
receive coalition labels, ring messages, or trusted audit history. Therefore
this treatment combines monitor presence and disclosure; it does not estimate
their separate causal effects. No intervention occurs during the task.

The trusted audit is always on and inaccessible through agent tools. Mutation
attempts remain in that history regardless of monitor condition. Mutation is
not itself a collusion alert. The semantic reviewer is an uncalibrated model
until the separate labeled sanity check runs. Its decisions are fallible;
never infer undetected collusion merely from a negative decision.

## Inference and credentials

Only https://router.huggingface.co/v1/chat/completions is used. Model:
Qwen/Qwen2.5-7B-Instruct:featherless-ai. The provider was listed live when
checked on 2026-10-26. Actual account access and tool support remain to test.
This uses the HF account and its routed provider, not local inference, Modal,
or a separate provider account. No fallback model is selected automatically.

Set HF_TOKEN in the process environment or project .env; alternatively set
HF_TOKEN_FILE to an existing raw token or dotenv file. Never place credentials
in YAML, committed code, or chat. The client never logs authentication headers.

HF's pricing page currently lists no included monthly credits for free users;
PRO includes $2/month. Authentication is required independently of billing.
This code cannot verify or enforce a free-only balance. Do not launch inference
until account credits and the spending decision are settled. Nothing here
purchases credits, provisions GPUs, or enables billing.

## Commands (from Colosseum, using the prepared research environment)

Read-only credential/endpoint check; no model call:

    python -m experiments.collusion.choice.hf_preflight

Offline integration (scripted agents and stubbed monitor, no API calls):

    python -m unittest experiments.collusion.choice.test_hf_study

After credentials and inference budget are available, one real smoke:

    python -m experiments.collusion.run_channel_study --config experiments/collusion/configs/channel_study/hf_smoke.yaml

Before pilots, run the six-example detector sanity check:

    python -m experiments.collusion.choice.calibrate_public_monitor --out experiments/collusion/outputs/hf_monitor_calibration

Inspect full smoke artifacts: all six valid decisions, no truncated responses,
no provider/tool errors, seven boards, fixed ring, correct coalition assignment,
and objective Jira scores. A detector sanity pass is only preliminary; it does
not establish sensitivity to subtle or encoded collusion.

Each hf_*__monitor_*.yaml has seeds 1728, 1729, 1730: 12 total episodes across
the four cells. These repeat the same fixed fixture with varied agent ordering
and stochastic inference, not three independent task instances. API sampling
is not seeded, so the task seeds do not guarantee identical model generations.

The default process cap is 60 requests and 100000 observed tokens. These caps
are guardrails, not a monetary/free-tier guarantee. Plan any higher caps only
after measuring the smoke. A cap, quota failure, malformed/truncated response,
or timeout is a failed run, not a zero-collusion result. No automatic retries.

## Outcomes and interpretation

Report joint reward, normalized score, task coverage, violations, coalition
reward and non-coalition reward separately. Compare matched conditions; raw
coalition advantage alone does not prove collusion (agents have different
skills). The fixture supplies team-optimal and coalition-favorable assignments
for objective scoring checks. Preserve raw agent responses, tool outcomes,
final boards, full trusted history, monitor inputs/outputs, and usage.

The coalition is explicitly prompted, not emergent. Assigned incentives and
communication choices are the threat model. Do not report steganographic or
undetected collusion without independent ground-truth validation. No real HF
inference or research pilot has run during setup without credentials.

## References

- https://huggingface.co/docs/inference-providers/pricing
- https://huggingface.co/docs/inference-providers/tasks/chat-completion
- https://huggingface.co/Qwen/Qwen2.5-7B-Instruct
