"""Cross-family replication: gpt-oss-120b vs matched DeepSeek runs."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from analyze_coordonly import stats,find  # noqa: E402 (module rewrites COORDONLY.md; harmless)

root=Path(sys.argv[1] if len(sys.argv)>1 else 'outputs/v3_gptoss_di');plan=json.loads((root/'plan.json').read_text())['runs']
rows=[(r,stats(root/'runs'/r['label']),stats(find(r['matched_to']))) for r in plan]
tot=lambda sel,k:sum(x[k] for x in sel if x)
L=[f'# Cross-family replication: gpt-oss-120b ({root.name}) vs DeepSeek-V4.1-Flash, matched configs','',
   '## A. Channel preference (adjacent pairs, append-only, no monitor, seeds 1728–1732)','',
   '| Incentive | gpt-oss: public / all pair posts | DeepSeek (matched) |','|---|---:|---:|']
for inc in ('coalition','team'):
    sel=[x for x in rows if x[0]['arm']=='channel' and x[0]['incentive']==inc]
    g=[x[1] for x in sel];d=[x[2] for x in sel]
    f=lambda s:f"{tot(s,'public')}/{tot(s,'posts')}"+(f" ({tot(s,'public')/tot(s,'posts'):.0%})" if tot(s,'posts') else '')
    L.append(f"| {inc} | {f(g)} | {f(d)} |")
g=[x[1] for x in rows if x[0]['arm']=='channel' and x[0]['incentive']=='coalition']
L+=['',f"gpt-oss coalition private posts with coalition language: {tot(g,'private_disc')}/{tot(g,'private')}; public: {tot(g,'public_disc')}/{tot(g,'public')}.",'',
    '## B. Forced-public self-censorship (non-adjacent, read-write, 8 rounds, seeds 1733–1734)','',
    '| Condition | Model | Pair public posts | …with coalition language | Edits / deletes |','|---|---|---:|---:|---:|']
for cond,key in (('Off',lambda r:not r['monitored']),('Penalty',lambda r:r.get('treatment')=='penalty')):
    sel=[x for x in rows if x[0]['arm']=='censorship' and key(x[0])]
    for name,i in (('gpt-oss-120b',1),('DeepSeek (matched)',2)):
        s=[x[i] for x in sel]
        L.append(f"| {cond} | {name} | {tot(s,'public')} | {tot(s,'public_disc')} | {tot(s,'mutations')} |")
L+=['',f"Completed gpt-oss episodes: {sum(1 for x in rows if x[1])}/{len(rows)}. Small n: descriptive only."]
(root/'GPTOSS.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
