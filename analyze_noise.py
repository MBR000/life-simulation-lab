"""N1 paired sensitivity check; no rerun of the simulator. Standard library only."""
from pathlib import Path
import json,csv,gzip,statistics as st,math,hashlib
R=Path(__file__).resolve().parents[1];N=R.parent/'N_noise'
a={r['seed']:r for r in map(json.loads,(R/'runs.jsonl').open())}
b=[r for r in map(json.loads,(N/'runs.jsonl').open()) if r['id'].startswith('N1-')]
b.sort(key=lambda r:r['seed']); assert len(b)==len({r['seed'] for r in b})==2000
assert {r['seed'] for r in b}=={f'A-{i:06d}' for i in range(1,2001)}
assert not (N/'errors.jsonl').read_text().strip()
pairs=[(a[r['seed']],r) for r in b]
for x,y in pairs:
 assert x['opts']=={'by':2002} and y['opts']=={'by':2002,'burn':1}
 assert x['engine']==y['engine']=='0.8.30'
 with gzip.open(R/'raw'/(x['file']+'.json.gz'),'rt') as f:ox=json.load(f)
 with gzip.open(N/'raw'/(y['file']+'.json.gz'),'rt') as f:oy=json.load(f)
 assert ox['birthState']==oy['birthState'],x['seed']
 assert ox['snaps']==x['snaps'] and oy['snaps']==y['snaps']
def med(v):return st.median(v) if v else None
def rnd(v):return round(v,4) if v is not None else None
def ranks(v):
 ids=sorted(range(len(v)),key=v.__getitem__);out=[0]*len(v);i=0
 while i<len(ids):
  j=i+1
  while j<len(ids) and v[ids[j]]==v[ids[i]]:j+=1
  for k in ids[i:j]:out[k]=(i+j-1)/2
  i=j
 return out
def rho(ss):
 x=ranks([s['nwMed'] for s in ss]);y=ranks([s['h'] for s in ss]);mx=st.mean(x);my=st.mean(y)
 den=math.sqrt(sum((v-mx)**2 for v in x)*sum((v-my)**2 for v in y))
 return sum((v-mx)*(w-my) for v,w in zip(x,y))/den if den else None
rows=[];survival=[]
for age in ['24','30','35','40','50','65']:
 xs=[x['snaps'][age] for x,y in pairs if age in x['snaps']];ys=[y['snaps'][age] for x,y in pairs if age in y['snaps']]
 common=[(x['snaps'][age],y['snaps'][age]) for x,y in pairs if age in x['snaps'] and age in y['snaps']]
 survival.append({'age':age,'a':len(xs),'b':len(ys),'both':len(common),'a_only':len(xs)-len(common),'b_only':len(ys)-len(common),'neither':2000-len(xs)-len(ys)+len(common)})
 def add(label,va,vb,unit):rows.append({'age':age,'metric':label,'a':rnd(va),'b':rnd(vb),'delta':rnd(vb-va),'unit':unit,'a_n':len(xs),'b_n':len(ys)})
 add('存活快照覆盖率',len(xs)/20,len(ys)/20,'百分点')
 for label,k,div in [('年收入','income',1),('月均收入','income',12),('现金余额','money',1),('净资产','nw',1)]:add(label,med([s[k] for s in xs])*3.5/div,med([s[k] for s in ys])*3.5/div,'元，中位数')
 for label,k in [('幸福','h'),('健康','hl')]:add(label,med([s[k] for s in xs]),med([s[k] for s in ys]),'分，中位数')
 add('大学及以上',100*sum(s['edu']>=4 for s in xs)/len(xs),100*sum(s['edu']>=4 for s in ys)/len(ys),'百分点')
 add('资产与幸福相关',rho(xs),rho(ys),'Spearman ρ')
paired=[]
for age in ['24','40','65','death']:
 ss=[(x['snaps'][age],y['snaps'][age]) for x,y in pairs if age in x['snaps'] and age in y['snaps']]
 for label,k,factor in [('年收入','income',3.5),('净资产','nw',3.5),('幸福','h',1),('健康','hl',1)]:
  ds=[(y[k]-x[k])*factor for x,y in ss];paired.append({'age':age,'metric':label,'n':len(ds),'mean_delta':rnd(st.mean(ds)),'sd_delta':rnd(st.stdev(ds)),'mean_abs_delta':rnd(st.mean(abs(v) for v in ds)),'median_abs_delta':rnd(med([abs(v) for v in ds]))})
life_d=[y['age']-x['age'] for x,y in pairs]
life={'a_median':med([x['age'] for x,y in pairs]),'b_median':med([y['age'] for x,y in pairs]),'a_mean':rnd(st.mean(x['age'] for x,y in pairs)),'b_mean':rnd(st.mean(y['age'] for x,y in pairs)),'mean_delta':rnd(st.mean(life_d)),'mean_abs_delta':rnd(st.mean(abs(v) for v in life_d)),'sd_delta':rnd(st.stdev(life_d)),'changed_n':sum(v!=0 for v in life_d),'edu_changed_n':sum(x['edu']!=y['edu'] for x,y in pairs),'cause_changed_n':sum(x['cause']!=y['cause'] for x,y in pairs)}
q=[]
for arm in [0,1]:
 for v in [1,5]:
  rs=[p[arm]['snaps']['24'] for p in pairs if p[arm]['q']==v and '24' in p[arm]['snaps']]
  q.append({'arm':'A' if arm==0 else 'N1','q':v,'n':len(rs),'college_pct':rnd(100*sum(s['edu']>=4 for s in rs)/len(rs)),'income_median':rnd(med([s['income'] for s in rs])*3.5)})
def csvout(name,data):
 with (R/'tables'/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
csvout('noise_group.csv',rows);csvout('noise_paired.csv',paired);csvout('noise_survival.csv',survival);csvout('noise_q.csv',q)
d={'n':2000,'birth_verified':True,'groups':rows,'survival':survival,'paired':paired,'life':life,'q':q,'source_sha256':hashlib.sha256((N/'runs.jsonl').read_bytes()).hexdigest()}
(R/'tables/noise_analysis.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
print(json.dumps({'age24':[r for r in rows if r['age']=='24'],'life':life,'q':q,'survival24':survival[0]},ensure_ascii=False,indent=2))
