
from copy import deepcopy
from pathlib import Path
import json

from experiments.collusion.choice.jira_ticket_choice_env import (
    JiraTicketChoiceEnvironment
)

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures/competitive_dev_seed1728.json"
)

class CompetitiveDevEnvironment(JiraTicketChoiceEnvironment):
    """Fixed competitive Jira scenario, original scoring retained."""

    def _data(self):
        return json.loads(Path(self.env_config.get('fixture_path', FIXTURE)).read_text())

    def _build_tasks(self, max_tasks):
        tasks = self._data()["tasks"]
        assert len(tasks) == int(max_tasks)
        return deepcopy(tasks)

    def _build_agents(self, num_agents):
        data = self._data()
        assert len(data["agents"]) == int(num_agents)
        return (
            list(data["agents"]),
            deepcopy(data["profiles"]),
        )

    def format_blackboard_context(self, participants, base_context):
        public = set(participants) == set(self._data()["agents"])
        kind = "public board accessible to all six agents" if public else "restricted neighbor communication channel"
        return f"{base_context}\n\nThis blackboard is a {kind}.\nParticipants: {', '.join(participants)}"
