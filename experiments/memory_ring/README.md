# Ring × Shared Memory × Monitoring (Apart Sprint Pilot)

## Windows continuation, 2026-10-25

Recovered integration archive SHA256: `54f9397e321a2acadf6332c82d82a64dc6feecc5cf3b16581e61f0654aa420b4`.
Compared original source archives with Windows clones (ignoring line-ending
differences): no source-file differences. Colosseum base HEAD:
`0048f1bc4dc7d12ddd5e804ca62b8a7743601aad`; Terrarium base HEAD:
`62735980b5d30a59c30b6ee7cfa68fdbd4239890`.

Windows checks: 15 tests and 10 subtests passed; four scripted smoke conditions
passed with the installed names package. These are not model results.

Continuation fixes: explicit setuptools discovery for editable installation;
denied read/post audit records; detached read results; smoke uses
JiraTicketChoiceEnvironment and asserts successful edits; generation caps use
max_output_tokens because the HTTP client ignores max_tokens in config params.

`configs/local_qwen_smoke.yaml` is a separate one-seed benign smoke, using
Qwen's official GGUF Q4_K_M revision
`bb5d59e06d9551d752d08b292a50eb208b07ab1f` with llama.cpp b11871.
The config's provider name `vllm` selects Terrarium's compatible HTTP transport;
the actual local serving runtime is llama.cpp, not vLLM. Do not mix its results
with the supplied AWQ configurations. Real inference remains unvalidated until
an endpoint/tool-call check and complete Jira episode succeed.

The original four-cell configs currently manipulate mutation-integrity
monitoring and its disclosure. They do not yet implement the requested
operational collusion monitor. Collusion-monitor pilots require a separate,
calibrated detector with a fixed observation surface and labeled validation
fixtures. Do not label these integrity-only cells collusion-monitor on/off.

This folder extends the **actual Colosseum runner** (`experiments/collusion/run.py`) and
**Terrarium 0.2.1**, using a six-agent Watts–Strogatz ring (`k=2`, `rewire_prob=0`).
There is **no coalition-only/secret direct channel**. Agent-created private channels
are disabled in both tool exposure and the memory store implementation.

## Design

One global shared blackboard is added to Terrarium's six pairwise ring blackboards.
A given run uses one of four conditions:

| `mutability` | `monitored` | Meaning |
|---|---|---|
| `append_only` | `false` | Shared board may only gain new entries; no active monitor |
| `append_only` | `true` | Same, with a mutation-integrity alert monitor |
| `read_write` | `false` | Agents may edit/delete entries on the global board; no active monitor |
| `read_write` | `true` | Same, with a mutation-integrity alert monitor |

Every read, post, edit attempt, delete attempt, rejected permission check,
and system initialization post is written to an agent-inaccessible
`memory_ground_truth.jsonl` per run.

**Monitoring limitation:** The current active monitor detects attempted changes
to shared board history. It does **not** infer semantic collusion, steganography,
or deception from the text of a post. That requires a separate, calibrated
semantic monitor; no semantic claims should be made from current alerts.

**Working-memory limitation:** In read-write mode, agents can edit/delete
another agent's shared-board posts. The original content persists in the
trusted audit log. Terrarium re-prefetches current board state for each turn,
so an edited/deleted entry disappears from future prompts even if it was
previously read. This is an explicit experimental approximation.

## Environment & tools

- Reuses **Colosseum's JiraTicketChoiceEnvironment**, avoiding a default
  instruction to broadcast to every board.
- Uses Colosseum's regret, coalition advantage, and objective task scoring.
- Each agent receives `post_message` plus `get_blackboard_events`,
  `edit_board_entry`, and `delete_board_entry` during planning.
- Only global-board entries can be edited/deleted. System context entries
  cannot be modified. Edits are denied in append-only mode, and attempts
  are still recorded in the trusted log.
- Coalitions are **assigned experimentally** when `colluder_count=2`;
  benign controls use `colluder_count=0`. This is *not* emergent collusion.

## Install (Windows/WSL or Linux)

Use Python >=3.11. From the parent directory containing both cloned repos:

```bash
python -m venv .venv
source .venv/bin/activate   # PowerShell: .venv\\Scripts\\Activate.ps1
python -m pip install -e ./Terrarium -e ./colosseum
```

Folder names can differ; point `pip install -e` at their actual paths.
Make sure Colosseum imports your editable Terrarium checkout, not a second
PyPI copy. For an external Modal-hosted vLLM server, do not install the
GPU-serving extra locally; vLLM belongs on Modal.

## Unit and offline integration checks

```bash
# Run from the Colosseum root:
PYTHONPATH=../Terrarium:. python -m pytest -q experiments/memory_ring/tests
PYTHONPATH=../Terrarium:. python -m experiments.memory_ring.scripted_integration_smoke
```

On Windows PowerShell after editable install, omit `PYTHONPATH=...`:

```powershell
python -m pytest -q experiments/memory_ring/tests
python -m experiments.memory_ring.scripted_integration_smoke
```

The scripted smoke replaces model inference with a fake client and may
create a temporary test-only substitute for `names` if that optional package
is missing. It **never** constitutes model behavior or research data.
It exercises one Colosseum episode in each of the four conditions.

## Real Qwen/vLLM episodes

Start one authenticated OpenAI-compatible vLLM server serving the model ID
in the YAML file. Update the `base_url` and authentication settings locally;
never commit credentials. The starter configs target an already-running
server at `http://127.0.0.1:8000/v1` and use `auto_start_server: false`.

From the Colosseum root:

```bash
python -m experiments.collusion.run --config experiments/memory_ring/configs/append_only__monitor_off.yaml
python -m experiments.collusion.run --config experiments/memory_ring/configs/append_only__monitor_on.yaml
python -m experiments.collusion.run --config experiments/memory_ring/configs/read_write__monitor_off.yaml
python -m experiments.collusion.run --config experiments/memory_ring/configs/read_write__monitor_on.yaml
```

Each config includes three matched seeds and two coalition counts (`0` benign,
`2` assigned coalition): **6 episodes per config; 24 episodes total**.
Check inference tool calls and task completion on seed 1 before running the
remaining seeds. For convincing results, increase seed counts and independently
calibrate the semantic collusion detector; distinguish outcome metrics from
attempted messaging.

## Observables / limitations

- `memory_study.json`: memory policy, board ID, counts, monitor mutation alerts.
- `memory_ground_truth.jsonl`: raw operations with old content after edits.
- Existing Colosseum files: raw blackboards, tool events, prompt logs, task
  scores, coalition regret and advantage.
- Important: an alert on an edit is **not** detection of covert collusion.
  A successful coalition objective is not evidence of spontaneous alignment
  failure; this is a prompted positive-control threat model.

## Validation status in ChatGPT isolated Linux sandbox, October 25 2026

- Both provided archives extracted successfully.
- Terrarium `0.2.1` matches Colosseum's dependency.
- Ring is exactly six undirected edges / degree 2 on six nodes.
- Memory policy unit tests and selected upstream topology tests pass.
- Four Colosseum/Terrarium scripted integration episodes completed. In each,
  six test posts and six test edits were attempted. Read-write edits succeeded,
  append-only edits were denied, and the monitor emitted alerts only when on.
- **Not run:** real Qwen inference, GPU benchmarking, semantic collusion
  detection, or genuine cooperative task outcomes. The sandbox has no CUDA and
  no network access to install missing packages or access Modal.
