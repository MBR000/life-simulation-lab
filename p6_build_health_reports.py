# -*- coding: utf-8 -*-
from pathlib import Path
import json,sys,shutil
ROOT=Path(__file__).resolve().parents[1]
def main(exp):
 r=ROOT/'experiments'/exp;d=json.loads((r/'tables/analysis.json').read_text());ins=exp=='P5_ins';prefix='p5_' if ins else 'p6_'
 names={'basic':'基本保障','more':'较完整保险'} if ins else {'usual':'随周围人饮食','good':'少盐蔬菜全谷'}
 def pair(age,m):return next(p for p in d['pairs'] if p['iso']=='CHN' and p['age']==str(age) and p['metric']==m and p['mode']=='all')
 def n(x):return f'{x:,.0f}'
 def card(a,b):return f'<div class="panel"><h3>{a}</h3><p>{b}</p></div>'
 a,b,h=pair(40,'nw'),pair(65,'nw'),pair(65,'hl')
 life=[next(x for x in d['life'] if x['iso']=='CHN' and x['arm']==arm) for arm in d['arms']]
 title='多买保险，换来了什么？' if ins else '吃得更健康，人生怎样变化？'
 findings='<div class="grid">'+card('中国组：保障与财富分开看' if ins else '中国组：健康也有经济成本',f'干预臂相对对照，40岁净资产配对差中位为 <b>{n(a["median"])} 元</b>（{a["n"]} 对），65岁为 <b>{n(b["median"])} 元</b>（{b["n"]} 对）。不能据此把健康或风险保障的价值归零。')+card('65岁：健康评分的配对差',f'{h["n"]} 对中，健康差中位为 <b>{h["median"]:.2f} 分</b>。干预/对照健康评分中位为 {h["right"]["median"]:.2f} / {h["left"]["median"]:.2f}；它是游戏评分，不是医学量表。')+card('全体出生样本：寿命分布',f'各1,000局，干预/对照寿命中位为 <b>{n(life[1]["median"])} / {n(life[0]["median"])} 岁</b>，均值为 {life[1]["mean"]:.2f} / {life[0]["mean"]:.2f} 岁。两个中位数之差不是个人寿命增益，也没有现实因果含义。')+'</div>'
 if ins:
  mechanism='''<p>18岁起，每年将保险设为较完整或基本保障。较完整保险将适用医疗自付比例再乘0.3；不是所有医疗费直接变成总费用的30%，基本自付比例仍取决于国家、工作和既有制度，部分费用还有下限。</p><div class="two"><div class="panel"><h3>保费基数已经核实</h3><p>每年基数为当地中位年收入 incomeAt(country,0.5)，费率为1.2% + 已婚0.6% + 每个同住孩子0.4% + 未满70岁0.6%。它不是本人收入百分比。年度可见保费账目会被压缩，不能当作完整保费总额。</p></div><div class="panel"><h3>医疗与身故保障不同</h3><p>本人、配偶、子女的适用医疗支出受到影响；部分国家还有候诊等分支差异。18–69岁死亡且有存活配偶或25岁以下存活子女时，引擎向家人支付4倍当地中位年收入。固定年龄幸存者表不衡量这项身故保障，不能仅靠它宣布保险“不划算”。</p></div></div><p>医院决策子组只取干预臂截至观察年龄已明确选择本人或孩子 hospital 的人，配偶医疗等不在这个子组内。选择医院不等于已经获得保险赔款；未按理赔金额挑人，但比较仍要求双方都有该年龄快照，存在幸存者选择。</p>'''
  subset='当前：另要求较完整保险臂截至该年龄已明确选择本人或孩子到医院治疗。该子组不含所有配偶医疗，不等于理赔成功；医疗选择和幸存条件带来选择偏差。'
 else:
  mechanism='''<p>18岁起，每年设置 good 或 usual。good 额外花费当地中位年收入的1.5%，在监禁等条件下不适用；这里不是本人实际收入的1.5%。usual 是周围人的一般饮食，不是强制不健康饮食。</p><div class="two"><div class="panel"><h3>健康加成不是每年净加1.5</h3><p>dietFit 的1.5进入健康目标值，健康仍受年龄、疾病、运动、家境等因素共同影响。高血压、糖尿病、心脏病的发生风险因子分别乘0.8、0.75、0.8，这是游戏参数，不是本实验从现实人群估计出的效应。</p></div><div class="panel"><h3>疾病人数受寿命影响</h3><p>活得更久就可能有更多时间患病。下面的终局疾病人数来自各人死亡时的记录，年龄不齐，既不是同年龄患病率，也不是标准化发病率。固定年龄只提供慢病个数，不能据此伪造同年龄的分病种结果。</p></div></div><p>实际饮食支出只从年度主要账目识别，未出现可能是合并进“其他”。对照臂也有少量可见健康采买，说明方针设定不等于每个年内事件都严格隔离；不把这类记录删除来美化组间差异。</p>'''
  subset='当前：另要求健康饮食臂截至该年龄已出现明确的蔬菜全谷采买账目。压缩账本会漏记小额项目，所以这是可见执行子组，不是全部执行者，更没有筛选健康改善成功的人。'
 t=(ROOT/'scripts/policy_report.template.html').read_text()
 t=t.replace('收入位置、学历与身心状态','慢病与身心状态')
 t=t.replace('使用各臂自己的年龄快照样本。收入位置为游戏 pct × 100，非现实收入排名；学历0–5为类别编码，不能当作线性年数。幸福、健康为游戏内部评分。','使用各臂自己的年龄快照样本。慢病个数来自快照 nConds，幸福和健康为游戏内部评分。')
 t=t.replace('另要求策略臂截至该年龄有执行证据','另要求干预臂已有相关场景证据')
 old='当前：另要求策略臂截至该年龄，年度记账可见至少一次指定学习支出。年度记账只保留主要条目，可能漏掉小额学习，因此这是可观测学习子组，不是全部成功学习者；支出也不等于毕业。'
 t=t.replace(old,subset).replace("'月收入差中位'","'健康差中位'").replace("x.metric==='income'","x.metric==='hl'").replace('fmt(inc.median)',"inc.median==null?'—':inc.median.toFixed(2)")
 t=t.replace("['策略','收入位置中位','学历编码中位','幸福中位','健康中位']","['策略','慢病个数中位','人际中位','幸福中位','健康中位']").replace("['pct','edu','h','hl']","['nConds','so','h','hl']")
 start=t.index('let cov=D.coverage');end=t.index("$('life').innerHTML",start)
 t=t[:start]+'''let cov=D.coverage.filter(r=>r.iso===iso);$('coverage').innerHTML=table(['策略','本人住院覆盖/1,000','本人住院事件数','本人/孩子医院决策人数','有可见保费人数','有可见健康采买人数','终局开关符合人数'],cov.map(r=>[NAMES[r.arm],r.hospital_people,r.hospital_events,r.hospital_choice_people,r.visible_premium_people,r.visible_diet_people,r.final_policy_matches]));$('exposure').innerHTML=table(['策略','年龄段','可见收支条目','条目次数'],D.bands.filter(r=>r.iso===iso&&['保险费','医疗费','孩子的医疗费','配偶的医疗费','多选蔬菜、全谷的采买'].includes(r.event)).map(r=>[NAMES[r.arm],r.band,r.event,r.n]))+'<h3>终局慢病记录：每臂1,000个出生样本</h3>'+table(['策略','高血压人数','糖尿病人数','心脏病人数'],cov.map(r=>[NAMES[r.arm],r.htn_at_death,r.dm_at_death,r.heart_at_death]))+'<p class="note">各人死亡年龄不同；这些人数不能用于直接比较同年龄风险。住院覆盖是终身本人hospAt记录，不是全家所有医疗，更不是理赔次数。</p>';''' + t[end:]
 t=t.replace('收益差不等于投资回报率；资产还受劳动收入、家庭、住房、健康和路径分岔影响。收益率需要资金进出和本金时间序列，本报告没有据此编造年化回报或最大回撤。','资产结果不是保险赔付收益率或饮食成本效益。原始账本只保留主要收支，无法完整核算保费、医疗和采买成本，因此不据此宣称已经算出完整回本率。')
 tokens={'TITLE':title,'EXPERIMENT':exp,'N':'10,000','QUESTION':'同样的出生起点，比较经济负担、健康与风险保障。主结果保留全部策略样本，执行场景另列。','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':'按年龄拆开：可见支出与终局疾病','DETAIL_NOTE':'年度 fl.it 压缩为主要收支，条目次数只是可见下限，费用为四舍五入后的条目，不能复原完整账单。未列出的年龄段表示该来源没有可见记录，不是保证没有发生。终局开关不符合可能来自成年前死亡或年内状态变化。','FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
 pub=ROOT/'work/github-pages-peers2002';files=[r/'tables'/f for f in ['groups.csv','pairs.csv','coverage.csv','lifespan.csv','common_survivors.csv','health_bands.csv']]
 for deployed in [False,True]:
  links=' · '.join(f'<a href="{prefix+f.name if deployed else "tables/"+f.name}">{f.name}</a>' for f in files)
  links+='<p>'+ ' · '.join(f'<a href="{prefix+f if deployed else "../../scripts/"+f}">{f}</a>' for f in ['analyze_health_reports.py','build_health_reports.py','policy_report.template.html'])+'</p>'
  out=t
  for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():out=out.replace('__'+k+'__',v)
  out=out.replace('analyze_policy_reports.py','analyze_health_reports.py').replace('build_policy_reports.py','build_health_reports.py')
  (pub/(exp+'.html') if deployed else r/'report.html').write_text(out)
 for f in files:shutil.copyfile(f,pub/(prefix+f.name))
 for f in ['analyze_health_reports.py','build_health_reports.py','policy_report.template.html']:shutil.copyfile(ROOT/'scripts'/f,pub/(prefix+f))
 print('Built',exp,len(out))
if __name__=='__main__':main(sys.argv[1])
