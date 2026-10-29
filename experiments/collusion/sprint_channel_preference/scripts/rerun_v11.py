"""Re-run, once, v11 episodes that did not finish for infrastructure reasons (reviewer 504 before the streaming fix,
or killed by the low-memory reaper). Originals are archived under failed_infra/ with the reason; model failures are
never re-run. Usage: rerun_v11.py <root> [workers]"""
import json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

root=Path(sys.argv[1]);workers=int(sys.argv[2]) if len(sys.argv)>2 else 1
plan={r['label']:r for r in json.loads((root/'plan.json').read_text())['runs']}
done=set()
for p in root.glob('attempts_w*.jsonl'):
    for r in map(json.loads,p.read_text().splitlines()):
        if r['status']=='complete':done.add(r['label'])
todo=[]
for d in sorted((root/'runs').iterdir()):
    if d.name in done:continue
    log=(d/'console.log').read_text(encoding='utf-8',errors='replace') if (d/'console.log').exists() else ''
    if 'EXPERIMENT END (completed=1' in log:continue
    reason='reviewer HTTP 504 (pre-streaming)' if 'HTTP 504' in log else ('interrupted (process killed: low-memory reaper or Windows Update restart)' if 'Traceback' not in log else None)
    if reason is None:print('NOT infrastructure, left as is:',d.name);continue
    todo.append((d.name,reason))
print('re-running',len(todo),todo,flush=True)

def run(item):
    label,reason=item
    arch=root/'failed_infra'/label;arch.parent.mkdir(exist_ok=True)
    if arch.exists():print('already archived once, not re-running:',label);return
    shutil.move(str(root/'runs'/label),str(arch));(arch/'ARCHIVE_REASON.txt').write_text(reason)
    dest=root/'runs'/label;dest.mkdir()
    env=os.environ.copy();env.update(HF_MAX_REQUESTS=os.environ.get('PILOT_MAX_REQUESTS','90'),HF_MAX_TOTAL_TOKENS='400000',PYTHONUNBUFFERED='1')
    with (dest/'console.log').open('w') as log:
        rc=subprocess.run([sys.executable,'-m','experiments.collusion.run_channel_study','--config',plan[label]['config'],'--out-dir',str(dest)],
                          env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    with (root/'attempts_wrerun.jsonl').open('a') as f:
        f.write(json.dumps({'label':label,'status':'complete' if rc==0 else 'failed','rerun_reason':reason})+'\n')
    print(label,'complete' if rc==0 else 'failed',flush=True)

with ThreadPoolExecutor(workers) as pool:list(pool.map(run,todo))
