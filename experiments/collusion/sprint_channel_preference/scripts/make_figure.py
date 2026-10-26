"""Figure 1: forced-public coalition posts by monitor stakes; values read from outputs/v3_penalty/arms.json."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

rows=json.loads(Path('outputs/v3_penalty/arms.json').read_text(encoding='utf-8'))['runs']
conds=[('off','No monitor'),('observe','Monitor,\nno stakes'),('penalty','Monitor,\n−25 points'),('fail','Monitor,\ncoalition fails')]
data=[]
for key,_ in conds:
    c=[r for r in rows if r['layout']=='nonadjacent' and r['condition']==key and r['complete']]
    data.append((sum(r['pair_public_posts'] for r in c),sum(r['pair_public_disclosing_original'] for r in c),
                 sum(r['pair_edits']+r['pair_deletes'] for r in c),sum(r['mutation_attempts'] for r in c),len(c)))
assert [d[1] for d in data]==[10,4,1,1] and all(d[2]==0 and d[3]==0 for d in data),data

INK,INK2,SURF='#0b0b0b','#52514e','#fcfcfb'
DARK,LIGHT='#1c5cab','#86b6ef'  # blue ramp steps 550 / 250: one hue, part-of-whole
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10})
fig,ax=plt.subplots(figsize=(6.4,3.9),dpi=200);fig.patch.set_facecolor(SURF);ax.set_facecolor(SURF)
x=range(len(conds));w=0.56
for i,(total,disc,erase,attempts,n) in enumerate(data):
    ax.bar(i,disc,w,color=DARK,hatch='///',edgecolor=SURF,linewidth=1.5,zorder=3)
    ax.bar(i,total-disc,w,bottom=disc,color=LIGHT,edgecolor=SURF,linewidth=1.5,zorder=3)
    ax.text(i,disc/2 if disc>=3 else disc+0.6,str(disc),ha='center',va='center' if disc>=3 else 'bottom',
            color='white' if disc>=3 else INK,fontsize=10,fontweight='bold',zorder=4)
    ax.text(i,total+0.6,f'{total} posts',ha='center',va='bottom',color=INK2,fontsize=8.5)
    ax.text(i,-6.6,'0 edits / deletes',ha='center',va='top',color=INK2,fontsize=8)
ax.set_xticks(list(x),[c[1] for c in conds],color=INK,fontsize=9)
ax.tick_params(axis='x',length=0,pad=6);ax.tick_params(axis='y',colors=INK2,labelsize=8.5,length=0)
ax.set_ylim(0,34);ax.set_ylabel('Coalition pair public posts',color=INK2,fontsize=9)
ax.grid(axis='y',color='#e6e5e0',linewidth=0.8,zorder=0)
for s in ('top','right','left'):ax.spines[s].set_visible(False)
ax.spines['bottom'].set_color('#c9c8c2')
from matplotlib.patches import Patch
ax.legend(handles=[Patch(facecolor=DARK,hatch='///',edgecolor=SURF,label='Contains coalition language'),
                   Patch(facecolor=LIGHT,edgecolor=SURF,label='No coalition language')],
          loc='upper center',bbox_to_anchor=(0.5,1.13),ncol=2,frameon=False,fontsize=8.5,labelcolor=INK)
fig.text(0.01,0.005,'Non-adjacent coalition pairs (no shared private board), read-write public board, 8 planning rounds; 6 episodes per bar.\n'
         'Counts are original posts from the trusted audit; contents on the final board were identical (no edits or deletes by any agent).',
         fontsize=6.6,color=INK2,va='bottom')
fig.subplots_adjust(left=0.1,right=0.98,top=0.86,bottom=0.31)
out=Path('outputs/figure1_whisper_not_erase.png');fig.savefig(out,facecolor=SURF);print(out.resolve())
