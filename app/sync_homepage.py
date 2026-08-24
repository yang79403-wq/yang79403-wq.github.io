from pathlib import Path
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
DATA = ROOT / 'data' / 'content'
MARKET = ROOT / 'data' / 'market'
QR = '/assets/wechat-customer-qr.svg'


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
    out=[]
    for p in sorted(DATA.glob('*.json')):
        for x in read_records(p):
            if isinstance(x,dict) and x.get('status','published')=='published' and x.get('title'):
                y=dict(x); y['_file']=p.stem; out.append(y)
    out.sort(key=lambda x:x.get('date',''),reverse=True)
    return out


def all_market():
    out=[]
    for p in sorted(MARKET.glob('*.json')):
        for x in read_records(p):
            if isinstance(x,dict):
                y=dict(x); y['_file']=p.stem; out.append(y)
    return out[:20]


def text(el):
    return el.get_text(' ',strip=True) if el else ''


def detail_href(item):
    return f"detail.html?cat={item.get('_file','content')}&id={item.get('id','')}"


def make_article(soup,item):
    li=soup.new_tag('li')
    a=soup.new_tag('a',href=detail_href(item)); a.string=item.get('title','未命名资料')
    a['style']='display:block;color:inherit;text-decoration:none;cursor:pointer'
    li.append(a); return li


def make_market_li(soup,item):
    li=soup.new_tag('li')
    a=soup.new_tag('a',href=detail_href(item)); a['class']='title'
    a['style']='display:block;flex:1;color:inherit;text-decoration:none;cursor:pointer'
    a.string=item.get('title') or item.get('name') or item.get('品种') or '行情资料'
    li.append(a)
    price=item.get('price') or item.get('价格') or item.get('value')
    if price not in (None,''):
        p=soup.new_tag('span',**{'class':'date'}); p.string=str(price); li.append(p)
    return li


def make_latest_panel(soup,contents):
    old=soup.find(id='latest-content')
    if old: old.decompose()
    panel=soup.new_tag('div',id='latest-content'); panel['class']='panel'; panel['style']='margin-top:24px'
    head=soup.new_tag('div',**{'class':'panel-head'})
    h3=soup.new_tag('h3'); h3.string='📰 最新收藏内容'; head.append(h3)
    more=soup.new_tag('span',**{'class':'more'}); more.string='点击标题查看详情 ›'; head.append(more); panel.append(head)
    body=soup.new_tag('div',**{'class':'panel-body'}); ul=soup.new_tag('ul',**{'class':'market-list'})
    if contents:
        for item in contents[:20]:
            li=make_article(soup,item); li['style']='padding:10px 0;border-bottom:1px dashed var(--border)'; ul.append(li)
    else:
        li=soup.new_tag('li'); li.string='暂无已发布内容'; ul.append(li)
    body.append(ul); panel.append(body); return panel


def make_customer_qr(soup):
    marker='hongsheng-customer-qr'
    old=soup.find(id=marker)
    if old: old.decompose()
    section=soup.new_tag('section',id=marker)
    section['style']='background:#fffdf8;border:1px solid var(--border);border-radius:4px;margin:24px 0;padding:22px 24px;display:flex;align-items:center;justify-content:center;gap:28px'
    img=soup.new_tag('img',src=QR,alt='微信客服二维码')
    img['style']='width:150px;height:150px;object-fit:contain;background:#fff;border:6px solid #fff;border-radius:4px;box-shadow:0 2px 10px rgba(0,0,0,.08)'
    box=soup.new_tag('div'); box['style']='max-width:520px'
    h=soup.new_tag('h3'); h.string='📱 微信客服'; h['style']='color:var(--red-dark);font-size:18px;margin-bottom:8px'; box.append(h)
    p=soup.new_tag('p'); p.string='扫码联系客服，进行公益收藏知识交流与咨询。'; p['style']='font-size:13px;color:var(--text-light);line-height:1.8;margin:0'; box.append(p)
    p2=soup.new_tag('p'); p2.string='免费咨询 · 鉴赏交流 · 行情资料 · 收藏研究'; p2['style']='font-size:12px;color:var(--text);line-height:1.8;margin:6px 0 0'; box.append(p2)
    section.append(img); section.append(box)
    return section


def add_footer_qr(soup):
    footer=soup.find('footer')
    if not footer: return
    marker='hongsheng-footer-qr'
    old=footer.find(id=marker)
    if old: old.decompose()
    box=soup.new_tag('div',id=marker)
    box['style']='display:flex;flex-direction:column;align-items:center;gap:8px;min-width:150px'
    img=soup.new_tag('img',src=QR,alt='微信客服二维码')
    img['style']='width:110px;height:110px;object-fit:contain;background:#fff;border:6px solid #fff;border-radius:4px'
    box.append(img)
    p=soup.new_tag('div'); p.string='📱 扫一扫联系客服'; p['style']='font-size:12px;color:#e8cf9a;text-align:center'; box.append(p)
    footer.insert(0,box)


def find_insert_target(soup):
    market=soup.find(id='market')
    if market:return market
    hero=soup.find(class_='hero')
    if hero:return hero
    return soup.body


def make_static_market_links(soup,ul):
    """没有结构化行情数据时，不删除首页现有行情，而是把每一行变成可点击详情。"""
    from urllib.parse import quote
    for li in ul.find_all('li',recursive=False):
        if li.find('a'): continue
        title=text(li)
        if not title: continue
        a=soup.new_tag('a',href='detail.html?marketTitle='+quote(title,safe=''))
        a['class']='title'; a['style']='display:block;flex:1;color:inherit;text-decoration:none;cursor:pointer'
        a.string=title
        li.clear(); li.append(a)


def main():
    soup=BeautifulSoup(INDEX.read_text(encoding='utf-8'),'html.parser')
    contents=all_content()[:20]; markets=all_market()

    for heading in soup.find_all(['h2','h3','h4']):
        if '最新资讯' in text(heading):
            panel=heading.find_parent(class_='panel'); body=panel.find(class_='panel-body') if panel else None
            if body:
                ul=body.find('ul')
                if ul:
                    ul.clear()
                    for item in contents: ul.append(make_article(soup,item))
            break

    target=find_insert_target(soup); latest=make_latest_panel(soup,contents)
    if target and target.name=='div' and target.get('id')=='market': target.insert_after(latest)
    elif target and target.name=='section' and 'hero' in (target.get('class') or []): target.insert_after(latest)

    if not soup.find(id='hongsheng-customer-qr'):
        nav=soup.find('nav',class_='mainnav')
        if nav: nav.insert_after(make_customer_qr(soup))
        else: soup.body.insert(0,make_customer_qr(soup))

    for heading in soup.find_all(['h2','h3','h4']):
        if '行情' in text(heading) and '最新' not in text(heading):
            panel=heading.find_parent(class_='panel')
            if not panel: continue
            ul=panel.find('ul',class_='market-list')
            if not ul: continue
            if markets:
                ul.clear()
                for item in markets[:12]: ul.append(make_market_li(soup,item))
            else:
                make_static_market_links(soup,ul)
            break

    add_footer_qr(soup)
    INDEX.write_text(str(soup),encoding='utf-8')

if __name__=='__main__': main()
