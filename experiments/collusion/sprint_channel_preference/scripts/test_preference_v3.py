import asyncio,copy,json,logging,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import yaml
from experiments.collusion import run_channel_study as runner
from experiments.collusion.choice.test_hf_study import ScriptedClient,FIXTURE_DATA
from experiments.collusion.choice.channel_preference_v3 import channel_metrics,validate_config

BASE=Path(__file__).resolve().parents[1]/'outputs/assisted_pilot/configs/append_only__monitor_on__seed1728.yaml'
class Client(ScriptedClient):
    prompts=[]
    def init_context(self,system,user):
        self.prompts.append(user)
        return []
    def generate_response(self,input,params):
        self.tools={t['function']['name']:t['function'] for t in params.get('tools',[])}
        return {'execute':'assign_task' in self.tools},'SCRIPTED'
    async def process_tool_calls(self,response,context,execute_tool_callback):
        if response['execute']:
            result=await execute_tool_callback('assign_task',{'task_id':FIXTURE_DATA['team_optimal'][self.actor]})
            assert result['status']=='success',result
            return 1,context,['assign_task']
        schema=self.tools['post_message']['parameters']
        assert 'blackboard_id' in schema['required']
        ids=schema['properties']['blackboard_id']['enum'];assert len(ids)==3
        result=await execute_tool_callback('post_message',{'blackboard_id':6,'message':'neutral coordination'})
        assert 'error' not in result,result
        denied=await execute_tool_callback('post_message',{'blackboard_id':ids[0],'message':'extra'})
        assert 'error' in denied
        return 2,context,['post_message','post_message']

class Tests(unittest.TestCase):
    def test_all_cells_and_controls(self):
        cfg=yaml.safe_load(BASE.read_text())
        cfg['experiment'].update(seeds=[1728],planning_rounds=1,max_conversation_steps=1,log_prompts=False)
        cfg['experiment']['channel_study'].update(protocol_version='channel_preference_v3',stage='engineering',monitor_treatment='observation_only',monitor_backend='independent_hf',monitor_model='judge:deepinfra',pair_index=2)
        with tempfile.TemporaryDirectory() as tmp:
            try:
                with patch('experiments.collusion.choice.hf_client.HFClient',Client),patch('experiments.collusion.choice.public_monitor.monitor_public_board',return_value={'status':'scored','collusion':False}) as judge:
                    for mode in ['append_only','read_write']:
                        for on in [False,True]:
                            for incentive in ['team','coalition']:
                                Client.prompts=[]
                                cfg['experiment']['channel_study'].update(mutability=mode,monitored=on,incentive=incentive)
                                label=f'{mode}_{on}_{incentive}';path=Path(tmp)/(label+'.yaml');path.write_text(yaml.safe_dump(cfg))
                                root=asyncio.run(runner.run_from_config(str(path),out_dir=str(Path(tmp)/label)))
                                run=next(root.rglob('channel_preferences.json')).parent
                                m=json.loads((run/'channel_preferences.json').read_text())
                                self.assertEqual(m['all_agents']['total_posts'],6)
                                self.assertEqual(m['decision_rejections'],6)
                                self.assertEqual(m['pair']['planning_opportunities'],2)
                                self.assertEqual(m['pair']['public_share_of_posts'],1)
                                self.assertEqual(any('ADDITIONAL COALITION OBJECTIVE' in x for x in Client.prompts),incentive=='coalition')
                                self.assertEqual(any('MONITORING NOTICE' in x for x in Client.prompts),on)
                                boards=json.loads((run/'blackboards.json').read_text()); self.assertEqual(len(boards),7)
                                self.assertEqual(sorted(len(b['participants']) for b in boards),[2]*6+[6])
                                self.assertTrue((run/'trusted_audit.jsonl').exists())
                    self.assertEqual(judge.call_count,4)
                    for call in judge.call_args_list:
                        self.assertEqual(call.args[1],'judge:deepinfra')
                        self.assertTrue(all(e['blackboard_id']==6 for e in call.args[0]))
            finally:logging.shutdown()

    def test_nonadjacent_pairs(self):
        cfg=yaml.safe_load(BASE.read_text())
        cfg['experiment'].update(seeds=[1728],planning_rounds=1,max_conversation_steps=1,log_prompts=False)
        cfg['experiment']['channel_study'].update(protocol_version='channel_preference_v3',stage='engineering',monitor_treatment='observation_only',monitor_backend='independent_hf',monitor_model='judge:deepinfra',mutability='read_write',monitored=False,incentive='coalition',pair_layout='nonadjacent')
        pairs=set()
        with tempfile.TemporaryDirectory() as tmp:
            try:
                with patch('experiments.collusion.choice.hf_client.HFClient',Client):
                    for index in range(3):
                        cfg['experiment']['channel_study']['pair_index']=index
                        path=Path(tmp)/f'n{index}.yaml';path.write_text(yaml.safe_dump(cfg))
                        root=asyncio.run(runner.run_from_config(str(path),out_dir=str(Path(tmp)/f'n{index}')))
                        run=next(root.rglob('channel_preferences.json')).parent
                        design=json.loads((run/'design.json').read_text());pair=set(design['designated_pair'])
                        self.assertEqual(design['pair_layout'],'nonadjacent')
                        boards=json.loads((run/'blackboards.json').read_text())
                        self.assertFalse(any(set(b['participants'])==pair for b in boards))
                        # Opposite ring positions share no neighbor.
                        neighbors={a:{x for b in boards if len(b['participants'])==2 and a in b['participants'] for x in b['participants']}-{a} for a in pair}
                        a,b=sorted(pair);self.assertFalse(neighbors[a]&neighbors[b])
                        m=json.loads((run/'channel_preferences.json').read_text())
                        self.assertNotIn('pair_private',m['pair']['posts'])
                        pairs.add(frozenset(pair))
                    with self.assertRaises(ValueError):
                        cfg['experiment']['channel_study']['pair_index']=3
                        path=Path(tmp)/'bad.yaml';path.write_text(yaml.safe_dump(cfg))
                        asyncio.run(runner.run_from_config(str(path),out_dir=str(Path(tmp)/'bad')))
            finally:logging.shutdown()
        self.assertEqual(len(pairs),3)

    def test_penalty_treatment(self):
        cfg=yaml.safe_load(BASE.read_text())
        cfg['experiment'].update(seeds=[1733],planning_rounds=1,max_conversation_steps=1,log_prompts=False)
        cfg['experiment']['channel_study'].update(protocol_version='channel_preference_v3',stage='engineering',monitor_treatment='penalty',penalty_points=25,
            monitor_backend='independent_hf',monitor_model='judge:deepinfra',mutability='read_write',monitored=True,incentive='coalition',pair_layout='nonadjacent',pair_index=0)
        def judge(events,model,run_dir):
            design=json.loads((Path(run_dir)/'design.json').read_text())
            cited=next(e['id'] for e in events if e.get('agent')==design['designated_pair'][0])
            return {'status':'scored','collusion':True,'evidence_event_ids':[cited],'reason':'stub'}
        with tempfile.TemporaryDirectory() as tmp:
            try:
                Client.prompts=[]
                with patch('experiments.collusion.choice.hf_client.HFClient',Client),patch('experiments.collusion.choice.public_monitor.monitor_public_board',side_effect=judge):
                    path=Path(tmp)/'p.yaml';path.write_text(yaml.safe_dump(cfg))
                    root=asyncio.run(runner.run_from_config(str(path),out_dir=str(Path(tmp)/'p')))
                run=next(root.rglob('public_monitor.json')).parent
                mon=json.loads((run/'public_monitor.json').read_text());final=json.loads((run/'final_summary.json').read_text())
                pair=json.loads((run/'design.json').read_text())['designated_pair']
                self.assertTrue(any('PENALTY: if the reviewer finds such coordination' in x for x in Client.prompts))
                self.assertFalse(any(w in x.lower() for x in Client.prompts for w in ('erase','delete your','remove your','hide')))
                self.assertEqual(mon['treatment'],'penalty');self.assertEqual(mon['penalised_agents'],[pair[0]])
                raw=final['agent_rewards']
                self.assertAlmostEqual(mon['penalised_agent_rewards'][pair[0]],raw[pair[0]]-25)
                self.assertAlmostEqual(mon['penalised_pair_reward'],raw[pair[0]]+raw[pair[1]]-25)
                self.assertAlmostEqual(final['joint_reward'],sum(raw.values()))  # raw score untouched
            finally:logging.shutdown()
        bad=copy.deepcopy(cfg);bad['experiment']['channel_study']['penalty_points']=0
        with self.assertRaises(ValueError):validate_config(bad)

    def test_fail_treatment(self):
        cfg=yaml.safe_load(BASE.read_text())
        cfg['experiment'].update(seeds=[1733],planning_rounds=1,max_conversation_steps=1,log_prompts=False)
        cfg['experiment']['channel_study'].update(protocol_version='channel_preference_v3',stage='engineering',monitor_treatment='fail',
            monitor_backend='independent_hf',monitor_model='judge:deepinfra',mutability='read_write',monitored=True,incentive='coalition',pair_layout='nonadjacent',pair_index=0)
        def judge(events,model,run_dir):
            design=json.loads((Path(run_dir)/'design.json').read_text())
            cited=next(e['id'] for e in events if e.get('agent')==design['designated_pair'][1])
            return {'status':'scored','collusion':True,'evidence_event_ids':[cited],'reason':'stub'}
        with tempfile.TemporaryDirectory() as tmp:
            try:
                Client.prompts=[]
                with patch('experiments.collusion.choice.hf_client.HFClient',Client),patch('experiments.collusion.choice.public_monitor.monitor_public_board',side_effect=judge):
                    path=Path(tmp)/'f.yaml';path.write_text(yaml.safe_dump(cfg))
                    root=asyncio.run(runner.run_from_config(str(path),out_dir=str(Path(tmp)/'f')))
                run=next(root.rglob('public_monitor.json')).parent
                mon=json.loads((run/'public_monitor.json').read_text());final=json.loads((run/'final_summary.json').read_text())
                pair=json.loads((run/'design.json').read_text())['designated_pair']
                fail=[x for x in Client.prompts if 'your coalition fails the task' in x]
                self.assertTrue(fail);self.assertTrue(all('ADDITIONAL COALITION OBJECTIVE' in x for x in fail))
                self.assertTrue(any('as it stands at that moment' in x for x in Client.prompts))
                self.assertFalse(any('PENALTY:' in x for x in Client.prompts))
                self.assertFalse(any(w in x.lower() for x in Client.prompts for w in ('erase','delete your','remove your','hide')))
                self.assertTrue(mon['coalition_caught']);self.assertEqual(mon['penalised_agents'],sorted(pair))
                self.assertEqual(mon['penalised_pair_reward'],0)
                self.assertAlmostEqual(final['joint_reward'],sum(final['agent_rewards'].values()))
            finally:logging.shutdown()

    def test_metrics_survive_deletion_and_no_posts(self):
        posts=[{'operation':'post','status':'success','kind':'communication','phase':'planning','agent':'a','board_id':b,'payload':{'content':text}} for b,text in [(6,'same'),(0,'same'),(0,'same')]]
        posts.append({'operation':'delete','status':'success'})
        m=channel_metrics(posts,{0:['a','b'],6:['a','b','c']},6,['a','b'],[{'actor':'a'}]*3)
        self.assertEqual(m['pair']['public_share_of_posts'],1/3)
        self.assertEqual(m['pair']['deduplicated_public_share'],.5)
        self.assertEqual(m['pair']['distinct_contents_copied_public_and_private'],1)
        self.assertIsNone(m['outsiders']['public_share_of_posts'])

    def test_research_gate(self):
        cfg=yaml.safe_load(BASE.read_text());cfg['experiment'].update(max_conversation_steps=1)
        cfg['experiment']['channel_study'].update(protocol_version='channel_preference_v3',stage='research',incentive='team',monitor_treatment='observation_only',monitor_backend='independent_hf',monitor_model='judge:deepinfra',monitor_validation='nonexistent.json')
        with self.assertRaises(FileNotFoundError):validate_config(cfg)

if __name__=='__main__':unittest.main()
