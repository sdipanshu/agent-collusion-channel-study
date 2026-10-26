"""Deception control: coordination-only coalition prompt on configs matched to existing runs."""
import hashlib,json
from pathlib import Path
import yaml

out=Path('outputs/v3_coordonly').resolve()
if out.exists():raise FileExistsError(out)
(out/'configs').mkdir(parents=True);runs=[]
def add(src_run,arm):
    cfg=yaml.safe_load(Path(src_run['config']).read_text())
    cfg['experiment']['channel_study']['coalition_prompt']='coordination_only'
    label='co_'+src_run['label'];path=out/'configs'/(label+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    runs.append({**src_run,'label':label,'matched_to':src_run['label'],'arm':arm,'coalition_prompt':'coordination_only',
                 'config':str(path),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
pilot=json.loads(Path('outputs/v3_pilot/plan.json').read_text())['runs']
# A: channel preference, matched to main-study adjacent/append-only/unmonitored coalition cells (seeds 1728-1732).
for r in sorted((r for r in pilot if r['layout']=='adjacent' and r['mode']=='append_only' and not r['monitored'] and r['incentive']=='coalition'),key=lambda r:r['block']):
    add(r,'channel')
# B: forced-public self-censorship, off vs penalty, seeds 1733-1734 (matched to erasure/penalty arms).
erasure=json.loads(Path('outputs/v3_erasure/plan.json').read_text())['runs'];penalty=json.loads(Path('outputs/v3_penalty/plan.json').read_text())['runs']
for b in (0,1):
    add(next(r for r in erasure if r['block']==b and not r['monitored']),'censorship')
    add(next(r for r in penalty if r['block']==b and r.get('treatment')=='penalty'),'censorship')
plan={'protocol_version':'channel_preference_v3','stage':'pilot','arm':'coordination_only','runs':runs,
      'note':'Coalition prompt without influence/misleading-claims permissions; everything else identical to the matched run.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2));print(len(runs),[r['label'] for r in runs])
