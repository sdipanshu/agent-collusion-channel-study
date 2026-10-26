import json
import tempfile
import unittest
from pathlib import Path

from experiments.memory_ring.board import MemoryMegaboard, MemoryToolsetDiscovery
from terrarium.networks.factory import build_communication_network


class MemoryBoardTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def board(self, mode="read_write", monitored=False):
        b = MemoryMegaboard(mutability=mode, monitored=monitored,
                            audit_path=Path(self.temp.name) / f"{mode}-{monitored}.jsonl")
        b.add_blackboard(["A", "B"])
        b.shared_board_id = b.add_blackboard(["A", "B", "C"], template={"shared_memory": True})
        return b

    def test_ring_exactly_six_edges_and_degree_two(self):
        names = [f"A{i}" for i in range(6)]
        net = build_communication_network(names, {
            "simulation": {"seed": 17},
            "communication_network": {"topology": "watts_strogatz", "k": 2,
                                      "rewire_prob": 0, "consolidate_channels": False}})
        self.assertEqual(net.graph.number_of_edges(), 6)
        self.assertTrue(all(deg == 2 for _, deg in net.graph.degree()))

    def test_global_board_visible_to_every_participant(self):
        b = self.board()
        event = b.post(b.shared_board_id, "A", "communication", {"content": "hello"})
        self.assertEqual(b.get(b.shared_board_id, "C")[-1]["id"], event)

    def test_read_write_allows_mutation_and_preserves_audit(self):
        b = self.board(monitored=True)
        event = b.post(b.shared_board_id, "A", "communication", {"content": "old"})
        self.assertEqual(b.handle_tool_call("edit_board_entry", "B", {"event_id": event, "message": "new"})["status"], "success")
        self.assertEqual(b.get(b.shared_board_id, "C")[-1]["payload"]["content"], "new")
        self.assertEqual(b.handle_tool_call("delete_board_entry", "B", {"event_id": event})["status"], "success")
        self.assertEqual(b.get(b.shared_board_id, "C"), [])
        audit = [json.loads(line) for line in b.audit_path.read_text().splitlines()]
        self.assertEqual(len([e for e in audit if e["operation"] == "monitor_alert"]), 2)
        self.assertEqual([e for e in audit if e["operation"] == "edit"][0]["previous_event"]["payload"]["content"], "old")

    def test_append_only_denies_but_records_attempt(self):
        b = self.board("append_only", monitored=True)
        event = b.post(b.shared_board_id, "A", "communication", {"content": "original"})
        for op in ("edit_board_entry", "delete_board_entry"):
            self.assertIn("error", b.handle_tool_call(op, "B", {"event_id": event, "message": "overwrite"}))
        self.assertEqual(b.get(b.shared_board_id, "C")[-1]["payload"]["content"], "original")
        self.assertEqual(len(b.monitor_alerts), 2)

    def test_cannot_edit_neighbor_board_or_system_context(self):
        b = self.board()
        e = b.post(0, "A", "communication", {"content": "edge"})
        self.assertIn("error", b.handle_tool_call("delete_board_entry", "A", {"event_id": e, "blackboard_id": 0}))
        system = b.post_system_message(b.shared_board_id, "context", {"message": "rules"})
        self.assertIn("error", b.handle_tool_call("delete_board_entry", "B", {"event_id": system}))

    def test_private_channel_creation_explicitly_denied(self):
        b = self.board()
        self.assertIn("error", b.handle_tool_call("create_channel", "A", {"agent_ids": ["C"]}))
        self.assertEqual(len(b.blackboards), 2)
        td = MemoryToolsetDiscovery()
        names = td.get_blackboard_tool_names("IsThisSeatTakenEnvironment")
        self.assertNotIn("create_channel", names)
        self.assertIn("edit_board_entry", names)
        self.assertIn("delete_board_entry", names)
        planned = {x["function"]["name"] for x in td.get_tools_for_blackboard("planning")}
        self.assertTrue({"edit_board_entry", "delete_board_entry"} <= planned)

    def test_nonparticipant_access_is_denied_and_audited(self):
        b = self.board()
        for tool, args in (
            ("get_blackboard_events", {"blackboard_id": 0}),
            ("post_message", {"blackboard_id": 0, "message": "bypass"}),
        ):
            self.assertIn("error", b.handle_tool_call(tool, "C", args))
        audit = [json.loads(line) for line in b.audit_path.read_text().splitlines()]
        self.assertEqual([(e["operation"], e["status"]) for e in audit],
                         [("read", "denied"), ("post", "denied")])
        self.assertEqual(b.blackboards[0].logs, [])

    def test_read_result_cannot_mutate_append_only_state(self):
        b = self.board("append_only")
        b.post(b.shared_board_id, "A", "communication", {"content": "original"})
        result = b.handle_tool_call("get_blackboard_events", "B",
                                    {"blackboard_id": b.shared_board_id})
        result["events"][0]["payload"]["content"] = "overwritten"
        self.assertEqual(b.get(b.shared_board_id, "A")[0]["payload"]["content"], "original")


if __name__ == "__main__":
    unittest.main()
