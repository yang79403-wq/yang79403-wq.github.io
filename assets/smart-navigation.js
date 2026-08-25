(function(){'use strict';
const MAP={
 '收藏交流':'content','鉴赏参考':'content','品相研究':'content','收藏知识':'content','市场资讯':'market','真伪知识':'content','收藏普及':'content','藏品展示':'content',
 '每日行情':'market','今日热点':'market','银元':'market','古钱币':'market','纸币':'market','福建钱币':'fujian',
 '最新收藏内容':'content','福建钱币专区':'fujian','福建银元 铜币':'fujian','福建古钱 花钱':'fujian','福建纸币':'fujian','福建货币文化':'fujian',
 '钱币研究中心':'content','老银元收藏研究':'content','古钱币版别研究':'content','纸币收藏研究':'content','纪念币研究':'content','机制币版别研究':'content',
 '评级知识交流':'services','收藏学院':'advisor','藏友交流':'content','银元交流':'content','古钱币交流':'content','纸币交流':'content','纪念币交流':'content','徽章交流':'content','经验分享':'content',
 '藏品保管建议':'advisor','防潮':'advisor','防氧化':'advisor','存放环境':'advisor','保护盒':'advisor','纸币保护':'advisor','长期保存':'advisor','关于我们':'about'
};
function clean(t){return(t||'').replace(/更多\s*[›>]?/g,'').replace(/进入专区\s*[›>]?/g,'').replace(/公益平台/g,'').replace(/点击标题查看详情\s*[›>]?/g,'').trim()}
function target(text){const t=clean(text);const g=MAP[t]||Object.keys(MAP).find(k=>t.includes(k));const group=typeof g==='string'?g:(g?MAP[g]:null);return group?'section.html?group='+encodeURIComponent(group):null}
function makeClickable(el,url){if(!el||el.dataset.hsSmartLinked)return;el.dataset.hsSmartLinked='1';el.style.cursor='pointer';el.setAttribute('role','link');el.setAttribute('tabindex','0');const go=e=>{if(e.target.closest('a'))return;e.preventDefault();location.href=url};el.addEventListener('click',go);el.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){go(e)}})}
function apply(){
 document.querySelectorAll('.panel-head h3,.panel-head .more,.service-card h4,.research-card h4,.fujian-card h4,.rate-card,.m-item').forEach(el=>{const u=target(el.textContent);if(u)makeClickable(el,u)});
 document.querySelectorAll('.service-card,.research-card,.fujian-card').forEach(el=>{const u=target(el.textContent);if(u)makeClickable(el,u)});
 document.querySelectorAll('.mainnav a').forEach(a=>{const u=target(a.textContent);if(u&&(!a.getAttribute('href')||a.getAttribute('href')==='#'))a.href=u});
}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',apply);else apply();
})();
