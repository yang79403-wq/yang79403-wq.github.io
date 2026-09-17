const q=document.querySelector('#researchInput'),out=document.querySelector('#researchResult');

document.querySelector('#researchBtn')?.addEventListener('click',()=>{
  const v=q.value.trim();
  if(!v){q.focus();return;}
  const safe=v.replace(/[<>]/g,'');
  out.innerHTML=`研究任务：<b>${safe}</b><br>已建立研究任务。当前网站会优先从公开资料、评级信息与市场证据中匹配相关内容；图像识别和更深层 AI 推理接口仍在接入中。`;
});
q?.addEventListener('keydown',e=>{if(e.key==='Enter')document.querySelector('#researchBtn').click()});

(async()=>{
  const discover=document.querySelector('#discover');
  if(!discover) return;
  try{
    const r=await fetch('/data/realtime_ai.json?t='+Date.now(),{cache:'no-store'});
    if(!r.ok) throw new Error('data');
    const d=await r.json();
    const items=Array.isArray(d.items)?d.items:[];
    const section=document.createElement('section');
    section.className='wrap section research-feed';
    section.id='latestResearch';
    section.innerHTML=`<h2>01A · 今日研究资料</h2><p class="sub">只把通过主题相关性、正文质量、来源优先级与去重门槛的资料带到首页。</p>`;
    const grid=document.createElement('div');
    grid.className='grid';
    if(!items.length){
      grid.innerHTML='<article class="card big"><div class="num">NO NEW MATERIAL</div><h3>暂无通过质量门槛的新资料</h3><p>系统会继续从公开来源采集；宁可少发，也不拿低质量内容填充首页。</p></article>';
    }else{
      grid.innerHTML=items.slice(0,6).map(x=>{
        const esc=s=>String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
        const badge=(x.evidence_level||'C');
        return `<article class="card"><div class="num">${esc(x.category||'收藏研究')} · 证据 ${esc(badge)}</div><h3>${esc(x.title||'未命名资料')}</h3><p>${esc((x.summary||'').slice(0,260))}</p><div class="result"><b>研究提示</b><br>${esc((x.analysis||'').slice(0,220))}</div><span class="signal">${esc(x.date||'')} · ${esc(x.source||'公开资料')}</span></article>`;
      }).join('');
    }
    section.appendChild(grid);
    discover.after(section);
  }catch(e){
    // 首页保持可用，数据层故障不影响主页面。
  }
})();
