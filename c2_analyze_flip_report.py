# -*- coding: utf-8 -*-
"""Reproduce C2 single-decision flip aggregates from immutable batch exports. No engine execution."""
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
def main():
    from functools import lru_cache
    root=ROOT/'experiments/C2_flip';base=ROOT/'experiments/A_peers2002';noise_root=ROOT/'experiments/N_noise'
    manifest=json.loads((root/'manifest.json').read_text());assert manifest['dataValidated'] and manifest['finishedAt'] and manifest['errors']==0
    assert not (root/'errors.jsonl').read_text().strip()
    paths=[root/'runs.jsonl',base/'runs.jsonl',noise_root/'runs.jsonl'];before=[(p.stat().st_size,p.stat().st_mtime_ns) for p in paths]
    aa={r['seed']:r for r in map(json.loads,(base/'runs.jsonl').open())};nn={r['seed']:r for r in map(json.loads,(noise_root/'runs.jsonl').open()) if r['id'].startswith('N1-')}
    jobs={r['id']:r for r in map(json.loads,(root/'jobs.jsonl').open())};selection=json.loads((ROOT/'work/data-run/c2-selection.json').read_text());ids=[x[0] for x in selection['decisions']]
    assert len(jobs)==manifest['plannedRuns']==manifest['runs']==15000
    @lru_cache(maxsize=16)
    def loadbase(seed):
        p=base/'raw'/(aa[seed]['file']+'.json.gz')
        rawstats[str(p)]=(p.stat().st_size,p.stat().st_mtime_ns)
        with gzip.open(p,'rt') as f:return json.load(f)
    def effects(x,y):
        return dict(life=y['age']-x['age'],abs_life=abs(y['age']-x['age']),life_same=int(y['age']==x['age']),edu_changed=int(y['edu']!=x['edu']),job_changed=int(y['lastJob']!=x['lastJob']),kids_changed=int(y['kids']!=x['kids']),cause_changed=int(y['cause']!=x['cause']),partner_changed=(int(y['partnerState']!=x['partnerState']) if 'partnerState' in x and 'partnerState' in y else None))
    def aggregate(rr):
        return dict(n=len(rr),**{m:stats([r[m] for r in rr if r[m] is not None]) for m in ['life','abs_life','life_same','edu_changed','job_changed','kids_changed','cause_changed','partner_changed']})
    rawstats={};seen=set();runs={};records=[];byid=defaultdict(list);ages=[];choice=defaultdict(list);countries=Counter();audit=Counter()
    for i,r in enumerate(map(json.loads,(root/'runs.jsonl').open())):
        assert r['id'] not in seen;seen.add(r['id']);runs[r['id']]=r;j=jobs[r['id']];assert r['seed']==j['seed'] and r['opts']==j['opts'];x=aa[r['seed']]
        p=root/'raw'/(r['file']+'.json.gz');rawstats[str(p)]=(p.stat().st_size,p.stat().st_mtime_ns)
        with gzip.open(p,'rt') as f:o=json.load(f)
        ctrl=loadbase(r['seed']);assert o['snaps']==r['snaps'] and ctrl['snaps']==x['snaps'] and o['engine']['version']==ctrl['engine']['version']=='0.8.30'
        assert o['birthState']==ctrl['birthState'];audit['birth_equal']+=1
        flip=o.get('flipped');valid=False;prefix=False;title=j['opts']['flip']['id'];auto='?';target=j['opts']['flip']['k'];al='未记录';tl='未记录';age=None
        if flip:
            nth=flip['nth'];cd=ctrl['decisions'][nth];td=o['decisions'][nth];age=td['age'];auto=cd['picked'];title=cd['view']['title'];valid=(td['id']==j['opts']['flip']['id'] and td['picked']==target and target!=auto and td['why']=='flip')
            prefix=ctrl['decisions'][:nth]==o['decisions'][:nth] and cd['view']==td['view'] and cd['age']==td['age'] and cd['auto']==td['auto'] and ctrl['log'][:cd['logIndex']]==o['log'][:td['logIndex']]
            assert prefix,('prefix mismatch',r['id']);assert sum(z['why']=='flip' for z in o['decisions'])==1
            al=next((z['label'] for z in cd['view']['choices'] if z['k']==auto),auto);tl=next((z['label'] for z in td['view']['choices'] if z['k']==target),target)
        audit['actual_flip']+=valid;audit['prefix_equal']+=prefix
        fid=j['opts']['flip']['id'];iso=o['birthState']['born'];countries[(fid,iso)]+=1
        rec=dict(id=r['id'],seed=r['seed'],decision=fid,title=title,iso=iso,flip_age=age,executed=valid,prefix_equal=prefix,auto=auto,target=target,auto_label=al,target_label=tl,**effects(x,r))
        records.append(rec);byid[fid].append(rec);choice[(fid,auto,target)].append(rec)
        for a in AGES:
            bs=x['snaps'].get(a);ts=r['snaps'].get(a)
            if age is not None and age<=int(a) and bs and ts:
                ages.append(dict(decision=fid,age=a,seed=r['seed'],executed=valid,nw_delta=(ts['nw']-bs['nw'])*3.5,base_nw=bs['nw']*3.5,flip_nw=ts['nw']*3.5,income_delta=(ts['income']-bs['income'])*3.5/12,h_delta=ts['h']-bs['h'],hl_delta=ts['hl']-bs['hl']))
        if (i+1)%5000==0:print('C2 validated pairs',i+1,flush=True)
    assert seen==set(jobs) and len(records)==15000
    rankings=[];choices=[];age_rows=[]
    for fid in ids:
        rr=byid[fid];assert len(rr)==500
        nr=[effects(aa[r['seed']],nn[r['seed']]) for r in rr if r['seed'] in nn]
        rankings.append(dict(life_hist=[sum(test(r['life']) for r in rr) for test in [lambda v:v<=-20,lambda v:-20<v<=-10,lambda v:-10<v<0,lambda v:v==0,lambda v:0<v<10,lambda v:10<=v<20,lambda v:v>=20]],decision=fid,title=Counter(r['title'] for r in rr).most_common(1)[0][0],planned=len(rr),executed=sum(r['executed'] for r in rr),prefix=sum(r['prefix_equal'] for r in rr),unique_countries=len({r['iso'] for r in rr}),flip_age=stats([r['flip_age'] for r in rr if r['flip_age'] is not None]),effect=aggregate(rr),noise=aggregate(nr)))
        for a in AGES:
            ar=[x for x in ages if x['decision']==fid and x['age']==a];age_rows.append(dict(decision=fid,age=a,planned=500,not_yet=sum(x['flip_age'] is None or x['flip_age']>int(a) for x in rr),both_observed=len(ar),base_missing=sum(x['flip_age'] is not None and x['flip_age']<=int(a) and a not in aa[x['seed']]['snaps'] for x in rr),flip_missing=sum(x['flip_age'] is not None and x['flip_age']<=int(a) and a not in runs[x['id']]['snaps'] for x in rr),exposed_missing=500-sum(x['flip_age'] is None or x['flip_age']>int(a) for x in rr)-len(ar),**{m:stats([x[m] for x in ar]) for m in ['nw_delta','base_nw','flip_nw','income_delta','h_delta','hl_delta']}))
    for (fid,auto,target),rr in choice.items():
        choices.append(dict(decision=fid,auto=auto,target=target,auto_labels=[x for x,n in Counter(r['auto_label'] for r in rr).most_common(3)],target_labels=[x for x,n in Counter(r['target_label'] for r in rr).most_common(3)],**aggregate(rr)))
    # Representative pair near median absolute life change for five highest-ranked decisions, plus reflect if absent.
    top=[x['decision'] for x in sorted(rankings,key=lambda r:r['effect']['abs_life']['mean'],reverse=True)[:5]]
    if 'reflect' not in top:top.append('reflect')
    cases=[]
    for fid in top:
        rr=sorted(byid[fid],key=lambda r:(r['abs_life'],r['seed']));r=rr[len(rr)//2];ctrl=loadbase(r['seed']);t=json.load(gzip.open(root/'raw'/(r['id']+'.json.gz'),'rt'))
        cases.append(dict(**r,lives=[dict(arm=arm,name=o['birthState']['name']['full'],age=o['deathAt']['age'],log=o['log'],snaps=o['snaps']) for arm,o in [('原自动选择',ctrl),('改选一次',t)]]))
    for p,(size,mt) in rawstats.items():stt=Path(p).stat();assert(size,mt)==(stt.st_size,stt.st_mtime_ns)
    assert before==[(p.stat().st_size,p.stat().st_mtime_ns) for p in paths]
    out=root/'tables';out.mkdir(exist_ok=True)
    def flat(x,prefix=''):
        d={}
        for k,v in x.items():
            name=prefix+k
            if isinstance(v,dict):d.update(flat(v,name+'_'))
            else:d[name]=json.dumps(v,ensure_ascii=False) if isinstance(v,list) else v
        return d
    for name,rs in [('flip_effect',rankings),('choice_directions',choices),('age_effect',age_rows)]:write_csv(out/(name+'.csv'),[flat(x) for x in rs])
    write_csv(out/'pair_audit.csv',records);country_rows=[dict(decision=k[0],iso=k[1],n=v) for k,v in sorted(countries.items())];write_csv(out/'country_mix.csv',country_rows)
    (out/'selection.json').write_text(json.dumps(selection,ensure_ascii=False,indent=2))
    data=dict(experiment='C2_flip',n=len(records),unique_seeds=len({r['seed'] for r in records}),audit=dict(audit),rankings=rankings,choices=choices,age_rows=age_rows,countries=country_rows,cases=cases,selection=selection['rule'],finished=manifest['finishedAt'],source_hashes={p.parent.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (out/'analysis.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')));print('C2 DONE',dict(audit),data['unique_seeds'],flush=True)
if __name__=='__main__':main()
