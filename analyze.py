#!/usr/bin/env python3
"""Offline full-cohort analysis. Standard library only. Run from any directory."""
import csv,gzip,hashlib,json,math,re,statistics as st
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
rows=[json.loads(s) for s in (ROOT/'runs.jsonl').open() if s.strip()]
N=len(rows); AGES=[24,30,35,40,50,65]
assert N==10000 and len({r['id'] for r in rows})==N
jobs=[json.loads(s) for s in (ROOT/'jobs.jsonl').open() if s.strip()]
assert {r['id'] for r in rows}=={r['id'] for r in jobs}
assert not (ROOT/'errors.jsonl').read_text().strip()
assert all(r['engine']=='0.8.30' and r['by']==2002 and r['opts']=={'by':2002} for r in rows)
CODES=json.loads((ROOT/'tables/codes.json').read_text())
def quant(v,p):
 v=sorted(x for x in v if isinstance(x,(int,float)) and math.isfinite(x))
 if not v:return None
 i=(len(v)-1)*p;a=int(i);return round(v[a]+(v[min(a+1,len(v)-1)]-v[a])*(i-a),3)
def med(v):return quant(v,.5)
def stat(v):return {k:quant(v,p) for k,p in [('p10',.1),('p25',.25),('median',.5),('p75',.75),('p90',.9)]}
def rate(k,n):return round(100*k/n,2) if n else None
def table(name,data):
 if not data:return
 keys=list(dict.fromkeys(k for r in data for k in r))
 with (ROOT/'tables'/name).open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(data)
def distribution(seq):
 c=Counter(seq);return [{'label':str(k),'n':v,'pct':rate(v,sum(c.values()))} for k,v in c.most_common()]
def ranks(v):
 ix=sorted(range(len(v)),key=lambda i:v[i]);out=[0]*len(v);a=0
 while a<len(ix):
  b=a+1
  while b<len(ix) and v[ix[b]]==v[ix[a]]:b+=1
  for i in ix[a:b]:out[i]=(a+b-1)/2
  a=b
 return out
def corr(a,b):
 a=ranks(a);b=ranks(b)
 if len(a)<3:return None
 ma=st.mean(a);mb=st.mean(b);den=math.sqrt(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))
 return round(sum((x-ma)*(y-mb) for x,y in zip(a,b))/den,3) if den else None
countries={};issues=Counter();meta={};raw_bytes=0;comp_bytes=0;raw_hash=hashlib.sha256()
# Read exactly one complete raw record at a time. Do not retain full lives in memory.
for i,r in enumerate(rows):
 f=ROOT/'raw'/(r['file']+'.json.gz');z=f.read_bytes();raw_hash.update(r['id'].encode()+hashlib.sha256(z).digest());comp_bytes+=len(z)
 b=gzip.decompress(z);raw_bytes+=len(b);o=json.loads(b)
 assert o['seed']==r['seed'] and o['jobId']==r['id'] and o['snaps']==r['snaps']
 assert len(o['log'])==r['nLog'] and len(o['decisions'])==r['nDecisions']
 assert o['birthState']['by']==2002
 countries[r['iso']]=o['country']['ko']
 for a in AGES:
  s=r['snaps'].get(str(a))
  if s:assert s['age']==a and s['year']==2002+a and all(isinstance(s[k],(int,float)) and math.isfinite(s[k]) for k in ['nwMed','incMed','h','hl','so'])
  if r['age']>=a and not s:issues[f'age_ge_{a}_without_snap']+=1
 years=o.get('years',[])
 meta[r['id']]={'name':o['birthState']['name']['full'],'abroad':any(y.get('cur') and y['cur']!=r['iso'] for y in years)}
 issues['birth_month_undefined']+=int('undefined' in (o.get('birthStory') or ''))
 if (i+1)%2500==0:print('Validated raw',i+1,flush=True)

def group(rs,key,label):
 snaps={}
 for a in AGES:
  ss=[r['snaps'][str(a)] for r in rs if str(a) in r['snaps']]
  snaps[str(a)]={'n':len(ss),'coverage':rate(len(ss),len(rs)),'age_ge_n':sum(r['age']>=a for r in rs),'metrics':{k:stat([s[k] for s in ss]) for k in ['money','nw','income','nwMed','incMed','h','hl','so']},'college_n':sum(s['edu']>=4 for s in ss),'married_n':sum(bool(s['married']) for s in ss),'kids_n':sum(s['kids']>0 for s in ss),'student_n':sum(s['job']=='student' for s in ss),'corr':{k:corr([s['nwMed'] for s in ss],[s[k] for s in ss]) for k in ['h','hl','so']}}
 return {'key':key,'label':label,'n':len(rs),'life':stat([r['age'] for r in rs]),'mean_age':round(st.mean(r['age'] for r in rs),2),'under5':sum(r['age']<5 for r in rs),'snaps':snaps,'education':distribution(CODES['edu'][r['edu']] for r in rs),'ever_married':sum((r.get('partnerN') or 0)>0 for r in rs),'kids':sum((r.get('kids') or 0)>0 for r in rs),'lost_child':sum((r.get('kidsLost') or 0)>0 for r in rs),'grand':sum((r.get('grand') or 0)>0 for r in rs),'abroad':sum(meta[r['id']]['abroad'] for r in rs)}
groups=[group(rows,'all','全球样本'),group([r for r in rows if r['iso']=='CHN'],'CHN','中国出生'),group([r for r in rows if r['iso']!='CHN'],'nonCHN','中国以外')]
for iso,n in Counter(r['iso'] for r in rows).most_common():
 if n>=100 and iso!='CHN':groups.append(group([r for r in rows if r['iso']==iso],iso,countries[iso]+'出生'))
qgroups=[group([r for r in rows if r['q']==q],str(q),'家境 Q'+str(q)) for q in range(1,6)]
country_q=[group([r for r in rows if r['iso']==iso and r['q']==q],iso+'_'+str(q),countries[iso]+' Q'+str(q)) for iso in ['IND','CHN','USA','NGA'] for q in [1,5]]
birth=[{'iso':iso,'country':countries[iso],'n':n,'pct':rate(n,N)} for iso,n in Counter(r['iso'] for r in rows).most_common()]
lifehist=[{'label':f'{a}–{a+4}','n':sum(a<=r['age']<a+5 for r in rows)} for a in range(0,max(r['age'] for r in rows)+1,5)]
happy=[]
for a in range(0,110,10):
 eligible=[r for r in rows if r['age']>=a]
 hits=[r for r in rows if (m:=re.match(r'(\d+)岁',r['happiest'] or '')) and a<=int(m[1])<a+10]
 happy.append({'label':f'{a}–{a+9}','n':len(hits),'eligible_n':len(eligible)})
causes=[]
for label,rs in [('<5岁',[r for r in rows if r['age']<5]),('5–49岁',[r for r in rows if 5<=r['age']<50]),('50岁及以上',[r for r in rows if r['age']>=50])]:
 for x in distribution(r['causeLabel'] for r in rs):causes.append({'age_group':label,'denominator':len(rs),**x})
# Deterministic case selection: 6 group medoids + 4 wealth/happiness combinations + 2 life outcomes.
selected=[]
def pick(rs,reason,keys,age=24,target=None):
 rs=[r for r in rs if str(age) in r['snaps'] and r['id'] not in {x[0]['id'] for x in selected}]
 if not rs:return
 m={k:med([r['snaps'][str(age)][k] for r in rs]) for k in keys};scale={k:max(.01,quant([r['snaps'][str(age)][k] for r in rs],.75)-quant([r['snaps'][str(age)][k] for r in rs],.25)) for k in keys}
 r=min(rs,key=lambda r:(sum(abs(r['snaps'][str(age)][k]-(target or m)[k])/scale[k] for k in keys),r['id']))
 selected.append((r,reason))
for iso in ['IND','CHN','NGA']:
 for q in [1,5]:pick([r for r in rows if r['iso']==iso and r['q']==q],countries[iso]+f'出生、家境 Q{q}：24 岁四项指标距本组中位数最近（按四分位距缩放）',['nwMed','incMed','h','hl'])
s40=[r for r in rows if '40' in r['snaps']];wlo=quant([r['snaps']['40']['nwMed'] for r in s40],.25);whi=quant([r['snaps']['40']['nwMed'] for r in s40],.75);hlo=quant([r['snaps']['40']['h'] for r in s40],.25);hhi=quant([r['snaps']['40']['h'] for r in s40],.75)
quadrants=[]
for w in ['高','低']:
 for h in ['高','低']:
  rs=[r for r in s40 if (r['snaps']['40']['nwMed']>=whi if w=='高' else r['snaps']['40']['nwMed']<=wlo) and (r['snaps']['40']['h']>=hhi if h=='高' else r['snaps']['40']['h']<=hlo)]
  quadrants.append({'label':f'{w}资产／{h}幸福','n':len(rs),'denominator':len(s40)})
  pick(rs,f'40 岁{w}资产／{h}幸福组合的中位数附近个案；高低指各自全体快照的上／下四分位',['nwMed','h'],40)
early=sorted([r for r in rows if r['age']<5],key=lambda r:(abs(r['age']-med([x['age'] for x in rows if x['age']<5])),r['id']))[0];selected.append((early,'5 岁前去世者中，享年最接近该组中位数；同距按 seed 排序'))
long=max(rows,key=lambda r:(r['age'],r['id']));selected.append((long,'全样本最长寿个案；同寿命按 seed 取最大值。极端个案不代表普遍情况'))
cases=[]
for r,reason in selected:
 with gzip.open(ROOT/'raw'/(r['file']+'.json.gz'),'rt') as f:o=json.load(f)
 cases.append({'id':r['id'],'name':meta[r['id']]['name'],'country':countries[r['iso']],'q':r['q'],'sex':r['sex'],'age':r['age'],'reason':reason,'birth':(o.get('birthStory') or '').replace('undefined','?'),'story':o.get('story') or '', 'cause':r['causeLabel'],'snaps':r['snaps'],'log':[{'age':x['a'],'kind':x.get('kind'),'text':x['text']} for x in o['log']],'raw':'raw/'+r['file']+'.json.gz'})
flat=[]
for r in rows:
 for age,s in r['snaps'].items():flat.append({'id':r['id'],'iso':r['iso'],'q':r['q'],'snap':age,**s})
table('snaps.csv',flat)
table('birth_country.csv',birth);table('age_at_death.csv',lifehist);table('causes.csv',causes);table('happiest_year.csv',happy);table('wealth_happiness_quadrants.csv',quadrants)
table('edu_job.csv',[{'type':'education',**x} for x in groups[0]['education']]+[{'type':'last_job',**x} for x in distribution(CODES['jobs'].get(r.get('lastJob'),r.get('lastJob') or '未记录') for r in rows)])
table('case_selection.csv',[{'id':c['id'],'name':c['name'],'reason':c['reason']} for c in cases])
table('group_age_metrics.csv',[{'group':g['label'],'group_n':g['n'],'snap':a,'n':s['n'],'coverage_pct':s['coverage'],'metric':k,**v} for g in groups+qgroups+country_q for a,s in g['snaps'].items() for k,v in s['metrics'].items()])
table('money_cny.csv',[{'group':g['label'],'birth_n':g['n'],'age':a,'snapshot_n':snap['n'],'metric':k,'unit':'CNY purchasing power; engine factor 3.5',**{q:round(v*CODES['currency']['k']/(12 if k=='monthly_income' else 1),2) if v is not None else None for q,v in snap['metrics']['income' if k=='monthly_income' else k].items()}} for g in groups+qgroups+country_q for a,snap in g['snaps'].items() for k in ['income','monthly_income','money','nw']])
table('family_mobility.csv',[{'group':g['label'],'n':g['n'],**{k:g[k] for k in ['ever_married','kids','lost_child','grand','abroad']}} for g in groups])
D={'meta':{'n':N,'countries':len(countries),'logs':sum(r['nLog'] for r in rows),'decisions':sum(r['nDecisions'] for r in rows),'raw_bytes':raw_bytes,'compressed_bytes':comp_bytes,'runs_sha256':hashlib.sha256((ROOT/'runs.jsonl').read_bytes()).hexdigest(),'raw_inventory_sha256':raw_hash.hexdigest(),'issues':dict(issues),'dream_nonnull':sum(r.get('dream') is not None for r in rows),'happy_missing':sum(not re.match(r'\d+岁',r['happiest'] or '') for r in rows),'engine':'0.8.30','date':'2026-10-24'},'groups':groups,'qgroups':qgroups,'country_q':country_q,'birth':birth,'lifehist':lifehist,'happy':happy,'causes':causes,'quadrants':quadrants,'cases':cases,'codes':CODES}
(ROOT/'tables/analysis.json').write_text(json.dumps(D,ensure_ascii=False,separators=(',',':')))
print(json.dumps({'all':groups[0],'q24':[{ 'q':g['key'],'n':g['snaps']['24']['n'],'income':g['snaps']['24']['metrics']['incMed'],'h':g['snaps']['24']['metrics']['h']} for g in qgroups],'issues':dict(issues),'cases':len(cases)},ensure_ascii=False))
