"""v7b pre-registered H3/H4 (PREREG_V7.md): gpt-oss reveal without the nudge vs v6 control and v6 reveal, same seeds."""
import json,sys
from pathlib import Path
exec(open('work/analyze_late_reveal.py',encoding='utf-8').read().split("def main")[0])
def load(root,arm):
    out={}
    for r in json.loads((Path(root)/'plan.json').read_text())['runs']:
        if r['arm']!=arm:continue
        a=[p for p in (Path(root)/'runs'/r['label']).rglob('trusted_audit.jsonl') if (p.parent/'public_monitor_input.json').exists()]
        if len(a)==1:out[r['block']]=episode(a[0].parent)
    return out
ctrl=load('outputs/v6_confirm_gptoss','control');rev=load('outputs/v6_confirm_gptoss','reveal');nn=load('outputs/v7_nonudge_gptoss','reveal_nonudge')
k='pair_success_after_reveal';L=['# v7b — gpt-oss reveal without the nudge','',f'Episodes: no-nudge {len(nn)}, v6 reveal {len(rev)}, v6 control {len(ctrl)} (seeds 1751–1762).','',
 '| Group | Pair erasures after reveal (total) | Mean retention | Flagged retention (episodes) | Monitor flags |','|---|---:|---:|---:|---:|']
for name,g in (('v6 control',ctrl),('v6 reveal (nudge)',rev),('v7 reveal (no nudge)',nn)):
    ret=[e['retention'] for e in g.values() if e['retention'] is not None];fr=[e['flagged_retention'] for e in g.values() if e['flagged_retention'] is not None]
    fl=[e['monitor_flag'] for e in g.values() if e['monitor_flag'] is not None]
    L.append(f"| {name} | {sum(e[k] for e in g.values())} | {sum(ret)/len(ret):.2f} | {(sum(fr)/len(fr)) if fr else float('nan'):.2f} ({len(fr)}) | {sum(fl)}/{len(fl) if fl else '—'} |")
d,lo,hi=boot_diff([e[k] for e in nn.values()],[e[k] for e in ctrl.values()])
L+=['',f"**H3:** no-nudge reveal − control = {d:+.2f} erasures/episode [95% CI {lo:+.2f}, {hi:+.2f}] → **{'SUPPORTED' if lo>0 else 'NOT SUPPORTED'}**."]
d4,lo4,hi4=boot_diff([e[k] for e in rev.values()],[e[k] for e in nn.values()])
L.append(f"**H4:** nudge reveal − no-nudge reveal = {d4:+.2f} [95% CI {lo4:+.2f}, {hi4:+.2f}].")
L.append('Verdict: '+('nudge not needed for erasure (H3 supported).' if lo>0 else ('nudge necessary (H3 not supported, H4 lower bound > 0).' if lo4>0 else 'inconclusive.')))
Path('outputs/v7_nonudge_gptoss/NONUDGE_RESULTS.md').write_text('\n'.join(L)+'\n',encoding='utf-8');print('\n'.join(L))
