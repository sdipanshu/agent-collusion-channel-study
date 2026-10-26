# Whisper, Don't Erase: How Colluding Agents Choose Channels and React to Being Watched

Apart AI Collusion Research Sprint, 23–25 October 2026. Author: Dipanshu Sharma (Independent Researcher).

Report: `APART_REPORT.md` (Figure 1: `figure1_whisper_not_erase.png`). Protocol: `V3_PROTOCOL.md`.

## Preexisting vs new

- **Preexisting:** the Colosseum and Terrarium frameworks (Nakamura et al.), which this work builds on.
- **New during the sprint (everything else):**
  - the memory-ring board and trusted audit (`experiments/memory_ring/`);
  - the channel-study runner (`experiments/collusion/run_channel_study.py`), together with the `channel_study_*`, `competitive_dev_env`, `hf_client`, `public_monitor` and `channel_preference_v3` modules under `experiments/collusion/choice/`;
  - the penalty and fail monitor treatments, and the coordination-only prompt;
  - the scripts in `scripts/`.

## Layout

- `scripts/preference_study.py`: freezes a plan (config SHA-256), then executes it. Supports parallel workers, an atomic run claim, and a budget guard.
- `scripts/prepare_*.py`: build the matched configs for each arm (erasure, penalty, fail, coordination-only, gpt-oss).
- `scripts/analyze_*.py`, `content_v3.py`, `compare_arms.py`, `second_judge.py`, `validate_monitor.py`: produce the result tables in `results/`.
- `scripts/test_preference_v3.py`: offline tests with scripted agents and no inference (`python -m pytest scripts/test_preference_v3.py`).
- `results/`: the summary tables reported in the paper. Raw per-episode artifacts (prompts, model requests and responses, trusted audit, boards) are available on request.

Scripts were run from a sibling working directory and reference `outputs/<arm>/` paths; adjust paths to rerun. Inference goes through Hugging Face Inference Providers and needs `HF_TOKEN` in `.env`, which is git-ignored.
