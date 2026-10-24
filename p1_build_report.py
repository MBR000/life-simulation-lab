from pathlib import Path
import json, shutil
R=Path(__file__).resolve().parents[1]
d=json.loads((R/'tables/analysis.json').read_text())
html=(R/'scripts/report.template.html').read_text().replace('__DATA__',json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'))
(R/'report.html').write_text(html)
pub=R.parents[1]/'work/github-pages-peers2002'
for p in (R/'tables').glob('*.csv'):
    shutil.copyfile(p,pub/('p1_'+p.name))
html=html.replace('tables/${n}.csv','p1_${n}.csv').replace('scripts/analyze.py','p1_analyze.py').replace('scripts/build_report.py','p1_build_report.py').replace('scripts/report.template.html','p1_report.template.html')
(pub/'P1_abroad.html').write_text(html)
for name in ['analyze.py','build_report.py','report.template.html']:
    shutil.copyfile(R/'scripts'/name,pub/('p1_'+name))
print('Built',R/'report.html',len(html.encode()),'bytes')
