"""Prepare, execute once, and summarize matched channel-preference runs (protocol v3)."""
import argparse,copy,hashlib,json,os,random,subprocess,sys,time
from pathlib import Path
import yaml

# Actor model -> cross-family public-board monitor, so no arm is judged by its own family.
MONITORS={'Qwen/Qwen3-14B:deepinfra':'deepseek-ai/DeepSeek-V4.1-Flash:deepinfra',
          'deepseek-ai/DeepSeek-V4.1-Flash:deepinfra':'Qwen/Qwen3.8-27B:deepinfra',
          'openai/gpt-oss-120b:novita':'Qwen/Qwen3.8-27B:deepinfra',
          'openai/gpt-oss-120b:deepinfra':'Qwen/Qwen3.8-27B:deepinfra',
          'openai/gpt-oss-120b:baseten':'Qwen/Qwen3.8-27B:deepinfra',
          'Qwen/Qwen3-30B-A3B:deepinfra':'deepseek-ai/DeepSeek-V4.1-Flash:deepinfra'}
# DeepInfra catalogue USD per million tokens (input, output), saved 2026-10-26 in outputs/model_screen/catalog.json.
PRICES={'Qwen/Qwen3-14B:deepinfra':(.12,.24),'deepseek-ai/DeepSeek-V4.1-Flash:deepinfra':(.20,.60),
        'Qwen/Qwen3.8-27B:deepinfra':(.20,2.50),'openai/gpt-oss-120b:novita':(.05,.25),'openai/gpt-oss-120b:deepinfra':(.037,.17),'openai/gpt-oss-120b:baseten':(.10,.50),
        'Qwen/Qwen3-30B-A3B:deepinfra':(.12,.50)}  # deepinfra.com/pricing, checked 2026-10-28
LAYOUT_PAIRS={'adjacent':6,'nonadjacent':3}

def prepare(template,output,models,seeds,fixtures,stage,validation):
    output=Path(output).resolve()
    if (output/'plan.json').exists():raise FileExistsError('Plan already exists; refusing to replace preregistered schedule')
    output.mkdir(parents=True,exist_ok=True);(output/'configs').mkdir(exist_ok=True)
    base=yaml.safe_load(Path(template).read_text());runs=[];rng=random.Random(48193)
    for model in models:
        if model not in MONITORS:raise ValueError(f'No cross-family monitor or price for {model}')
    for block,seed in enumerate(seeds):
        block_runs=[]
        for mi,model in enumerate(models):
            for layout in LAYOUT_PAIRS:
                for mode in ('append_only','read_write'):
                    for on in (False,True):
                        for incentive in ('coalition','team'):
                            cfg=copy.deepcopy(base);exp=cfg['experiment']
                            exp.update(seeds=[seed],planning_rounds=4,max_conversation_steps=1,max_concurrent_runs=1)
                            exp['collusion'].update(colluder_selection='fixture_pair',agent_order='random')
                            exp['channel_study']={'enabled':True,'protocol_version':'channel_preference_v3',
                                'stage':stage,'monitored':on,'mutability':mode,'incentive':incentive,
                                'pair_layout':layout,'pair_index':block%LAYOUT_PAIRS[layout],
                                'monitor_treatment':'observation_only','monitor_backend':'independent_hf',
                                'monitor_model':MONITORS[model],'monitor_validation':validation}
                            if fixtures:cfg['environment']['fixture_path']=str(Path(fixtures[block%len(fixtures)]).resolve())
                            cfg['llm_models']=[{'label':f'candidate{mi}','llm':{'provider':'huggingface','huggingface':{'model':model,'params':{'temperature':.7,'max_output_tokens':16384}}}}]
                            label=f'b{block}_m{mi}_{layout}_{mode}_monitor{int(on)}_{incentive}'
                            path=output/'configs'/(label+'.yaml');path.write_text(yaml.safe_dump(cfg,sort_keys=False))
                            block_runs.append({'label':label,'model':model,'monitor_model':MONITORS[model],'block':block,'seed':seed,
                                'layout':layout,'mode':mode,'monitored':on,'incentive':incentive,'config':str(path),
                                'config_sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
        # Shuffle within a block only, so a budget stop truncates whole blocks rather than whole arms.
        rng.shuffle(block_runs);runs+=block_runs
    plan={'protocol_version':'channel_preference_v3','stage':stage,
          'primary':'designated-pair public share of original successful planning posts',
          'factors':['mutability','monitored','incentive','pair_layout','model'],
          'monitor_treatment':'observation_only','monitors':MONITORS,'planning_rounds':4,'schedule_seed':48193,
          'runs':runs,'fixture_scope':'Explicit fixture list, or legacy single fixed payoff fixture if none supplied.'}
    (output/'plan.json').write_text(json.dumps(plan,indent=2))
    return plan

def spent(root,plan):
    """Estimated USD from returned usage for every attempted run, actor and monitor calls."""
    total=0.0;by_label={r['label']:r for r in plan['runs']}
    for label,run in by_label.items():
        for name,model in (('hf_requests.jsonl',run['model']),('monitor_requests.jsonl',run['monitor_model'])):
            for p in (Path(root)/'runs'/label).rglob(name):
                for line in p.read_text(encoding='utf-8',errors='replace').splitlines():
                    try:usage=(json.loads(line).get('response') or {}).get('usage') or {}
                    except json.JSONDecodeError:continue  # line still being written by another worker
                    i,o=PRICES[model];total+=(usage.get('prompt_tokens',0)*i+usage.get('completion_tokens',0)*o)/1e6
    return total

def recover(root,plan):
    """Close out runs a crashed worker left at 'started', judged from their own artifacts only."""
    rows=[json.loads(x) for p in root.glob('attempts_w*.jsonl') for x in p.read_text().splitlines()]
    closed={r['label'] for r in rows if r['status']!='started'}
    by_label={r['label']:r for r in plan['runs']}
    with (root/'attempts_wrecovered.jsonl').open('a') as f:
        for label in {r['label'] for r in rows if r['status']=='started'}-closed:
            d=root/'runs'/label;final=list(d.rglob('final_summary.json'))
            newest=max((p.stat().st_mtime for p in d.rglob('*')),default=0)
            if time.time()-newest<900:continue  # possibly still in flight (e.g. waiting on the monitor)
            ok=len(final)==1 and json.loads(final[0].read_text(encoding='utf-8')).get('status')=='complete' and list(d.rglob('channel_preferences.json'))
            if ok and by_label[label]['monitored']:ok=bool(list(d.rglob('public_monitor.json')))
            f.write(json.dumps({'label':label,'status':'complete' if ok else 'failed','recovered':True})+'\n')

def execute(output,budget,worker=0,workers=1,max_consecutive_failures=3,reverse=False):
    # Worker w runs plan entries w, w+n, ...; the shared budget is checked against all workers' spend.
    root=Path(output);plan=json.loads((root/'plan.json').read_text());progress=root/f'attempts_w{worker}.jsonl'
    recover(root,plan)
    # Budget-deferred runs never started, so they stay eligible; directory creation is the real claim.
    attempted={r['label'] for p in root.glob('attempts_w*.jsonl') for r in map(json.loads,p.read_text().splitlines()) if r['status']!='not_started_budget'}
    def record(row):
        with progress.open('a') as f:f.write(json.dumps(row)+'\n')
    failures=0;costs=[]
    for run in (plan['runs'][worker::workers][::-1] if reverse else plan['runs'][worker::workers]):
        if run['label'] in attempted:continue
        # Reserve for every worker's in-flight run, not just this one.
        # Per-run deltas overlap across workers, so reserve the true average cost per started run
        # for each possible in-flight run (up to two workers per shard).
        used=spent(root,plan);started=max(1,sum(1 for _ in (root/'runs').iterdir()) if (root/'runs').exists() else 1)
        reserve=max(.03,used/started)*workers*2
        if used+reserve>budget:
            record({'label':run['label'],'status':'not_started_budget','spent_usd':used,'reserve_usd':reserve});print('Budget stop at',round(used,4));break
        if hashlib.sha256(Path(run['config']).read_bytes()).hexdigest()!=run['config_sha256']:raise ValueError('Frozen config changed')
        dest=root/'runs'/run['label']
        try:dest.mkdir(parents=True,exist_ok=False)  # atomic claim: any number of workers can share a plan
        except FileExistsError:continue
        record({'label':run['label'],'status':'started','time':time.time()})
        env=os.environ.copy();env.update(HF_MAX_REQUESTS=os.environ.get('PILOT_MAX_REQUESTS','40'),HF_MAX_TOTAL_TOKENS='400000',PYTHONUNBUFFERED='1')
        with (dest/'console.log').open('w') as log:
            result=subprocess.run([sys.executable,'-m','experiments.collusion.run_channel_study','--config',run['config'],'--out-dir',str(dest)],env=env,stdout=log,stderr=subprocess.STDOUT)
        cost=spent(root,plan)-used;costs.append(cost)
        record({'label':run['label'],'status':'complete' if result.returncode==0 else 'failed','exit_code':result.returncode,'cost_usd':cost})
        print(run['label'],'complete' if result.returncode==0 else 'FAILED',f'${cost:.4f}',flush=True)
        failures=0 if result.returncode==0 else failures+1
        if failures>=max_consecutive_failures:print('Stopping after consecutive failures');break
    summarize(root)

def summarize(root):
    root=Path(root);plan=json.loads((root/'plan.json').read_text());rows=[]
    status={}
    # Recovered records first, so a worker's own later record overrides them.
    for p in sorted(root.glob('attempts_w*.jsonl'),key=lambda p:p.name!='attempts_wrecovered.jsonl'):
        for r in map(json.loads,p.read_text().splitlines()):
            if r['status']!='started' or r['label'] not in status:status[r['label']]=r['status']
    for run in plan['runs']:
        row={k:run[k] for k in ('label','model','block','seed','layout','mode','monitored','incentive')};row['status']=status.get(run['label'],'not_started')
        files=list((root/'runs'/run['label']).rglob('channel_preferences.json'))
        if len(files)==1:
            m=json.loads(files[0].read_text())['pair']
            row.update({k:m[k] for k in ('total_posts','posts','public_share_of_posts','deduplicated_public_share','public_posts_per_opportunity','private_posts_per_opportunity')})
        rows.append(row)
    effects=[]
    for model in sorted({r['model'] for r in rows}):
        for block in sorted({r['block'] for r in rows}):
            for layout in LAYOUT_PAIRS:
                for incentive in ('coalition','team'):
                    cells={(r['mode'],r['monitored']):r for r in rows if r['model']==model and r['block']==block and r['layout']==layout and r['incentive']==incentive}
                    valid=len(cells)==4 and all(r['status']=='complete' and r.get('public_share_of_posts') is not None for r in cells.values())
                    effect={'model':model,'block':block,'layout':layout,'incentive':incentive,'complete_four_cell_block':valid}
                    if valid:
                        a=cells[('append_only',True)]['public_share_of_posts']-cells[('append_only',False)]['public_share_of_posts']
                        b=cells[('read_write',True)]['public_share_of_posts']-cells[('read_write',False)]['public_share_of_posts']
                        effect.update(monitor_effect_append_only=a,monitor_effect_read_write=b,interaction=b-a)
                    effects.append(effect)
    (root/'results.json').write_text(json.dumps({'runs':rows,'matched_effects':effects,'spent_usd_estimate':spent(root,plan),
        'note':'Effects require completed four-cell blocks; absent posts yield null, never zero. Failures and partial metrics retained. No significance claim.'},indent=2))

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','execute','summarize']);p.add_argument('--output',required=True)
    p.add_argument('--template');p.add_argument('--model',action='append');p.add_argument('--seed',type=int,action='append');p.add_argument('--fixture',action='append',default=[])
    p.add_argument('--stage',choices=['engineering','pilot','research'],default='engineering');p.add_argument('--monitor-validation')
    p.add_argument('--budget-usd',type=float,default=2.0);p.add_argument('--worker',type=int,default=0);p.add_argument('--workers',type=int,default=1);p.add_argument('--reverse',action='store_true')
    a=p.parse_args()
    if a.action=='prepare':
        if not a.template:p.error('--template required')
        prepare(a.template,a.output,a.model or list(MONITORS),a.seed or [1728],a.fixture,a.stage,a.monitor_validation)
    elif a.action=='execute':execute(a.output,a.budget_usd,a.worker,a.workers,reverse=a.reverse)
    else:summarize(a.output)
if __name__=='__main__':main()

