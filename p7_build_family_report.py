# -*- coding: utf-8 -*-
"""Build P7 report from script-validated aggregates; does not execute the game."""
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1]
r=ROOT/'experiments/P7_family';d=json.loads((r/'tables/analysis.json').read_text());pub=ROOT/'work/github-pages-peers2002'
names={'drift':'随波逐流','single':'倾向不结婚','nokids':'结合后不生育'}
def card(title,body):return '<div class="panel"><h3>'+title+'</h3><p>'+body+'</p></div>'
def pair(arm,age,m):return next(x for x in d['pairs'] if x['iso']=='CHN' and x['arm']==arm and x['age']==str(age) and x['metric']==m and x['mode']=='all')
findings='<div class="grid">'
for arm in ['single','nokids']:
 p=pair(arm,65,'nw');h=pair(arm,65,'h')
 findings+=card('中国65岁：'+names[arm],f'相对随波逐流，双方均有快照的 {p["n"]} 对人生，净资产配对差中位 <b>{p["median"]:,.0f} 元</b>；幸福评分配对差中位 <b>{h["median"]:.2f}</b> 分。这些是模拟路径差异。')
findings+=card('先确认“做到”是什么意思','不登记结婚仍可能同居、生孩子；不生育策略只在伴侣结合后设置。下表先公开发生过的结合、生育与强迫早婚。pN 包含同居，不能直接叫结婚率。')+'</div><div id="complianceAll" class="scroll"></div><p class="note">分母为每国每臂1,000个出生样本，包含成年前死亡；同时列出活到18岁人数。pN 对18岁前死亡者不输出，因此“曾伴侣结合”是有记录人数下限；强迫早婚日志可能多于该人数。末段合法结合代码仅描述最后一段关系，不能复原终身法律婚史。</p>'
mechanism='''<p>single 在说媒、谈婚、同居转婚、早婚提议、恋人怀孕和旧情复燃等抉择中选择拒绝、分开、维持同居或分开付抚养费。它不是清空所有关系，也不保证没有孩子。nokids 的婚恋仍走自动决策，结合后写入当前关系的 noKidsM，并在生育／不孕抉择中选择停止。</p><div class="two"><div class="panel"><h3>方针失败如何识别</h3><p>“你没能说服他们，婚礼还是举行了”是明确的拒绝早婚失败证据。其余 pN&gt;0 只说明引擎记录过伴侣结合，可能是同居；不能全判成拒婚失败。生育使用 stats.kidsBorn；快照 kids 只数在世子女，且可含继子女，两者不混用。nokids 未改写 datepreg（恋人怀孕）抉择，可能在结婚或同居的同一抉择内迎来孩子，下一轮写入 noKidsM 时已经来不及。下方按首次子女记录与同年怀孕抉择列出证据，未匹配者保留为其他，不强行归因。</p></div><div class="panel"><h3>晚年照护字段有个陷阱</h3><p>summary.care 来自 cared / careHome，记录的是本人照顾父母，不是晚年谁照顾本人。因此报告不把 mom、dad 解释成自己的养老照护来源，也不拿死亡前最后三条日志推断谁送终。当前导出不能可靠回答这两项。</p></div></div><h3>所选国家：方针与伴侣结合</h3>'''
t=(ROOT/'scripts/policy_report.template.html').read_text()
t=t.replace('01 / 先看结果，再解释原因','01 / 方针生效情况与主要结果')
t=t.replace('另要求策略臂截至该年龄有执行证据','另看截至该年龄达到指定状态者')
old='当前：另要求策略臂截至该年龄，年度记账可见至少一次指定学习支出。年度记账只保留主要条目，可能漏掉小额学习，因此这是可观测学习子组，不是全部成功学习者；支出也不等于毕业。'
t=t.replace(old,'当前：不结婚臂要求截至该年龄已有拒婚策略抉择且当前无伴侣结合；不生育臂要求当前有伴侣结合、无在世孩子且未见此前子女出生记录。前者不等于终身从未结婚，后者不是生育能力判断。这是状态筛选，存在选择偏差，不是因果净收益。')
t=t.replace("'月收入差中位'","'幸福差中位'").replace("x.metric==='income'","x.metric==='h'").replace('fmt(inc.median)',"inc.median==null?'—':inc.median.toFixed(2)")
t=t.replace('收入位置、学历与身心状态','家庭状态与身心状态').replace('使用各臂自己的年龄快照样本。收入位置为游戏 pct × 100，非现实收入排名；学历0–5为类别编码，不能当作线性年数。幸福、健康为游戏内部评分。','使用各臂自己的年龄快照样本。伴侣结合包含同居；子女数为在世子女。幸福、健康、人际均为游戏内部评分。')
a=t.index("$('outcomes').innerHTML=");b=t.index('let n=ps[0].noise',a)
t=t[:a]+"let fs=D.family_summary.filter(r=>r.iso===iso&&r.age===age);$('outcomes').innerHTML=table(['策略','快照数','当前伴侣结合','有在世子女','幸福中位','人际中位','健康中位'],D.arms.map(a=>{let f=fs.find(x=>x.arm===a);return [NAMES[a],f.n,pct(f.in_union/f.n),pct(f.has_kids/f.n),...['h','so','hl'].map(m=>get(a,m).median.toFixed(2))]}));"+t[b:]
a=t.index('let cov=D.coverage');b=t.index("$('life').innerHTML",a)
t=t[:a]+'''let cov=D.coverage.filter(r=>r.iso===iso);$('coverage').innerHTML=table(['策略','活到18岁','终身有策略抉择','改写默认选择','曾伴侣结合','曾有生育','明确强迫早婚'],cov.map(r=>[NAMES[r.arm],r.adult_people,r.policy_people,r.changed_people,r.ever_union_people,r.ever_birth_people,r.forced_marriage_people]));let os=D.old_summary.filter(r=>r.iso===iso);$('exposure').innerHTML=table(['策略','活到70岁人数','70岁后出现独处词','终局幸福P10 / 中位 / P90','终局人际中位'],os.map(r=>[NAMES[r.arm],r.n,r.alone_word,pct(r.h.p10/100)+' / '+r.h.median.toFixed(2)+' / '+r.h.p90.toFixed(2),r.so.median.toFixed(2)]))+'<h3>方针未完全实现：记录证据分类</h3>'+table(['策略','证据类别','人数'],D.reason_summary.filter(r=>r.iso===iso).map(r=>[NAMES[r.arm],esc(r.reason),r.n]));''' +t[b:]
t=t.replace("pct(r.h.p10/100)","r.h.p10.toFixed(2)")
t=t.replace('收益差不等于投资回报率；资产还受劳动收入、家庭、住房、健康和路径分岔影响。收益率需要资金进出和本金时间序列，本报告没有据此编造年化回报或最大回撤。','财富、幸福与寿命分别呈现，不把其中一项换成婚育价值。晚年表条件于活到70岁，终局年龄不同，不能视作同年龄配对效果；65岁表才使用相同年龄快照。')
t=t.replace("$('downloads').innerHTML=__DOWNLOADS__;", "$('complianceAll').innerHTML=table(['国家','策略','活到18岁','曾伴侣结合 / 1,000','曾生育 / 1,000','明确强迫早婚 / 1,000'],D.coverage.map(r=>[D.countries[r.iso],NAMES[r.arm],r.adult_people,r.ever_union_people,r.ever_birth_people,r.forced_marriage_people]));$('downloads').innerHTML=__DOWNLOADS__;")
tokens={'TITLE':'不结婚、不生育，老了以后怎样？','EXPERIMENT':'P7_family','N':'15,000','QUESTION':'相同出生起点，三种家庭方针。先核对伴侣与生育状态，再比较钱、幸福、人际和晚年。','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':'活到70岁的人：终局状态与日志线索','DETAIL_NOTE':'“独自／一个人住”仅为70岁后日志关键词命中，可能是临时活动；不是可靠独居率，未命中也不等于有人同住。终局幸福与人际是在各自不同死亡年龄观察，幸存者筛选和年龄差异均存在。','FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
files=[r/'tables'/f for f in ['groups.csv','pairs.csv','coverage.csv','lifespan.csv','common_survivors.csv','family_summary.csv','old_age_summary.csv','noncompliance.csv']]
scripts=['analyze_family_report.py','build_family_report.py','policy_report.template.html']
for deploy in [False,True]:
 links=' · '.join(f'<a href="{"p7_"+f.name if deploy else "tables/"+f.name}">{f.name}</a>' for f in files)
 links+='<p>'+' · '.join(f'<a href="{"p7_"+f if deploy else "../../scripts/"+f}">{f}</a>' for f in scripts)+'</p>'
 out=t
 for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():out=out.replace('__'+k+'__',v)
 out=out.replace('analyze_policy_reports.py','analyze_family_report.py').replace('build_policy_reports.py','build_family_report.py')
 (pub/'P7_family.html' if deploy else r/'report.html').write_text(out)
for f in files:shutil.copyfile(f,pub/('p7_'+f.name))
for f in scripts:shutil.copyfile(ROOT/'scripts'/f,pub/('p7_'+f))
print('Built P7',len(out))
