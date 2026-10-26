"""List live tool-capable HF router models from non-Qwen/DeepSeek families, cheapest first."""
import requests
from experiments.collusion.choice.hf_client import load_token
r=requests.get('https://router.huggingface.co/v1/models',headers={'Authorization':'Bearer '+load_token()},timeout=40);r.raise_for_status()
rows=[]
for m in r.json()['data']:
    mid=m['id']
    if any(f in mid.lower() for f in ('qwen','deepseek')):continue
    for p in m.get('providers',[]):
        pr=p.get('pricing') or {}
        if p.get('status')=='live' and p.get('supports_tools') and pr.get('input') is not None:
            rows.append((pr['input']+pr['output'],mid,p['provider'],pr['input'],pr['output'],p.get('throughput'),p.get('context_length')))
for cost,mid,prov,i,o,tp,ctx in sorted(rows)[:40]:
    print(f"{mid:55s} {prov:14s} in {i:<5} out {o:<5} tok/s {tp if tp is None else round(tp)} ctx {ctx}")
