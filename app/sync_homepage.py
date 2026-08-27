from pathlib import Path
import json
from bs4 import BeautifulSoup
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
DATA = ROOT / 'data' / 'content'
MARKET = ROOT / 'data' / 'market'
QR = '/assets/wechat-customer-qr.svg'

SECTION_MAP = {
    '收藏交流': 'content', '鉴赏参考': 'content', '品相研究': 'content', '收藏知识': 'content',
    '市场资讯': 'market', '真伪知识': 'content', '收藏普及': 'content', '藏品展示': 'content',
    '鉴赏学习': 'content', '行情资讯': 'market', '评级知识': 'services',
    '每日行情': 'market', '今日热点': 'market', '银元': 'market', '古钱币': 'content', '纸币': 'zhibi', '福建钱币': 'fujian',
    '福建钱币专区': 'fujian', '福建银元 铜币': 'fujian', '福建古钱 花钱': 'fujian', '福建纸币': 'fujian', '福建货币文化': 'fujian',
    '钱币研究中心': 'content', '老银元收藏研究': 'content', '古钱币版别研究': 'content', '纸币收藏研究': 'zhibi', '纪念币研究': 'content', '机制币版别研究': 'content',
    '评级知识交流': 'services', '收藏学院': 'advisor', '藏友交流': 'content', '银元交流': 'content', '古钱币交流': 'content', '纸币交流': 'zhibi', '纪念币交流': 'content', '徽章交流': 'content', '经验分享': 'content',
    '藏品保管建议': 'advisor', '防潮': 'advisor', '防氧化': 'advisor', '存放环境': 'advisor', '保护盒': 'advisor', '纸币保护': 'zhibi', '长期保存': 'advisor', '关于我们': 'about'
}


def section_href(label):
    t = ' '.join(str(label or '').split())
    for key, group in SECTION_MAP.items():
        if t == key or key in t:
            return 'section.html?group=' + quote(group, safe='')
    return None


def read_records(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ('records', 'items', 'data', 'articles'):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def all_content():
    out = []
    for p in sorted(DATA.glob('*.json')):
        for x in read_records(p):
            if isinstance(x, dict) and x.get('status', 'published') == 'published' and x.get('title'):
                y = dict(x)
                y['_file'] = p.stem
                out.append(y)
    out.sort(key=lambda x: x.get('date', ''), reverse=True)
    return out


def all_market():
    out = []
    for p in sorted(MARKET.glob('*.json')):
        for x in read_records(p):
            if isinstance(x, dict):
                y = dict(x)
                y['_file'] = p.stem
                out.append(y)
    return out[:20]


def text(el):
    return el.get_text(' ', strip=True) if el else ''


def detail_href(item):
    return f"detail.html?cat={item.get('_file', 'content')}&id={item.get('id', '')}"


def make_article(soup, item):
    li = soup.new_tag('li')
    a = soup.new_tag('a', href=detail_href(item))
    a.string = item.get('title', '未命名资料')
    a['style'] = 'display:block;color:inherit;text-decoration:none;cursor:pointer'
    li.append(a)
    return li


def make_market_li(soup, item):
    li = soup.new_tag('li')
    a = soup.new_tag('a', href=detail_href(item))
    a['class'] = 'title'
    a['style'] = 'display:block;flex:1;color:inherit;text-decoration:none;cursor:pointer'
    a.string = item.get('title') or item.get('name') or item.get('品种') or '行情资料'
    li.append(a)
    price = item.get('price') or item.get('价格') or item.get('value')
    if price not in (None, ''):
        p = soup.new_tag('span', **{'class': 'date'})
        p.string = str(price)
        li.append(p)
    return li


def make_latest_panel(soup, contents):
    old = soup.find(id='latest-content')
    if old:
        old.decompose()
    panel = soup.new_tag('div', id='latest-content')
    panel['class'] = 'panel'
    panel['style'] = 'margin-top:24px'
    head = soup.new_tag('div', **{'class': 'panel-head'})
    h3 = soup.new_tag('h3')
    h3.string = '📰 最新收藏内容'
    head.append(h3)
    more = soup.new_tag('span', **{'class': 'more'})
    more.string = '点击标题查看详情 ›'
    head.append(more)
    panel.append(head)
    body = soup.new_tag('div', **{'class': 'panel-body'})
    ul = soup.new_tag('ul', **{'class': 'market-list'})
    if contents:
        for item in contents[:20]:
            li = make_article(soup, item)
            li['style'] = 'padding:10px 0;border-bottom:1px dashed var(--border)'
            ul.append(li)
    else:
        li = soup.new_tag('li')
        li.string = '暂无已发布内容'
        ul.append(li)
    body.append(ul)
    panel.append(body)
    return panel


def add_hero_qr(soup):
    hero = soup.find('section', class_='hero')
    if not hero:
        return
    current = hero.get('style', '')
    if 'position:' not in current:
        hero['style'] = (current + ';position:relative').strip(';')
    old = hero.find(id='hongsheng-hero-qr')
    if old:
        old.decompose()
    box = soup.new_tag('div', id='hongsheng-hero-qr')
    box['style'] = 'position:absolute;right:8%;top:50%;transform:translateY(-50%);z-index:5;width:190px;padding:12px 12px 10px;background:rgba(28,12,8,.72);border:1px solid #c9a35a;border-radius:6px;box-shadow:0 8px 28px rgba(0,0,0,.32);text-align:center;backdrop-filter:blur(2px)'
    img = soup.new_tag('img', src=QR, alt='微信客服二维码')
    img['style'] = 'width:150px;height:150px;margin:0 auto;object-fit:contain;background:#fff;border:5px solid #fff;border-radius:3px'
    box.append(img)
    title = soup.new_tag('div')
    title.string = '📱 微信客服'
    title['style'] = 'margin-top:8px;color:#f3d99a;font-size:15px;font-weight:700;letter-spacing:1px'
    box.append(title)
    sub = soup.new_tag('div')
    sub.string = '扫码联系客服'
    sub['style'] = 'margin-top:3px;color:#eadcc4;font-size:11px'
    box.append(sub)
    hero.append(box)


def add_footer_qr(soup):
    footer = soup.find('footer')
    if not footer:
        return
    contact = footer.find(class_='footer-contact')
    if not contact:
        return
    for node in list(contact.find_all(class_='qr-box')):
        node.decompose()
    for node in list(contact.find_all(class_='qr-label')):
        node.decompose()
    wrap = soup.new_tag('div', **{'class': 'hs-footer-qr-wrap'})
    wrap['style'] = 'width:160px;margin:12px 0 8px;display:block;position:relative'
    box = soup.new_tag('div', **{'class': 'hs-footer-qr-image'})
    box['style'] = 'width:150px;height:150px;background:#fff;border-radius:6px;border:6px solid #fff;display:flex;align-items:center;justify-content:center;overflow:hidden;padding:0;box-sizing:content-box'
    img = soup.new_tag('img', src=QR, alt='微信客服二维码')
    img['style'] = 'display:block;width:150px;height:150px;max-width:none;object-fit:contain;margin:0;padding:0;border:0'
    box.append(img)
    wrap.append(box)
    label = soup.new_tag('div')
    label.string = '📱 微信客服'
    label['style'] = 'margin-top:8px;color:#e8cf9a;font-size:12px;text-align:center;white-space:nowrap;display:block;width:162px'
    wrap.append(label)
    contact.append(wrap)


def make_static_market_links(soup, ul):
    for li in ul.find_all('li', recursive=False):
        if li.find('a'):
            continue
        title = text(li)
        if not title:
            continue
        a = soup.new_tag('a', href='detail.html?marketTitle=' + quote(title, safe=''))
        a['class'] = 'title'
        a['style'] = 'display:block;flex:1;color:inherit;text-decoration:none;cursor:pointer'
        a.string = title
        li.clear()
        li.append(a)


def remove_legacy_qr(soup):
    old = soup.find(id='hongsheng-customer-qr')
    if old:
        old.decompose()


def add_search_bar(soup):
    if soup.find(id='hs-home-search'):
        return
    nav = soup.select_one('.mainnav')
    if not nav:
        return
    wrap = soup.new_tag('div', id='hs-home-search')
    wrap['style'] = 'margin-left:auto;display:flex;align-items:center;gap:6px;padding:8px 12px'
    inp = soup.new_tag('input', id='hs-search-input', type='search', placeholder='搜索收藏资料、行情、版别')
    inp['style'] = 'width:190px;max-width:24vw;padding:7px 10px;border:1px solid rgba(232,207,154,.4);border-radius:4px;outline:none;background:#fffdf8;color:#3a2f22;font-size:12px'
    btn = soup.new_tag('button', id='hs-search-btn', type='button')
    btn.string = '搜索'
    btn['style'] = 'border:0;border-radius:4px;padding:7px 10px;background:#c9a35a;color:#4b2c06;font-size:12px;font-weight:700;cursor:pointer'
    wrap.append(inp)
    wrap.append(btn)
    nav.append(wrap)
    script = soup.new_tag('script')
    script.string = '''
(function(){
  const input=document.getElementById('hs-search-input'),btn=document.getElementById('hs-search-btn');
  function go(){const q=(input.value||'').trim();if(q)location.href='search.html?q='+encodeURIComponent(q);}
  btn&&btn.addEventListener('click',go); input&&input.addEventListener('keydown',e=>{if(e.key==='Enter')go();});
})();
'''
    soup.body.append(script)


def add_responsive_rules(soup):
    if soup.find(id='hs-responsive-enhancements'):
        return
    style = soup.new_tag('style', id='hs-responsive-enhancements')
    style.string = '''
@media(max-width:900px){
  .header{padding:12px 16px}.brand-text h1{font-size:20px}.brand-slogan{display:none}.header-icons{gap:12px;margin-left:10px}.header-icons li{font-size:11px}.mainnav{padding:0 10px;flex-wrap:wrap}.mainnav a{padding:10px 12px;font-size:13px}.hero{min-height:360px;padding:34px 28px}.hero-content{max-width:60%}.hero-content h2{font-size:34px}.hero-content h3{font-size:18px}.wrap{padding:0 14px}.section-row{flex-direction:column}.research-grid{grid-template-columns:repeat(3,1fr)}.three-col{grid-template-columns:1fr}.service-grid{grid-template-columns:repeat(2,1fr)}.fujian-grid{grid-template-columns:repeat(2,1fr)}.rate-grid{grid-template-columns:repeat(2,1fr)}#hongsheng-hero-qr{right:3%!important;width:160px!important}#hongsheng-hero-qr img{width:122px!important;height:122px!important}
}
@media(max-width:640px){
  .topbar{padding:6px 12px}.topbar-search{display:none}.header{align-items:flex-start}.brand{gap:8px}.brand-emblem{width:44px;height:44px;font-size:18px}.brand-text h1{font-size:18px}.brand-text p{font-size:10px}.header-icons{gap:8px}.header-icons .icon-circle{width:30px;height:30px}.header-icons li span:last-child{display:none}.mainnav{overflow-x:auto;flex-wrap:nowrap;white-space:nowrap}.mainnav li{flex:0 0 auto}.hero{min-height:420px;padding:28px 18px}.hero-content{max-width:100%;padding-right:2px}.hero-content h2{font-size:30px}.hero-content h3{font-size:16px}.checks{gap:12px;flex-wrap:wrap}.hero-btns{gap:8px;flex-wrap:wrap}.hero-btns a{padding:9px 14px}.hero-coins-right{width:50%;opacity:.38}.hero-dots{bottom:10px}.notice{padding:10px 12px}.notice-icons{display:none}.wrap{width:100%;padding:0 12px}.section-row{padding:16px 0}.panel-body{padding:12px}.service-grid,.fujian-grid,.rate-grid,.research-grid{grid-template-columns:repeat(2,1fr);gap:10px}.service-card{padding:12px 6px}.research-img{height:90px}.three-col{gap:12px}.footer{padding:26px 14px 14px}.footer-top{flex-direction:column}.footer-desc{text-align:left}.footer-contact{min-width:0}.hs-footer-qr-wrap{margin-left:auto!important;margin-right:auto!important}#hongsheng-hero-qr{display:none!important}#hs-home-search{width:100%;margin:0;padding:7px 10px;border-top:1px solid rgba(232,207,154,.2)}#hs-search-input{max-width:none!important;flex:1;width:auto!important}
}
'''
    soup.head.append(style)


def add_real_section_links(soup):
    for li in soup.select('.header-icons li'):
        if li.find('a'):
            continue
        href = section_href(text(li))
        if not href:
            continue
        a = soup.new_tag('a', href=href)
        a['class'] = 'hs-header-link'
        a['style'] = 'display:flex;flex-direction:column;align-items:center;gap:6px;color:inherit;text-decoration:none;cursor:pointer'
        for child in list(li.contents):
            a.append(child.extract())
        li.append(a)

    for card in soup.select('.service-card, .fujian-card, .research-card, .rate-card'):
        if card.find_parent('a'):
            continue
        href = section_href(text(card))
        if href:
            a = soup.new_tag('a', href=href)
            a['class'] = 'hs-click-card'
            a['style'] = 'display:block;color:inherit;text-decoration:none;cursor:pointer;height:100%'
            card.wrap(a)

    for item in soup.select('.mini-icons .m-item'):
        if item.find_parent('a'):
            continue
        href = section_href(text(item))
        if href:
            a = soup.new_tag('a', href=href)
            a['class'] = 'hs-mini-link'
            a['style'] = 'display:block;color:inherit;text-decoration:none;cursor:pointer;height:100%'
            item.wrap(a)

    for head in soup.select('.panel-head'):
        if head.find_parent('a'):
            continue
        href = section_href(text(head))
        if not href:
            continue
        a = soup.new_tag('a', href=href)
        a['class'] = 'hs-panel-link'
        a['style'] = 'display:block;color:inherit;text-decoration:none;cursor:pointer'
        head.wrap(a)

    for a in soup.select('.mainnav a'):
        href = section_href(text(a))
        if href and text(a) != '首页':
            a['href'] = href

    for li in soup.select('.notice-icons li'):
        if li.find('a'):
            continue
        href = section_href(text(li))
        if href:
            a = soup.new_tag('a', href=href)
            a['style'] = 'display:flex;flex-direction:column;align-items:center;gap:5px;color:inherit;text-decoration:none;cursor:pointer'
            for child in list(li.contents):
                a.append(child.extract())
            li.append(a)

    style = soup.new_tag('style')
    style.string = '''
.hs-click-card,.hs-mini-link,.hs-header-link,.hs-panel-link{transition:opacity .15s ease,transform .15s ease}
.hs-click-card:hover,.hs-mini-link:hover,.hs-header-link:hover,.hs-panel-link:hover{opacity:.86}
.hs-panel-link>.panel-head{width:100%}
'''
    soup.head.append(style)


def main():
    if not INDEX.exists():
        raise FileNotFoundError(f'首页不存在: {INDEX}')
    soup = BeautifulSoup(INDEX.read_text(encoding='utf-8'), 'html.parser')
    contents = all_content()[:20]
    markets = all_market()

    remove_legacy_qr(soup)

    latest_heading = None
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        if '最新资讯' in text(heading):
            latest_heading = heading
            panel = heading.find_parent(class_='panel')
            body = panel.find(class_='panel-body') if panel else None
            if body:
                ul = body.find('ul')
                if ul:
                    ul.clear()
                    for item in contents:
                        ul.append(make_article(soup, item))
            break

    target = soup.find(id='market')
    latest = make_latest_panel(soup, contents)
    if target:
        target.insert_after(latest)

    add_hero_qr(soup)

    for heading in soup.find_all(['h2', 'h3', 'h4']):
        if '行情' in text(heading) and '最新' not in text(heading):
            panel = heading.find_parent(class_='panel')
            if not panel:
                continue
            ul = panel.find('ul', class_='market-list')
            if not ul:
                continue
            if markets:
                ul.clear()
                for item in markets[:12]:
                    ul.append(make_market_li(soup, item))
            else:
                make_static_market_links(soup, ul)
            break

    add_footer_qr(soup)
    add_real_section_links(soup)
    add_search_bar(soup)
    add_responsive_rules(soup)

    INDEX.write_text(str(soup), encoding='utf-8')


if __name__ == '__main__':
    main()
