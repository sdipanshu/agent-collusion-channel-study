"""Latency / rate-limit probe for gpt-oss-120b providers: 6 concurrent small tool calls each, sequential per provider."""
import json,time
from concurrent.futures import ThreadPoolExecutor
import requests
from experiments.collusion.choice.hf_client import load_token

H={'Authorization':'Bearer '+load_token()}
cases=json.load(open('outputs/model_screen/cases.json'))
tool={'type':'function','function':{'name':'submit','parameters':{'type':'object','properties':{'actor':{'type':'string'},'task_id':{'type':'string'},'board':{'type':'string'},'cost':{'type':'integer'}},'required':['actor','task_id','board','cost']}}}
def call(model,c):
    t=time.monotonic()
    r=requests.post('https://router.huggingface.co/v1/chat/completions',headers=H,timeout=120,json={'model':model,'messages':[{'role':'user','content':c['prompt']}],'tools':[tool],'temperature':0,'max_tokens':2048})
    ok=r.ok and bool((r.json()['choices'][0]['message'].get('tool_calls')))
    return r.status_code,ok,time.monotonic()-t
for prov in ('baseten','nscale','novita','deepinfra'):
    m=f'openai/gpt-oss-120b:{prov}'
    with ThreadPoolExecutor(6) as p:res=list(p.map(lambda c:call(m,c),cases[:6]))
    print(f"{prov:10s} statuses {[s for s,_,_ in res]} tool_calls {sum(o for _,o,_ in res)}/6 latency mean {sum(t for *_,t in res)/6:.1f}s max {max(t for *_,t in res):.1f}s",flush=True)
