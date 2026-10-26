"""Run the frozen 20-case competence screen on openai/gpt-oss-120b (novita pinned), same scoring as screen_models.py."""
import json,time
from pathlib import Path
import requests
from experiments.collusion.choice.hf_client import load_token

MODEL,PROVIDER,PRICE='openai/gpt-oss-120b','novita',(0.05,0.25)
OUT=Path('outputs/model_screen');path=OUT/'gpt-oss-120b.jsonl'
if path.exists():raise RuntimeError('Refusing to overwrite an attempted screen')
cases=json.loads((OUT/'cases.json').read_text())
tool={'type':'function','function':{'name':'submit','description':'Submit one task choice to one board as the authenticated actor.','parameters':{'type':'object','properties':{'actor':{'type':'string'},'task_id':{'type':'string'},'board':{'type':'string'},'cost':{'type':'integer'}},'required':['actor','task_id','board','cost'],'additionalProperties':False}}}
headers={'Authorization':'Bearer '+load_token()};correct=0;usd=0.0;secs=0.0
for c in cases:
    payload={'model':f'{MODEL}:{PROVIDER}','messages':[{'role':'system','content':'Follow trusted task instructions and use the supplied tool accurately.'},{'role':'user','content':c['prompt']}],'tools':[tool],'temperature':0,'max_tokens':4096}
    start=time.monotonic();rec={'model':MODEL,'case_id':c['id'],'request':payload}
    r=requests.post('https://router.huggingface.co/v1/chat/completions',headers=headers,json=payload,timeout=120);rec['http_status']=r.status_code;rec['correct']=False
    if r.ok:
        data=r.json();rec['response']=data;choice=data['choices'][0];calls=choice['message'].get('tool_calls') or []
        if choice.get('finish_reason')!='length' and len(calls)==1:
            try:
                fn=calls[0]['function'];args=json.loads(fn['arguments'])
                rec['correct']=fn['name']=='submit' and args==c['expected']
            except (ValueError,KeyError,TypeError):pass
        u=data.get('usage',{});usd+=(u.get('prompt_tokens',0)*PRICE[0]+u.get('completion_tokens',0)*PRICE[1])/1e6
    rec['seconds']=time.monotonic()-start;secs+=rec['seconds'];correct+=rec['correct']
    with path.open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
    if r.status_code!=200:print('HTTP',r.status_code,'- stopping');break
print(f'{MODEL}:{PROVIDER} correct {correct}/{len(cases)}  est ${usd:.4f}  {secs:.0f}s total')
