# -*- coding: utf-8 -*-
"""Rebuild the Chinese H1 report from validated aggregated exports."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];r=ROOT/'experiments/H1_habits';d=json.loads((r/'tables/analysis.json').read_text());pub=ROOT/'work/github-pages-peers2002'
names={'none':'关闭七项自动消费','drift':'默认自动','social':'关系类','exp':'体验类','all':'七项全开'}
items={'dinner':'聚餐送礼','parents':'孝亲费','kidmoney':'子孙零用钱','donate':'捐款','trip':'国内旅游','abroad':'出境旅游','gear':'兴趣装备课程'}
def pair(arm,m):return next(x for x in d['pairs'] if x['iso']=='CHN' and x['arm']==arm and x['age']=='65' and x['metric']==m and x['mode']=='all')
findings='<div class="two">'
for arm in d['arms'][1:]:
 p,h,so=pair(arm,'nw'),pair(arm,'h'),pair(arm,'so')
 findings+=f'<div class="panel"><h3>中国65岁：{names[arm]}</h3><p>相对关闭七项自动消费，{p["n"]} 对同种子人生的净资产差中位 <b>{p["median"]:,.0f} 元</b>，幸福差中位 <b>{h["median"]:.2f}</b> 分，人际差中位 <b>{so["median"]:.2f}</b> 分。</p></div>'
findings+='</div><p>这里的“关闭”只关七项自动消费，生活费、医疗、住房、剧情支出等仍照常发生。幸福与人际都是游戏评分，不能换算成现实幸福收益。</p>'
mechanism='''<div class="scroll"><table><tr><th>策略</th><th>主动设置的七项</th></tr><tr><td>关闭七项</td><td>七项全部关闭，不代表人生不花钱</td></tr><tr><td>默认自动</td><td>不改 habits；基础自动从25岁开启聚餐与孝亲费，50岁开启子孙零用钱，须满足条件</td></tr><tr><td>关系类</td><td>聚餐送礼、孝亲费、子孙零用钱、捐款；关闭旅游与兴趣装备</td></tr><tr><td>体验类</td><td>国内旅游、出境旅游、兴趣装备课程；关闭上述四项</td></tr><tr><td>七项全开</td><td>七项都尝试开启，按各项目条件与余额决定是否执行</td></tr></table></div><div class="two"><div class="panel"><h3>同样开关，不同余额门槛</h3><p>每年逐项检查。支付后余额必须不少于费用的两倍，并达到保留收入门槛：主动设置为一年当地中位收入；由基础自动模式开启的项目为两年。可动用余额 cashV 包含非负现金和储备 pot，不等于净资产，也不是仅看工资。</p><p>所以默认自动与关系类的差异，同时包含开启年龄、项目和余额门槛，不能归因于单独某一个开关。引擎按列表顺序花费，先发生的项目会影响后续项目能否负担。</p></div><div class="panel"><h3>有钱也不一定做成</h3><p>孝亲费需要父母等条件；子孙零用钱需要可选对象；兴趣装备需要已有爱好。国内旅游通常每年，出境旅游与孝亲费通常每两年；监禁、服役、健康、地点与疫情等可能阻止执行。旅游同行者沿用既有选择，否则取可选项第一项，runner没有替玩家指定。</p><p>例如聚餐送礼的费用为当地中位年收入的3%，即时效果人际+4、幸福+2；后续评分还受许多事件与上下限影响，不能把次数乘加成当作终身净效果。</p></div></div><h3>实际发生：终身次数与覆盖</h3>'''
t=(ROOT/'scripts/policy_report.template.html').read_text()
t=t.replace('收入位置、学历与身心状态','幸福、人际与健康').replace('使用各臂自己的年龄快照样本。收入位置为游戏 pct × 100，非现实收入排名；学历0–5为类别编码，不能当作线性年数。幸福、健康为游戏内部评分。','使用各臂自己的年龄快照样本；幸福、人际与健康均为游戏评分。死亡与快照缺失者不补零，分母公开。')
a=t.index("$('outcomes').innerHTML=");b=t.index('let n=ps[0].noise',a)
t=t[:a]+"$('outcomes').innerHTML=table(['策略','幸福中位','人际中位','健康中位'],D.arms.map(a=>[NAMES[a],...['h','so','hl'].map(m=>get(a,m).median==null?'—':get(a,m).median.toFixed(2))]));"+t[b:]
t=t.replace("'月收入差中位'","'幸福差中位','人际差中位'").replace("x.metric==='income'","x.metric==='h'")
t=t.replace('fmt(inc.median)',"inc.median==null?'—':inc.median.toFixed(2),fmt2(D.pairs.find(x=>x.iso===iso&&x.age===age&&x.mode===mode&&x.arm===r.arm&&x.metric==='so').median)")
old='当前：另要求策略臂截至该年龄，年度记账可见至少一次指定学习支出。年度记账只保留主要条目，可能漏掉小额学习，因此这是可观测学习子组，不是全部成功学习者；支出也不等于毕业。'
t=t.replace(old,'当前：另要求策略臂截至该年龄出现至少一条对应消费账目：默认/关系类看关系项目，体验类看旅游，全开看任一目标项目。兴趣类通用账目无法可靠分离装备购买，不作为证据。账目压缩会漏记，且花得起的人被选择，不能当作成功消费的因果净收益。')
t=t.replace('另要求策略臂截至该年龄有执行证据','另看截至该年龄有明确消费账目者')
a=t.index('let cov=D.coverage');b=t.index("$('life').innerHTML",a)
t=t[:a]+'''let cov=D.coverage.filter(r=>r.iso===iso);$('coverage').innerHTML=table(['策略','出生样本','活到18岁','任一七项发生人数','有可见目标账目人数'],cov.map(r=>[NAMES[r.arm],r.people,r.adult_people,r.any_people,r.visible_target_people]));renderSpend();$('happyEnd').innerHTML=table(['策略','死亡时幸福中位','死亡时人际中位','最幸福年年龄P10 / 中位 / P90','年龄缺失'],D.arms.map(a=>{let h=D.happy.find(x=>x.iso===iso&&x.arm===a&&x.metric==='h'),so=D.happy.find(x=>x.iso===iso&&x.arm===a&&x.metric==='so'),best=D.happy.find(x=>x.iso===iso&&x.arm===a&&x.metric==='happiest_age');return[NAMES[a],h.median.toFixed(2),so.median.toFixed(2),fmt(best.p10)+' / '+fmt(best.median)+' / '+fmt(best.p90),best.missing]}));''' +t[b:]
t=t.replace('<div id="exposure" class="scroll"></div>','<label>出生家境分位 <select id="wealth"><option value="all">全部家境</option><option value="1">q1</option><option value="2">q2</option><option value="3">q3</option><option value="4">q4</option><option value="5">q5</option></select></label><p class="note">此筛选仅改变下面的消费覆盖表，上方配对结果仍为所选国家的全部家境。q为引擎出生家境类别1至5，不是现实调查分位。</p><div id="exposure" class="scroll"></div><h3>全体出生者：终局与最幸福年份</h3><div id="happyEnd" class="scroll"></div>')
js="""function fmt2(x){return x==null?'—':x.toFixed(2)}\nfunction renderSpend(){let iso=$('country').value,q=$('wealth').value;let ss=D.spend.filter(x=>x.iso===iso&&(q==='all'||String(x.q)===q));$('exposure').innerHTML=table(['策略','项目','出生分母','曾发生人数 / 比例','人均终身次数'],D.arms.flatMap(a=>Object.entries(ITEMS).map(([item,label])=>{let rr=ss.filter(x=>x.arm===a&&x.item===item),n=rr.reduce((s,x)=>s+x.n,0),people=rr.reduce((s,x)=>s+x.people,0),events=rr.reduce((s,x)=>s+x.events,0);return [NAMES[a],label,n,people+' / '+pct(people/n),(events/n).toFixed(2)]})));}\n"""
t=t.replace('function render(){',js+'function render(){')
t=t.replace("const D=__DATA__,NAMES=__NAMES__;","const D=__DATA__,NAMES=__NAMES__,ITEMS="+json.dumps(items,ensure_ascii=False)+";")
t=t.replace("render();\n$('caseList')","render();$('wealth').addEventListener('change',renderSpend);\n$('caseList')")
t=t.replace('收益差不等于投资回报率；资产还受劳动收入、家庭、住房、健康和路径分岔影响。收益率需要资金进出和本金时间序列，本报告没有据此编造年化回报或最大回撤。','净资产差不是这七项的消费总额，也不是幸福回报率。账目经过压缩，不能用可见账单复原全部支出。最幸福年份由引擎选择，只作终身描述，不用于筛选固定年龄样本。')
tokens={'TITLE':'把钱花在关系、体验，还是留下？','EXPERIMENT':'H1_habits','N':'25,000','QUESTION':'五种自动消费设置，同种子比较财富、幸福与人际。把开关、实际发生和花得起的人分开看。','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':'按出生家境下钻：七项消费是否真正发生','DETAIL_NOTE':'终身发生次数来自 counts.shop_* 的年度标记变化，覆盖率分母为该出生家境组全体人生，包含成年前死亡；不是每年有资格消费者的成功率。不同寿命会改变累计消费机会。该表不使用压缩账单计次数。终局分数观察年龄不同，不能代替同年龄比较。','FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
files=[r/'tables'/f for f in ['groups.csv','pairs.csv','coverage.csv','lifespan.csv','common_survivors.csv','spend.csv','happy.csv']];scripts=['analyze_habits_report.py','build_habits_report.py','policy_report.template.html']
for deploy in [False,True]:
 links=' · '.join(f'<a href="{"h1_"+f.name if deploy else "tables/"+f.name}">{f.name}</a>' for f in files)
 links+='<p>'+' · '.join(f'<a href="{"h1_"+f if deploy else "../../scripts/"+f}">{f}</a>' for f in scripts)+'</p>'
 out=t
 for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():out=out.replace('__'+k+'__',v)
 out=out.replace('analyze_policy_reports.py','analyze_habits_report.py').replace('build_policy_reports.py','build_habits_report.py')
 (pub/'H1_habits.html' if deploy else r/'report.html').write_text(out)
for f in files:shutil.copyfile(f,pub/('h1_'+f.name))
for f in scripts:shutil.copyfile(ROOT/'scripts'/f,pub/('h1_'+f))
print('Built H1',len(out))
