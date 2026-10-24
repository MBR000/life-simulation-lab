"""Descriptive same-seed comparison conditional on observed migration by age.
Not a causal estimator: both survival and migration success select the sample.
"""
from pathlib import Path
import json,statistics,csv,math
R=Path(__file__).resolve().parents[1]
D=json.loads((R/'tables/analysis.json').read_text())
M=json.loads((R/'tables/migration.json').read_text())
idx={(r['opts']['iso'],r['seed'],r['opts']['policy']['abroad']):r for r in map(json.loads,(R/'runs.jsonl').open())}
mig={r['id']:r for r in M['records']}
metrics={'monthly_cny':('income',3.5/12),'nw_cny':('nw',3.5),'money_cny':('money',3.5),'h':('h',1)}
def summary(v):
    return {'n':len(v),'median':statistics.median(v) if v else None,'mean':statistics.mean(v) if v else None}
SCOPES=['primary','work','study','spouse','nomad','refugee','adopt','family','unknown','minor','all']
def in_scope(m,scope):
    if scope=='all':return True
    if scope=='primary':return m['first_age']>=18 and m['route'] in ['work','study']
    if scope in ['work','study']:return m['first_age']>=18 and m['route']==scope
    if scope=='minor':return m['first_age']<18 and m['route'] in ['work','study']
    return m['route']==scope
out=[];detail=[]
for iso in D['countries']:
 for age in D['ages']:
  for mode in ['ever','current']:
   for scope in SCOPES:
    pairs=[];eligible=0
    for i in range(1,1001):
     seed=f'P-{i:06d}';a,b=[idx[(iso,seed,arm)] for arm in ['avoid','seek']]
     ma,mb=mig.get(a['id']),mig.get(b['id'])
     if not mb:continue
     cutoff=float('inf') if age=='death' else int(age)
     if mb['first_age']>cutoff:continue
     if not in_scope(mb,scope):continue
     # Control must have no observed foreign residence up to this observation age.
     if ma and ma['first_age']<=cutoff:continue
     eligible+=1
     if age not in a['snaps'] or age not in b['snaps']:continue
     sa,sb=a['snaps'][age],b['snaps'][age]
     if sa['cur']!=iso:continue
     if mode=='current' and sb['cur']==iso:continue
     pairs.append((sa,sb));detail.append({'iso':iso,'age':age,'mode':mode,'scope':scope,'seed':seed})
    vals={}
    for k,(field,factor) in metrics.items():
     av=[a[field]*factor for a,b in pairs];bv=[b[field]*factor for a,b in pairs]
     dv=[y-x for x,y in zip(av,bv)];vals[k]={'avoid':summary(av),'seek':summary(bv),'paired':summary(dv)}
    out.append({'iso':iso,'age':age,'mode':mode,'scope':scope,'eligible':eligible,'n':len(pairs),'metrics':vals})
(R/'tables/success.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
with (R/'tables/success_comparison.csv').open('w',newline='') as f:
 rows=[{k:v for k,v in r.items() if k!='metrics'}|{'metric':m,'group':arm,**s} for r in out for m,v in r['metrics'].items() for arm,s in v.items()]
 w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
with (R/'tables/success_pairs.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(detail[0]));w.writeheader();w.writerows(detail)
print(json.dumps([r for r in out if r['iso']=='CHN' and r['age'] in ['24','40'] and r['mode']=='ever' and r['scope']=='all'],ensure_ascii=False))
