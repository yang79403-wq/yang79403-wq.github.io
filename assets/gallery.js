(() => {
  const DATA_URL = '/data/image-index.json';
  const style = document.createElement('style');
  style.textContent = `
    .hs-gallery{margin:26px 0 10px;background:#fffdf8;border:1px solid #e3d6bf;border-radius:16px;padding:20px;box-shadow:0 5px 18px #2b15100d}
    .hs-gallery h2{margin:0 0 5px;color:#741712;font:900 25px "Songti SC","Microsoft YaHei",serif}
    .hs-gallery-sub{margin:0 0 16px;color:#766657;font-size:13px;line-height:1.7}
    .hs-gallery-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}
    .hs-photo{margin:0;overflow:hidden;border:1px solid #e3d6bf;border-radius:12px;background:#f6f0e4}
    .hs-photo a{display:block;text-decoration:none}
    .hs-photo img{display:block;width:100%;height:170px;object-fit:cover;background:#eee;transition:transform .25s ease}
    .hs-photo:hover img{transform:scale(1.035)}
    .hs-caption{padding:10px 11px 12px}
    .hs-topic{font-weight:900;color:#741712;font-size:14px}
    .hs-title{margin-top:4px;color:#4b3b31;font-size:12px;line-height:1.5;min-height:36px}
    .hs-credit{margin-top:5px;color:#8a7b6d;font-size:10px;line-height:1.45}
    .hs-credit a{color:#741712;text-decoration:none}
    @media(max-width:900px){.hs-gallery-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
    @media(max-width:650px){.hs-gallery{padding:15px}.hs-gallery-grid{grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}.hs-photo img{height:135px}.hs-gallery h2{font-size:21px}}
    @media(max-width:390px){.hs-gallery-grid{grid-template-columns:1fr}.hs-photo img{height:190px}}
  `;
  document.head.appendChild(style);

  function esc(s){return String(s||'').replace(/[&<>\"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[m]));}

  fetch(DATA_URL, {cache:'no-store'}).then(r => r.ok ? r.json() : Promise.reject(r.status)).then(data => {
    const main = document.querySelector('main');
    if (!main || !Array.isArray(data.items) || !data.items.length) return;
    const byTopic = {};
    data.items.forEach(x => { (byTopic[x.topic] ||= []).push(x); });
    const preferred = ['古钱币','银元','机制币','纸币','纪念币','金银币','钱币鉴赏','版别研究','福建钱币','泉州收藏','收藏资讯','收藏文化'];
    const items = preferred.flatMap(t => (byTopic[t] || []).slice(0,1));
    if (!items.length) return;

    const section = document.createElement('section');
    section.className = 'hs-gallery';
    section.innerHTML = `<h2>🖼️ 高清钱币图鉴</h2><p class="hs-gallery-sub">自动整理可再利用的公开图片，为知识、鉴赏、版别、地域与收藏资讯板块提供视觉资料。图片保留来源、作者与许可证信息。</p><div class="hs-gallery-grid"></div>`;
    const grid = section.querySelector('.hs-gallery-grid');
    items.forEach(x => {
      const fig = document.createElement('figure');
      fig.className = 'hs-photo';
      fig.innerHTML = `<a href="${esc(x.source_url)}" target="_blank" rel="noopener"><img src="${esc(x.image)}" alt="${esc(x.topic+' '+x.title)}" loading="lazy"></a><figcaption class="hs-caption"><div class="hs-topic">${esc(x.topic)}</div><div class="hs-title">${esc(x.title)}</div><div class="hs-credit">${esc(x.author)} · ${esc(x.license)} · <a href="${esc(x.source_url)}" target="_blank" rel="noopener">查看来源</a></div></figcaption>`;
      grid.appendChild(fig);
    });
    main.insertBefore(section, main.firstElementChild);
  }).catch(() => {});
})();
