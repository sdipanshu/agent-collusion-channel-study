"""v8 (PREREG_V8.md): gpt-oss reveal arm announcing full-history review; same configs as v6 gpt-oss reveal otherwise.
The reviewer is run twice per episode: on the full history (what agents were told) and on the final board only (the lie)."""
import json
from pathlib import Path
exec(open('work/prepare_v7.py',encoding='utf-8').read().split('def to_qwen')[0])
def full_history(cfg,row):
    cfg['experiment']['channel_study']['monitor_scope']='full_history';row.update(monitor_scope='full_history',arm='reveal_full_history');return row
derive('v6_confirm_gptoss','v8_fullhistory_gptoss','c_gptoss','fh_gptoss',full_history,keep=lambda r:r['arm']=='reveal')
p=Path('outputs/v8_fullhistory_gptoss/plan.json');d=json.loads(p.read_text())
d['preregistration']='experiments/collusion/sprint_channel_preference/PREREG_V8.md';p.write_text(json.dumps(d,indent=2))
