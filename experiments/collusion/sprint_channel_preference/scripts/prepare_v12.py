"""v12 (PREREG_V12.md): public board + one private board per coalition, no neighbour boards. 2v2 and 3v2 x none/midrun/continuous
x 6 seeds (1763-1768, same as v11); cells shuffled within each seed block. Plus one live gate (2v2 continuous, seed 1738)."""
import json
from pathlib import Path
exec(open('work/prepare_v11.py',encoding='utf-8').read().split('for exp,lays in LAYOUTS.items():')[0])
import random
C=Path(r'C:\Users\dipan\colosseum\experiments\collusion\configs\channel_study\coalition_boards')
def cfg12(exp,cond,seed):
    c=yaml.safe_load((C/f'cb_{exp}_{cond}.yaml').read_text());c['simulation']['seed']=seed;c['experiment']['seeds']=[seed]
    c['llm_models'][0]['llm']['huggingface']['model']=MODEL;c['experiment']['channel_study']['monitor_model']=MONITOR;return c
spec=[];rng=random.Random(1201)
for b,seed in enumerate(SEEDS):
    cells=[(exp,cond) for exp in ('2v2','3v2') for cond in ('none','midrun','continuous')];rng.shuffle(cells)
    for exp,cond in cells:spec.append((f'cb_{exp}_b{b}_{cond}',cfg12(exp,cond,seed),{'experiment':exp,'block':b,'seed':seed,'condition':cond,'layout':'coalition_boards'}))
write('outputs/v12_coalition_boards',spec,{'stage':'pilot','arm':'coalition_boards','order':'seed blocks; 6 cells shuffled within each block'})
write('outputs/v12_gate',[('gate_v12',cfg12('2v2','continuous',1738),{'experiment':'2v2','seed':1738,'condition':'continuous','arm':'gate','layout':'coalition_boards'})],
      {'stage':'engineering','arm':'gate','note':'Live gate only; never analysed.'})
for d in ('v12_coalition_boards','v12_gate'):
    p=Path(f'outputs/{d}/plan.json');j=json.loads(p.read_text());j['preregistration']='experiments/collusion/sprint_channel_preference/PREREG_V12.md';p.write_text(json.dumps(j,indent=2))
