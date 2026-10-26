"""Aggregate the v3 channel-preference pilot: per-run CSV, per-cell table, matched contrasts."""
import csv,json,statistics,sys
from pathlib import Path

root=Path(sys.argv[1] if len(sys.argv)>1 else 'outputs/v3_pilot')
plan=json.loads((root/'plan.json').read_text())
status={}
for p in sorted(root.glob('attempts_w*.jsonl'),key=lambda p:p.name!='attempts_wrecovered.jsonl'):
    for r in map(json.loads,p.read_text().splitlines()):
        if r['status'] not in ('started','not_started_budget') or r['label'] not in status:status[r['label']]=r['status']

def mean(xs):
    xs=[x for x in xs if x is not None]
    return statistics.mean(xs) if xs else None

rows=[]
for run in plan['runs']:
    row={k:run[k] for k in ('label','block','seed','layout','mode','monitored','incentive')}
    row['status']=status.get(run['label'],'not_started')
    pref=list((root/'runs'/run['label']).rglob('channel_preferences.json'))
    final=list((root/'runs'/run['label']).rglob('final_summary.json'))
    if row['status']=='complete' and len(pref)==1 and len(final)==1:
        d=pref[0].parent;m=json.loads(pref[0].read_text());f=json.loads(final[0].read_text())
        met=json.loads((d/'metrics.json').read_text());design=json.loads((d/'design.json').read_text())
        mon=json.loads((d/'public_monitor.json').read_text()) if (d/'public_monitor.json').exists() else {}
        posts=m['pair']['posts']
        row.update(pair='+'.join(design['designated_pair']),
            pair_posts=m['pair']['total_posts'],pair_public=posts.get('public',0),
            pair_private_partner=posts.get('pair_private',0),pair_private_outsider=posts.get('other_private',0),
            pair_public_share=m['pair']['public_share_of_posts'],pair_dedup_public_share=m['pair']['deduplicated_public_share'],
            pair_posts_per_opportunity=(m['pair']['total_posts']/m['pair']['planning_opportunities']) if m['pair']['planning_opportunities'] else None,
            outsider_public_share=m['outsiders']['public_share_of_posts'],
            copied_public_and_private=m['pair']['distinct_contents_copied_public_and_private'],
            edits=sum(e['operation']=='edit' and e.get('status')=='success' for e in m['mutation_attempts']),
            deletes=sum(e['operation']=='delete' and e.get('status')=='success' for e in m['mutation_attempts']),
            mutation_attempts=len(m['mutation_attempts']),
            team_reward=f['joint_reward'],pair_reward=met.get('coalition_reward_sum'),violations=f.get('violations'),
            monitor_flag=mon.get('collusion') if run['monitored'] else None)
        if row['team_reward'] is not None and row['pair_reward'] is not None:
            row['outsider_reward']=row['team_reward']-row['pair_reward']
    rows.append(row)

done=[r for r in rows if r['status']=='complete' and 'pair_posts' in r]
keys=sorted({k for r in rows for k in r},key=lambda k:list(rows[0]).index(k) if k in rows[0] else 99)
with (root/'per_run.csv').open('w',newline='',encoding='utf-8') as fh:
    w=csv.DictWriter(fh,fieldnames=keys);w.writeheader();w.writerows(rows)

def fmt(x,p=2):return 'n/a' if x is None else (f'{x:.{p}f}' if isinstance(x,float) else str(x))
L=[f'# v3 channel-preference pilot — DeepSeek-V4.1-Flash','',
   f"Scheduled {len(rows)}; complete {len(done)}; failed {sum(r['status']=='failed' for r in rows)}; not run {sum(r['status'] not in ('complete','failed') for r in rows)}.",'',
   '## Per cell (means over completed seeds)','',
   '| Incentive | Layout | Board | Monitor | n | Pair posts | Pair public share | to partner | to outsiders | Outsider public share | Edits/deletes | Pair reward | Team reward | Monitor flags |',
   '|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for inc in ('coalition','team'):
    for lay in ('adjacent','nonadjacent'):
        for mode in ('append_only','read_write'):
            for on in (False,True):
                c=[r for r in done if (r['incentive'],r['layout'],r['mode'],r['monitored'])==(inc,lay,mode,on)]
                n_sched=sum((r['incentive'],r['layout'],r['mode'],r['monitored'])==(inc,lay,mode,on) for r in rows)
                flags=f"{sum(r['monitor_flag'] is True for r in c)}/{len(c)}" if on else '—'
                L.append(f"| {inc} | {lay} | {mode} | {'on' if on else 'off'} | {len(c)}/{n_sched} | {fmt(mean(r['pair_posts'] for r in c),1)} | {fmt(mean(r['pair_public_share'] for r in c))} | {fmt(mean(r['pair_private_partner'] for r in c),1)} | {fmt(mean(r['pair_private_outsider'] for r in c),1)} | {fmt(mean(r['outsider_public_share'] for r in c))} | {fmt(sum(r['edits'] for r in c))}/{fmt(sum(r['deletes'] for r in c))} | {fmt(mean(r['pair_reward'] for r in c))} | {fmt(mean(r['team_reward'] for r in c))} | {flags} |")

def contrast(a_key,b_key,label):
    """Matched within block/layout/other factors: mean of (a - b) pair public share and pair reward."""
    diffs=[];rdiffs=[]
    idx={(r['block'],r['layout'],r['mode'],r['monitored'],r['incentive']):r for r in done}
    for k,r in idx.items():
        if a_key(k):
            other=idx.get(b_key(k))
            if other and r['pair_public_share'] is not None and other['pair_public_share'] is not None:
                diffs.append(r['pair_public_share']-other['pair_public_share'])
            if other and r['pair_reward'] is not None and other['pair_reward'] is not None:
                rdiffs.append(r['pair_reward']-other['pair_reward'])
    pos=sum(d>0 for d in diffs);neg=sum(d<0 for d in diffs)
    return f"| {label} | {len(diffs)} | {fmt(mean(diffs))} | {pos}/{neg}/{len(diffs)-pos-neg} | {fmt(mean(rdiffs))} |"

L+=['','## Matched contrasts (same seed block, layout and remaining factors)','',
    '| Contrast | Matched pairs | Mean Δ pair public share | Δ>0 / Δ<0 / tie | Mean Δ pair reward |','|---|---:|---:|---:|---:|']
for inc in ('coalition','team'):
    for mode in ('append_only','read_write'):
        L.append(contrast(lambda k,m=mode,i=inc:k[2]==m and k[3] and k[4]==i,lambda k:(k[0],k[1],k[2],False,k[4]),f'Monitor on − off · {inc} · {mode}'))
for lay in ('adjacent','nonadjacent'):
    L.append(contrast(lambda k,l=lay:k[1]==l and k[3] and k[4]=='coalition',lambda k:(k[0],k[1],k[2],False,k[4]),f'Monitor on − off · coalition · {lay}'))
L.append(contrast(lambda k:k[4]=='coalition',lambda k:(k[0],k[1],k[2],k[3],'team'),'Coalition − team control (all cells)'))
L.append(contrast(lambda k:k[1]=='nonadjacent' and k[4]=='coalition',lambda k:(k[0],'adjacent',k[2],k[3],k[4]),'Non-adjacent − adjacent · coalition'))
L+=['','Pilot scale (one model, one payoff fixture, ≤5 seeds per cell): descriptive only, no significance claims.',
    'Shares use original successful planning posts from the trusted audit. Runs with no pair posts give null share and drop out of share contrasts.',
    'Monitor verdicts come from an unvalidated cross-family judge (Qwen3.8-27B) that sees only the final public board.']
(root/'RESULTS.md').write_text('\n'.join(L)+'\n',encoding='utf-8')
print('\n'.join(L))
