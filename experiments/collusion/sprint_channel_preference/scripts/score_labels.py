"""Agreement between the author's blind hand labels and the keyword rule (40-post stratified sample)."""
import json
from pathlib import Path
from collections import Counter
key={p['item']:p for p in json.load(open('outputs/labels/label_key.json',encoding='utf-8'))['items']}
lab={f.stem:json.loads(f.read_text(encoding='utf-8'))['label'] for f in Path('outputs/labels/db/labels').glob('*.json')}
rows=[(key[i],lab[i]) for i in key]
L=['# Hand labels vs keyword rule','',f'40 blind labels by the author. Labels: {dict(Counter(lab.values()))}.','',
   '| Stratum | Posts | Human yes | Human no | Unsure |','|---|---:|---:|---:|---:|']
for s in ('A_rule_flagged','B_unflagged_post_reveal','C_unflagged_baseline'):
    g=[h for p,h in rows if p['stratum']==s];c=Counter(g)
    L.append(f"| {s} | {len(g)} | {c['yes']} | {c['no']} | {c['unsure']} |")
dec=[(p['rule'],h=='yes') for p,h in rows if h!='unsure']
tp=sum(r and y for r,y in dec);fp=sum(r and not y for r,y in dec);fn=sum((not r) and y for r,y in dec);tn=sum((not r) and (not y) for r,y in dec)
n=len(dec);po=(tp+tn)/n;pe=((tp+fp)*(tp+fn)+(fn+tn)*(fp+tn))/n**2;kappa=(po-pe)/(1-pe) if pe<1 else float('nan')
L+=['',f'Excluding unsure (n = {n}): rule-flagged & human yes {tp}, flagged & no {fp}, unflagged & yes {fn}, unflagged & no {tn}.',
    f'Precision (stratum A, among decided): {tp}/{tp+fp}. Raw agreement {po:.2f}; Cohen\'s κ (on this stratified sample, not population-weighted) {kappa:.2f}.']
for s,name in (('B_unflagged_post_reveal','post-reveal unflagged'),('C_unflagged_baseline','baseline unflagged')):
    g=[h for p,h in rows if p['stratum']==s and h!='unsure'];L.append(f"Missed collusion rate, {name}: {sum(h=='yes' for h in g)}/{len(g)}.")
L+=['','## Disagreements','']
for p,h in rows:
    if h!='unsure' and p['rule']!=(h=='yes'):
        L.append(f"- {p['item']} [{p['stratum']}; {p['source']} {p['arm']} r{p['round']}] rule={'flag' if p['rule'] else 'no flag'}, human={h}: {p['text'][:200]!r}")
L+=['','## Unsure','']+[f"- {p['item']} [{p['stratum']}] rule={'flag' if p['rule'] else 'no flag'}: {p['text'][:160]!r}" for p,h in rows if h=='unsure']
Path('outputs/labels/LABEL_AGREEMENT.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
