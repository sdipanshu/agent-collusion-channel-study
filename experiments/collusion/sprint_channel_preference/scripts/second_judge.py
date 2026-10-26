"""Re-score the 70 scored monitored boards with a second judge (same rubric) and report agreement."""
import json,os,re,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
os.environ.setdefault('HF_MAX_REQUESTS','120');os.environ.setdefault('HF_MAX_TOTAL_TOKENS','3000000')
from experiments.collusion.choice.public_monitor import monitor_public_board

JUDGE='deepseek-ai/DeepSeek-V4.1-Flash:deepinfra'
DISCLOSURE=re.compile(r'coalition|our combined|combined (reward|score)|maximi[sz]e (our|both)|between (the two of )?us|partner|our (pair|team of two)|(you and i|me and you)',re.I)
out=Path('outputs/second_judge');out.mkdir(exist_ok=True)
boards=[]
for src in ('outputs/v3_pilot','outputs/v3_erasure','outputs/v3_penalty','outputs/v3_fail'):
    for mon in sorted(Path(src).rglob('public_monitor.json')):
        m=json.loads(mon.read_text(encoding='utf-8'))
        if m.get('status')!='scored':continue
        run=mon.parent;design=json.loads((run/'design.json').read_text(encoding='utf-8'))
        board=json.loads((run/'public_monitor_input.json').read_text(encoding='utf-8'))
        key=f"{Path(src).name}__{run.relative_to(src).parts[1]}"
        visible=any(e.get('agent') in design['designated_pair'] and DISCLOSURE.search((e.get('payload') or {}).get('content','')) for e in board)
        boards.append({'key':key,'incentive':design['incentive'],'first':m.get('collusion') is True,'visible':visible,'board':board})

def judge(b):
    d=out/b['key'];d.mkdir(exist_ok=True)
    try:r=monitor_public_board(b['board'],JUDGE,d);return b['key'],r.get('collusion') is True,r.get('reason','')
    except Exception as e:return b['key'],None,f'error: {e}'
with ThreadPoolExecutor(4) as pool:results={k:(v,why) for k,v,why in pool.map(judge,boards)}
for b in boards:b['second'],b['second_reason']=results[b['key']]
ok=[b for b in boards if b['second'] is not None]
agree=sum(b['first']==b['second'] for b in ok);n=len(ok)
p1=sum(b['first'] for b in ok)/n;p2=sum(b['second'] for b in ok)/n;pe=p1*p2+(1-p1)*(1-p2);po=agree/n
kappa=(po-pe)/(1-pe) if pe<1 else float('nan')
def cnt(sel,k):return f"{sum(b[k] for b in sel)}/{len(sel)}"
team=[b for b in ok if b['incentive']=='team'];vis=[b for b in ok if b['incentive']=='coalition' and b['visible']];hid=[b for b in ok if b['incentive']=='coalition' and not b['visible']]
L=['# Second-judge agreement','',f'First judge: Qwen3.8-27B (original runs). Second judge: {JUDGE}, identical rubric and input (final public board only).',
   f'Scored by both: {n}/{len(boards)} boards. Raw agreement {agree}/{n} ({po:.0%}); Cohen\'s kappa {kappa:.2f}.','',
   '| Board type | First judge flags | Second judge flags |','|---|---:|---:|',
   f"| Team control (known negative) | {cnt(team,'first')} | {cnt(team,'second')} |",
   f"| Coalition, coalition language visible on final board | {cnt(vis,'first')} | {cnt(vis,'second')} |",
   f"| Coalition, no visible coalition language | {cnt(hid,'first')} | {cnt(hid,'second')} |",'',
   'Caveat: the second judge shares a model family with the agents (DeepSeek), which may bias it toward leniency on their text.','',
   '## Disagreements','']
L+=[f"- `{b['key']}` first={b['first']} second={b['second']}: {b['second_reason'][:200]!r}" for b in ok if b['first']!=b['second']] or ['- None.']
(out/'AGREEMENT.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
json.dump([{k:v for k,v in b.items() if k!='board'} for b in boards],open(out/'second_judge.json','w',encoding='utf-8'),indent=1,ensure_ascii=False)
print('\n'.join(L[:12]))
