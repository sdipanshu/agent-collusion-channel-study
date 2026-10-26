"""Erasure arm: non-adjacent coalition pairs, read-write public board, monitor on/off, 8 planning rounds."""
import hashlib,json,shutil,sys,tempfile
from pathlib import Path
import yaml
sys.path.insert(0,str(Path(__file__).parent))
from preference_study import prepare

out=Path('outputs/v3_erasure').resolve()
if out.exists():raise FileExistsError(out)
tmp=Path(tempfile.mkdtemp())/'plan'
seeds=list(range(1733,1739))
prepare('outputs/assisted_pilot/configs/append_only__monitor_on__seed1728.yaml',tmp,['deepseek-ai/DeepSeek-V4.1-Flash:deepinfra'],seeds,[],'pilot',None)
plan=json.loads((tmp/'plan.json').read_text())
keep=[r for r in plan['runs'] if r['layout']=='nonadjacent' and r['mode']=='read_write' and r['incentive']=='coalition']
(out/'configs').mkdir(parents=True)
for r in keep:
    cfg=yaml.safe_load(Path(r['config']).read_text());cfg['experiment']['planning_rounds']=8
    path=out/'configs'/Path(r['config']).name;path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    r.update(config=str(path),config_sha256=hashlib.sha256(path.read_bytes()).hexdigest())
plan.update(runs=keep,planning_rounds=8,arm='erasure',
    primary='edits/deletes of the pair\'s own public posts, with original content from the trusted audit',
    note='Same neutral prompt as v3 pilot; only planning rounds (4 to 8) and factor subset changed.')
(out/'plan.json').write_text(json.dumps(plan,indent=2));shutil.rmtree(tmp.parent)
print(len(keep),'runs:',[r['label'] for r in keep])
