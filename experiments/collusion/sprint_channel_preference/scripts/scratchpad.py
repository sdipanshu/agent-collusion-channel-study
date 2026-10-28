"""Reasoning scratchpads from logged model calls (reasoning_content in hf_requests.jsonl). Exploratory, read-only.

Per run: SCRATCHPAD.md with every planning turn (round, agent, role, action, reasoning).
Per root: REASONING_ERASURES.md with every edit/delete decision, and REASONING_REVEAL.md with pair members'
first turn after the reveal (where the decision to go quiet, erase or carry on is made).
Each actor gets one generation per planning decision, so its n-th planning request is its round-n turn.
"""
import json,sys
from pathlib import Path

def turns(run):
    design=json.loads((run/'design.json').read_text(encoding='utf-8'));pair=set(design['designated_pair'])
    seen={};out=[]
    for line in (run/'hf_requests.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line)
        if 'response' not in r:continue  # failed attempt (retried); the successful attempt follows
        tools={t['function']['name'] for t in r['request'].get('tools',[])}
        if 'assign_task' in tools:continue  # execution phase
        actor=r['actor'];seen[actor]=seen.get(actor,0)+1
        msg=r['response']['choices'][0]['message']
        calls=[(c['function']['name'],json.loads(c['function']['arguments'] or '{}')) for c in (msg.get('tool_calls') or [])]
        out.append({'round':seen[actor],'agent':actor,'pair':actor in pair,'reasoning':(msg.get('reasoning_content') or msg.get('reasoning') or '').strip(),
                    'content':(msg.get('content') or '').strip(),'calls':calls})
    return design,out

def action(t):
    if not t['calls']:return 'no tool call'
    name,args=t['calls'][0]
    return f"{name}({', '.join(f'{k}={str(v)[:160]!r}' for k,v in args.items())})"+(f' (+{len(t["calls"])-1} more, rejected)' if len(t['calls'])>1 else '')

def block(t,run_label):
    role='coalition pair' if t['pair'] else 'outsider'
    return (f"### {run_label} — round {t['round']} — {t['agent']} ({role})\n\n**Action:** `{action(t)}`\n\n"
            +(f"**Reasoning:**\n\n> "+t['reasoning'].replace('\n','\n> ')+'\n\n' if t['reasoning'] else '*No reasoning returned.*\n\n')
            +(f"**Visible reply:** {t['content'][:400]}\n\n" if t['content'] else ''))

def main(root):
    root=Path(root);plan=json.loads((root/'plan.json').read_text())['runs'];erasures=[];reveal=[]
    for r in plan:
        runs=[p.parent for p in (root/'runs'/r['label']).rglob('trusted_audit.jsonl')]
        if len(runs)!=1 or not (runs[0]/'hf_requests.jsonl').exists():continue
        run=runs[0];design,ts=turns(run);rr=design.get('reveal_round') or 0
        head=f"# Scratchpad — {r['label']} ({r.get('arm')})\n\nScripted analysis of logged reasoning; exploratory. Pair: {', '.join(design['designated_pair'])}. Reveal round: {rr or 'none'}.\n\n"
        (run/'SCRATCHPAD.md').write_text(head+''.join(block(t,r['label']) for t in ts),encoding='utf-8')
        for t in ts:
            if t['calls'] and t['calls'][0][0] in ('edit_board_entry','delete_board_entry'):erasures.append((r,t))
        first={}
        for t in ts:
            if t['pair'] and t['round']>=rr and t['agent'] not in first:first[t['agent']]=t
        reveal+=[(r,t) for t in first.values()]
    hdr='Exploratory: model reasoning as logged by the provider (`reasoning_content`). Not evidence of faithful internal reasoning.\n\n'
    (root/'REASONING_ERASURES.md').write_text('# Reasoning behind every edit/delete decision\n\n'+hdr+''.join(f"*Arm: {r.get('arm')}*\n\n"+block(t,r['label']) for r,t in erasures),encoding='utf-8')
    (root/'REASONING_REVEAL.md').write_text('# Pair members\' first turn after the reveal round\n\n'+hdr+''.join(f"*Arm: {r.get('arm')}*\n\n"+block(t,r['label']) for r,t in reveal),encoding='utf-8')
    print(root,'erasure decisions',len(erasures),'post-reveal first turns',len(reveal))

if __name__=='__main__':
    for root in sys.argv[1:]:main(root)
