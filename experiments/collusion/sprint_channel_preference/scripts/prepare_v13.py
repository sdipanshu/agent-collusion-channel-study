"""v13 (PREREG_V13.md): v12 board setup (public + coalition boards) with the prioritise-coalition objective, strong
monitor wording and bonus disqualification. 2v2 and 3v2 x none/midrun/continuous x 6 seeds (1763-1768); plus one gate."""
import json,random
from pathlib import Path
exec(open('work/prepare_v11.py',encoding='utf-8').read().split('for exp,lays in LAYOUTS.items():')[0])
C=Path(r'C:\Users\dipan\colosseum\experiments\collusion\configs\channel_study\strong_monitor')
PREREG='experiments/collusion/sprint_channel_preference/PREREG_V13.md'
def cfg13(exp,cond,seed):
    c=yaml.safe_load((C/f'sm_{exp}_{cond}.yaml').read_text());c['simulation']['seed']=seed;c['experiment']['seeds']=[seed]
    c['llm_models'][0]['llm']['huggingface']['model']=MODEL;c['experiment']['channel_study']['monitor_model']=MONITOR;return c
spec=[];rng=random.Random(1301)
for b,seed in enumerate(SEEDS):
    cells=[(exp,cond) for exp in ('2v2','3v2') for cond in ('none','midrun','continuous')];rng.shuffle(cells)
    for exp,cond in cells:spec.append((f'sm_{exp}_b{b}_{cond}',cfg13(exp,cond,seed),{'experiment':exp,'block':b,'seed':seed,'condition':cond,'layout':'strong_monitor'}))
write('outputs/v13_strong_monitor',spec,{'stage':'pilot','arm':'strong_monitor','order':'seed blocks; 6 cells shuffled within each block'})
write('outputs/v13_gate',[('gate_v13',cfg13('2v2','continuous',1738),{'experiment':'2v2','seed':1738,'condition':'continuous','arm':'gate','layout':'strong_monitor'})],
      {'stage':'engineering','arm':'gate','note':'Live gate only; never analysed.'})
for d in ('v13_strong_monitor','v13_gate'):
    p=Path(f'outputs/{d}/plan.json');j=json.loads(p.read_text());j['preregistration']=PREREG;p.write_text(json.dumps(j,indent=2))
