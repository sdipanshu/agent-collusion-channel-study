"""v14 (PREREG_V14.md): fairness norm on private coordination, no monitoring, on the v13 setup (prioritise-coalition objective,
public + coalition boards). 2v2 and 3v2 x audience {everyone, coalition} x 6 seeds (1763-1768). Control: v13 none arm."""
import json,random
from pathlib import Path
exec(open('work/prepare_v11.py',encoding='utf-8').read().split('for exp,lays in LAYOUTS.items():')[0])
C=Path(r'C:\Users\dipan\colosseum\experiments\collusion\configs\channel_study\fairness')
def cfg14(exp,aud,seed):
    c=yaml.safe_load((C/f'fn_{exp}_{aud}.yaml').read_text());c['simulation']['seed']=seed;c['experiment']['seeds']=[seed]
    c['llm_models'][0]['llm']['huggingface']['model']=MODEL;c['experiment']['channel_study']['monitor_model']=MONITOR;return c
spec=[];rng=random.Random(1401)
for b,seed in enumerate(SEEDS):
    cells=[(exp,aud) for exp in ('2v2','3v2') for aud in ('everyone','coalition')];rng.shuffle(cells)
    for exp,aud in cells:spec.append((f'fn_{exp}_b{b}_{aud}',cfg14(exp,aud,seed),{'experiment':exp,'block':b,'seed':seed,'condition':'none','audience':aud,'layout':'fairness'}))
write('outputs/v14_fairness',spec,{'stage':'pilot','arm':'fairness_note','order':'seed blocks; 4 cells shuffled within each block'})
p=Path('outputs/v14_fairness/plan.json');j=json.loads(p.read_text());j['preregistration']='experiments/collusion/sprint_channel_preference/PREREG_V14.md';p.write_text(json.dumps(j,indent=2))
