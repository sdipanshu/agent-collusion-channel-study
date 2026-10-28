"""v11 (PREREG_V11.md): multi-coalition experiments on levelled fixtures. 2v2 and 3v2 x 3 layouts x 3 monitoring x 6 seeds.
gpt-oss-120b (Baseten) agents, Qwen3.8-27B reviewer. Cells shuffled within each seed block. Plus one live gate per experiment."""
import hashlib,json,random
from pathlib import Path
import yaml
C=Path(r'C:\Users\dipan\colosseum\experiments\collusion\configs\channel_study\multi_coalition')
MODEL='openai/gpt-oss-120b:baseten';MONITOR='Qwen/Qwen3.8-27B:deepinfra';SEEDS=list(range(1763,1769))
LAYOUTS={'2v2':['both_adjacent','one_adjacent','neither_adjacent'],'3v2':['chain3_adj2','chain3_nonadj2','spread3_nonadj2']}
def cfg_for(exp,lay,cond,seed):
    c=yaml.safe_load((C/f'mc_{exp}_{lay}_{cond}.yaml').read_text());c['simulation']['seed']=seed;c['experiment']['seeds']=[seed]
    c['llm_models'][0]['llm']['huggingface']['model']=MODEL;c['experiment']['channel_study']['monitor_model']=MONITOR;return c
def write(out,spec,meta):
    out=Path(out).resolve()
    if out.exists():raise FileExistsError(out)
    (out/'configs').mkdir(parents=True);runs=[]
    for label,c,row in spec:
        p=out/'configs'/(label+'.yaml');p.write_text(yaml.safe_dump(c,sort_keys=False))
        runs.append({**row,'label':label,'model':MODEL,'monitor_model':MONITOR,'config':str(p),'config_sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    (out/'plan.json').write_text(json.dumps({'protocol_version':'channel_preference_v3','preregistration':'experiments/collusion/sprint_channel_preference/PREREG_V11.md',**meta,'runs':runs},indent=2));print(out,len(runs))
for exp,lays in LAYOUTS.items():
    rng=random.Random({'2v2':1102,'3v2':1132}[exp]);spec=[]
    for b,seed in enumerate(SEEDS):
        cells=[(lay,cond) for lay in lays for cond in ('none','midrun','continuous')];rng.shuffle(cells)
        for lay,cond in cells:spec.append((f'{exp}_b{b}_{lay}_{cond}',cfg_for(exp,lay,cond,seed),{'experiment':exp,'block':b,'seed':seed,'layout':lay,'condition':cond}))
    write(f'outputs/v11_{exp}',spec,{'stage':'pilot','arm':f'multi_coalition_{exp}','order':'seed blocks; 9 cells shuffled within each block'})
    write(f'outputs/v11_gate_{exp}',[(f'gate_{exp}',cfg_for(exp,lays[0],'continuous',1738),{'experiment':exp,'seed':1738,'layout':lays[0],'condition':'continuous','arm':'gate'})],
          {'stage':'engineering','arm':'gate','note':'Live gate only; never analysed.'})
