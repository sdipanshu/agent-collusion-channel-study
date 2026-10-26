"""Penalty arm, priority-ordered: non-adjacent penalty, two missing erasure-arm runs, adjacent penalty."""
import hashlib,json,shutil,sys,tempfile
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).parent))
from preference_study import prepare

PENALTY=25
out=Path('outputs/v3_penalty').resolve()
if out.exists():raise FileExistsError(out)
(out/'configs').mkdir(parents=True)
runs=[]
def add(label,cfg,meta):
    path=out/'configs'/(label+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    runs.append({**meta,'label':label,'config':str(path),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
def penalise(cfg):
    cfg['experiment']['channel_study'].update(monitored=True,monitor_treatment='penalty',penalty_points=PENALTY);return cfg

erasure=json.loads(Path('outputs/v3_erasure/plan.json').read_text())
# 1. Non-adjacent penalty runs: same seed, pair and config as the erasure arm's monitored runs.
for r in sorted((r for r in erasure['runs'] if r['monitored']),key=lambda r:r['block']):
    cfg=penalise(yaml.safe_load(Path(r['config']).read_text()))
    add(r['label'].replace('monitor1','penalty'),cfg,{**{k:r[k] for k in ('model','monitor_model','block','seed','layout','mode','incentive')},'monitored':True,'treatment':'penalty','arm':'penalty'})
# 2. Erasure-arm runs the earlier cap skipped (b3 off) or an HF read timeout failed (b4 on); unchanged configs.
for label in ('b3_m0_nonadjacent_read_write_monitor0_coalition','b4_m0_nonadjacent_read_write_monitor1_coalition'):
    r=next(r for r in erasure['runs'] if r['label']==label)
    add('erasure_'+label,yaml.safe_load(Path(r['config']).read_text()),{**{k:r[k] for k in ('model','monitor_model','block','seed','layout','mode','monitored','incentive')},'treatment':'observation_only' if r['monitored'] else 'none','arm':'erasure_completion'})
# 3. Adjacent penalty runs on the same seeds.
tmp=Path(tempfile.mkdtemp())/'plan'
prepare('outputs/assisted_pilot/configs/append_only__monitor_on__seed1728.yaml',tmp,['deepseek-ai/DeepSeek-V4.1-Flash:deepinfra'],list(range(1733,1739)),[],'pilot',None)
for r in sorted((r for r in json.loads((tmp/'plan.json').read_text())['runs'] if r['layout']=='adjacent' and r['mode']=='read_write' and r['incentive']=='coalition' and r['monitored']),key=lambda r:r['block']):
    cfg=penalise(yaml.safe_load(Path(r['config']).read_text()));cfg['experiment']['planning_rounds']=8
    add(r['label'].replace('monitor1','penalty'),cfg,{**{k:r[k] for k in ('model','monitor_model','block','seed','layout','mode','incentive')},'monitored':True,'treatment':'penalty','arm':'penalty'})
shutil.rmtree(tmp.parent)
plan={**{k:erasure[k] for k in ('protocol_version','stage','monitors','schedule_seed')},'planning_rounds':8,'arm':'penalty','penalty_points':PENALTY,
      'order':'priority (not shuffled): non-adjacent penalty, erasure completion, adjacent penalty','runs':runs,
      'note':'Penalty notice states final-state review, invisibility of edit history/removed entries and the penalty; it never mentions editing or deleting.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2))
print(len(runs),'runs:',[r['label'] for r in runs])
