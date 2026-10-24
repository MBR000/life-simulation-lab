"""Reconstruct observed residence transitions; classify only explicit event evidence.
Annual snapshots are not a complete border-crossing log. No model classification.
"""
from pathlib import Path
import json, gzip, csv, re, hashlib
from collections import Counter

R = Path(__file__).resolve().parents[1]
country_file = R.parent/'A_peers2002/tables/birth_country.csv'
names = {r['iso']:r['country'] for r in csv.DictReader(country_file.open())}
names.update({'ARE':'阿拉伯联合酋长国','GBR':'英国','USA':'美国','CHN':'中国','MLT':'马耳他'})
routes = {'study':'留学','work':'工作机会','refugee':'战争避难','spouse':'随配偶外派',
          'family':'晚年与子女团聚','adopt':'跨国收养','nomad':'数字游牧后定居',
          'return':'回流 / 归乡','return_study':'学业结束回国','return_visa':'就业或签证受阻回国',
          'return_post':'外派期满回国','other':'其他已记录迁移','unknown':'原因未能确认'}

def classify(l):
    t=l['text']; d=l.get('d','')
    if d=='studyto' and '出国留学了' in t:return 'study'
    if d=='abroad' and '你抵达了' in t:return 'work'
    if d=='war' and ('逃到了' in t or '逃到' in t):return 'refugee'
    if d=='ptpost' and '全家一起搬到了' in t:return 'spouse'
    if d=='oldhome' and ('你离开' in t or '你搬到' in t):return 'family'
    if '新家人身边' in t and '出生' in t:return 'adopt'
    if '结束漂泊的生活' in t and '定居' in t:return 'nomad'
    if ('回到了故乡' in t or '回到故乡' in t) and '派驻期满' in t:return 'return_post'
    if ('回到了故乡' in t or '回到故乡' in t) and ('签证' in t or '找到工作' in t):return 'return_visa'
    if '回到了故乡' in t and '完成学业' in t:return 'return_study'
    if d=='homecoming' and '回到了故乡' in t:return 'return'
    return None

records=[]; all_events=[]; groups=[]; manifest_counts=Counter()
for n,r in enumerate(map(json.loads,(R/'runs.jsonl').open()),1):
    iso=r['opts']['iso'];arm=r['opts']['policy']['abroad'];manifest_counts[(iso,arm)]+=1
    with gzip.open(R/'raw'/(r['file']+'.json.gz'),'rt') as f:o=json.load(f)
    bs=o['birthState']; born=bs['born'];prev=born;previous_age=-1;events=[]
    for y in o['years']:
        dest=y.get('cur')
        if dest and dest!=prev:
            # Snapshot transition falls in (previous snapshot, this snapshot].
            # Log ages only have integer resolution, so retain both endpoint ages.
            candidates=[]
            for ix,l in enumerate(o['log']):
                if previous_age<=l['a']<=y['a']:
                    route=classify(l)
                    if route and names.get(dest,dest) in l['text']:
                        candidates.append((ix,l,route))
            if candidates and len({x[2] for x in candidates})==1:
                ix,l,route=candidates[-1]
                evidence={'index':ix,'age':l['a'],'text':l['text'],'tag':l.get('d','')}
                decisions=[d for d in o['decisions'] if d['age']==l['a'] and d['id']==l.get('d') and d['logIndex']<=ix]
                decision=decisions[-1] if decisions else None
                choice=next((c for c in decision['view'].get('choices',[]) if c['k']==decision['picked']),{}) if decision else {}
                option={'title':decision['view']['title'],'label':choice.get('label',''),'sub':choice.get('sub',''),'why':decision['why']} if decision else None
            else:
                route='unknown';evidence=None;option=None
            e={'from':prev,'to':dest,'age':y['a'],'route':route,'evidence':evidence,'choice':option}
            events.append(e);all_events.append({'id':r['id'],'iso':iso,'arm':arm,'seed':r['seed'],**e});prev=dest
        previous_age=y['a']
    if events:
        assert events[0]['from']==born and events[0]['to']!=born
        first=events[0];final=o['final']['cur']
        records.append({'id':r['id'],'iso':iso,'arm':arm,'seed':r['seed'],'name':bs['name']['full'],
          'born':born,'first_age':first['age'],'destination':first['to'],'route':first['route'],
          'final':final,'returned':any(e['to']==born for e in events),
          'final_home':final==born,'destinations':list(dict.fromkeys(e['to'] for e in events if e['to']!=born)),
          'events':events,'death_age':r['age'],
          'final_unobserved':final!=events[-1]['to']})
    if n%2500==0:print('migration raw',n,flush=True)

assert n==10000 and len(manifest_counts)==10 and set(manifest_counts.values())=={1000}
D=json.loads((R/'tables/analysis.json').read_text())
for iso in D['countries']:
    for arm in ['avoid','seek']:
        rs=[r for r in records if r['iso']==iso and r['arm']==arm]
        expected=next(a['ever_n'] for a in D['arms'] if a['iso']==iso and a['arm']==arm)
        assert len(rs)==expected,(iso,arm,len(rs),expected)
        groups.append({'iso':iso,'arm':arm,'n':1000,'ever':len(rs),
          'returned':sum(r['returned'] for r in rs),'final_home':sum(r['final_home'] for r in rs),
          'final_unobserved':sum(r['final_unobserved'] for r in rs),
          'routes':dict(Counter(r['route'] for r in rs)),
          'first_destinations':dict(Counter(r['destination'] for r in rs)),
          'final_destinations':dict(Counter(r['final'] for r in rs))})
out={'names':names,'routes':routes,'groups':groups,'records':records,
     'source_hash':hashlib.sha256((R/'runs.jsonl').read_bytes()).hexdigest(),
     'events_n':len(all_events),'unknown_events':sum(e['route']=='unknown' for e in all_events),
     'unknown_first':sum(r['route']=='unknown' for r in records)}
(R/'tables/migration.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':')))
def csvout(name,rows):
    with (R/'tables'/name).open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
csvout('migration_people.csv',[{k:v for k,v in r.items() if k not in ['events','destinations']}|{'destinations':'|'.join(r['destinations'])} for r in records])
csvout('migration_events.csv',[{k:v for k,v in e.items() if k not in ['evidence','choice']}|{'evidence_index':e['evidence']['index'] if e['evidence'] else '', 'evidence':e['evidence']['text'] if e['evidence'] else '', 'choice':json.dumps(e['choice'],ensure_ascii=False) if e['choice'] else ''} for e in all_events])
print(json.dumps({'groups':groups,'events_n':out['events_n'],'unknown_first':out['unknown_first'],'unknown_events':out['unknown_events']},ensure_ascii=False))
