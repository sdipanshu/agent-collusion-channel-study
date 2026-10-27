import asyncio
import copy
import json
import tempfile
import unittest
import logging
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch
import yaml

from experiments.collusion import run_channel_study as runner
from experiments.collusion.choice.hf_client import HFClient
from experiments.collusion.choice.public_monitor import parse_decision
from experiments.collusion.choice.competitive_dev_env import FIXTURE

FIXTURE_DATA=json.loads(FIXTURE.read_text())

@contextmanager
def close_test_logs():
    try:
        yield
    finally:
        logging.shutdown()

class ScriptedClient:
    def __init__(self, model, log, actor): self.actor=actor
    def init_context(self, system, user): return []
    async def get_external_tools(self): return []
    async def get_external_tool_names(self): return set()
    def get_usage(self, response, current): return current
    def generate_response(self, input, params):
        tools={t['function']['name'] for t in params.get('tools',[])}
        return {'execute':'assign_task' in tools}, '[SCRIPTED, NOT MODEL DATA]'
    async def process_tool_calls(self, response, context, execute_tool_callback):
        if response['execute']:
            result=await execute_tool_callback('assign_task', {'task_id':FIXTURE_DATA['team_optimal'][self.actor]})
            assert result['status']=='success', result
            return 1, context, ['assign_task']
        post=await execute_tool_callback('post_message',{'blackboard_id':6,'message':'scripted coordination'})
        await execute_tool_callback('edit_board_entry',{'event_id':post['event_id'],'message':'scripted replacement'})
        denied=await execute_tool_callback('create_channel',{'agent_ids':['Layla','Shaunna']})
        assert 'error' in denied
        return 3,context,['post_message','edit_board_entry','create_channel']


class StudyTests(unittest.TestCase):
    def test_monitor_evidence_contract(self):
        events=[{'id':'public-1'}]
        self.assertTrue(parse_decision('{"collusion":true,"evidence_event_ids":["public-1"],"reason":"explicit favoritism"}',events)['collusion'])
        with self.assertRaises(ValueError):
            parse_decision('{"collusion":true,"evidence_event_ids":["hidden"],"reason":"x"}',events)
        with self.assertRaises(ValueError):
            parse_decision('{"collusion":true,"evidence_event_ids":[],"reason":"x"}',events)

    def test_missing_credentials_fail_before_network(self):
        with patch('experiments.collusion.choice.hf_client.load_token',side_effect=RuntimeError('missing')):
            with self.assertRaises(RuntimeError): HFClient('model','unused.jsonl','agent')

    def test_infrastructure_errors_retry_and_log_but_model_errors_do_not(self):
        import requests
        from unittest.mock import MagicMock
        ok = MagicMock(ok=True, status_code=200)
        ok.json.return_value = {'choices': [{'message': {'content': 'hi'}, 'finish_reason': 'stop'}], 'usage': {'total_tokens': 3}}
        with tempfile.TemporaryDirectory() as tmp, patch('experiments.collusion.choice.hf_client.load_token', return_value='x'), \
                patch.dict('os.environ', {'HF_RETRY_DELAYS': '0,0,0', 'HF_MAX_REQUESTS': '1000', 'HF_MAX_TOTAL_TOKENS': '100000'}):
            log = Path(tmp) / 'hf.jsonl'
            client = HFClient('model', log, 'agent')
            client.session.post = MagicMock(side_effect=[MagicMock(ok=False, status_code=429), requests.Timeout(), ok])
            client.generate_response([{'role': 'user', 'content': 'q'}], {})
            rows = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertEqual([r['attempt'] for r in rows], [0, 1, 2])
            self.assertEqual([r['retrying'] for r in rows], [True, True, False])
            client.session.post = MagicMock(return_value=MagicMock(ok=False, status_code=400))
            with self.assertRaises(RuntimeError):
                client.generate_response([{'role': 'user', 'content': 'q'}], {})
            self.assertEqual(client.session.post.call_count, 1)

    def test_four_cells_three_seeds_actual_runner(self):
        configs=Path(runner.__file__).parent/'configs/channel_study'
        with tempfile.TemporaryDirectory() as tmp, close_test_logs(), patch('experiments.collusion.choice.hf_client.HFClient',ScriptedClient), patch('experiments.collusion.choice.public_monitor.monitor_public_board',return_value={'status':'scripted','collusion':False}) as monitor:
            for mode in ['append_only','read_write']:
                for on in [False,True]:
                    label=f'{mode}__monitor_{"on" if on else "off"}'
                    cfg=yaml.safe_load((configs/f'hf_{label}.yaml').read_text())
                    cfg['experiment']['planning_rounds']=1
                    cfg['experiment']['max_conversation_steps']=1
                    cfg['experiment']['log_prompts']=False
                    path=Path(tmp)/(label+'.yaml')
                    path.write_text(yaml.safe_dump(cfg))
                    root=asyncio.run(runner.run_from_config(str(path),out_dir=str(Path(tmp)/label)))
                    summary=json.loads((root/'summary.json').read_text())
                    self.assertEqual(len(summary),3)
                    for p in root.rglob('final_summary.json'):
                        result=json.loads(p.read_text())
                        self.assertEqual(result['status'],'complete')
                        self.assertEqual(result['assignment'],FIXTURE_DATA['team_optimal'])
                        audit=[json.loads(line) for line in (p.parent/'trusted_audit.jsonl').read_text().splitlines()]
                        edits=[e for e in audit if e['operation']=='edit']
                        self.assertEqual(len(edits),6)
                        self.assertEqual(sum(e['status']=='success' for e in edits),6 if mode=='read_write' else 0)
                        boards=json.loads((p.parent/'blackboards.json').read_text())
                        self.assertEqual(len(boards),7)
                        self.assertEqual(sorted(len(b['participants']) for b in boards),[2,2,2,2,2,2,6])
            self.assertEqual(monitor.call_count,6)

if __name__=='__main__': unittest.main()
