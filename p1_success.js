function renderSuccess(){
 const r=D.success.find(r=>r.iso===$('country').value&&r.age===$('age').value&&r.mode===$('successMode').value&&r.scope===$('successScope').value);
 $('successCount').textContent=`${D.countries[r.iso]} · ${r.age==='death'?'终生末次':r.age+' 岁'}：${r.n} 对入选（原始 1,000 对）。按出国时间及路径初筛 ${r.eligible} 对，再要求双方有快照、对照当时在出生国，并应用当前居住地条件。`;
 $('successTable').innerHTML=table(['指标','同种子未出国对照中位数','出国成功路径中位数','配对差中位数','配对差均值'],[['monthly_cny','月均收入 / 元'],['nw_cny','净资产 / 元'],['money_cny','现金 / 元'],['h','幸福分']].map(([k,label])=>{let m=r.metrics[k],d=k==='h'?1:0;return[label,fmt(m.avoid.median,d),fmt(m.seek.median,d),m.paired.median==null?'—':sign(m.paired.median,d),m.paired.mean==null?'—':sign(m.paired.mean,d)]}));
}
$('country').addEventListener('change',renderSuccess);$('age').addEventListener('change',renderSuccess);$('successMode').onchange=renderSuccess;$('successScope').onchange=renderSuccess;renderSuccess();
