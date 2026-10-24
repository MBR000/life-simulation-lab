# -*- coding: utf-8 -*-
from pathlib import Path
import json,shutil
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
d=json.loads((R/'tables/analysis.json').read_text());names={'full':'包足礼金','none':'只到场致意'}
def pair(age,metric):return next(p for p in d['pairs'] if p['iso']=='CHN' and p['age']==str(age) and p['mode']=='all' and p['metric']==metric)
def n(x):return f'{x:,.0f}'
def card(title,body):return f'<div class="panel"><h3>{title}</h3><p>{body}</p></div>'
a=pair(40,'nw');b=pair(40,'so');c=pair(65,'nw');h=pair(40,'h')
findings='<div class="grid">'+card('中国组40岁：省钱有没有留下资产？',f'{a["n"]} 对共同幸存者中，只到场相对包足礼金的净资产差中位为 <b>{n(a["median"])} 元</b>，资产更高的比例为 {a["win"]:.1%}。两臂净资产中位分别为 {n(a["right"]["median"])} / {n(a["left"]["median"])} 元。')+card('同一批人：人际与幸福也要一起看',f'40岁人际评分配对差中位为 <b>{format(b["median"],".2f")}</b> 分，幸福差中位为 <b>{format(h["median"],".2f")}</b> 分。评分来自游戏内部，不能解读为现实朋友数量或幸福百分比。')+card('65岁：长期结果不等于礼金总额',f'{c["n"]} 对中，净资产差中位为 <b>{n(c["median"])} 元</b>，P10 / P90 为 {n(c["p10"])} / {n(c["p90"])} 元。后续人生会分岔，不能把这笔差额全归为直接省下的礼金。')+'</div>'
findings+='<p class="warn">均值与中位数可能给出不同方向：中国组40岁资产差中位约 +10,143 元，但均值约 −5,317 元；65岁中位差转为负值。各国和年龄也不一致，因此证据不支持“少送礼必定更富”这样的单一结论。此处数值包含路径分岔，不是纯粹礼金节省。</p>'
mechanism='''<p>18岁起，每年将 gift 设为 full 或 none。礼金系数分别为1和0：影响亲戚丧礼、朋友婚礼，以及孙辈入学、考大学和结婚的部分贺礼。它不代表拒绝全部亲友支出，也不是“从不参加社交”。</p><div class="two"><div class="panel"><h3>亲戚丧礼与朋友婚礼</h3><p>只到场走 giftSkip 分支：幸福 +1、人际 +1，另有15%概率再扣人际2分。包足礼金参加朋友婚礼通常人际 +3、幸福 +2；但缺钱、无收入或其他限制下也可能只帮忙，不一定真付钱。因此不能把 full 当作人人每次都成功支付。</p></div><div class="panel"><h3>孙辈的贺礼</h3><p>礼金开关改变对应支出；这几类事件中的幸福与人际增益仍可能保留。不同事件机制不能混成一个“不给红包就失去朋友”的假设。</p></div></div><p>exp_funeral 是亲戚丧礼事件计数，在零礼金分支也会更新，适合衡量是否遇到场景，不能当作支付次数。policyActs 不记录这种每年直接赋值的开关，零条操作不等于没有生效。下表为终身覆盖，独立于顶部年龄筛选。</p>'''
t=(ROOT/'scripts/policy_report.template.html').read_text()
t=t.replace('另要求策略臂截至该年龄有执行证据','另要求只到场臂截至该年龄遇到婚丧场景')
t=t.replace('fmt(inc.median)',"inc.median==null?'—':inc.median.toFixed(2)")
t=t.replace('净资产：P10 — 中位数 — P90','净资产：P10 — 中位数 — P90')
t=t.replace('收益差不等于投资回报率；资产还受劳动收入、家庭、住房、健康和路径分岔影响。收益率需要资金进出和本金时间序列，本报告没有据此编造年化回报或最大回撤。','净资产差不等于直接省下的礼金。年度账本会将较小项目并入“其他”，且婚丧账目可能包括其他费用，不能据此伪造完整礼金账单。')
t=t.replace("'月收入差中位'","'人际差中位'").replace("x.metric==='income'","x.metric==='so'")
t=t.replace("['策略','收入位置中位','学历编码中位','幸福中位','健康中位']","['策略','收入位置中位','人际中位','幸福中位','健康中位']").replace("['pct','edu','h','hl']","['pct','so','h','hl']")
t=t.replace('当前：另要求策略臂截至该年龄，年度记账可见至少一次指定学习支出。年度记账只保留主要条目，可能漏掉小额学习，因此这是可观测学习子组，不是全部成功学习者；支出也不等于毕业。','当前：另要求只到场臂截至该年龄，原始日志明确出现成年亲戚丧礼或朋友婚礼。它是遇到场景的证据，不是支付成功筛选；未能从日志可靠识别的孙辈事件不进入该子组。两臂机会与日志可见性可能不同，仍有选择偏差。')
start=t.index('let cov=D.coverage');end=t.index("$('life').innerHTML",start)
t=t[:start]+'''let cov=D.coverage.filter(r=>r.iso===iso);$('coverage').innerHTML=table(['策略','亲戚丧礼覆盖/1,000','亲戚丧礼事件数','成年明确婚丧日志人数','成年明确日志条数','终局开关符合人数'],cov.map(r=>[NAMES[r.arm],r.funeral_people+(r.funeral_people<200?' · 场景覆盖不足20%':''),r.funeral_events,r.observed_event_people,r.observed_event_count,r.final_policy_matches]));$('exposure').innerHTML=table(['策略','年龄段','日志场景','可见事件数'],D.bands.filter(r=>r.iso===iso&&['亲戚丧礼','朋友婚礼'].includes(r.event)).map(r=>[NAMES[r.arm],r.band,r.event,r.n]));''' + t[end:]
tokens={'TITLE':'红白包，包钱还是到场？','EXPERIMENT':'P4_gift','N':'10,000','QUESTION':'相同出生起点，改变礼金习惯：省下的钱、人际关系与幸福如何变化？','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':'按年龄拆开：明确可见的婚丧场景','DETAIL_NOTE':'日志分类只匹配成年“亲戚丧礼/讣告”和“朋友婚礼”等明确文字；不把普通亲友死亡、自己的婚礼算进去。日志可能被省略，所以不是完整婚丧次数，不能将两臂可见日志差直接解释为社交机会增减。完整亲戚丧礼事件数见上方 exp_funeral 计数；孙辈贺礼只解释已核对机制，未冒充完整分类。终局开关不符合可能是18岁前死亡，不能当作成年执行失败。','FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
pub=ROOT/'work/github-pages-peers2002';files=[R/'tables'/f for f in ['groups.csv','pairs.csv','coverage.csv','lifespan.csv','common_survivors.csv','event_bands.csv']]
sources=[('analyze.py','p4_analyze.py'),('build_report.py','p4_build_report.py')]
for deployed in [False,True]:
    links=' · '.join(f'<a href="{"p4_"+f.name if deployed else "tables/"+f.name}">{f.name}</a>' for f in files)
    links+='<p>'+ ' · '.join(f'<a href="{remote if deployed else "scripts/"+local}">{local}</a>' for local,remote in sources)+'</p>'
    links+='<p><a href="'+('p4_base.template.html' if deployed else '../../scripts/policy_report.template.html')+'">基础模板</a></p>'
    out=t
    for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():out=out.replace('__'+k+'__',v)
    begin=out.index('复算：把 analyze_policy_reports.py');end=out.index('</p>',begin)
    out=out[:begin]+'复算：在原项目目录运行 python3 experiments/P4_gift/scripts/analyze.py P4_gift，再运行 python3 experiments/P4_gift/scripts/build_report.py。需要原始 experiments 数据、N_noise 与 scripts/policy_report.template.html；下载的基础模板放回该位置。'+out[end:]
    (pub/'P4_gift.html' if deployed else R/'report.html').write_text(out)
for f in files:shutil.copyfile(f,pub/('p4_'+f.name))
for local,remote in sources:shutil.copyfile(R/'scripts'/local,pub/remote)
shutil.copyfile(ROOT/'scripts/policy_report.template.html',pub/'p4_base.template.html')
print('Built P4',len(out))
