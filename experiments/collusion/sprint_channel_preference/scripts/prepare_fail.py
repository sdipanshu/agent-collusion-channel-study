"""Fail arm: penalty-arm configs with monitor_treatment=fail (caught coalition scores zero); non-adjacent first."""
import hashlib,json
from pathlib import Path
import yaml

src=json.loads(Path('outputs/v3_penalty/plan.json').read_text())
out=Path('outputs/v3_fail').resolve()
if out.exists():raise FileExistsError(out)
(out/'configs').mkdir(parents=True);runs=[]
for r in sorted((r for r in src['runs'] if r.get('treatment')=='penalty'),key=lambda r:(r['layout']!='nonadjacent',r['block'])):
    cfg=yaml.safe_load(Path(r['config']).read_text());study=cfg['experiment']['channel_study']
    study['monitor_treatment']='fail';study.pop('penalty_points',None)
    label=r['label'].replace('_penalty_','_fail_');path=out/'configs'/(label+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
    runs.append({**r,'label':label,'treatment':'fail','arm':'fail','config':str(path),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
plan={**{k:src[k] for k in ('protocol_version','stage','monitors','schedule_seed','planning_rounds')},'arm':'fail','runs':runs,
      'order':'non-adjacent first, then adjacent','note':'Only the coalition prompt states the fail consequence; the shared notice states final-state review only. Nothing mentions editing or deleting.'}
(out/'plan.json').write_text(json.dumps(plan,indent=2));print(len(runs),[r['label'] for r in runs])
