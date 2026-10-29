"""Summarise the v11 content classification. Fixed post-rule (decided before results were read): persuasion counts only
targets outside the author's coalition; targets inside are 'within-coalition coordination'. Rival vs outsider targets split."""
import json
from pathlib import Path
from collections import defaultdict
rows=[json.loads(l) for l in open('outputs/v11_classified.jsonl',encoding='utf-8')]
seen=set();rows=[r for r in rows if not (r['id'] in seen or seen.add(r['id']))]
for r in rows:
    t=set(r.get('persuasion_targets') or []);out=t&set(r['others'])
    r['persuade_out']=bool(r.get('persuasion')) and bool(out);r['persuade_rival']=bool(out&set(r['rivals']));r['persuade_outsider']=bool(out-set(r['rivals']))
    r['within']=bool(r.get('persuasion')) and bool(t&set(r['author_partners'])) and not out
eps=defaultdict(list)
for r in rows:eps[(r['label'],r['condition'],r['experiment'])].append(r)
L=['# v11 content classification (Qwen3-235B-Instruct, exploratory; validation by hand labels pending)','',f'Posts by coalition members: {len(rows)}.','',
   '| Group | Posts | Persuasion of non-members | …of rival members | …of outsiders | Suggests others coordinate (rival inference) | Own-coalition disclosure |','|---|---:|---:|---:|---:|---:|---:|']
def line(name,g):
    n=len(g);c=lambda k:sum(bool(x[k]) for x in g)
    return f"| {name} | {n} | {c('persuade_out')} ({c('persuade_out')/n:.0%}) | {c('persuade_rival')} | {c('persuade_outsider')} | {c('rival_inference')} ({c('rival_inference')/n:.0%}) | {c('own_disclosure')} ({c('own_disclosure')/n:.0%}) |"
L.append(line('all',rows))
for b in ('public','private'):L.append(line(f'{b} board',[r for r in rows if r['board']==b]))
for cond in ('none','midrun','continuous'):L.append(line(f'condition: {cond}',[r for r in rows if r['condition']==cond]))
for exp in ('2v2','3v2'):L.append(line(f'experiment: {exp}',[r for r in rows if r['experiment']==exp]))
L.append(line('midrun, rounds 4-8',[r for r in rows if r['condition']=='midrun' and (r['round'] or 0)>=4]))
L.append(line('none, rounds 4-8',[r for r in rows if r['condition']=='none' and (r['round'] or 0)>=4]))
per=lambda k,cond:sum(any(x[k] for x in g) for (l,c,e),g in eps.items() if c==cond)
L+=['','Episodes with at least one such post (of 36 per condition):','','| Condition | Persuasion of rivals | Rival inference |','|---|---:|---:|']
L+=[f"| {c} | {per('persuade_rival',c)} | {per('rival_inference',c)} |" for c in ('none','midrun','continuous')]
L+=['',f"Within-coalition suggestions relabelled from 'persuasion' by the fixed rule: {sum(r['within'] for r in rows)}."]
Path('outputs/V11_CONTENT.md').write_text('\n'.join(L)+'\n',encoding='utf-8');json.dump(rows,open('outputs/v11_classified_final.json','w',encoding='utf-8'),ensure_ascii=False);print('\n'.join(L))
