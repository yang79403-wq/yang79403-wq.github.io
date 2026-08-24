from pathlib import Path
import json
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
DATA = ROOT / 'data' / 'content'
MARKET = ROOT / 'data' / 'market'


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


def make_article(soup, item):
    li = soup.new_tag('li')
    a = soup.new_tag('a', href=f"detail.html?cat={item.get('_file', 'content')}&id={item.get('id', '')}")
    a.string = item.get('title', '未命名资料')
    li.append(a)
    return li


def make_market_li(soup, item):
    li = soup.new_tag('li')
    span = soup.new_tag('span', **{'class': 'title'})
    span.string = item.get('title') or item.get('name') or item.get('品种') or '行情资料'
    li.append(span)
    price = item.get('price') or item.get('价格') or item.get('value')
    if price not in (None, ''):
        p = soup.new_tag('span', **{'class': 'date'})
        p.string = str(price)
        li.append(p)
    return li


def main():
    html = INDEX.read_text(encoding='utf-8')
    soup = BeautifulSoup(html, 'html.parser')
    contents = all_content()[:12]
    markets = all_market()

    # 保持现有网站设计，只同步首页的数据列表。
    for heading in soup.find_all(['h2', 'h3', 'h4']):
        if '最新资讯' in text(heading):
            panel = heading.find_parent(class_='panel')
            if panel:
                body = panel.find(class_='panel-body')
                if body:
                    ul = body.find('ul')
                    if ul:
                        ul.clear()
                        for item in contents:
                            ul.append(make_article(soup, item))
                    else:
                        links = body.find_all('a', recursive=True)
                        for a in links:
                            a.decompose()
                        for item in contents:
                            body.append(make_article(soup, item))
            break

    for heading in soup.find_all(['h2', 'h3', 'h4']):
        if '行情' in text(heading) and '最新' not in text(heading):
            panel = heading.find_parent(class_='panel')
            if panel:
                ul = panel.find('ul', class_='market-list')
                if ul:
                    ul.clear()
                    for item in markets[:12]:
                        ul.append(make_market_li(soup, item))
                    break

    INDEX.write_text(str(soup), encoding='utf-8')


if __name__ == '__main__':
    main()
