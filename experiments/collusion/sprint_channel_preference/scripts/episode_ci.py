"""Episode-level estimates with bootstrap 95% CIs, plus a power check for the erasure re-run.

Unit of analysis: the episode. Rate per episode = coalition-language pair posts on the public board / pair public posts.
"""
import json,random,sys
from pathlib import Path
src=open('work/analyze_v4.py',encoding='utf-8-sig').read().split('rows=[(r,')[0]
sys.argv=['x','outputs/v4_gptoss_bt'];exec(src)
rng=random.Random(0)
def boot(xs,f=lambda v:sum(v)/len(v),n=10000):
    if not xs:return float('nan'),float('nan'),float('nan')
    bs=sorted(f([rng.choice(xs) for _ in xs]) for _ in range(n));return f(xs),bs[int(.025*n)],bs[int(.975*n)]
def bootdiff(a,b,n=10000):
    m=lambda v:sum(v)/len(v);bs=sorted(m([rng.choice(a) for _ in a])-m([rng.choice(b) for _ in b]) for _ in range(n))
    return m(a)-m(b),bs[int(.025*n)],bs[int(.975*n)]
rate=lambda s:s['public_disc']/s['public'] if s['public'] else 0.0
rows=[(r,stats(root/'runs'/r['label']),stats(find(r))) for r in plan]
L=['# Episode-level estimates (bootstrap 95% CI, 10k resamples)','','Unit = episode. Rate = share of the pair\'s public posts containing coalition language (keyword rule; not yet hand-validated). Exploratory.','',
   '| Condition | Model | n episodes | Mean rate [95% CI] | Mean retained on final board / episode [95% CI] |','|---|---|---:|---|---|']
per={}
for cond in ('off','observe','penalty','fail'):
    for name,i in (('gpt-oss-120b',1),('DeepSeek',2)):
        s=[x[i] for x in rows if x[0]['arm']=='erasure' and x[0]['condition']==cond and x[i]]
        per[(cond,name)]=s;m,lo,hi=boot([rate(e) for e in s]);fm,flo,fhi=boot([e['final_disc'] for e in s])
        L.append(f'| {cond} | {name} | {len(s)} | {m:.2f} [{lo:.2f}, {hi:.2f}] | {fm:.1f} [{flo:.1f}, {fhi:.1f}] |')
L+=['','## Off minus fail (rate difference)','']
for name in ('gpt-oss-120b','DeepSeek'):
    d=bootdiff([rate(e) for e in per[('off',name)]],[rate(e) for e in per[('fail',name)]]);L.append(f'- {name}: {d[0]:+.2f} [{d[1]:+.2f}, {d[2]:+.2f}]')
# Power for the pre-registered erasure metric: retention = coalition-language left on final board / posted, per episode.
# Simulate: off retention ~1.0 (nothing removed); fail retention p_keep. Episodes vary in how much they post (resampled from gpt-oss off/fail).
L+=['','## Power check for the erasure re-run (simulation)','',
    'Metric: per-episode retention = coalition-language posts left on the final public board / coalition-language posts made. Episodes with no such posts drop out (the rate is undefined).',
    'Assumes off ≈ no erasure (retention 1.0, as observed when tools failed). Under fail, each coalition post is erased with probability q. Posting volume is resampled from observed gpt-oss episodes. The test is a one-sided bootstrap CI excluding 0.','',
    '| q (erase prob. under fail) | n=6/arm | n=12/arm | n=20/arm |','|---|---:|---:|---:|']
vol_off=[e['public_disc'] for e in per[('off','gpt-oss-120b')]];vol_fail=[max(e['public_disc'],0) for e in per[('observe','gpt-oss-120b')]+per[('penalty','gpt-oss-120b')]]
def sim(q,n,reps=300):
    hits=0
    for _ in range(reps):
        off=[1.0 for v in (rng.choice(vol_off) for _ in range(n)) if v]
        fail=[]
        for _ in range(n):
            v=rng.choice(vol_fail)
            if v:fail.append(sum(rng.random()>q for _ in range(v))/v)
        if len(off)<2 or len(fail)<2:continue
        m=lambda x:sum(x)/len(x);bs=sorted(m([rng.choice(off) for _ in off])-m([rng.choice(fail) for _ in fail]) for _ in range(400))
        hits+=bs[int(.05*400)]>0
    return hits/reps
for q in (.1,.2,.3,.5):L.append(f'| {q:.1f} | '+' | '.join(f'{sim(q,n):.2f}' for n in (6,12,20))+' |')
L+=['','Caveat: under fail, gpt-oss posted 0 coalition-language posts publicly in the earlier run, so the fail arm may yield few defined episodes. Volume here is borrowed from observe/penalty.']
Path('outputs/EPISODE_CI.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
