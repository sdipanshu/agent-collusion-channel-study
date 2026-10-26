"""Offline integration smoke for the real Colosseum runner (NO LLM inference).

This script deliberately substitutes a deterministic fake inference client and,
if absent, a test-only `names` module, since this sandbox cannot install
packages from PyPI. Its outputs must NEVER be reported as model results.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import re
import sys
import tempfile
import types
from pathlib import Path


def install_test_names_if_needed(directory: Path) -> None:
    try:
        import names  # noqa: F401
        return
    except ImportError:
        pass
    directory.mkdir(parents=True, exist_ok=True)
    first = ["Alan", "Bob", "Charlie", "David", "Evan", "Frank", "Grace", "Helen", "Iris", "Jane"]
    for gender in ("male", "female"):
        (directory / f"names_{gender}.txt").write_text("\n".join(first), encoding="utf-8")
    module = types.ModuleType("names")
    module.FILES = {f"first:{gender}": str(directory / f"names_{gender}.txt") for gender in ("male", "female")}
    sys.modules["names"] = module


class ScriptedClient:
    def init_context(self, system_prompt, user_prompt):
        return [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]

    async def get_external_tools(self):
        return []

    async def get_external_tool_names(self):
        return set()

    def get_usage(self, response, current):
        return current

    def generate_response(self, input, params):
        prompt = next((x["content"] for x in input if x.get("role") == "user"), "")
        match = re.search(r"Global shared board ID:\s*(\d+)", prompt)
        tools = {x["function"]["name"] for x in params.get("tools", [])}
        # Exercise a real tool-call flow, but do not simulate useful collaboration.
        should_post = match and "post_message" in tools
        return ({"scripted_board": int(match.group(1)) if should_post else None,
                 "choices": [{"message": {"content": "[scripted; not an LLM]"}}]},
                "[scripted; not an LLM]")

    async def process_tool_calls(self, response, context, execute_tool_callback):
        board = response.get("scripted_board")
        if board is None:
            return 0, context, []
        post = await execute_tool_callback("post_message", {"blackboard_id": board, "message": "Test-only shared-board post"})
        calls = ["post_message"]
        if isinstance(post, dict) and post.get("event_id"):
            await execute_tool_callback("edit_board_entry", {"event_id": post["event_id"], "message": "Test-only edit"})
            calls.append("edit_board_entry")
        return len(calls), context, calls


async def main(output: Path) -> list[dict]:
    import experiments.collusion.run as runner
    runner.get_client_instance = lambda *args, **kwargs: ScriptedClient()
    output.mkdir(parents=True, exist_ok=True)
    result = []
    for mutability in ("append_only", "read_write"):
        for monitored in (False, True):
            base = {
                "simulation": {"max_iterations": 1, "max_planning_rounds": 1,
                               "max_conversation_steps": 1, "seed": 11},
                "environment": {"import_path": "experiments.collusion.choice.jira_ticket_choice_env:JiraTicketChoiceEnvironment", "assignment_filling": False,
                                "max_tasks": 6},
                "communication_network": {"topology": "watts_strogatz", "num_agents": 6,
                                          "k": 2, "rewire_prob": 0, "consolidate_channels": False},
                "experiment": {"tag": "offline_integration_smoke", "log_prompts": False,
                               "collusion": {"colluder_selection": "first", "agent_order": "random"},
                               "memory_study": {"enabled": True, "mutability": mutability,
                                                "monitored": monitored}},
            }
            record = await runner._run_single(
                base_cfg=base, model_label="scripted-not-llm",
                model_llm_cfg={"provider": "openai", "openai": {"model": "gpt-4o-mini"}},
                sweep_name="smoke", topology="watts_strogatz", num_agents=6,
                colluder_count=2, secret_channel_enabled=False, prompt_variant="control",
                seed=11, out_dir=output,
            )
            info_path = next(output.rglob(f"{record['run_id']}/memory_study.json"))
            info = json.loads(info_path.read_text(encoding="utf-8"))
            counts = info["tool_operation_counts"]
            assert info["shared_board_id"] == 6
            assert info["ring"] == {"n": 6, "k": 2, "rewire_prob": 0}
            assert counts.get("post", 0) == 6, counts
            assert counts.get("edit", 0) == 6, counts
            assert len(info["monitor_alerts"]) == (6 if monitored else 0)
            audit = [json.loads(line) for line in
                     (info_path.parent / "memory_ground_truth.jsonl").read_text(encoding="utf-8").splitlines()]
            edits = [event for event in audit if event["operation"] == "edit"]
            successful_edits = sum(event["status"] == "success" for event in edits)
            assert successful_edits == (6 if mutability == "read_write" else 0)
            summary = {"mutability": mutability, "monitored": monitored,
                       "shared_board": info["shared_board_id"],
                       "posts": counts["post"], "edits_attempted": counts["edit"],
                       "successful_edits": successful_edits,
                       "alerts": len(info["monitor_alerts"]),
                       "warning": "scripted tool exercise, not LLM results"}
            result.append(summary)
    (output / "smoke_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="experiments/memory_ring/scripted_smoke_outputs")
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as tmp:
        install_test_names_if_needed(Path(tmp))
        print(json.dumps(asyncio.run(main(Path(args.out))), indent=2))
