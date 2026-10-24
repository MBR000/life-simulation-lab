# -*- coding: utf-8 -*-
"""B_country streamed archive validation and paired descriptive statistics."""
from pathlib import Path
import json,gzip,hashlib,statistics as st
from analyze_policy_reports import stats,delta,write_csv,AGES
ROOT=Path(__file__).resolve().parents[1];R=ROOT/'experiments/B_country';countries={'CHN':'中国','NGA':'尼日利亚','COD':'刚果（金）','IND':'印度','BRA':'巴西','USA':'美国','JPN':'日本','DEU':'德国','AUS':'澳大利亚'};metrics={'nw':3.5,'income':3.5/12,'nwMed':1,'incMed':1,'h':1,'hl':1,'pct':100,'edu':1}
def main():
 m=json.load(open(R/'manifest.json'));assert m['dataValidated'] and m['finishedAt'] and m['errors']==0
 p=R/'runs.jsonl';sz=p.stat();rr=list(map(json.loads,p.open()));jobs=list(map(json.loads,(R/'jobs.jsonl').open()));assert len(rr)==len(jobs)==18000 and len({r['id'] for r in rr})==18000 and {r['id'] for r in rr}=={j['id'] for j in jobs};assert not (R/'errors.jsonl').read_text().strip()
 idx={(r['id'][:2],r['opts']['iso'],r['seed']):r for r in rr};assert len(idx)==18000
 for ver in ['B1','B2']:
  for iso in countries:
   for i in range(1,1001):assert (ver,iso,f'B-{i:06}') in idx
 birth={};personas={};rawstats=[];actual=[];names={};overseas={}
 for n,r in enumerate(rr):
  z=R/'raw'/(r['file']+'.json.gz');s=z.stat();rawstats.append((z,s.st_size,s.st_mtime_ns));o=json.load(gzip.open(z,'rt'));assert o['snaps']==r['snaps'] and o['seed']==r['seed'] and o['engine']['version']=='0.8.30';b=o['birthState'];names[r['id']]=b['name']['full'];ver=r['id'][:2];iso=r['opts']['iso'];birth[ver,iso,r['seed']]={k:b.get(k) for k in ['sex','q','tal']}
  if ver=='B1':
   pe=json.dumps(o['persona'],sort_keys=True);assert personas.setdefault(r['seed'],pe)==pe
  actual.append(dict(version=ver,iso=iso,seed=r['seed'],sex=b['sex'],q=b['q'],changed_sex=(b['sex']!=o['persona']['sex']) if ver=='B1' else None,changed_q=(b['q']!=o['persona']['q']) if ver=='B1' else None,changed_tal=(b['tal']!=o['persona']['tal']) if ver=='B1' else None))
  overseas[r['id']]=any(y.get('cur',iso)!=iso for y in o['years'])
  if (n+1)%3000==0:print('B raw',n+1,flush=True)
 groups=[];cells=[];pairs=[];flows=[];life_pairs=[];common=[];ranges=[];audit=[]
 for ver in ['B1','B2']:
  for iso in countries:
   rs=[idx[ver,iso,f'B-{i:06}'] for i in range(1,1001)];aa=[x for x in actual if x['version']==ver and x['iso']==iso]
   cells.append(dict(version=ver,iso=iso,n=1000,life_mean=st.mean(r['age'] for r in rs),life_median=st.median(r['age'] for r in rs),survive5=sum(r['age']>=5 for r in rs)/1000,higher_edu=sum(r['edu']>=4 for r in rs)/1000,ever_overseas=sum(overseas[r['id']] for r in rs)/1000,death_partner=sum(r['snaps']['death']['married'] for r in rs)/1000,kids_mean=st.mean(r['kids'] for r in rs)))
   audit.append(dict(version=ver,iso=iso,sex_changed=sum(x['changed_sex'] is True for x in aa),q_changed=sum(x['changed_q'] is True for x in aa),tal_changed=sum(x['changed_tal'] is True for x in aa)))
   life_pairs.append(dict(version=ver,iso=iso,**delta([r['age']-idx[ver,'CHN',r['seed']]['age'] for r in rs])))
   for age in AGES+['death']:
    ss=[r['snaps'][age] for r in rs if age in r['snaps']]
    for met,factor in metrics.items():groups.append(dict(version=ver,iso=iso,age=age,metric=met,**stats([s[met]*factor for s in ss]),negative=sum(s[met]<0 for s in ss)/len(ss) if ss else None))
    pp=[(idx[ver,'CHN',r['seed']],r) for r in rs];ok=[(x,y) for x,y in pp if age in x['snaps'] and age in y['snaps']];flows.append(dict(version=ver,iso=iso,age=age,planned=1000,china_missing=sum(age not in x['snaps'] for x,y in pp),country_missing=sum(age not in y['snaps'] for x,y in pp),both=len(ok)))
    for met in ['nw','income','h','hl']:
     factor=metrics[met];pairs.append(dict(version=ver,iso=iso,age=age,metric=met,**delta([(y['snaps'][age][met]-x['snaps'][age][met])*factor for x,y in ok])))
  for age in AGES+['death']:
   seeds=[f'B-{i:06}' for i in range(1,1001) if all(age in idx[ver,iso,f'B-{i:06}']['snaps'] for iso in countries)]
   for iso in countries:
    common.append(dict(version=ver,iso=iso,age=age,**stats([idx[ver,iso,s]['snaps'][age]['nw']*3.5 for s in seeds])))
 for i in range(1,1001):
  seed=f'B-{i:06}';l={iso:idx['B1',iso,seed]['age'] for iso in countries};mn=min(l.values());mx=max(l.values());ranges.append(dict(seed=seed,minimum=mn,maximum=mx,range=mx-mn,shortest='|'.join(k for k,v in l.items() if v==mn),longest='|'.join(k for k,v in l.items() if v==mx)))
 cases=[]
 for row in sorted(ranges,key=lambda r:(-r['range'],r['seed']))[:3]:
  lives=[]
  for iso in countries:
   r=idx['B1',iso,row['seed']];o=json.load(gzip.open(R/'raw'/(r['file']+'.json.gz'),'rt'));lives.append(dict(iso=iso,id=r['id'],age=r['age'],name=names[r['id']],log=o['log'],snaps=r['snaps'],birth={k:o['birthState'][k] for k in ['sex','q','tal']}))
  cases.append(dict(seed=row['seed'],range=row['range'],lives=lives))
 for z,size,mt in rawstats:assert (z.stat().st_size,z.stat().st_mtime_ns)==(size,mt)
 assert (p.stat().st_size,p.stat().st_mtime_ns)==(sz.st_size,sz.st_mtime_ns)
 out=R/'tables';out.mkdir(exist_ok=True)
 for name,data in [('by_country',cells),('money_by_country',groups),('pairs_vs_china',pairs),('sample_flow',flows),('lifespan_pairs',life_pairs),('common_survivors',common),('per_person_range',ranges),('birth_audit',audit),('birth_details',actual)]:write_csv(out/(name+'.csv'),data)
 d=dict(n=18000,countries=countries,cells=cells,groups=groups,pairs=pairs,flows=flows,life_pairs=life_pairs,common=common,audit=audit,range_stats=stats([r['range'] for r in ranges]),cases=cases,finished=m['finishedAt'],source_hash=hashlib.sha256(p.read_bytes()).hexdigest())
 (out/'analysis.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')));print('B DONE',flush=True)
if __name__=='__main__':main()
