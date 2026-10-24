const M=D.migration,cn=i=>M.names[i]||i;
let migPage=0;
$('migCountry').innerHTML=countries.map(([k,v])=>`<option value="${k}">${v}</option>`).join('');$('migCountry').value='CHN';
const migGroup=()=>M.groups.find(g=>g.iso===$('migCountry').value&&g.arm===$('migArm').value);
const migRecords=()=>M.records.filter(r=>r.iso===$('migCountry').value&&r.arm===$('migArm').value);
function migOverview(){
  const g=migGroup(),rr=migRecords(),ages=rr.map(r=>r.first_age).sort((a,b)=>a-b),med=ages.length?(ages[Math.floor((ages.length-1)/2)]+ages[Math.ceil((ages.length-1)/2)])/2:null;
  $('migrationStats').innerHTML=`<div class="card"><small>本策略组曾出国</small><div class="stat">${g.ever} / ${g.n}</div><p>${fmt(g.ever/g.n*100,1)}% 的完整人生</p></div><div class="card"><small>首次观测出国年龄中位数</small><div class="stat">${fmt(med,1)} 岁</div><p>分母：${g.ever} 位曾出国者</p></div><div class="card"><small>曾回国 / 最终在出生国</small><div class="stat">${g.returned} / ${g.final_home} 人</div><p>占曾出国者 ${fmt(g.returned/g.ever*100,1)}% / ${fmt(g.final_home/g.ever*100,1)}%</p></div>`;
  const routes=Object.entries(g.routes).sort((a,b)=>b[1]-a[1]);
  $('migrationRoutes').innerHTML=table(['路径','人数','占曾出国者'],routes.map(([k,n])=>[`<button data-mig-route="${k}">${M.routes[k]}</button>`,n,fmt(n/g.ever*100,1)+'%']));
  const dests=[...new Set([...Object.keys(g.first_destinations),...Object.keys(g.final_destinations)])].sort((a,b)=>(g.first_destinations[b]||0)-(g.first_destinations[a]||0)||a.localeCompare(b));
  $('migrationDestinations').innerHTML=table(['国家','首次人数','最后人数'],dests.map(k=>[`<button data-mig-dest="${k}" ${!g.first_destinations[k]?'disabled':''}>${cn(k)}</button>`,g.first_destinations[k]||0,g.final_destinations[k]||0]));
  $('migRoute').innerHTML='<option value="all">全部路径</option>'+routes.map(([k,n])=>`<option value="${k}">${M.routes[k]} · ${n} 人</option>`).join('');
  $('migDest').innerHTML='<option value="all">全部目的地</option>'+dests.filter(k=>g.first_destinations[k]).map(k=>`<option value="${k}">${cn(k)} · ${g.first_destinations[k]} 人</option>`).join('');
  $('migAge').value='all';$('migSearch').value='';migPage=0;migPeople();
  document.querySelectorAll('[data-mig-route]').forEach(el=>el.onclick=()=>{$('migRoute').value=el.dataset.migRoute;migPage=0;migPeople()});
  document.querySelectorAll('[data-mig-dest]').forEach(el=>el.onclick=()=>{$('migDest').value=el.dataset.migDest;migPage=0;migPeople()});
}
function migFiltered(){const route=$('migRoute').value,dest=$('migDest').value,age=$('migAge').value,search=$('migSearch').value.trim().toLowerCase();return migRecords().filter(r=>(route==='all'||r.route===route)&&(dest==='all'||r.destination===dest)&&(age==='all'||age==='child'&&r.first_age<18||age==='young'&&r.first_age>=18&&r.first_age<30||age==='mid'&&r.first_age>=30&&r.first_age<50||age==='older'&&r.first_age>=50)&&(!search||(r.seed+' '+r.name).toLowerCase().includes(search))).sort((a,b)=>a.seed.localeCompare(b.seed));}
function migPeople(){
 const rs=migFiltered(),pages=Math.max(1,Math.ceil(rs.length/20));migPage=Math.max(0,Math.min(migPage,pages-1));
 $('migrationCount').textContent=`当前筛选 ${rs.length} 人 / 本组 ${migGroup().ever} 位曾出国者。`;
 $('migrationPeople').innerHTML=table(['种子 / 姓名','首次年龄','首次路径','首次 → 最后居住地','回过国','轨迹'],rs.slice(migPage*20,migPage*20+20).map(r=>[esc(r.seed)+'<br>'+esc(r.name),r.first_age+' 岁',M.routes[r.route],cn(r.destination)+' → '+cn(r.final),r.returned?'是':'否',`<button data-mig-id="${r.id}">查看轨迹</button>`]));
 $('migPage').textContent=`第 ${migPage+1} / ${pages} 页`;$('migPrevious').disabled=migPage===0;$('migNext').disabled=migPage>=pages-1;
 document.querySelectorAll('[data-mig-id]').forEach(el=>el.onclick=()=>migOpen(el.dataset.migId));
}
function migOpen(id){
 const r=M.records.find(r=>r.id===id);
 $('caseContent').innerHTML=`<h2>${esc(r.name)} · ${r.seed}</h2><p>${cn(r.born)}出生 · ${names[r.arm]}策略 · 寿命 ${r.death_age} 岁</p><p>首次年度观测：${r.first_age} 岁 → ${cn(r.destination)}；最后居住地：${cn(r.final)}。</p><p class="note">下面是年度居住地改变的 ${r.events.length} 次记录。起止国家来自年度快照；原文可能提到快照之间的中途国家，因此不是每次跨境的完整清单。事件原文的年龄与快照年龄可能相差 1 年。日志序号从 0 开始，可在迁移事件 CSV 中核对。</p>`+r.events.map(e=>`<article class="panel" style="margin:15px 0"><h3>${e.age} 岁 · ${cn(e.from)} → ${cn(e.to)}（年度观测）</h3><span class="pill">${M.routes[e.route]}</span>${e.evidence?`<p>${esc(e.evidence.text)}</p><p class="note">原始日志 #${e.evidence.index} · ${e.evidence.age} 岁 · 事件 ${esc(e.evidence.tag||'无决策标签')}</p>`:'<p>年度居住国发生变化，但未能在相邻年龄窗口内唯一匹配明确原因。保留未知，不根据相邻申请事件猜测。</p>'}${e.choice?`<details><summary>当时的选择与条件</summary><p>${esc(e.choice.title)} → ${esc(e.choice.label)}</p><p>${esc(e.choice.sub)}</p><p class="note">选择来源：${e.choice.why==='policy:abroad'?'出国策略覆盖':esc(e.choice.why)}。选项说明不等于最终身份或实际花费。</p></details>`:''}</article>`).join('')+(r.final_unobserved?`<p class="callout">死亡时居住地为${cn(r.final)}，与最后年度记录不同；没有补写未观测到的迁移步骤。</p>`:'');
 $('caseDialog').showModal();
}
$('migCountry').onchange=migOverview;$('migArm').onchange=migOverview;
['migRoute','migDest','migAge'].forEach(id=>$(id).onchange=()=>{migPage=0;migPeople()});$('migSearch').oninput=()=>{migPage=0;migPeople()};
$('migReset').onclick=()=>{['migRoute','migDest','migAge'].forEach(id=>$(id).value='all');$('migSearch').value='';migPage=0;migPeople()};
$('migPrevious').onclick=()=>{migPage--;migPeople()};$('migNext').onclick=()=>{migPage++;migPeople()};migOverview();
