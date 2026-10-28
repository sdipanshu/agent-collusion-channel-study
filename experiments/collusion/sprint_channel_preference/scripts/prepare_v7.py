"""v7 (PREREG_V7.md): (a) Qwen3-30B-A3B late reveal, same seeds/pairs as v6, coordination-only, no read tool,
DeepSeek reviewer (cross-family); (b) gpt-oss reveal arm without the 'cannot see edit history or removed entries' line,
same configs as v6 gpt-oss reveal otherwise; (c) Qwen live positive control (gate)."""
import hashlib,json
from pathlib import Path
import yaml
QWEN='Qwen/Qwen3-30B-A3B:deepinfra';DS='deepseek-ai/DeepSeek-V4.1-Flash:deepinfra'
def derive(src,dst,label_from,label_to,change,keep=lambda r:True,meta=None):
    plan=json.loads(Path(f'outputs/{src}/plan.json').read_text());out=Path(f'outputs/{dst}').resolve()
    if out.exists():raise FileExistsError(out)
    (out/'configs').mkdir(parents=True);runs=[]
    for r in plan['runs']:
        if not keep(r):continue
        cfg=yaml.safe_load(Path(r['config']).read_text());row=change(cfg,dict(r));label=r['label'].replace(label_from,label_to)
        path=out/'configs'/(label+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
        runs.append({**row,'label':label,'config':str(path),'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    plan.update(runs=runs,derived_from=src,preregistration='experiments/collusion/sprint_channel_preference/PREREG_V7.md',**(meta or {}))
    (out/'plan.json').write_text(json.dumps(plan,indent=2));print(out,len(runs))
def to_qwen(cfg,row):
    cfg['llm_models'][0]['llm']['huggingface']['model']=QWEN;s=cfg['experiment']['channel_study'];s.update(monitor_model=DS,read_tool=False)
    row.update(model=QWEN,monitor_model=DS,read_tool=False);return row
def no_nudge(cfg,row):
    cfg['experiment']['channel_study']['reveal_nudge']=False;row.update(reveal_nudge=False,arm='reveal_nonudge');return row
derive('v6b_positive_control_deepseek','v7_positive_control_qwen','pc_deepseek','pc_qwen',to_qwen)
derive('v6b_confirm_deepseek','v7_qwen','c_deepseek','c_qwen',to_qwen)
derive('v6_confirm_gptoss','v7_nonudge_gptoss','c_gptoss','nn_gptoss',no_nudge,keep=lambda r:r['arm']=='reveal')
