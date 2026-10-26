"""Re-run episodes that failed on infrastructure errors (HTTP 429 / timeouts) once, archiving the originals."""
import json,os,shutil,subprocess,sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

root=Path(sys.argv[1]);workers=int(sys.argv[2]) if len(sys.argv)>2 else 2
INFRA=('HTTP 429','ReadTimeout','Read timed out','HTTP 5')
plan={r['label']:r for r in json.loads((root/'plan.json').read_text())['runs']}
status={}
for p in sorted(root.glob('attempts_w*.jsonl')):
    for r in map(json.loads,p.read_text().splitlines()):
        if r['status']!='started':status[r['label']]=r['status']
todo=[]
for label,s in status.items():
    if s!='failed':continue
    log=(root/'runs'/label/'console.log').read_text(encoding='utf-8',errors='replace')
    if any(m in log for m in INFRA):todo.append(label)
    else:print('NOT infrastructure, left as failed:',label)
print('re-running',len(todo),todo,flush=True)
def run(label):
    arch=root/'failed_infra'/label;arch.parent.mkdir(exist_ok=True);shutil.move(str(root/'runs'/label),str(arch))
    dest=root/'runs'/label;dest.mkdir()
    env=os.environ.copy();env.update(HF_MAX_REQUESTS='70',HF_MAX_TOTAL_TOKENS='400000',PYTHONUNBUFFERED='1')
    with (dest/'console.log').open('w') as log:
        rc=subprocess.run([sys.executable,'-m','experiments.collusion.run_channel_study','--config',plan[label]['config'],'--out-dir',str(dest)],env=env,stdout=log,stderr=subprocess.STDOUT).returncode
    s='complete' if rc==0 else 'failed'
    with (root/'attempts_wrerun.jsonl').open('a') as f:f.write(json.dumps({'label':label,'status':s,'rerun_reason':'infrastructure (HTTP 429 / timeout)'})+'\n')
    print(label,s,flush=True)
with ThreadPoolExecutor(workers) as pool:list(pool.map(run,todo))
