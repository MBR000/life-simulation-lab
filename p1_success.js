const scopeLabels={primary:'成年工作 + 留学',work:'成年工作',study:'成年留学',spouse:'随配偶外派',nomad:'数字游牧后定居',refugee:'战争避难',adopt:'跨国收养',family:'晚年与子女团聚',unknown:'原因未能确认',minor:'未成年工作或留学',all:'全部实际出国路径'};
function renderSuccess(){
 const r=D.success.find(r=>r.iso===$('country').value&&r.age===$('age').value&&r.mode===$('successMode').value&&r.scope===$('successScope').value);
 $('successCount').textContent=`${D.countries[r.iso]} · ${r.age==='death'?'终生末次':r.age+' 岁'} · ${scopeLabels[r.scope]}：${r.n} 对入选（原始 1,000 对）。按出国时间、路径和未出国对照初筛 ${r.eligible} 对，再应用双方快照与居住地条件。`;
 $('successWarning').textContent=r.n===0?'本口径没有符合条件的配对，金额留空；并不表示该路径不存在。':r.n<30?'本口径不足 30 对，仅作个案性描述，不据此作稳定结论。':!['primary','work','study'].includes(r.scope)?'当前是其他情境或全路径参照，不进入成年工作 / 留学的主结论。':'';
 $('successTable').innerHTML=table(['指标','同种子未出国对照中位数','出国成功路径中位数','配对差中位数','配对差均值'],[['monthly_cny','月均收入 / 元'],['nw_cny','净资产 / 元'],['money_cny','现金 / 元'],['h','幸福分']].map(([k,label])=>{let m=r.metrics[k],d=k==='h'?1:0;return[label,fmt(m.avoid.median,d),fmt(m.seek.median,d),m.paired.median==null?'—':sign(m.paired.median,d),m.paired.mean==null?'—':sign(m.paired.mean,d)]}));
 const pick=scope=>D.success.find(x=>x.iso===r.iso&&x.age===r.age&&x.mode===r.mode&&x.scope===scope);
 $('routeComparison').innerHTML=table(['首次路径','配对数','月均收入 未出 / 出（元）','收入配对差中位数','净资产 未出 / 出（元）','资产配对差中位数'],['work','study'].map(k=>{let x=pick(k),a=x.metrics.monthly_cny,b=x.metrics.nw_cny;return [scopeLabels[k],x.n,fmt(a.avoid.median)+' / '+fmt(a.seek.median),a.paired.median==null?'—':sign(a.paired.median,0),fmt(b.avoid.median)+' / '+fmt(b.seek.median),b.paired.median==null?'—':sign(b.paired.median,0)]}));
 $('specialComparison').innerHTML=table(['其他首次路径','初筛配对数','最终入选配对数'],['spouse','nomad','refugee','adopt','family','unknown','minor'].map(k=>{let x=pick(k);return [scopeLabels[k],x.eligible,x.n]}));
}
$('country').addEventListener('change',renderSuccess);$('age').addEventListener('change',renderSuccess);$('successMode').onchange=renderSuccess;$('successScope').onchange=renderSuccess;renderSuccess();
