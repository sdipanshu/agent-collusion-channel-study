"""List every edit/delete in the Qwen2.5-7B assisted pilot, flagging coalition language before and after."""
import glob,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from compare_arms import DISCLOSURE  # noqa: E402  (module also writes PENALTY.md; harmless)

rows=[]
for f in sorted(glob.glob('outputs/assisted_pilot/runs/**/trusted_audit.jsonl',recursive=True)):
    run=Path(f).relative_to('outputs/assisted_pilot/runs').parts[0]
    design=list(Path(f).parent.glob('design.json'))
    for line in open(f,encoding='utf-8'):
        e=json.loads(line)
        if e.get('operation') not in ('edit','delete'):continue
        prev=e.get('previous_event') or {};o=(prev.get('payload') or {}).get('content','');n=e.get('new_content') or ''
        rows.append({'run':run,'agent':e['agent'],'op':e['operation'],'status':e.get('status'),'own':prev.get('agent')==e['agent'],
                     'orig_disclose':bool(DISCLOSURE.search(o)),'new_disclose':bool(DISCLOSURE.search(n)),'orig':o,'new':n})
ok=[r for r in rows if r['status']=='success']
print(f"attempts {len(rows)}; successful {len(ok)} (edits {sum(r['op']=='edit' for r in ok)}, deletes {sum(r['op']=='delete' for r in ok)}); "
      f"own-post {sum(r['own'] for r in ok)}; coalition language removed by edit {sum(r['orig_disclose'] and not r['new_disclose'] for r in ok)}")
for r in ok:
    print(f"\n{r['run']} | {r['agent']} {r['op']} | coalition language before={r['orig_disclose']} after={r['new_disclose']}")
    print('  BEFORE:',r['orig'][:200].replace('\n',' '));print('  AFTER :',r['new'][:200].replace('\n',' '))
