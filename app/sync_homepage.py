from pathlib import Path
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
DATA = ROOT / 'data' / 'content'
MARKET = ROOT / 'data' / 'market'
QR = '/assets/wechat-customer-qr.svg'

# 首页母版保持不变：主视觉右侧二维码 + 联系我们原二维码占位框。
def read_records(path):
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return []
    if isinstance(data, list): return data
    if isinstance(data, dict):
        for key in ('records','items','data','articles'):
            if isinstance(data.get(key), list): return data[key]
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

def text(el): return el.get_text(' ',strip=True) if el else ''
def detail_href(item): return f"detail.html?cat={item.get('_file','content')}&id={item.get('id','')}"

def make_article(soup,item):
    li=soup.new_tag('li')
    a=soup.new_tag('a',href=detail_href(item)); a.string=item.get('title','未命名资料')
    a['style']='display:block;color:inherit;text-decoration:none;cursor:pointer'
    li.append(a); return li

def make_market_li(soup,item):
    li=soup.new_tag('li')
    a=soup.new_tag('a',href=detail_href(item)); a['class']='title'; a['style']='display:block;flex:1;color:inherit;text-decoration:none;cursor:pointer'
    a.string=item.get('title') or item.get('name') or item.get('品种') or '行情资料'; li.append(a)
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

def add_hero_qr(soup):
    hero=soup.find('section',class_='hero')
    if not hero: return
    current=hero.get('style','')
    if 'position:' not in current: hero['style']=(current+';position:relative').strip(';')
    old=hero.find(id='hongsheng-hero-qr')
    if old: old.decompose()
    box=soup.new_tag('div',id='hongsheng-hero-qr')
    box['style']='position:absolute;right:8%;top:50%;transform:translateY(-50%);z-index:5;width:190px;padding:12px 12px 10px;background:rgba(28,12,8,.72);border:1px solid #c9a35a;border-radius:6px;box-shadow:0 8px 28px rgba(0,0,0,.32);text-align:center;backdrop-filter:blur(2px)'
    img=soup.new_tag('img',src=QR,alt='微信客服二维码'); img['style']='width:150px;height:150px;margin:0 auto;object-fit:contain;background:#fff;border:5px solid #fff;border-radius:3px'; box.append(img)
    title=soup.new_tag('div'); title.string='📱 微信客服'; title['style']='margin-top:8px;color:#f3d99a;font-size:15px;font-weight:700;letter-spacing:1px'; box.append(title)
    sub=soup.new_tag('div'); sub.string='扫码联系客服'; sub['style']='margin-top:3px;color:#eadcc4;font-size:11px'; box.append(sub)
    hero.append(box)

def add_footer_qr(soup):
    footer=soup.find('footer')
    if not footer: return
    contact=footer.find(class_='footer-contact')
    if not contact: return

    # 彻底删除旧二维码框及旧版标签，避免旧 CSS/伪元素再次叠加。
    for node in list(contact.find_all(class_='qr-box')):
        node.decompose()
    for node in list(contact.find_all(class_='qr-label')):
        node.decompose()
    for node in list(contact.find_all(['div','span','p'])):
        if text(node).strip() in ('📱 微信客服','微信客服','📱 微信二维码','微信二维码'):
            node.decompose()

    # 使用全新的类名，二维码本体只占原白色占位区域，文字放在框外下方。
    wrap=soup.new_tag('div',**{'class':'hs-footer-qr-wrap'})
    wrap['style']='width:160px;margin:12px 0 8px;display:block;position:relative'
    box=soup.new_tag('div',**{'class':'hs-footer-qr-image'})
    box['style']='width:150px;height:150px;background:#fff;border-radius:6px;border:6px solid #fff;display:flex;align-items:center;justify-content:center;overflow:hidden;padding:0;box-sizing:content-box'
    img=soup.new_tag('img',src=QR,alt='微信客服二维码')
    img['style']='display:block;width:150px;height:150px;max-width:none;object-fit:contain;margin:0;padding:0;border:0'
    box.append(img)
    wrap.append(box)
    label=soup.new_tag('div')
    label.string='📱 微信客服'
    label['style']='margin-top:8px;color:#e8cf9a;font-size:12px;text-align:center;white-space:nowrap;display:block;width:162px'
    wrap.append(label)
    contact.append(wrap)

def make_static_market_links(soup,ul):
    from urllib.parse import quote
    for li in ul.find_all('li',recursive=False):
        if li.find('a'): continue
        title=text(li)
        if not title: continue
        a=soup.new_tag('a',href='detail.html?marketTitle='+quote(title,safe='')); a['class']='title'; a['style']='display:block;flex:1;color:inherit;text-decoration:none;cursor:pointer'; a.string=title
        li.clear(); li.append(a)

def remove_legacy_qr(soup):
    old=soup.find(id='hongsheng-customer-qr')
    if old: old.decompose()

def main():
    soup=BeautifulSoup(INDEX.read_text(encoding='utf-8'),'html.parser')
    contents=all_content()[:20]; markets=all_market()
    remove_legacy_qr(soup)
    for heading in soup.find_all(['h2','h3','h4']):
        if '最新资讯' in text(heading):
            panel=heading.find_parent(class_='panel'); body=panel.find(class_='panel-body') if panel else None
            if body:
                ul=body.find('ul')
                if ul:
                    ul.clear()
                    for item in contents: ul.append(make_article(soup,item))
            break
    target=soup.find(id='market'); latest=make_latest_panel(soup,contents)
    if target: target.insert_after(latest)
    add_hero_qr(soup)
    for heading in soup.find_all(['h2','h3','h4']):
        if '行情' in text(heading) and '最新' not in text(heading):
            panel=heading.find_parent(class_='panel')
            if not panel: continue
            ul=panel.find('ul',class_='market-list')
            if not ul: continue
            if markets:
                ul.clear()
                for item in markets[:12]: ul.append(make_market_li(soup,item))
            else: make_static_market_links(soup,ul)
            break
    add_footer_qr(soup)
    INDEX.write_text(str(soup),encoding='utf-8')

if __name__=='__main__': main()
