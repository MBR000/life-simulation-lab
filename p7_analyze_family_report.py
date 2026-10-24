# -*- coding: utf-8 -*-
"""Reproduce P7 family policy aggregates from immutable batch exports. No engine execution."""
from pathlib import Path
from collections import Counter, defaultdict
import json, gzip, hashlib, csv, statistics as st, math, sys
ROOT=Path(__file__).resolve().parents[1]
AGES=['24','30','35','40','50','65']
COUNTRIES={'CHN':'中国','NGA':'尼日利亚','IND':'印度','BRA':'巴西','USA':'美国'}
METRICS={'nw':3.5,'income':3.5/12,'money':3.5,'edu':1,'h':1,'hl':1,'pct':100,'so':1,'nConds':1}
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
    assert exp == 'P7_family'
    insurance=exp=='P5_ins'
    arms=['drift','single','nokids']
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
    extra={};birth={};evidence=Counter();band=Counter();coverage=defaultdict(Counter);exposure=Counter();costlabels=Counter();old=[];reasons=[];family_age=[]
    raw_stats=[]
    for i,r in enumerate(rows):
        iso=r['opts']['iso'];arm=r['id'].rsplit('_',1)[-1];k=(iso,arm)
        path=root/'raw'/(r['file']+'.json.gz');raw_stats.append((str(path),path.stat().st_size,path.stat().st_mtime_ns))
        with gzip.open(path,'rt') as f:o=json.load(f)
        assert o['snaps']==r['snaps'] and o['seed']==r['seed'] and o['engine']['version']=='0.8.30'
        bh=hashlib.sha256(json.dumps(o['birthState'],sort_keys=True).encode()).hexdigest();bk=(iso,r['seed'])
        assert birth.setdefault(bk,bh)==bh
        pd=[d for d in o['decisions'] if d.get('why')=='policy:family']
        co=coverage[k];co['people']+=1;co['adult_people']+=r['age']>=18;co['policy_people']+=bool(pd);co['policy_decisions']+=len(pd)
        co['changed_people']+=any(d['picked']!=d['auto'] for d in pd)
        co['union_history_missing']+='pN' not in o['summary']
        co['ever_union_people']+=(o['summary'].get('pN',0) or 0)>0
        co['ever_birth_people']+=o['stats'].get('kidsBorn',0)>0
        co['kids_born']+=o['stats'].get('kidsBorn',0)
        co['final_legal_union_people']+=o['summary'].get('pU')=='m'
        co['final_nonlegal_union_people']+=o['summary'].get('pU')=='none'
        forced=[l for l in o['log'] if '你没能说服他们，婚礼还是举行了' in l['text']]
        co['forced_marriage_people']+=bool(forced)
        if arm=='single' and (o['summary'].get('pN',0) or 0)>0:
            reason='明确拒绝早婚仍举行' if forced else '末段结合为未登记同居' if o['summary'].get('pU')=='none' else '其他结合记录，不能仅凭pN确认为法律婚姻'
            reasons.append(dict(id=r['id'],iso=iso,arm=arm,reason=reason,pN=o['summary'].get('pN'),pU=o['summary'].get('pU'),evidence=' / '.join(l['text'] for l in forced)))
        fam=o['final']['fam'];kids=fam.get('kids',[])
        if arm=='nokids' and o['stats'].get('kidsBorn',0)>0:
            own=[c for c in kids if not c.get('step') and isinstance(c.get('bornAt'),(int,float))]
            firstborn=min((c['bornAt'] for c in own),default=None)
            preg=[z for z in o['decisions'] if z['id']=='datepreg' and z['age']==firstborn]
            why='首次子女记录同年发生恋人怀孕抉择' if preg else '首次子女前有拒绝早婚失败记录' if any(l['a']<=(firstborn or -1) for l in forced) else '其他生育路径，未按关键词归因'
            reasons.append(dict(id=r['id'],iso=iso,arm=arm,reason=why,pN=o['summary'].get('pN'),pU=o['summary'].get('pU'),evidence=' / '.join(str(z['age'])+'岁 datepreg:'+z['picked'] for z in preg)))
        for age in AGES:
            if age not in r['snaps']:continue
            snap=r['snaps'][age]
            # Use only birth timing, never future survival/health/outcome success.
            births=[c for c in kids if isinstance(c.get('bornAt'),(int,float)) and c['bornAt']<=int(age) and not c.get('step')]
            state_ok=(not snap['married'] and any(d['age']<=int(age) for d in pd)) if arm=='single' else (snap['married'] and not births and snap['kids']==0)
            extra.setdefault(r['id'],dict(name=o['birthState']['name']['full'],eligible={} ))['eligible'][age]=state_ok
            family_age.append(dict(id=r['id'],iso=iso,arm=arm,age=age,married=int(snap['married']),living_kids=snap['kids'],recorded_children_by_age=len(births),observed_state=int(state_ok)))
        extra.setdefault(r['id'],dict(name=o['birthState']['name']['full'],eligible={}))
        if r['age']>=70:
            logs=[l for l in o['log'] if l['a']>=70]
            alone=[l for l in logs if '独自' in l['text'] or '一个人住' in l['text']]
            old.append(dict(id=r['id'],iso=iso,arm=arm,age=r['age'],alone_word=int(bool(alone)),care_parent_code=o['summary'].get('care') or '未记录',h=o['snaps']['death']['h'],so=o['snaps']['death']['so'],nw_cny=o['snaps']['death']['nw']*3.5,last3=' / '.join(l['text'] for l in o['log'][-3:]),alone_evidence=' / '.join(l['text'] for l in alone[:2])))
        for d in pd:band[(iso,arm,str(d['age']),d['id']+':'+d['picked'])]+=1
        if (i+1)%5000==0:print(exp,'validated raw',i+1,flush=True)
    for path,size,mt in raw_stats:
        stt=Path(path).stat();assert (size,mt)==(stt.st_size,stt.st_mtime_ns)
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
                    selected=pp if mode=='all' else [(x,y) for x,y in pp if extra[y['id']]['eligible'].get(age,False)]
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
    for name,data in [('groups',groups),('common_survivors',cohorts),('coverage',coverage_rows),('exposure',exp_rows),('health_bands',band_rows),('lifespan',life)]:write_csv(out/(name+'.csv'),data)
    write_csv(out/'pairs.csv',[{**{k:v for k,v in r.items() if k not in ['left','right','noise']}, **{side+'_'+k:v for side in ['left','right','noise'] for k,v in r[side].items()}} for r in pairs])
    write_csv(out/'family_age.csv',family_age)
    write_csv(out/'old_age.csv',old)
    write_csv(out/'noncompliance.csv',reasons)
    old_summary=[]
    for iso in COUNTRIES:
        for arm in arms:
            oo=[x for x in old if x['iso']==iso and x['arm']==arm]
            old_summary.append(dict(iso=iso,arm=arm,n=len(oo),alone_word=sum(x['alone_word'] for x in oo),h=stats([x['h'] for x in oo]),so=stats([x['so'] for x in oo]),nw=stats([x['nw_cny'] for x in oo]),care=dict(Counter(x['care_parent_code'] for x in oo))))
    family_summary=[]
    for iso in COUNTRIES:
        for arm in arms:
            for age in AGES:
                ff=[x for x in family_age if x['iso']==iso and x['arm']==arm and x['age']==age]
                family_summary.append(dict(iso=iso,arm=arm,age=age,n=len(ff),in_union=sum(x['married'] for x in ff),has_kids=sum(x['living_kids']>0 for x in ff),no_recorded_children=sum(x['recorded_children_by_age']==0 for x in ff)))
    write_csv(out/'family_summary.csv',family_summary)
    write_csv(out/'old_age_summary.csv',[dict(iso=x['iso'],arm=x['arm'],n=x['n'],alone_word=x['alone_word'],h_median=x['h']['median'],so_median=x['so']['median'],nw_median_cny=x['nw']['median']) for x in old_summary])
    d=dict(old_summary=old_summary,family_summary=family_summary,reason_summary=[dict(iso=iso,arm=arm,reason=reason,n=n) for (iso,arm,reason),n in Counter((x['iso'],x['arm'],x['reason']) for x in reasons).items()],experiment=exp,n=len(rows),countries=COUNTRIES,arms=arms,ref=ref,groups=groups,common=cohorts,pairs=pairs,coverage=coverage_rows,exposure=exp_rows,bands=band_rows,life=life,cases=cases,source_hash=hashlib.sha256(source.read_bytes()).hexdigest(),finished=manifest['finishedAt'],cost_labels=costlabels,investment_labels=evidence)
    assert before==(source.stat().st_size,source.stat().st_mtime_ns)
    (out/'analysis.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
    print(exp,'DONE',len(rows),len(pairs),flush=True)
if __name__=='__main__':main(sys.argv[1])
