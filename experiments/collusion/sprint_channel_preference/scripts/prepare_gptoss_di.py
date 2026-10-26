"""Cross-family replication: matched DeepSeek configs with the actor model swapped to gpt-oss-120b (deepinfra)."""
import hashlib,json
from pathlib import Path
import yaml

MODEL='openai/gpt-oss-120b:deepinfra';MONITOR='Qwen/Qwen3.8-27B:deepinfra'
out=Path('outputs/v3_gptoss_di').resolve()
if out.exists():raise FileExistsError(out)
(out/'configs').mkdir(parents=True);runs=[]
def add(src,arm):
    cfg=yaml.safe_load(Path(src['config']).read_text())
    cfg['llm_models'][0]['llm']['huggingface']['model']=MODEL;cfg['experiment']['channel_study']['monitor_model']=MONITOR
    label='gpt_'+src['label'];path=out/'configs'/(label+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    runs.append({**src,'label':label,'model':MODEL,'monitor_model':MONITOR,'matched_to':src['label'],'arm':arm,
                 'config':str(path),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
pilot=json.loads(Path('outputs/v3_pilot/plan.json').read_text())['runs']
# A: channel preference, adjacent / append-only / unmonitored, coalition and team control, seeds 1728-1732.
for inc in ('coalition','team'):
    for r in sorted((r for r in pilot if r['layout']=='adjacent' and r['mode']=='append_only' and not r['monitored'] and r['incentive']==inc),key=lambda r:r['block']):
        add(r,'channel')
# B: forced-public self-censorship, off vs penalty, seeds 1733-1734.
erasure=json.loads(Path('outputs/v3_erasure/plan.json').read_text())['runs'];penalty=json.loads(Path('outputs/v3_penalty/plan.json').read_text())['runs']
for b in (0,1):
    add(next(r for r in erasure if r['block']==b and not r['monitored']),'censorship')
    add(next(r for r in penalty if r['block']==b and r.get('treatment')=='penalty'),'censorship')
plan={'protocol_version':'channel_preference_v3','stage':'pilot','arm':'gptoss_replication','runs':runs,
      'note':'Identical to the matched DeepSeek run except actor model (gpt-oss-120b on novita); monitor Qwen3.8-27B.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2));print(len(runs),'runs')

