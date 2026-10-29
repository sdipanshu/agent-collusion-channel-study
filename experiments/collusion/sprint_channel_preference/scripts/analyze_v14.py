"""v14 pre-registered H14a/H14b (PREREG_V14.md): fairness note vs v13 none arm, same seeds. Written before results were viewed."""
import json,re
from pathlib import Path
exec(open('work/analyze_v12.py',encoding='utf-8').read().split('\ndef main(')[0])
def main(root='outputs/v14_fairness'):
    eps=load12(root);ctrl=[e for e in load12('outputs/v13_strong_monitor') if e['condition']=='none']
    f=lambda key:lambda e:[c[key] for c in e['coalitions'] if c[key] is not None]
    L=['# v14 — fairness norm on private coordination (pre-registered analysis)','',f'Episodes: {len(eps)}; control (v13 none): {len(ctrl)}.','']
    for h,aud in (('H14a','everyone'),('H14b','coalition')):
        E=[e for e in eps if e['audience']==aud];d,lo,hi=boot(E,ctrl,f('private_share'))
        L.append(f"**{h} (note shown to {aud}) reduces coalition-board share:** {aud} − control = {d:+.2f} [95% CI {lo:+.2f}, {hi:+.2f}] → **{'SUPPORTED' if hi<0 else 'NOT SUPPORTED'}**.")
    m=lambda v:'—' if not v else f'{sum(v)/len(v):.2f}'
    L+=['','| Group | Exp | Episodes | Coalition-board share | Public coalition-language posts | Team reward |','|---|---|---:|---:|---:|---:|']
    for name,G in (('control (v13 none)',ctrl),('note: everyone',[e for e in eps if e['audience']=='everyone']),('note: coalition only',[e for e in eps if e['audience']=='coalition'])):
        for exp in ('2v2','3v2'):
            E=[e for e in G if e['experiment']==exp];cs=[c for e in E for c in e['coalitions']]
            L.append(f"| {name} | {exp} | {len(E)} | {m([c['private_share'] for c in cs if c['private_share'] is not None])} | {m([c['pub_disc'] for c in cs])} | {m([e['team_reward_final'] for e in E])} |")
    Path(root,'V14_RESULTS.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
if __name__=='__main__':import sys;main(*(sys.argv[1:] or []))
