from pathlib import Path
import json,gzip,statistics as st,math,csv,hashlib
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];COUNTRIES={'NGA':'尼日利亚','IND':'印度','CHN':'中国','BRA':'巴西','USA':'美国'};AGES=['24','30','35','40','50','65','death']
rows=[json.loads(s) for s in (R/'runs.jsonl').open()];jobs=[json.loads(s) for s in (R/'jobs.jsonl').open()]
assert len(rows)==len(jobs)==10000 and len({r['id'] for r in rows})==10000
assert {r['id'] for r in rows}=={r['id'] for r in jobs} and not (R/'errors.jsonl').read_text().strip()
idx={(r['opts']['iso'],r['seed'],r['opts']['policy']['abroad']):r for r in rows};noise={}
for r in map(json.loads,(R.parent/'N_noise/runs.jsonl').open()):
 if r['id'].startswith('N2-'):noise[(r['opts']['iso'],r['seed'],r['opts'].get('burn',0))]=r
assert len(noise)==10000
birth={};extra={};decision_ids=Counter()
for i,r in enumerate(rows):
 iso=r['opts']['iso'];arm=r['opts']['policy']['abroad'];assert r['engine']=='0.8.30' and r['opts']=={'by':2002,'iso':iso,'persona':True,'policy':{'abroad':arm}}
 with gzip.open(R/'raw'/(r['file']+'.json.gz'),'rt') as f:o=json.load(f)
 assert o['snaps']==r['snaps'] and o['seed']==r['seed']
 key=(iso,r['seed']);bs=o['birthState']
 if key in birth:assert birth.pop(key)==bs
 else:birth[key]=bs
 foreign=[y for y in o['years'] if y.get('cur') and y['cur']!=bs['born']]
 pd=[d for d in o['decisions'] if d.get('why')=='policy:abroad'];decision_ids.update(d['id'] for d in pd)
 ex={'ever':bool(foreign),'first_age':foreign[0]['a'] if foreign else None,'first_country':foreign[0]['cur'] if foreign else None,'pol_n':len(pd),'changed_n':sum(d['picked']!=d['auto'] for d in pd),'acts':len(o['policyActs']),'attempts':sum(x['act']=='moveplan:abroad' for x in o['policyActs']),'name':bs['name']['full'],'final_abroad':o['final']['cur']!=bs['born'],'plan_proxy':o['final']['cur']!=bs['born'] or bool(o['final'].get('mig'))}
 extra[r['id']]=ex
 if (i+1)%2500==0:print('raw',i+1,flush=True)
assert not birth
for iso in COUNTRIES:
 for i in range(1,1001):
  seed=f'P-{i:06d}'
  for arm in ['seek','avoid']:assert (iso,seed,arm) in idx
  for burn in [0,1]:
   n=noise[(iso,seed,burn)];assert n['engine']=='0.8.30' and n['opts']=={'by':2002,'iso':iso,'persona':True,**({'burn':1} if burn else {})}
def q(v,p):
 v=sorted(v)
 if not v:return None
 i=(len(v)-1)*p;a=int(i);return round(v[a]+(v[min(a+1,len(v)-1)]-v[a])*(i-a),4)
def stats(v):return {'n':len(v),'mean':st.mean(v) if v else None,'median':q(v,.5),'p10':q(v,.1),'p90':q(v,.9)}
def diff(v):
 if not v:return {'n':0}
 m=st.mean(v);se=st.stdev(v)/math.sqrt(len(v)) if len(v)>1 else 0
 return {'n':len(v),'mean':m,'median':q(v,.5),'lo':m-1.96*se,'hi':m+1.96*se,'abs':st.mean(abs(x) for x in v),'p025':q(v,.025),'p975':q(v,.975)}
metrics={'income_cny':('income',3.5),'monthly_cny':('income',3.5/12),'money_cny':('money',3.5),'nw_cny':('nw',3.5),'incMed':('incMed',1),'nwMed':('nwMed',1),'h':('h',1),'hl':('hl',1),'so':('so',1)}
arms=[];age_rows=[];pairs=[];cover=[];dest=[];qcov=[]
for iso in COUNTRIES:
 for arm in ['avoid','seek']:
  rs=[idx[(iso,f'P-{i:06d}',arm)] for i in range(1,1001)];es=[extra[r['id']] for r in rs]
  arms.append({'iso':iso,'arm':arm,'n':len(rs),'age':stats([r['age'] for r in rs]),'ever_n':sum(e['ever'] for e in es),'final_abroad_n':sum(e['final_abroad'] for e in es),'proxy_n':sum(e['plan_proxy'] for e in es),'first_age':stats([e['first_age'] for e in es if e['ever']]),'college_n':sum(r['edu']>=4 for r in rs)})
  cover.append({'iso':iso,'arm':arm,'n':1000,'policy_people':sum(e['pol_n']>0 for e in es),'policy_events':sum(e['pol_n'] for e in es),'changed_people':sum(e['changed_n']>0 for e in es),'attempt_people':sum(e['attempts']>0 for e in es),'attempt_events':sum(e['attempts'] for e in es),'ever_n':sum(e['ever'] for e in es)})
  for qq in range(1,6):
   rr=[r for r in rs if r['q']==qq];qcov.append({'iso':iso,'arm':arm,'q':qq,'n':len(rr),'ever_n':sum(extra[r['id']]['ever'] for r in rr),'attempt_n':sum(extra[r['id']]['attempts']>0 for r in rr)})
  for age in AGES:
   ss=[r['snaps'][age] for r in rs if age in r['snaps']];age_rows.append({'iso':iso,'arm':arm,'age':age,'n':len(ss),'metrics':{k:stats([s[field]*factor for s in ss]) for k,(field,factor) in metrics.items()},'outside_n':sum(s['cur']!=iso for s in ss)})
  if arm=='seek':
   for country,n in Counter(r['where'] for r in rs).most_common():dest.append({'iso':iso,'country':country,'n':n})
 pp=[(idx[(iso,f'P-{i:06d}','avoid')],idx[(iso,f'P-{i:06d}','seek')]) for i in range(1,1001)]
 nn=[(noise[(iso,f'P-{i:06d}',0)],noise[(iso,f'P-{i:06d}',1)]) for i in range(1,1001)]
 pairs.append({'iso':iso,'age':'life','metric':'lifespan','effect':diff([y['age']-x['age'] for x,y in pp]),'noise':diff([y['age']-x['age'] for x,y in nn])})
 for age in AGES:
  cc=[(x['snaps'][age],y['snaps'][age]) for x,y in pp if age in x['snaps'] and age in y['snaps']];nc=[(x['snaps'][age],y['snaps'][age]) for x,y in nn if age in x['snaps'] and age in y['snaps']]
  for k,(field,factor) in metrics.items():pairs.append({'iso':iso,'age':age,'metric':k,'effect':diff([(y[field]-x[field])*factor for x,y in cc]),'noise':diff([(y[field]-x[field])*factor for x,y in nc])})
# One representative pair per country: closest to median paired 40-year asset change among common survivors.
cases=[]
for iso in COUNTRIES:
 pp=[(idx[(iso,f'P-{i:06d}','avoid')],idx[(iso,f'P-{i:06d}','seek')]) for i in range(1,1001)];pp=[(x,y) for x,y in pp if '40' in x['snaps'] and '40' in y['snaps']]
 mid=st.median(y['snaps']['40']['nwMed']-x['snaps']['40']['nwMed'] for x,y in pp)
 x,y=min(pp,key=lambda p:(abs((p[1]['snaps']['40']['nwMed']-p[0]['snaps']['40']['nwMed'])-mid),p[0]['seed']))
 lives=[]
 for r in [x,y]:
  with gzip.open(R/'raw'/(r['file']+'.json.gz'),'rt') as f:o=json.load(f)
  lives.append({'arm':r['opts']['policy']['abroad'],'name':extra[r['id']]['name'],'age':r['age'],'cause':r['causeLabel'],'birth':o['birthStory'].replace('undefined','?'),'story':o['story'],'snaps':r['snaps'],'extra':extra[r['id']],'log':[{'age':l['a'],'text':l['text']} for l in o['log']]})
 cases.append({'iso':iso,'seed':x['seed'],'reason':'两臂均有40岁快照者中，净资产倍数配对差最接近本国中位差；平局按seed。不是效应最大的个案。','lives':lives})
def writecsv(name,data):
 with (R/'tables'/name).open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
writecsv('coverage.csv',cover);writecsv('coverage_q.csv',qcov);writecsv('abroad_dest.csv',dest)
writecsv('by_arm.csv',[{**{k:v for k,v in a.items() if k not in ['age','first_age']},'mean_age':a['age']['mean'],'median_age':a['age']['median'],'first_abroad_median_age':a['first_age']['median']} for a in arms])
writecsv('by_arm_age.csv',[{'iso':r['iso'],'arm':r['arm'],'age':r['age'],'metric':k,**s} for r in age_rows for k,s in r['metrics'].items()])
writecsv('paired_diff.csv',[{'iso':p['iso'],'age':p['age'],'metric':p['metric'],**{'effect_'+k:v for k,v in p['effect'].items()},**{'noise_'+k:v for k,v in p['noise'].items()}} for p in pairs])
D={'countries':COUNTRIES,'n':10000,'pairs_n':5000,'ages':AGES,'arms':arms,'ages_data':age_rows,'pairs':pairs,'coverage':cover,'dest':dest,'q':qcov,'cases':cases,'decision_ids':dict(decision_ids),'source_hash':hashlib.sha256((R/'runs.jsonl').read_bytes()).hexdigest(),'noise_hash':hashlib.sha256((R.parent/'N_noise/runs.jsonl').read_bytes()).hexdigest()}
(R/'tables/analysis.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
print(json.dumps({'coverage':cover,'life':[p for p in pairs if p['age']=='life']},ensure_ascii=False))
