# -*- coding: utf-8 -*-
from pathlib import Path
import json, shutil, re
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'tables/analysis.json').read_text())
d['migration']=json.loads((R/'tables/migration.json').read_text())
d['success']=json.loads((R/'tables/success.json').read_text())
template=(R/'scripts/report.template.html').read_text()
template=template.replace('</head>','<style>.controls label{max-width:100%}.controls select{min-width:0;max-width:100%}@media(max-width:750px){.controls label{width:100%}.controls select{flex:1;font-size:14px}.two>*,.grid>*{min-width:0}}</style></head>')
template=template.replace('先看结论：收入上升，不等于资产更多','全样本参照：收入上升，不等于资产更多')
def cohort(age,scope):
    return next(x for x in d['success'] if x['iso']=='CHN' and x['age']==age and x['mode']=='ever' and x['scope']==scope)
def amount(row,metric,arm):
    return f"{row['metrics'][metric][arm]['median']:,.0f}"
w,s,p=cohort('24','work'),cohort('24','study'),cohort('40','primary')
intro=f'''<section><h2>先分清问题：成年工作出国，与留学出国</h2><p>主比较只纳入成年后首次通过工作或留学成功出国的路径。收养、避难、配偶外派、游牧和晚年团聚保留为独立情境，不进入主结论。所有结果仍来自模拟。</p><div class="two"><div class="panel"><h3>中国组 24 岁：工作与留学的早期结果不同</h3><p>工作出国 {w['n']} 对：月均收入中位数，出国 <b>{amount(w,'monthly_cny','seek')} 元</b>，同种子未出国 <b>{amount(w,'monthly_cny','avoid')} 元</b>。</p>
<p>留学出国 {s['n']} 对：分别为 <b>{amount(s,'monthly_cny','seek')} 元</b> 与 <b>{amount(s,'monthly_cny','avoid')} 元</b>。两组出国路径的净资产中位数都低于各自未出国对照。</p><p class="note">工作与留学两组包含不同的人，各有自己的配对对照；不能根据组间金额直接判断哪种选择更好。</p></div>
<div class="panel"><h3>中国组 40 岁：收入与资产仍要分开看</h3><p>成年工作与留学合计 {p['n']} 对。出国 / 未出国的月均收入中位数为 <b>{amount(p,'monthly_cny','seek')} / {amount(p,'monthly_cny','avoid')} 元</b>；净资产中位数为 <b>{amount(p,'nw_cny','seek')} / {amount(p,'nw_cny','avoid')} 元</b>。</p><p class="note">口径为截至该年龄曾成功出国，包含已回国者。不同年龄的入选样本不同，不能把两组横截面差异直接解释为个人成长。人民币为游戏购买力换算；筛选成功者不等于消除了选择偏差。</p></div></div><p><a href="#compare">查看分路径配对金额 →</a> · <a href="#migration">查看出国方式与目的地 →</a></p></section>'''
template=re.sub(r'<section><h2>全样本参照：.*?</section>',lambda _:intro,template,count=1,flags=re.S)
template=template.replace('03 / 同起点，也可能走出很远</h2>','03 / 同起点，也可能走出很远</h2><p class="note">本节使用原始全策略配对作参照，不随“成功出国口径 / 路径范围”筛选变化。</p>')
template=template.replace('<a href="#compare">','<a href="#migration">迁移路径与目的地</a><a href="#compare">',1)
template=template.replace('<section id="compare">',(R/'scripts/migration.section.html').read_text()+'<section id="compare">',1)
template=template.replace('<div class="grid" id="money">',(R/'scripts/success.section.html').read_text()+'<div class="grid" id="money">',1)
template=template.replace('</script></body>',(R/'scripts/migration.js').read_text()+'\n'+(R/'scripts/success.js').read_text()+'\n</script></body>')
html=template.replace('__DATA__',json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
(R/'report.html').write_text(html)
pub=R.parents[1]/'work/github-pages-peers2002'
for p in (R/'tables').glob('*.csv'):
    shutil.copyfile(p,pub/('p1_'+p.name))
html=html.replace('tables/${n}.csv','p1_${n}.csv').replace('scripts/analyze.py','p1_analyze.py').replace('scripts/build_report.py','p1_build_report.py').replace('scripts/report.template.html','p1_report.template.html')
html=html.replace('tables/migration_people.csv','p1_migration_people.csv').replace('tables/migration_events.csv','p1_migration_events.csv').replace('scripts/analyze_migration.py','p1_analyze_migration.py')
html=html.replace('tables/success_comparison.csv','p1_success_comparison.csv').replace('tables/success_pairs.csv','p1_success_pairs.csv').replace('scripts/analyze_success.py','p1_analyze_success.py')
(pub/'P1_abroad.html').write_text(html)
for name in ['analyze.py','build_report.py','report.template.html','analyze_migration.py','migration.section.html','migration.js','analyze_success.py','success.section.html','success.js']:
    shutil.copyfile(R/'scripts'/name,pub/('p1_'+name))
print('Built',R/'report.html',len(html.encode()),'bytes')
