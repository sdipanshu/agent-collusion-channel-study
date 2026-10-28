"""v6 DeepSeek arm and gate, re-frozen with read_tool: false (deviation 1 in PREREG_CONFIRM.md).
Configs are otherwise byte-for-byte the v6 DeepSeek configs; the unrun originals are kept for the record."""
import hashlib,json
from pathlib import Path
import yaml
for src,dst in (('v6_positive_control_deepseek','v6b_positive_control_deepseek'),('v6_confirm_deepseek','v6b_confirm_deepseek')):
    plan=json.loads(Path(f'outputs/{src}/plan.json').read_text());out=Path(f'outputs/{dst}').resolve()
    if out.exists():raise FileExistsError(out)
    (out/'configs').mkdir(parents=True);runs=[]
    for r in plan['runs']:
        cfg=yaml.safe_load(Path(r['config']).read_text());cfg['experiment']['channel_study']['read_tool']=False
        path=out/'configs'/(r['label']+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
        runs.append({**r,'read_tool':False,'config':str(path),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    plan.update(runs=runs,derived_from=src,deviation='read_tool removed: one generation per decision means read results are never seen')
    (out/'plan.json').write_text(json.dumps(plan,indent=2));print(out,len(runs))
