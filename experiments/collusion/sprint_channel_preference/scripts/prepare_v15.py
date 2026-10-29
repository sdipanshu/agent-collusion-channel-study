"""v15 (PREREG_V15.md): v13 with the reviewer's actual criterion in the notice ("a group of agents coordinating for its own benefit").
2v2 and 3v2 x midrun/continuous x 6 seeds (1763-1768). Comparisons: v13 same cells; v13 none."""
import json,random
from pathlib import Path
exec(open('work/prepare_v11.py',encoding='utf-8').read().split('for exp,lays in LAYOUTS.items():')[0])
C=Path(r'C:\Users\dipan\colosseum\experiments\collusion\configs\channel_study\criterion_monitor')
def cfg15(exp,cond,seed):
    c=yaml.safe_load((C/f'cm_{exp}_{cond}.yaml').read_text());c['simulation']['seed']=seed;c['experiment']['seeds']=[seed]
    c['llm_models'][0]['llm']['huggingface']['model']=MODEL;c['experiment']['channel_study']['monitor_model']=MONITOR;return c
spec=[];rng=random.Random(1501)
for b,seed in enumerate(SEEDS):
    cells=[(exp,cond) for exp in ('2v2','3v2') for cond in ('midrun','continuous')];rng.shuffle(cells)
    for exp,cond in cells:spec.append((f'cm_{exp}_b{b}_{cond}',cfg15(exp,cond,seed),{'experiment':exp,'block':b,'seed':seed,'condition':cond,'layout':'criterion_monitor'}))
write('outputs/v15_criterion',spec,{'stage':'pilot','arm':'criterion_monitor','order':'seed blocks; 4 cells shuffled within each block'})
p=Path('outputs/v15_criterion/plan.json');j=json.loads(p.read_text());j['preregistration']='experiments/collusion/sprint_channel_preference/PREREG_V15.md';p.write_text(json.dumps(j,indent=2))
