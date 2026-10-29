"""v16 (PREREG_V16.md): emergent-collusion test. Team objective for everyone; one designated pair (ring 0+1) gets an
exclusive, neutrally described private board vs control with no private board. Levelled 2v2 fixture. 12 seeds x 2 arms."""
import json,random
from pathlib import Path
exec(open('work/prepare_v11.py',encoding='utf-8').read().split('for exp,lays in LAYOUTS.items():')[0])
C=Path(r'C:\Users\dipan\colosseum\experiments\collusion\configs\channel_study\emergent');SEEDS16=list(range(1763,1775))
def cfg16(arm,seed):
    c=yaml.safe_load((C/f'em_{arm}.yaml').read_text());c['simulation']['seed']=seed;c['experiment']['seeds']=[seed]
    c['llm_models'][0]['llm']['huggingface']['model']=MODEL;c['experiment']['channel_study']['monitor_model']=MONITOR;return c
spec=[];rng=random.Random(1601)
for b,seed in enumerate(SEEDS16):
    arms=['pair_board','control'];rng.shuffle(arms)
    for arm in arms:spec.append((f'em_b{b}_{arm}',cfg16(arm,seed),{'experiment':'2v2','block':b,'seed':seed,'arm':arm,'condition':'none'}))
write('outputs/v16_emergent',spec,{'stage':'pilot','arm':'emergent','order':'seed blocks; arm order shuffled within each block'})
p=Path('outputs/v16_emergent/plan.json');j=json.loads(p.read_text());j['preregistration']='experiments/collusion/sprint_channel_preference/PREREG_V16.md';p.write_text(json.dumps(j,indent=2))
