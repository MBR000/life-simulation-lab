# -*- coding: utf-8 -*-
from pathlib import Path
import json,shutil
ROOT=Path(__file__).resolve().parents[1];r=ROOT/'experiments/C_strategy';pub=ROOT/'work/github-pages-peers2002';d=json.loads((r/'tables/analysis.json').read_text());names={'drift':'默认人生','random':'随机选择','study':'持续学习','abroad':'寻求出国','stock':'股票方针','all':'组合方针'}
p=next(x for x in d['pairs'] if x['iso']=='CHN' and x['arm']=='all' and x['age']=='40' and x['metric']=='nw' and x['mode']=='all');v={x['component']:x['share'] for x in d['variance'] if x['metric']=='lifespan'}
findings=f'''<div class="grid"><div class="panel"><h3>中国40岁：组合减默认</h3><p>{p['n']}对双方有快照者，净资产配对差中位 <b>{p['median']:,.0f} 元</b>，均值 <b>{p['mean']:,.0f} 元</b>。金额包含路径变化；两者差别体现分布偏斜。</p></div><div class="panel"><h3>寿命变异来自哪里</h3><p>描述性平方和分解：国家 {v['country']:.1%}，方针 {v['strategy']:.1%}，交互 {v['interaction']:.2%}，未解释差异 {v['residual']:.1%}。残差混合出生个体差异与随机路径，不能全叫作“运气”。</p></div><div class="panel"><h3>组合不是简单相加</h3><p>组合使用学习＋出国＋全球指数；单独投资臂使用股票。没有完整交叉组合及单独全球指数臂，不能识别学习×出国的净交互或协同收益。</p></div></div>'''
mechanism='''<div class="two"><div class="panel"><h3>六种方针实际做什么</h3><p>默认臂使用游戏自动选择。随机臂在每次可选抉择中用独立的 seed|strategy 随机流抽选；它不是N_noise的“丢弃一个随机数”。学习臂改写匹配的升学选择，设置学习重心并开启课程、尝试成人教育。出国臂改写出国相关选择，成年后尝试寻找海外工作。股票臂持续切换股票；不可用时可回退现金。</p></div><div class="panel"><h3>组合与执行证据</h3><p>组合含学习、出国和全球指数；全球指数不可用可退股票或现金。选项匹配时投资、出国、学习按代码顺序处理，不是三个完全独立的治疗。</p><p>下表“学习证据”是成人教育成功操作或可见学习账目；“海外居住”是成年年度轨迹或年龄快照位于出生国之外，可能含儿童收养、避难后仍居海外，并不等于成年成功工作移民。“持仓证据”只用固定年龄快照中目标品种且现金为正，组合只认全球指数，可能漏掉两次快照间的投资。</p></div></div>'''
t=(ROOT/'scripts/policy_report.template.html').read_text().replace('5 × 1,000','3 × 1,000').replace('独立的5,000人','独立的3,000人')
t=t.replace('<h3>同种子扰动参考 N2</h3>','<h3>扰动基线的适用边界</h3>').replace('出生后丢弃一个随机数会移动后续随机路径；N2不是策略专属误差，不能从策略差中扣除。它与本次策略对照的幸存样本也可能不同。','本实验用C前缀seed；N2用P前缀seed，不能按序号冒充同种子配对。本报告不相减、不把N2当置信区间；可到既有报告查看独立的路径敏感性参考。')
a=t.index("let n=ps[0].noise;");b=t.index("$('life').innerHTML",a)
t=t[:a]+'''$('noise').textContent='本批没有C种子的专属扰动对照；随机选择臂改变多次实际选择，不能当作噪声基线。';
$('coverage').innerHTML=table(['方针','出生数','改写自动选择人数','有学习证据','曾成年海外居住','目标快照持仓','满足子组全部条件'],D.coverage.filter(r=>r.iso===iso).map(r=>[NAMES[r.arm],r.people,r.changed_people,r.study_people,r.abroad_people,r.invest_people,r.executed_people]));
$('exposure').innerHTML='<h3>年龄样本流失</h3>'+table(['方针','计划','默认缺快照','策略缺快照','双方可比'],D.flows.filter(r=>r.iso===iso&&r.age===age).map(r=>[NAMES[r.arm],r.planned,r.base_missing,r.arm_missing,r.both]))+'<h3>全部出生者寿命配对差（不按执行筛选）</h3>'+table(['方针减默认','配对数','差值P10 / 中位 / P90','均值'],D.lifepairs.filter(r=>r.iso===iso).map(r=>[NAMES[r.arm],r.n,[r.p10,r.median,r.p90].map(x=>x.toFixed(1)).join(' / '),r.mean.toFixed(2)]))+'<h3>达到所选年龄的完整出生队列比例</h3>'+table(['方针','达到年龄人数 / 出生数','比例'],D.survival.filter(r=>r.iso===iso&&r.age===age).map(r=>[NAMES[r.arm],r.reached+'/1000',pct(r.reached/1000)]))+'<p class="note">达到年龄按死亡年龄≥阈值统计，与该年龄快照可用数并不相同。</p><h3>描述性方差分解：18,000局终局值</h3>'+table(['指标','国家','方针','交互','未解释差异'],['lifespan','death_pct','death_edu','death_log_nonnegative_nw'].map(m=>[{lifespan:'享年',death_pct:'终局收入位置',death_edu:'终局学历编码',death_log_nonnegative_nw:'终局净资产 log1p(max(0,nw))'}[m],...['country','strategy','interaction','residual'].map(k=>pct(D.variance.find(r=>r.metric===m&&r.component===k).share))]))+'<p class="warn">平衡双因素平方和分解，无显著性检验。重复seed有关联；残差不是纯运气。终局金额混合死亡年龄，负净资产在这一项变换中被压成0；学历编码的距离不等于教育年限。比例仅属于这三国、六方针和当前模拟器，不能推广为现实人生决定因素。</p><h3>同一seed的寿命极差</h3>'+table(['比较范围','组别','seed数','极差P10 / 中位 / P90'],D.ranges.map(r=>[r.kind==='within_country'?'同国六方针':'同方针三国',D.countries[r.key]||NAMES[r.key],r.n,[r.p10,r.median,r.p90].map(x=>x.toFixed(1)).join(' / ')]));
''' +t[b:]
a=t.index("$('selected').textContent=");b=t.index('let cs=D.common',a)
t=t[:a]+"""$('selected').textContent=mode==='all'?'当前：双方均有该年龄快照，保留策略分配，不要求实际执行。':'当前：只用截至该年龄的证据。随机=至少一次偏离自动选择；学习=成人教育操作或学习账目；出国=成年海外居住（不限迁移原因）；股票=快照目标持仓且现金为正；组合=学习、海外居住、全球指数持仓三者均已观察。各策略门槛不同，不能直接互比；这是选择性、保守可见子组，不是成功者因果收益，也不按未来收益筛选。';"""+t[b:]
t=t.replace('收益差不等于投资回报率；资产还受劳动收入、家庭、住房、健康和路径分岔影响。收益率需要资金进出和本金时间序列，本报告没有据此编造年化回报或最大回撤。','组合臂使用全球指数，单独投资臂使用股票；设计不是全因子交叉，无法把组合优势解释成净协同。终局指标与固定年龄指标分开，所有年龄比较都有存活选择。')
tokens={'TITLE':'同一个人，换种活法','EXPERIMENT':'C_strategy','N':'18,000','QUESTION':'三国、六种方针。比较24岁到65岁的绝对金额、全部出生者寿命，以及实际执行和出生地的差异。','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':'样本、全寿命与方差下钻','DETAIL_NOTE':'方差分解与寿命极差使用全部终局样本；执行子组不会改变这些表。极差只描述当前六个方针或三个国家，选择更多条件通常会扩大极差。','FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
files=sorted((r/'tables').glob('*.csv'));scripts=['analyze_strategy_report.py','build_strategy_report.py','analyze_policy_reports.py','policy_report.template.html']
for deploy in [False,True]:
 links=' · '.join(f'<a href="{"c_"+f.name if deploy else "tables/"+f.name}">{f.name}</a>' for f in files)+'<p>'+' · '.join(f'<a href="{"c_"+f if deploy else "../../scripts/"+f}">{f}</a>' for f in scripts)+'</p>'
 out=t
 for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():out=out.replace('__'+k+'__',v)
 out=out.replace('运行 python3 scripts/analyze_policy_reports.py C_strategy','运行 python3 scripts/analyze_strategy_report.py').replace('python3 scripts/build_policy_reports.py C_strategy','python3 scripts/build_strategy_report.py')
 (pub/'C_strategy.html' if deploy else r/'report.html').write_text(out)
for f in files:shutil.copyfile(f,pub/('c_'+f.name))
for f in scripts:shutil.copyfile(ROOT/'scripts'/f,pub/('c_'+f))
print('Built C',len(out))
