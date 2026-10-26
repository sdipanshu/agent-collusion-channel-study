"""Read-only endpoint and credential checks; does not request inference."""
import json
import requests
from experiments.collusion.choice.hf_client import load_token

def main():
    try:
        token=load_token()
    except RuntimeError as exc:
        print(json.dumps({'ready':False,'reason':str(exc),'inference_calls':0},indent=2))
        return 2
    response=requests.get('https://router.huggingface.co/v1/models',
                          headers={'Authorization':'Bearer '+token},timeout=30)
    print(json.dumps({'http_status':response.status_code,
                      'inference_calls':0,
                      'note':'Model-list access does not establish a free credit balance or tool-call support.'},indent=2))
    return 0 if response.ok else 2

if __name__=='__main__': raise SystemExit(main())
