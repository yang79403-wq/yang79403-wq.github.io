(function(){'use strict';
const ROOT='';
const MAP={
 '收藏交流':'appreciation','鉴赏参考':'appreciation','品相研究':'appreciation','收藏知识':'knowledge','市场资讯':'yinyuan_jizhibi','真伪知识':'knowledge','收藏普及':'knowledge','藏品展示':'appreciation',
 '每日行情':'market','今日热点':'market','银元':'yinyuan_jizhibi','古钱币':'tongqian','纸币':'zhibi','福建钱币':'fujian',
 '最新收藏内容':'latest','福建钱币专区':'fujian','福建银元 铜币':'fujian','福建古钱 花钱':'fujian','福建纸币':'fujian','福建货币文化':'fujian',
 '钱币研究中心':'research','老银元收藏研究':'yinyuan_jizhibi','古钱币版别研究':'tongqian','纸币收藏研究':'zhibi','纪念币研究':'commemorative','机制币版别研究':'yinyuan_jizhibi',
 '评级知识交流':'rating','收藏学院':'academy','藏友交流':'appreciation','银元交流':'yinyuan_jizhibi','古钱币交流':'tongqian','纸币交流':'zhibi','纪念币交流':'commemorative','徽章交流':'appreciation','经验分享':'knowledge',
 '藏品保管建议':'knowledge','防潮':'knowledge','防氧化':'knowledge','存放环境':'knowledge','保护盒':'knowledge','纸币保护':'zhibi','长期保存':'knowledge','关于我们':'about'
};
function clean(t){return (t||'').replace(/更多\s*[›>]?/g,'').replace(/进入专区\s*[›>]?/g,'').replace(/公益平台/g,'').replace(/点击标题查看详情\s*[›>]?/g,'').trim()}
function target(text){const t=clean(text);if(MAP[t])return 'section.html?cat='+encodeURIComponent(MAP[t]);for(const k in MAP){if(t.includes(k))return 'section.html?cat='+encodeURIComponent(MAP[k])}return null}
function makeClickable(el,url){if(!el||el.dataset.hsSmartLinked)return;el.dataset.hsSmartLinked='1';el.style.cursor='pointer';el.setAttribute('role','link');el.addEventListener('click',function(e){if(e.target.closest('a'))return;e.preventDefault();location.href=url})}
function apply(){
 document.querySelectorAll('.panel-head h3,.panel-head .more,.service-card h4,.research-card h4,.fujian-card h4,.rate-card,.m-item').forEach(el=>{const u=target(el.textContent);if(u)makeClickable(el,u)});
 document.querySelectorAll('.service-card,.research-card,.fujian-card').forEach(el=>{const u=target(el.textContent);if(u)makeClickable(el,u)});
 document.querySelectorAll('.mainnav a').forEach(a=>{if(!a.getAttribute('href')||a.getAttribute('href')==='#'){const u=target(a.textContent);if(u)a.href=u}});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);else apply();
})();
