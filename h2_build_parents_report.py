# -*- coding: utf-8 -*-
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];r=ROOT/'experiments/H2_parents';d=json.loads((r/'tables/analysis.json').read_text());pub=ROOT/'work/github-pages-peers2002'
names={'off':'关闭自动孝亲费','on':'开启自动孝亲费'}
pair=lambda metric:next(x for x in d['pairs'] if x['iso']=='CHN' and x['age']=='65' and x['metric']==metric and x['mode']=='all')
findings='<div class="grid">'
for who,label in [('mom','母亲'),('dad','父亲')]:
 x=next(x for x in d['parent_pairs'] if x['iso']=='CHN' and x['who']==who)
 findings+=f'<div class="panel"><h3>中国组：{label}的共同随访</h3><p>{x["n"]} 对在子女20岁后仍在世的父母角色，在两条人生共同可观察、且最多到子女60岁的区间内，开启臂的存活年数配对差均值为 <b>{x["mean"]:.2f} 年</b>，中位为 {x["median"]:.2f} 年。不是完整寿命延长。</p></div>'
p=pair('nw');h=pair('h');so=pair('so')
findings+=f'<div class="panel"><h3>中国组：子女65岁的代价与状态</h3><p>{p["n"]} 对双方均有快照的人生，净资产配对差中位 <b>{p["median"]:,.0f} 元</b>，幸福差中位 {h["median"]:.2f} 分，人际差中位 {so["median"]:.2f} 分。</p></div></div>'
mechanism='''<p>本实验只切换 parentsAuto，其他消费设置保留默认；不是开启全部孝养行为，也不是切断其他照护。runner在条件满足时设置开关，并阻止关闭臂被基础自动模式重新打开。</p><div class="two"><div class="panel"><h3>费用与执行条件</h3><p>满20岁、父母至少一位在世且满足地点条件时，可每两年给一次。父母都在且父亲非缺席时，费用是当地中位年收入的12%；否则8.5%。父母在国外时采用引擎指定父母所在地的收入标尺。</p><p>主动开启的自动项目支付后仍须保留至少两倍费用与一年当地中位收入中的较大者，余额含现金和储备。没有足够余额或对象时会跳过，开关不等于成功给钱。</p></div><div class="panel"><h3>保护机制不只来自钱</h3><p>每次设置 parentCare 到当前年龄+5，保护有效时父母年度死亡概率乘0.8，并即时增加人际5、幸福2。引擎其他照护选择也能设置同一个保护标记，所以关闭孝亲费不等于父母完全没有保护。游戏参数不能理解为现实医疗效果。</p><p>不同策略会改变后续随机数消耗，疾病与家庭路径也会分岔；同种子只能固定出生起点，不能保证之后只差一笔钱。</p></div></div><h3>实际执行与可见费用</h3>'''
t=(ROOT/'scripts/policy_report.template.html').read_text()
t=t.replace('收入位置、学历与身心状态','幸福、人际与健康').replace('使用各臂自己的年龄快照样本。收入位置为游戏 pct × 100，非现实收入排名；学历0–5为类别编码，不能当作线性年数。幸福、健康为游戏内部评分。','使用各臂自己的年龄快照样本；幸福、人际与健康为游戏评分。')
t=t.replace("'月收入差中位'","'幸福差中位'").replace("x.metric==='income'","x.metric==='h'").replace('fmt(inc.median)',"inc.median==null?'—':inc.median.toFixed(2)")
a=t.index("$('outcomes').innerHTML=");b=t.index('let n=ps[0].noise',a)
t=t[:a]+"$('outcomes').innerHTML=table(['策略','幸福中位','人际中位','健康中位'],D.arms.map(a=>[NAMES[a],...['h','so','hl'].map(m=>get(a,m).median.toFixed(2))]));"+t[b:]
old='当前：另要求策略臂截至该年龄，年度记账可见至少一次指定学习支出。年度记账只保留主要条目，可能漏掉小额学习，因此这是可观测学习子组，不是全部成功学习者；支出也不等于毕业。'
t=t.replace(old,'当前：另要求开启臂截至该年龄出现明确的孝亲费·医药费支出账目。账目压缩会漏掉小额项目；有父母、花得起且双方存活的人被选择，不能把子组差异当作因果净收益。父母随访表独立使用20岁起点队列，不随这个子女筛选变化。')
a=t.index('let cov=D.coverage');b=t.index("$('life').innerHTML",a)
t=t[:a]+'''let cov=D.coverage.filter(r=>r.iso===iso);$('coverage').innerHTML=table(['策略','活到20岁 / 1,000','曾给钱人数 / 1,000','人均终身次数','可见账目金额人均 / 元'],cov.map(r=>[NAMES[r.arm],r.reached20,r.support_people,(r.support_events/1000).toFixed(2),fmt(r.visible_cost_cny/1000)]));let pp=D.parents.filter(r=>r.iso===iso);$('exposure').innerHTML=table(['父母角色','策略','20岁起点配对数','已观测死亡','未观测死亡 / 截断','缺席 / 出生总样本','已观测死亡年龄中位 / 均值'],pp.map(r=>[r.who==='mom'?'母亲':'父亲',NAMES[r.arm],r.eligible_paired,r.observed_deaths,r.censored,r.absent,fmt(r.death_age.median)+' / '+(r.death_age.mean==null?'—':r.death_age.mean.toFixed(2))]))+'<p class="warn">仅比较已经去世者的年龄会漏掉尚在世的父母。上表死亡年龄是被观察到的死亡子组描述，不代表全体父母的平均寿命，也不能直接相减当作延寿。</p><h3>子女30 / 40 / 50 / 60岁：父母存活与随访缺口</h3>'+table(['父母角色','策略','子女年龄','起点人数','状态已知','提前截断','已知在世','KM存活估计','该时点风险集'],D.parent_survival.filter(r=>r.iso===iso).map(r=>[r.who==='mom'?'母亲':'父亲',NAMES[r.arm],r.age,r.n,r.known,r.censored_before,r.known_alive,pct(r.km),r.at_risk]))+'<p class="note">KM从子女20岁起计算；父母去世为事件，子女先去世且父母尚在世为右删失。同年事件按死亡先于删失处理。它需要删失与父母后续死亡独立的假设，但家庭共同环境、子女死亡可能破坏这一假设，因此只作探索性描述。风险集小会不稳定。</p><h3>同一对父母、相同可观察区间</h3>'+table(['父母角色','配对数','共同区间存活年数差中位','均值','均值95%近似区间'],D.parent_pairs.filter(r=>r.iso===iso).map(r=>[r.who==='mom'?'母亲':'父亲',r.n,r.median.toFixed(2),r.mean.toFixed(2),r.lo.toFixed(2)+' / '+r.hi.toFixed(2)]));''' +t[b:]
t=t.replace('收益差不等于投资回报率；资产还受劳动收入、家庭、住房、健康和路径分岔影响。收益率需要资金进出和本金时间序列，本报告没有据此编造年化回报或最大回撤。','父母队列要求两臂子女都活到20岁，且对应父母非缺席、没有20岁及以前的死亡记录。同年死亡者保守排除；不是筛选未来延寿成功者。父母角色来自引擎记录，不保证都是生物学父母。共同区间取两臂子女寿命与60岁的最小值，统计20岁后区间内的父母存活年数；仍受随访截断影响，不是完整寿命因果效应。')
tokens={'TITLE':'给父母孝亲费，改变了什么？','EXPERIMENT':'H2_parents','N':'10,000','QUESTION':'比较父母存活、子女财富与人际；明确区分已观测死亡、尚未观测到的寿命和实际给钱。','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':'父母随访：先看分母与截断，再看寿命','DETAIL_NOTE':'父母统计仅随国家切换，不随上方子女年龄或执行子组切换。可见费用是年度主要账目中负项的人民币等价值，属于可见下限，不是完整累计成本。父母死亡年龄直接用导出字段；子女65岁的净资产差不等于孝亲费总额。','FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
files=[r/'tables'/f for f in ['groups.csv','pairs.csv','coverage.csv','lifespan.csv','common_survivors.csv','parents.csv','parent_survival.csv','parent_paired_followup.csv']];scripts=['analyze_parents_report.py','build_parents_report.py','policy_report.template.html']
for deploy in [False,True]:
 links=' · '.join(f'<a href="{"h2_"+f.name if deploy else "tables/"+f.name}">{f.name}</a>' for f in files)
 links+='<p>'+' · '.join(f'<a href="{"h2_"+f if deploy else "../../scripts/"+f}">{f}</a>' for f in scripts)+'</p>'
 out=t
 for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():out=out.replace('__'+k+'__',v)
 out=out.replace('analyze_policy_reports.py','analyze_parents_report.py').replace('build_policy_reports.py','build_parents_report.py')
 (pub/'H2_parents.html' if deploy else r/'report.html').write_text(out)
for f in files:shutil.copyfile(f,pub/('h2_'+f.name))
for f in scripts:shutil.copyfile(ROOT/'scripts'/f,pub/('h2_'+f))
print('Built H2',len(out))
