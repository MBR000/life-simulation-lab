# -*- coding: utf-8 -*-
"""Reproduce P4 gift aggregates from immutable batch exports. No engine execution."""
from pathlib import Path
from collections import Counter, defaultdict
import json, gzip, hashlib, csv, statistics as st, math, sys
ROOT=Path(__file__).resolve().parents[3]
AGES=['24','30','35','40','50','65']
COUNTRIES={'CHN':'中国','NGA':'尼日利亚','IND':'印度','BRA':'巴西','USA':'美国'}
METRICS={'nw':3.5,'income':3.5/12,'money':3.5,'edu':1,'h':1,'hl':1,'pct':100,'so':1}
def quant(v,p):
    if not v:return None
    v=sorted(v);t=(len(v)-1)*p;i=int(t)
    return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(t-i)
def stats(v):
    if not v:return dict(n=0,median=None,mean=None,p10=None,p90=None)
    return dict(n=len(v),median=quant(v,.5),mean=st.mean(v),p10=quant(v,.1),p90=quant(v,.9))
def delta(v):
    d=stats(v)
    if v:
        se=st.stdev(v)/math.sqrt(len(v)) if len(v)>1 else 0
        d.update(win=sum(x>0 for x in v)/len(v),lo=d['mean']-1.96*se,hi=d['mean']+1.96*se)
    return d
def write_csv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def main(exp):
    root=ROOT/'experiments'/exp;is_inv=exp=='P2_invest'
    assert exp=='P4_gift'
    arms=['full','none']
    ref=arms[0];manifest=json.loads((root/'manifest.json').read_text())
    assert manifest['dataValidated'] and manifest['finishedAt'] and manifest['errors']==0
    source=root/'runs.jsonl';before=(source.stat().st_size,source.stat().st_mtime_ns)
    rows=[json.loads(s) for s in source.open()];jobs=[json.loads(s) for s in (root/'jobs.jsonl').open()]
    assert len(rows)==len(jobs)==manifest['runs']==len(arms)*5000
    assert len({r['id'] for r in rows})==len(rows)
    assert {r['id'] for r in rows}=={r['id'] for r in jobs}
    assert not (root/'errors.jsonl').read_text().strip()
    idx={(r['opts']['iso'],r['seed'],r['id'].rsplit('_',1)[-1]):r for r in rows}
    assert len(idx)==len(rows)
    for iso in COUNTRIES:
        for seed in range(1,1001):
            for arm in arms:assert (iso,f'P-{seed:06}',arm) in idx
    extra={};birth={};evidence=Counter();band=Counter();coverage=defaultdict(Counter);exposure=Counter();costlabels=Counter()
    study_names=['证照·职训课程','夜间大学','在职研究所','高中同等学力','开放大学']
    for i,r in enumerate(rows):
        iso=r['opts']['iso'];arm=r['id'].rsplit('_',1)[-1];k=(iso,arm)
        with gzip.open(root/'raw'/(r['file']+'.json.gz'),'rt') as f:o=json.load(f)
        assert o['snaps']==r['snaps'] and o['seed']==r['seed'] and o['engine']['version']=='0.8.30'
        bh=hashlib.sha256(json.dumps(o['birthState'],sort_keys=True).encode()).hexdigest();bk=(iso,r['seed'])
        assert birth.setdefault(bk,bh)==bh
        pd=[d for d in o['decisions'] if d.get('why')=='policy:gift']
        co=coverage[k];co['people']+=1;co['policy_people']+=bool(pd);co['policy_decisions']+=len(pd)
        co['changed_people']+=any(d['picked']!=d['auto'] for d in pd)
        co['switch_people']+=bool(o['policyActs']);co['fallback_people']+=any(a.get('fallback') for a in o['policyActs'])
        first=None;first_cash=None;v='';first_cost=None;negative=False
        for y in o['years']:
            if 'v' in y:v=y['v']
            if y['a']>=18:
                exposure[(iso,arm,v or 'empty')]+=1
                if v==arm and first is None:first=y['a']
                if v=='cash' and first_cash is None:first_cash=y['a']
            age=y['a'];b='18–29' if age<30 else '30–44' if age<45 else '45–59' if age<60 else '60+'
            for label,amount in (y.get('fl') or {}).get('it',[]):
                costlabels[label]+=1
                if not is_inv and any(t in label for t in study_names) and age>=18:
                    band[(iso,arm,b,label)]+=1
                    first_cost=age if first_cost is None else min(first_cost,age)
                if is_inv and label in ['股票','全球指数','债券','股债各半基金','不动产投资','自行选股买卖']:
                    evidence[label]+=1
                    if amount<0:negative=True
        counts={t:r.get('counts',{}).get('shop_'+t,0) for t in ['course','nightuni','nightgrad','ged','openuni']}
        for t,n in counts.items():co[t+'_events']+=n;co[t+'_people']+=n>0
        co['learning_people']+=sum(counts.values())>0
        co['target_observed_people']+=first is not None;co['negative_return_people']+=negative
        for a in o['policyActs']:
            if not is_inv and a['act'] in ['ged','nightuni','nightgrad'] and a['age']>=18:
                b='18–29' if a['age']<30 else '30–44' if a['age']<45 else '45–59' if a['age']<60 else '60+'
                band[(iso,arm,b,'policyActs:'+a['act'])]+=1
        co['funeral_events']+=r.get('counts',{}).get('exp_funeral',0)
        co['funeral_people']+=r.get('counts',{}).get('exp_funeral',0)>0
        co['final_policy_matches']+=o['final'].get('gift','full')==arm
        observed=[]
        for log in o['log']:
            text=log['text'];a=log['a']
            if a<18:continue
            event=None
            if any(t in text for t in ['亲戚的丧礼','亲戚的讣告','亲戚丧礼']):event='亲戚丧礼'
            elif ('朋友' in text or '老友' in text) and ('婚礼' in text or '结婚典礼' in text or '婚宴' in text or '结婚式' in text):event='朋友婚礼'
            if event:
                observed.append(a)
                b='18–29' if a<30 else '30–44' if a<45 else '45–59' if a<60 else '60+'
                band[(iso,arm,b,event)]+=1
        first_cost=min(observed) if observed else None
        co['observed_event_people']+=bool(observed)
        co['observed_event_count']+=len(observed)
        extra[r['id']]=dict(first=first,first_cash=first_cash,first_cost=first_cost,name=o['birthState']['name']['full'],counts=counts)
        if (i+1)%5000==0:print(exp,'validated raw',i+1,flush=True)
    noise={}
    for r in map(json.loads,(ROOT/'experiments/N_noise/runs.jsonl').open()):
        if r['id'].startswith('N2-'):noise[(r['opts']['iso'],r['seed'],r['opts'].get('burn',0))]=r
    assert len(noise)==10000
    groups=[];pairs=[];life=[];cohorts=[]
    comparisons=[(a,ref) for a in arms if a!=ref]
    for iso in COUNTRIES:
        for arm in arms:
            rr=[idx[(iso,f'P-{i:06}',arm)] for i in range(1,1001)]
            life.append(dict(iso=iso,arm=arm,**stats([r['age'] for r in rr])))
            for age in AGES:
                ss=[r['snaps'][age] for r in rr if age in r['snaps']]
                for metric,factor in METRICS.items():
                    groups.append(dict(iso=iso,arm=arm,age=age,metric=metric,**stats([s[metric]*factor for s in ss]),negative=sum(s[metric]<0 for s in ss)/len(ss) if ss else None))
        for age in AGES:
            common=[i for i in range(1,1001) if all(age in idx[(iso,f'P-{i:06}',a)]['snaps'] for a in arms)]
            for arm in arms:
                for metric,factor in METRICS.items():
                    cohorts.append(dict(iso=iso,arm=arm,age=age,metric=metric,**stats([idx[(iso,f'P-{i:06}',arm)]['snaps'][age][metric]*factor for i in common])))
            nn=[(noise[(iso,f'P-{i:06}',0)],noise[(iso,f'P-{i:06}',1)]) for i in range(1,1001)]
            nn=[(x['snaps'][age],y['snaps'][age]) for x,y in nn if age in x['snaps'] and age in y['snaps']]
            for arm,base in comparisons:
                pp=[(idx[(iso,f'P-{i:06}',base)],idx[(iso,f'P-{i:06}',arm)]) for i in range(1,1001)]
                pp=[(x,y) for x,y in pp if age in x['snaps'] and age in y['snaps']]
                for mode in ['all','executed']:
                    selected=pp if mode=='all' else [(x,y) for x,y in pp if (extra[y['id']]['first' if is_inv else 'first_cost']) is not None and (extra[y['id']]['first' if is_inv else 'first_cost'])<=int(age)]
                    for metric,factor in METRICS.items():
                        pairs.append(dict(iso=iso,arm=arm,base=base,age=age,mode=mode,metric=metric,**delta([(y['snaps'][age][metric]-x['snaps'][age][metric])*factor for x,y in selected]),left=stats([x['snaps'][age][metric]*factor for x,y in selected]),right=stats([y['snaps'][age][metric]*factor for x,y in selected]),noise=delta([(y[metric]-x[metric])*factor for x,y in nn])))
    cases=[]
    for arm in arms[1:]:
        pp=[(idx[('CHN',f'P-{i:06}',ref)],idx[('CHN',f'P-{i:06}',arm)]) for i in range(1,1001)]
        pp=[(x,y) for x,y in pp if '40' in x['snaps'] and '40' in y['snaps']]
        pp.sort(key=lambda p:(p[1]['snaps']['40']['nw']-p[0]['snaps']['40']['nw'],p[0]['seed']))
        for position,label in [(len(pp)//10,'配对差第10百分位附近'),(len(pp)//2,'配对差中位附近'),(len(pp)*9//10,'配对差第90百分位附近')]:
            x,y=pp[position];lives=[]
            for r in [x,y]:
                o=json.load(gzip.open(root/'raw'/(r['file']+'.json.gz'),'rt'))
                lives.append(dict(id=r['id'],arm=r['id'].rsplit('_',1)[-1],name=extra[r['id']]['name'],snaps=r['snaps'],log=o['log'],decisions=[d for d in o['decisions'] if d.get('why','').startswith('policy:')],acts=o['policyActs']))
            cases.append(dict(arm=arm,seed=x['seed'],reason=label,lives=lives))
    out=root/'tables';out.mkdir(exist_ok=True)
    coverage_rows=[dict(iso=k[0],arm=k[1],**{a:v[a] for a in sorted(set().union(*(set(c) for c in coverage.values())))}) for k,v in coverage.items()]
    exp_rows=[dict(iso=k[0],arm=k[1],state=k[2],years=n) for k,n in sorted(exposure.items())]
    band_rows=[dict(iso=k[0],arm=k[1],band=k[2],event=k[3],n=n) for k,n in sorted(band.items())]
    for name,data in [('groups',groups),('common_survivors',cohorts),('coverage',coverage_rows),('exposure',exp_rows),('event_bands',band_rows),('lifespan',life)]:write_csv(out/(name+'.csv'),data)
    write_csv(out/'pairs.csv',[{**{k:v for k,v in r.items() if k not in ['left','right','noise']}, **{side+'_'+k:v for side in ['left','right','noise'] for k,v in r[side].items()}} for r in pairs])
    d=dict(experiment=exp,n=len(rows),countries=COUNTRIES,arms=arms,ref=ref,groups=groups,common=cohorts,pairs=pairs,coverage=coverage_rows,exposure=exp_rows,bands=band_rows,life=life,cases=cases,source_hash=hashlib.sha256(source.read_bytes()).hexdigest(),finished=manifest['finishedAt'],cost_labels=costlabels,investment_labels=evidence)
    assert before==(source.stat().st_size,source.stat().st_mtime_ns)
    (out/'analysis.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
    print(exp,'DONE',len(rows),len(pairs),flush=True)
if __name__=='__main__':main(sys.argv[1])
