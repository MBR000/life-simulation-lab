"""Stream and validate C_strategy archives; never execute simulations."""
from pathlib import Path
from collections import Counter
import json,gzip,hashlib,os,math,statistics as st
from analyze_policy_reports import stats,delta,write_csv,AGES,METRICS
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'experiments/C_strategy';arms=['drift','random','study','abroad','stock','all'];countries={'CHN':'中国','NGA':'尼日利亚','USA':'美国'}
def main():
 m=json.loads((R/'manifest.json').read_text());assert m['dataValidated'] and m['finishedAt'] and m['errors']==0
 src=R/'runs.jsonl';before=src.stat();rows=list(map(json.loads,src.open()));jobs=list(map(json.loads,(R/'jobs.jsonl').open()));assert len(rows)==len(jobs)==m['runs']==18000
 assert len({r['id'] for r in rows})==18000 and {r['id'] for r in rows}=={r['id'] for r in jobs};assert not (R/'errors.jsonl').read_text().strip()
 idx={(r['opts']['iso'],r['seed'],r['id'].rsplit('_',1)[1]):r for r in rows};assert len(idx)==18000
 for iso in countries:
  for i in range(1,1001):
   for arm in arms:assert (iso,f'C-{i:06}',arm) in idx
 birth={};extra={};coverage=[];rawstats=[];cov={};audit=[]
 for n,r in enumerate(rows):
  iso=r['opts']['iso'];arm=r['id'].rsplit('_',1)[1];p=R/'raw'/(r['file']+'.json.gz');s=p.stat();rawstats.append((p,s.st_size,s.st_mtime_ns));o=json.load(gzip.open(p,'rt'))
  assert o['snaps']==r['snaps'] and o['seed']==r['seed'] and o['engine']['version']=='0.8.30'
  h=hashlib.sha256(json.dumps(o['birthState'],sort_keys=True).encode()).hexdigest();assert birth.setdefault((iso,r['seed']),h)==h
  c=cov.setdefault((iso,arm),Counter());c['people']+=1
  ev={k:[] for k in ['changed','study','abroad','invest']}
  for z in o['decisions']:
   if z['picked']!=z['auto'] and (z['why']=='random' or z['why'].startswith('policy:')):ev['changed'].append(z['age'])
   if z['why'].startswith('policy:'):c[z['why']+'_decisions']+=1
  for z in o['policyActs']:
   if z['act'] in ['ged','nightuni','nightgrad']:ev['study'].append(z['age'])
  for y in o['years']:
   age=y['a']
   if age>=18 and any(any(t in lab for t in ['证照·职训课程','夜间大学','在职研究所','高中同等学力','开放大学']) and val<0 for lab,val in (y.get('fl') or {}).get('it',[])):ev['study'].append(age)
   if age>=18 and y.get('cur',iso)!=iso:ev['abroad'].append(age)
  # Country and assets are complete in fixed-age snapshots; supplement compressed year fields.
  for age,z in o['snaps'].items():
   if age=='death':continue
   if int(age)>=18 and z['cur']!=iso:ev['abroad'].append(int(age))
   if z.get('invest')==('world' if arm=='all' else 'stock') and z['money']>0:ev['invest'].append(int(age))
  first={k:min(v) if v else None for k,v in ev.items()};target={'random':['changed'],'study':['study'],'abroad':['abroad'],'stock':['invest'],'all':['study','abroad','invest']}.get(arm,[])
  first['executed']=max(first[k] for k in target) if target and all(first[k] is not None for k in target) else None
  for k in ev:c[k+'_people']+=first[k] is not None
  c['executed_people']+=first['executed'] is not None
  extra[r['id']]=dict(first=first,name=o['birthState']['name']['full']);audit.append(dict(id=r['id'],birth_hash=h,**first))
  if (n+1)%3000==0:print('raw validated',n+1,flush=True)
 keys=sorted(set().union(*(c.keys() for c in cov.values())))
 coverage=[dict(iso=i,arm=a,**{k:c[k] for k in keys}) for (i,a),c in cov.items()]
 groups=[];common=[];pairs=[];life=[];lifepairs=[];flows=[];survival=[];cells=[];ranges=[]
 for iso in countries:
  for arm in arms:
   rr=[idx[iso,f'C-{i:06}',arm] for i in range(1,1001)]
   life.append(dict(iso=iso,arm=arm,**stats([r['age'] for r in rr])))
   cells.append(dict(iso=iso,arm=arm,n=1000,life_mean=st.mean(r['age'] for r in rr),life_median=st.median(r['age'] for r in rr),higher_edu_rate=sum(r['edu']>=4 for r in rr)/1000,death_nw_cny_median=st.median(r['snaps']['death']['nw']*3.5 for r in rr)))
   for age in AGES:
    ss=[r['snaps'][age] for r in rr if age in r['snaps']];survival.append(dict(iso=iso,arm=arm,age=age,n=1000,reached=sum(r['age']>=int(age) for r in rr)))
    for metric,factor in METRICS.items():groups.append(dict(iso=iso,arm=arm,age=age,metric=metric,**stats([s[metric]*factor for s in ss]),negative=sum(s[metric]<0 for s in ss)/len(ss) if ss else None))
   if arm!='drift':lifepairs.append(dict(iso=iso,arm=arm,**delta([r['age']-idx[iso,r['seed'],'drift']['age'] for r in rr])))
  for age in AGES:
   cc=[i for i in range(1,1001) if all(age in idx[iso,f'C-{i:06}',a]['snaps'] for a in arms)]
   for a in arms:
    for metric,factor in METRICS.items():common.append(dict(iso=iso,arm=a,age=age,metric=metric,**stats([idx[iso,f'C-{i:06}',a]['snaps'][age][metric]*factor for i in cc])))
   for arm in arms[1:]:
    pp=[(idx[iso,f'C-{i:06}','drift'],idx[iso,f'C-{i:06}',arm]) for i in range(1,1001)];ok=[(x,y) for x,y in pp if age in x['snaps'] and age in y['snaps']]
    flows.append(dict(iso=iso,arm=arm,age=age,planned=1000,base_missing=sum(age not in x['snaps'] for x,y in pp),arm_missing=sum(age not in y['snaps'] for x,y in pp),both=len(ok)))
    for mode in ['all','executed']:
     sel=ok if mode=='all' else [(x,y) for x,y in ok if extra[y['id']]['first']['executed'] is not None and extra[y['id']]['first']['executed']<=int(age)]
     for metric,factor in METRICS.items():pairs.append(dict(iso=iso,arm=arm,base='drift',age=age,mode=mode,metric=metric,**delta([(y['snaps'][age][metric]-x['snaps'][age][metric])*factor for x,y in sel]),left=stats([x['snaps'][age][metric]*factor for x,y in sel]),right=stats([y['snaps'][age][metric]*factor for x,y in sel])))
  for i in range(1,1001):
   rr=[idx[iso,f'C-{i:06}',a] for a in arms];ranges.append(dict(kind='within_country',key=iso,seed=f'C-{i:06}',life_range=max(r['age'] for r in rr)-min(r['age'] for r in rr),death_nw_cny_range=(max(r['snaps']['death']['nw'] for r in rr)-min(r['snaps']['death']['nw'] for r in rr))*3.5))
 for a in arms:
  for i in range(1,1001):
   rr=[idx[iso,f'C-{i:06}',a] for iso in countries];ranges.append(dict(kind='across_countries',key=a,seed=f'C-{i:06}',life_range=max(r['age'] for r in rr)-min(r['age'] for r in rr),death_nw_cny_range=(max(r['snaps']['death']['nw'] for r in rr)-min(r['snaps']['death']['nw'] for r in rr))*3.5))
 variance=[]
 for metric in ['lifespan','death_pct','death_edu','death_log_nonnegative_nw']:
  val=lambda r:r['age'] if metric=='lifespan' else r['snaps']['death']['pct'] if metric=='death_pct' else r['snaps']['death']['edu'] if metric=='death_edu' else math.log1p(max(0,r['snaps']['death']['nw']))
  grand=st.mean(map(val,rows));cm={i:st.mean(val(r) for r in rows if r['opts']['iso']==i) for i in countries};am={a:st.mean(val(r) for r in rows if r['id'].endswith('_'+a)) for a in arms};cell={(i,a):st.mean(val(idx[i,f'C-{n:06}',a]) for n in range(1,1001)) for i in countries for a in arms}
  total=sum((val(r)-grand)**2 for r in rows);ss={'country':6000*sum((v-grand)**2 for v in cm.values()),'strategy':3000*sum((v-grand)**2 for v in am.values()),'interaction':1000*sum((v-cm[i]-am[a]+grand)**2 for (i,a),v in cell.items()),'residual':sum((val(r)-cell[r['opts']['iso'],r['id'].rsplit('_',1)[1]])**2 for r in rows)};assert abs(sum(ss.values())-total)<max(1,total)*1e-8
  variance.extend(dict(metric=metric,component=k,ss=v,share=v/total) for k,v in ss.items())
 cases=[]
 for arm in arms[1:]:
  pp=[(idx['CHN',f'C-{i:06}','drift'],idx['CHN',f'C-{i:06}',arm]) for i in range(1,1001)];pp=[(x,y) for x,y in pp if '40' in x['snaps'] and '40' in y['snaps']];pp.sort(key=lambda xy:(xy[1]['snaps']['40']['nw']-xy[0]['snaps']['40']['nw'],xy[0]['seed']))
  for fraction,label in [(.1,'第10百分位附近'),(.5,'中位附近'),(.9,'第90百分位附近')]:
   x,y=pp[int((len(pp)-1)*fraction)];lives=[]
   for r in [x,y]:
    o=json.load(gzip.open(R/'raw'/(r['file']+'.json.gz'),'rt'));lives.append(dict(id=r['id'],arm=r['id'].rsplit('_',1)[1],name=extra[r['id']]['name'],snaps=r['snaps'],log=o['log'],acts=o['policyActs'],decisions=[z for z in o['decisions'] if z['why']!='auto']))
   cases.append(dict(arm=arm,seed=x['seed'],reason=label,lives=lives))
 out=R/'tables';out.mkdir(exist_ok=True)
 for name,data in [('groups',groups),('common_survivors',common),('coverage',coverage),('lifespan',life),('lifespan_pairs',lifepairs),('sample_flow',flows),('survival',survival),('by_cell',cells),('variance_decomp',variance),('per_person_range',ranges),('execution_audit',audit)]:write_csv(out/(name+'.csv'),data)
 write_csv(out/'pairs.csv',[{**{k:v for k,v in r.items() if k not in ['left','right']},**{s+'_'+k:v for s in ['left','right'] for k,v in r[s].items()}} for r in pairs])
 for p,size,mt in rawstats:assert (p.stat().st_size,p.stat().st_mtime_ns)==(size,mt)
 assert (src.stat().st_size,src.stat().st_mtime_ns)==(before.st_size,before.st_mtime_ns)
 d=dict(experiment='C_strategy',n=18000,countries=countries,arms=arms,groups=groups,common=common,pairs=pairs,life=life,lifepairs=lifepairs,coverage=coverage,flows=flows,survival=survival,variance=variance,cells=cells,cases=cases,ranges=[dict(kind=k,key=j,**stats([x['life_range'] for x in ranges if x['kind']==k and x['key']==j])) for k,j in sorted({(x['kind'],x['key']) for x in ranges})],finished=m['finishedAt'],source_hash=hashlib.sha256(src.read_bytes()).hexdigest())
 (out/'analysis.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')));print('DONE',len(rows),len(birth),flush=True)
if __name__=='__main__':main()
