# -*- coding: utf-8 -*-
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];r=ROOT/'experiments/H3_checkup';d=json.loads((r/'tables/analysis.json').read_text());pub=ROOT/'work/github-pages-peers2002'
names={'off':'关闭年度健检课程','on':'开启年度健检课程'}
def pair(metric):return next(x for x in d['pairs'] if x['iso']=='CHN' and x['age']=='65' and x['metric']==metric and x['mode']=='all')
l=next(x for x in d['lifepairs'] if x['iso']=='CHN');p,h=pair('nw'),pair('hl')
findings=f'''<div class="grid"><div class="panel"><h3>中国组：全体出生者寿命</h3><p>1,000对同种子人生，开启减关闭的寿命差中位 <b>{l['median']:.2f} 岁</b>，均值 <b>{l['mean']:.2f} 岁</b>。包含成年前死亡，不以做过健检或活到老年筛选。</p></div><div class="panel"><h3>中国65岁：健康评分</h3><p>{h['n']}对双方有快照者，健康评分配对差中位 <b>{h['median']:.2f} 分</b>。这是游戏评分，干预同时包含健检、锻炼和慢病筛查。</p></div><div class="panel"><h3>中国65岁：净资产</h3><p>净资产配对差中位 <b>{p['median']:,.0f} 元</b>。它包含寿命、工作、家庭和随机路径变化，不能直接当作健检累计费用。</p></div></div>'''
mechanism='''<p>这里的 checkAuto 开启“全身健检·私人教练课”，不是单纯体检。25岁起满足条件后每年尝试一次，每次花费当地中位年收入的8%。普通剧情仍可能出现定期健康检查，因此关闭臂不是完全没有检查或医疗。</p><div class="two"><div class="panel"><h3>钱与健康如何变化</h3><p>检查前现金 money 必须至少达到费用的三倍；这与其他自动消费的“支付后保留一年中位收入”门槛不同。监禁等情况会跳过。成功时健康增加6乘年龄系数，healthy标记设到当前年龄+3，同时进行慢病筛查。</p><p>健康评分受上限、衰老和其他事件影响，不能把每次加分直接相加当作长期收益。记录到更多慢病也可能来自发现率变化，不一定意味着更容易患病。</p></div><div class="panel"><h3>癌症与死亡不能混为一谈</h3><p>引擎40–79岁相关筛查分支的基础参数为12%，当前或既往吸烟增加3个百分点，并乘医疗条件因子。这个参数不是本实验测得的现实早诊率。对照臂也存在公共筛查和随机健检路径。</p><p>死因占比存在竞争风险：一种死亡减少后，其他死因可能更多出现。下方展示完整出生队列的生存比例与死因人数，不将死因构成变化直接解释为某病的发病率变化。</p></div></div><h3>实际发生与可见费用</h3>'''
t=(ROOT/'scripts/policy_report.template.html').read_text()
t=t.replace('收入位置、学历与身心状态','慢病记录与身心状态').replace('使用各臂自己的年龄快照样本。收入位置为游戏 pct × 100，非现实收入排名；学历0–5为类别编码，不能当作线性年数。幸福、健康为游戏内部评分。','使用各臂自己的年龄快照样本。慢病个数来自nConds，筛查会影响疾病是否被发现；幸福、健康为游戏评分。')
t=t.replace("['策略','收入位置中位','学历编码中位','幸福中位','健康中位']","['策略','慢病个数中位','人际中位','幸福中位','健康中位']").replace("['pct','edu','h','hl']","['nConds','so','h','hl']")
t=t.replace("'月收入差中位'","'健康差中位'").replace("x.metric==='income'","x.metric==='hl'").replace('fmt(inc.median)',"inc.median==null?'—':inc.median.toFixed(2)")
old='当前：另要求策略臂截至该年龄，年度记账可见至少一次指定学习支出。年度记账只保留主要条目，可能漏掉小额学习，因此这是可观测学习子组，不是全部成功学习者；支出也不等于毕业。'
t=t.replace(old,'当前：另要求开启臂截至该年龄已有明确的全身健检·私人教练课支出账目。账目压缩可能漏记，花得起且活到该年龄的人被选择；不以未来寿命或健康改善筛选，也不是因果净收益。下方生存率始终使用全部出生者。')
a=t.index('let cov=D.coverage');b=t.index("$('life').innerHTML",a)
t=t[:a]+'''let cov=D.coverage.filter(r=>r.iso===iso);$('coverage').innerHTML=table(['策略','活到25岁 / 1,000','曾执行人数 / 1,000','人均终身次数','可见费用人均 / 元'],cov.map(r=>[NAMES[r.arm],r.reached25,r.check_people,(r.check_events/1000).toFixed(2),fmt(r.visible_cost_cny/1000)]));let sp=D.spend.filter(r=>r.iso===iso);$('exposure').innerHTML=table(['策略','出生家境q','出生分母','曾执行比例','人均终身次数'],sp.map(r=>[NAMES[r.arm],r.q,r.n,pct(r.rate),r.mean_times.toFixed(2)]))+'<h3>完整出生队列：达到各年龄的比例</h3>'+table(['策略','年龄','出生分母','达到该年龄人数','比例'],D.survival.filter(r=>r.iso===iso).map(r=>[NAMES[r.arm],r.age,r.n,r.survived,pct(r.rate)]))+'<p class="note">达到该年龄定义为死亡年龄≥阈值，包含在该整数年龄内去世者；不是生日后持续存活一整年的概率。</p><h3>全体同种子寿命配对差</h3>'+table(['配对数','差值P10 / 中位 / P90','差值均值','均值95%近似区间'],D.lifepairs.filter(r=>r.iso===iso).map(r=>[r.n,r.p10.toFixed(1)+' / '+r.median.toFixed(1)+' / '+r.p90.toFixed(1),r.mean.toFixed(2),r.lo.toFixed(2)+' / '+r.hi.toFixed(2)]))+'<h3>终身死因：每臂1,000人</h3>'+table(['策略','癌症','心脑血管病（明确标签）','其他'],D.arms.map(a=>{let rr=D.causes.filter(r=>r.iso===iso&&r.arm===a),c=rr.filter(r=>r.cause==='can').reduce((s,r)=>s+r.n,0),v=rr.filter(r=>['ihd','str'].includes(r.cause)||['高血压性心脏病','风湿性心脏病'].includes(r.label)).reduce((s,r)=>s+r.n,0);return[NAMES[a],c,v,1000-c-v]}))+'<details><summary>展开全部死因与代码</summary>'+table(['策略','代码','死因','人数','比例'],D.causes.filter(r=>r.iso===iso).sort((a,b)=>b.n-a.n).map(r=>[NAMES[r.arm],esc(r.cause),esc(r.label),r.n,pct(r.rate)]))+'</details>';''' +t[b:]
t=t.replace('收益差不等于投资回报率；资产还受劳动收入、家庭、住房、健康和路径分岔影响。收益率需要资金进出和本金时间序列，本报告没有据此编造年化回报或最大回撤。','本实验改变的是健检与私人教练组合，不能分离单独筛查和运动的效应。费用只展示压缩账单的可见金额，不伪造完整成本收益率；全寿命配对用全部出生者，固定年龄比较则有幸存者选择。')
tokens={'TITLE':'每年健检加教练课，改变了什么？','EXPERIMENT':'H3_checkup','N':'10,000','QUESTION':'把健康、寿命、财富和实际执行分开看；不把游戏中的组合干预当作现实的纯体检效果。','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':'出生家境、生存比例与死因下钻','DETAIL_NOTE':'生存与死因表只随国家切换，分母是全部出生者，不随上方执行子组改变。q是引擎出生家境类别。可见费用来自压缩年度账目，是可见下限；终身次数来自shop_checkup年度标记，可能随寿命改变。','FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
files=[r/'tables'/f for f in ['groups.csv','pairs.csv','coverage.csv','lifespan.csv','common_survivors.csv','survival.csv','causes.csv','lifespan_pairs.csv','spend.csv']];scripts=['analyze_checkup_report.py','build_checkup_report.py','policy_report.template.html']
for deploy in [False,True]:
 links=' · '.join(f'<a href="{"h3_"+f.name if deploy else "tables/"+f.name}">{f.name}</a>' for f in files)
 links+='<p>'+' · '.join(f'<a href="{"h3_"+f if deploy else "../../scripts/"+f}">{f}</a>' for f in scripts)+'</p>'
 out=t
 for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():out=out.replace('__'+k+'__',v)
 out=out.replace('analyze_policy_reports.py','analyze_checkup_report.py').replace('build_policy_reports.py','build_checkup_report.py')
 (pub/'H3_checkup.html' if deploy else r/'report.html').write_text(out)
for f in files:shutil.copyfile(f,pub/('h3_'+f.name))
for f in scripts:shutil.copyfile(ROOT/'scripts'/f,pub/('h3_'+f))
print('Built H3',len(out))
