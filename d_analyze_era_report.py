# -*- coding: utf-8 -*-
"""D_era: validate archived data and compare cohorts, without rerunning the engine."""
from pathlib import Path
from collections import Counter
import json,gzip,hashlib,statistics as st
from analyze_policy_reports import stats,delta,write_csv,AGES
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'experiments/D_era';countries={'CHN':'中国','IND':'印度','NGA':'尼日利亚','KOR':'韩国'};cohorts=[1950,1960,1978,1991,2002,2020];metrics={'nw':3.5,'income':3.5/12,'nwMed':1,'incMed':1,'h':1,'hl':1,'edu':1,'pct':100}
def main():
 m=json.load(open(R/'manifest.json'));assert m['dataValidated'] and m['finishedAt'] and m['errors']==0
 src=R/'runs.jsonl';before=src.stat();rows=list(map(json.loads,src.open()));jobs=list(map(json.loads,(R/'jobs.jsonl').open()));assert len(rows)==len(jobs)==m['runs']==24000 and len({r['id'] for r in rows})==24000 and {r['id'] for r in rows}=={r['id'] for r in jobs};assert not (R/'errors.jsonl').read_text().strip()
 idx={(r['opts']['iso'],r['opts']['by'],r['seed']):r for r in rows};assert len(idx)==24000
 for iso in countries:
  for by in cohorts:
   for i in range(1,1001):assert (iso,by,f'D-{i:06}') in idx
 persona={};audit={};rawstats=[];hist=Counter();histpeople=Counter();first={};first_audit=[];names={}
 for n,r in enumerate(rows):
  iso=r['opts']['iso'];by=r['opts']['by'];key=(iso,by);p=R/'raw'/(r['file']+'.json.gz');s=p.stat();rawstats.append((p,s.st_size,s.st_mtime_ns));o=json.load(gzip.open(p,'rt'));assert o['snaps']==r['snaps'] and o['seed']==r['seed'] and o['engine']['version']=='0.8.30' and o['birthState']['by']==by
  pe=json.dumps(o['persona'],sort_keys=True);assert persona.setdefault(r['seed'],pe)==pe;co=audit.setdefault(key,Counter());co['n']+=1
  for k in ['sex','q','tal']:co[k+'_changed']+=o['birthState'][k]!=o['persona'][k]
  names[r['id']]=o['birthState']['name']['full'];seen=set()
  for z in o['log']:
   if z.get('kind')=='hist':hist[(iso,by,z['text'])]+=1;seen.add(z['text'])
  for txt in seen:histpeople[(iso,by,txt)]+=1
  owns=o['final'].get('owns') or {}
  for item in ['phone','pc','car','house']:
   age=owns.get(item);valid=isinstance(age,(int,float)) and not isinstance(age,bool) and 0<=age<=r['age'];assert age is None or valid
   first.setdefault((iso,by,item),[])
   if valid:first[iso,by,item].append(age)
   first_audit.append(dict(id=r['id'],iso=iso,by=by,item=item,recorded_age=age,recorded_year=by+age if valid else None))
  if (n+1)%4000==0:print('D raw',n+1,flush=True)
 groups=[];cells=[];pairs=[];flows=[];life_pairs=[];common=[];survival=[]
 for iso in countries:
  for by in cohorts:
   rr=[idx[iso,by,f'D-{i:06}'] for i in range(1,1001)]
   cells.append(dict(iso=iso,by=by,n=1000,life_mean=st.mean(r['age'] for r in rr),life_median=st.median(r['age'] for r in rr),survive5=sum(r['age']>=5 for r in rr)/1000,higher_edu=sum(r['edu']>=4 for r in rr)/1000,kids_mean=st.mean(r['kids'] for r in rr),future_death=sum(by+r['age']>2026 for r in rr)/1000))
   life_pairs.append(dict(iso=iso,by=by,**delta([r['age']-idx[iso,2002,r['seed']]['age'] for r in rr])))
   for age in AGES+['death']:
    ss=[r['snaps'][age] for r in rr if age in r['snaps']]
    for met,f in metrics.items():
     vals=[s[met]*f for s in ss if s[met] is not None];groups.append(dict(iso=iso,by=by,age=age,metric=met,**stats(vals),negative=sum(v<0 for v in vals)/len(vals) if vals else None))
    pp=[(idx[iso,2002,r['seed']],r) for r in rr];ok=[(x,y) for x,y in pp if age in x['snaps'] and age in y['snaps']];flows.append(dict(iso=iso,by=by,age=age,planned=1000,base_missing=sum(age not in x['snaps'] for x,y in pp),cohort_missing=sum(age not in y['snaps'] for x,y in pp),both=len(ok)))
    for met in ['nw','income','h','hl']:
     f=metrics[met];pairs.append(dict(iso=iso,by=by,age=age,metric=met,**delta([(y['snaps'][age][met]-x['snaps'][age][met])*f for x,y in ok])))
   for age in AGES:survival.append(dict(iso=iso,by=by,age=age,reached=sum(r['age']>=int(age) for r in rr),n=1000))
  for age in AGES+['death']:
   seeds=[f'D-{i:06}' for i in range(1,1001) if all(age in idx[iso,by,f'D-{i:06}']['snaps'] for by in cohorts)]
   for by in cohorts:common.append(dict(iso=iso,by=by,age=age,**stats([idx[iso,by,s]['snaps'][age]['nw']*3.5 for s in seeds])))
 history=[dict(iso=i,by=b,text=t,events=v,people=histpeople[i,b,t]) for (i,b,t),v in hist.items()];items=[dict(iso=i,by=b,item=t,birth_n=1000,retained_rate=len(v)/1000,**stats(v)) for (i,b,t),v in first.items()];aud=[dict(iso=i,by=b,**v) for (i,b),v in audit.items()]
 cases=[]
 # Four countries, fixed 1960-v-2002 comparison; select the median lifespan-difference pair, never largest benefit.
 for iso in countries:
  pp=[(idx[iso,2002,f'D-{i:06}'],idx[iso,1960,f'D-{i:06}']) for i in range(1,1001)];pp.sort(key=lambda xy:(xy[1]['age']-xy[0]['age'],xy[0]['seed']));x,y=pp[len(pp)//2];lives=[]
  for r in [x,y]:
   o=json.load(gzip.open(R/'raw'/(r['file']+'.json.gz'),'rt'));lives.append(dict(id=r['id'],by=r['opts']['by'],age=r['age'],name=names[r['id']],log=o['log']))
  cases.append(dict(iso=iso,seed=x['seed'],difference=y['age']-x['age'],lives=lives))
 for p,size,mt in rawstats:assert (p.stat().st_size,p.stat().st_mtime_ns)==(size,mt)
 assert (src.stat().st_size,src.stat().st_mtime_ns)==(before.st_size,before.st_mtime_ns)
 out=R/'tables';out.mkdir(exist_ok=True)
 for name,data in [('by_cell',cells),('age_outcomes',groups),('paired_vs_2002',pairs),('sample_flow',flows),('lifespan_pairs',life_pairs),('common_survivors',common),('survival',survival),('history_events',history),('ownership_age',items),('ownership_audit',first_audit),('birth_audit',aud)]:write_csv(out/(name+'.csv'),data)
 d=dict(n=24000,countries=countries,cohorts=cohorts,cells=cells,groups=groups,pairs=pairs,flows=flows,life_pairs=life_pairs,common=common,survival=survival,history=history,items=items,audit=aud,cases=cases,finished=m['finishedAt'],source_hash=hashlib.sha256(src.read_bytes()).hexdigest());(out/'analysis.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')));print('D DONE',flush=True)
if __name__=='__main__':main()
