# -*- coding: utf-8 -*-
from pathlib import Path
import json,sys,shutil,html
ROOT=Path(__file__).resolve().parents[1]
def main(exp):
    r=ROOT/'experiments'/exp;d=json.loads((r/'tables/analysis.json').read_text());inv=exp=='P2_invest';prefix='p2_' if inv else 'p3_'
    names={'cash':'存款','bond':'债券','mix':'股债各半','stock':'股票指数','world':'全球指数','property':'不动产基金','trade':'自行选股'} if inv else {'drift':'随波逐流','course':'只开证照课程','max':'综合学习策略'}
    title='存下来的钱，放在哪里？' if inv else '一直学习，何时改变人生？'
    def pair(age,arm,base=None,metric='nw'):
        return next(p for p in d['pairs'] if p['iso']=='CHN' and p['age']==str(age) and p['arm']==arm and p['base']==(base or d['ref']) and p['metric']==metric and p['mode']=='all')
    def num(n):return f'{n:,.0f}'
    def card(heading,p):return f'<div class="panel"><h3>{heading}</h3><p>{p}</p></div>'
    if inv:
        w=pair(65,'world');t=pair(65,'trade','stock');early=pair(24,'property')
        findings='<div class="grid">'+card('中国组65岁：全球指数路径更高',f'与存款比较，{w["n"]} 对共同幸存者的净资产配对差中位为 <b>+{num(w["median"])} 元</b>；胜率 {w["win"]:.1%}。两臂净资产中位分别为 {num(w["right"]["median"])} / {num(w["left"]["median"])} 元。')+card('自行选股：多数配对低于指数',f'65岁与股票指数比较，{t["n"]} 对的净资产差中位为 <b>{num(t["median"])} 元</b>，胜率 {t["win"]:.1%}。这是整条策略路径差，不是交易账户的超额收益率。')+card('24岁：不动产臂几乎没有差异',f'相对存款，净资产差中位为 {num(early["median"])} 元，正差比例仅 {early["win"]:.1%}。应结合市场可用性与持有记录解释，不能据此说不动产终身无效。')+'</div>'
        mechanism='<p>七臂都在18岁起每年尝试设为目标理财方式。全球指数和自行选股不可用时先退到股票，再退存款；债券、股债各半、不动产不可用时退存款。条件改变后再尝试切回。现金臂也会改写自动选择，所以它不等于未经干预的默认人生。</p><p>policyActs 记录实际切换；当目标回退为现金、当前已经是现金时，没有切换记录。因此“曾回退人数”只是有显式 fallback 记录的人，零不等于从未受市场限制。策略抉择为零也不等于策略没执行，还可能通过每年直接切换生效。</p><p>年度 v 字段只记录状态变化：脚本向后延续上一状态，成年后 money&gt;0 时显示品种，money&lt;0 时显示 loan/debt；储备 pot 可能仍在投资，因此它不是完整投资账户。年度记账压缩为主要收支条目，不能完整复原每年的投资本金、收益或回撤。</p>'
        detail='成年年度轨迹：目标品种、存款与负债'
        note='按实际观察到的成年年度记录计分母；省略的 v 视为沿用上次状态，显式空值才清空。目标持有要求当年显示目标品种。存款臂的目标持有列与存款列重合，不可相加；其他臂各列互斥。未观察到目标不等于从未投资，可能存在 pot 或年内变化。'
    else:
        early=pair(24,'max');late=pair(65,'max');c=pair(65,'course');income=pair(40,'max',metric='income')
        findings='<div class="grid">'+card('中国组24岁：学习伴随早期资产代价',f'综合学习相对默认人生，{early["n"]} 对的净资产差中位为 <b>{num(early["median"])} 元</b>；不能只看退休结果而跳过早期投入。')+card('中国组中后期：综合策略出现优势',f'40岁月均收入配对差中位为 <b>{num(income["median"])} 元</b>；65岁净资产差中位为 <b>+{num(late["median"])} 元</b>（{late["n"]} 对，胜率 {late["win"]:.1%}）。这些年龄的样本并非完全相同。')+card('只开证照课程：并不复制综合学习结果',f'65岁相对默认人生，{c["n"]} 对的净资产差中位为 <b>{num(c["median"])} 元</b>。综合策略还改变升学选择、专注方向和在职教育，不能把它的结果归功于证照课程一个开关。')+'</div>'
        mechanism='<p>综合学习 max 在相关抉择中偏向继续学习，主动选择 study/learn/mind 专注，18岁后开启证照课程，并尝试同等学力、夜间大学和在职研究所。course 只强制证照课程开关；drift 保留默认自动人生，本次独立采集，未用噪声基线替换。</p><p>学习也有条件：课程自动行为每两年检查一次，需满足年龄、职业和资金门槛；缺钱会跳过。60岁关闭证照课程，在职研究所限制70岁以下。综合策略并没有额外主动调用开放大学购买动作，因此不能把它称作“保证一生持续读书”。</p><p>下表终身发生次数来自 counts.shop_*，人数来自至少一次事件；次数不是学历提升次数，也不是毕业人数。开关生效率低于20%的提示只适用于干预臂；默认人生没有要求学习开关有效。学历编码：0未上学、1小学、2初中、3高中、4大学、5研究生。</p>'
        detail='学习年龄段：可核验的事件证据'
        note='证照课程条目来自年度主要收支记账，可能被合并进“其他”，所以分年龄次数是可见下限。policyActs:ged/nightuni/nightgrad 是主动操作记录，与记账不能相加；未列出的年龄段表示该来源零条可见记录。终身完整次数以上表 counts 为准。开放大学未被主动调用，观察到的终身次数为0。无法从压缩账本确定所有普通升学的逐年成本。'
    tokens={'TITLE':title,'EXPERIMENT':exp,'N':num(d['n']),'QUESTION':'同样的出生起点，改变理财方针之后，财富、风险与整条人生如何分岔？' if inv else '升学、在职教育与证照课程，需要分别看投入、执行和不同年龄的结果。','FINDINGS':findings,'MECHANISM':mechanism,'DETAIL_TITLE':detail,'DETAIL_NOTE':note,'FINISHED':d['finished'],'HASH':d['source_hash'],'DATA':json.dumps(d,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c'),'NAMES':json.dumps(names,ensure_ascii=False)}
    template=(ROOT/'scripts/policy_report.template.html').read_text()
    files=[p.name for p in (r/'tables').glob('*.csv')]
    pub=ROOT/'work/github-pages-peers2002';pub.mkdir(exist_ok=True)
    for deployed in [False,True]:
        links=' · '.join(f'<a href="{prefix+f if deployed else "tables/"+f}">{html.escape(f)}</a>' for f in files)
        links+='<p>'+ ' · '.join(f'<a href="{prefix+f if deployed else "../../scripts/"+f}">{f}</a>' for f in ['analyze_policy_reports.py','build_policy_reports.py','policy_report.template.html'])+'</p>'
        h=template
        for k,v in {**tokens,'DOWNLOADS':json.dumps(links,ensure_ascii=False)}.items():h=h.replace('__'+k+'__',v)
        (pub/(exp+'.html') if deployed else r/'report.html').write_text(h)
    for f in files:shutil.copyfile(r/'tables'/f,pub/(prefix+f))
    for f in ['analyze_policy_reports.py','build_policy_reports.py','policy_report.template.html']:shutil.copyfile(ROOT/'scripts'/f,pub/(prefix+f))
    print('BUILT',exp,(r/'report.html').stat().st_size)
if __name__=='__main__':main(sys.argv[1])
