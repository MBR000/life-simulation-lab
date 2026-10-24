from pathlib import Path
import json, shutil
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'tables/analysis.json').read_text())
d['migration']=json.loads((R/'tables/migration.json').read_text())
d['success']=json.loads((R/'tables/success.json').read_text())
template=(R/'scripts/report.template.html').read_text()
template=template.replace('</head>','<style>.controls label{max-width:100%}.controls select{min-width:0;max-width:100%}@media(max-width:750px){.controls label{width:100%}.controls select{flex:1;font-size:14px}.two>*,.grid>*{min-width:0}}</style></head>')
template=template.replace('先看结论：收入上升，不等于资产更多','全样本参照：收入上升，不等于资产更多')
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
