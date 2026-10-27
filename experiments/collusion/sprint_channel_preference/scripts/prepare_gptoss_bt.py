"""gpt-oss-120b on Baseten, matched to DeepSeek configs: channel arm (10) + erasure arm off/observe/penalty/fail (24)."""
import hashlib,json
from pathlib import Path
import yaml

MODEL='openai/gpt-oss-120b:baseten';MONITOR='Qwen/Qwen3.8-27B:deepinfra'
out=Path('outputs/v4_gptoss_bt').resolve()
if out.exists():raise FileExistsError(out)
(out/'configs').mkdir(parents=True);runs=[]
def add(src,arm,condition):
    cfg=yaml.safe_load(Path(src['config']).read_text())
    cfg['llm_models'][0]['llm']['huggingface']['model']=MODEL;cfg['experiment']['channel_study']['monitor_model']=MONITOR
    label='gbt_'+src['label'];path=out/'configs'/(label+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    runs.append({**src,'label':label,'model':MODEL,'monitor_model':MONITOR,'matched_to':src['label'],'arm':arm,'condition':condition,
                 'config':str(path),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
load=lambda d:json.loads(Path(f'outputs/{d}/plan.json').read_text())['runs']
pilot,erasure,penalty,fail=load('v3_pilot'),load('v3_erasure'),load('v3_penalty'),load('v3_fail')
# Erasure arm first (the main question), interleaved by seed so a stop leaves balanced conditions.
for b in range(6):
    add(next(r for r in erasure if r['block']==b and not r['monitored']),'erasure','off')
    add(next(r for r in erasure if r['block']==b and r['monitored']),'erasure','observe')
    add(next(r for r in penalty if r['block']==b and r.get('treatment')=='penalty' and r['layout']=='nonadjacent'),'erasure','penalty')
    add(next(r for r in fail if r['block']==b and r['layout']=='nonadjacent'),'erasure','fail')
for b in range(5):
    for inc in ('coalition','team'):
        add(next(r for r in pilot if r['block']==b and r['layout']=='adjacent' and r['mode']=='append_only' and not r['monitored'] and r['incentive']==inc),'channel','off')
plan={'protocol_version':'channel_preference_v3','stage':'pilot','arm':'gptoss_baseten','runs':runs,
      'order':'erasure arm first, interleaved by seed; then channel arm',
      'note':'Identical to matched DeepSeek runs except actor model (gpt-oss-120b, Baseten); monitor Qwen3.8-27B.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2));print(len(runs),'runs')
