from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib, json, re, requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; HongshengJicang-ResearchBot/3.0; +public-research)'}

# 优先公开权威来源，其次评级机构与专业拍卖信息，最后才是行业媒体。
SOURCES = [
    {'name': '中国人民银行', 'url': 'https://www.pbc.gov.cn/goutongjiaoliu/113456/113469/index.html', 'category': '发行资讯', 'priority': 100, 'evidence': 'A', 'type': '官方'},
    {'name': '中国金币网', 'url': 'https://www.chngc.net/', 'category': '金银币资讯', 'priority': 96, 'evidence': 'A', 'type': '官方'},
    {'name': 'NGC', 'url': 'https://www.ngccoin.com/news/', 'category': '国际评级与拍卖', 'priority': 94, 'evidence': 'A', 'type': '评级机构'},
    {'name': 'PCGS', 'url': 'https://www.pcgs.com/news', 'category': '国际评级与拍卖', 'priority': 94, 'evidence': 'A', 'type': '评级机构'},
    {'name': '古泉园地', 'url': 'https://www.chcoin.com/', 'category': '钱币行业资讯', 'priority': 78, 'evidence': 'B', 'type': '行业平台'},
    {'name': '爱藏收藏新闻', 'url': 'https://news.airmb.com/', 'category': '收藏行业资讯', 'priority': 62, 'evidence': 'C', 'type': '行业媒体'},
]

COIN_TERMS = (
    '古钱币','古钱','秦半两','五铢','开元通宝','银元','袁大头','龙洋','机制币','铜元','铜钱',
    '纸币','纸钞','冠号','水印','纪念币','金银币','金币','银币','钱币版别','钱币鉴赏',
    '钱币历史','钱币文化','钱币研究','钱币拍卖','钱币展会','钱币评级','中国钱币','中国银元'
)
FIFTH_RMB_TERMS = ('第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币')
MARKETING_TERMS = ('招商加盟','广告位','代理加盟','加微信','扫码加','优惠券','下单购买','商城购买','立即购买','联系客服购买','代购','团购')
RESEARCH_CUES = ('发行','公告','规格','发行量','材质','铸造','版别','版式','边齿','压力','钱文','书体','评级','成交','结标','拍卖','历史','研究','图录','藏家','品相','来源','人口','存世')
DATE_PATTERNS = (
    re.compile(r'20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}(?:日)?'),
    re.compile(r'20\d{2}年\d{1,2}月\d{1,2}日')
)


def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()


def repair(s):
    if not isinstance(s, str) or not s:
        return s
    marks = ('Ã', 'Â', 'æ', 'ç', 'å', 'é', 'è', 'ä', 'ö', 'ð', 'ñ', 'â', 'ï', '¤', '�')
    if not any(m in s for m in marks):
        return s
    try:
        fixed = s.encode('latin1').decode('utf-8')
        return fixed if sum(fixed.count(m) for m in marks) < sum(s.count(m) for m in marks) else s
    except (UnicodeEncodeError, UnicodeDecodeError):
        return s


def text_has(text, terms):
    t = norm(text).lower()
    return any(x.lower() in t for x in terms)


def blocked(text):
    return text_has(text, FIFTH_RMB_TERMS) or text_has(text, MARKETING_TERMS)


def request_page(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, allow_redirects=True)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        return r.url, r.text
    except Exception:
        return '', ''


def extract_date(soup, text=''):
    for attrs in (
        {'property': 'article:published_time'},
        {'property': 'og:updated_time'},
        {'name': 'date'},
        {'name': 'publishdate'},
        {'itemprop': 'datePublished'},
        {'itemprop': 'dateModified'},
    ):
        node = soup.find('meta', attrs=attrs)
        if node and node.get('content'):
            date = normalize_date(node.get('content'))
            if date:
                return date
    for pattern in DATE_PATTERNS:
        m = pattern.search(text)
        if m:
            date = normalize_date(m.group(0))
            if date:
                return date
    return ''


def normalize_date(s):
    s = norm(s).replace('年', '-').replace('月', '-').replace('日', '').replace('/', '-').replace('.', '-')
    m = re.search(r'(20\d{2})-(\d{1,2})-(\d{1,2})', s)
    if not m:
        return ''
    y, mo, d = map(int, m.groups())
    try:
        return datetime(y, mo, d).strftime('%Y-%m-%d')
    except ValueError:
        return ''


def title_from(soup):
    h = soup.find('h1') or soup.find('h2')
    if h:
        title = repair(norm(h.get_text(' ', strip=True)))
        if 8 <= len(title) <= 160:
            return title
    if soup.title:
        title = repair(norm(soup.title.get_text(' ', strip=True)))
        title = re.sub(r'\s*[|｜-]\s*(NGC|PCGS|中国人民银行|中国金币).*$', '', title, flags=re.I)
        return title[:160]
    return ''


def extract_main_text(soup):
    # 只抽取正文区域，避免把导航、页脚、相关推荐拼进文章。
    for selector in ('article', 'main', '.article-content', '.article_body', '.article-body', '.content', '#content', '.detail-content'):
        root = soup.select_one(selector)
        if root:
            for x in root(['script', 'style', 'nav', 'footer', 'header', 'form', 'aside']):
                x.decompose()
            parts = [repair(norm(p.get_text(' ', strip=True))) for p in root.find_all(['p', 'h2', 'h3'])]
            parts = [x for x in parts if 30 <= len(x) <= 1400 and not blocked(x)]
            joined = norm(' '.join(parts))
            if len(joined) >= 180:
                return joined[:8000]
    parts = [repair(norm(p.get_text(' ', strip=True))) for p in soup.find_all('p')]
    parts = [x for x in parts if 30 <= len(x) <= 1400 and not blocked(x)]
    return norm(' '.join(parts))[:8000]


def article_links(source, page_url, html):
    root = urlparse(page_url)
    soup = BeautifulSoup(html, 'html.parser')
    links = []
    seen = set()
    for a in soup.find_all('a', href=True):
        title = repair(norm(a.get_text(' ', strip=True)))
        href = urljoin(page_url, a['href'])
        p = urlparse(href)
        if not title or len(title) < 8 or p.netloc != root.netloc or href in seen:
            continue
        context = repair(norm(a.parent.get_text(' ', strip=True) if a.parent else ''))
        combined = f'{title} {context}'
        if blocked(combined) or not text_has(combined, COIN_TERMS):
            continue
        # 排除明显的栏目、登录、分页等短链接。
        low = href.lower()
        if any(x in low for x in ('login', 'register', 'javascript:', 'mailto:')):
            continue
        seen.add(href)
        links.append((href, title))
        if len(links) >= 50:
            break
    return links


def discover_source(source):
    final, html = request_page(source['url'])
    if not html:
        return []
    links = article_links(source, final, html)
    # 有些专业站首页本身就能读取为文章目录，加入首页作为候选仅当正文够长。
    candidates = []
    soup = BeautifulSoup(html, 'html.parser')
    main_text = extract_main_text(soup)
    if title_from(soup) and len(main_text) >= 220 and text_has(title_from(soup), COIN_TERMS):
        candidates.append((final, title_from(soup)))
    candidates.extend(links)
    rows = []
    used = set()
    for url, guessed_title in candidates[:35]:
        if url in used:
            continue
        used.add(url)
        f, body = request_page(url)
        if not body:
            continue
        s = BeautifulSoup(body, 'html.parser')
        title = title_from(s) or guessed_title
        text = extract_main_text(s)
        if not title or len(text) < 220 or blocked(f'{title} {text}'):
            continue
        if not text_has(f'{title} {text}', COIN_TERMS):
            continue
        date = extract_date(s, text)
        if not date:
            # 无法确认日期的页面不冒充为今日资料，允许进入但降级。
            freshness = 0
        else:
            try:
                age = (datetime.now().date() - datetime.strptime(date, '%Y-%m-%d').date()).days
                if age > 180 or age < -1:
                    continue
                freshness = max(0, 60 - age * 2)
            except ValueError:
                freshness = 0
        rows.append({
            'title': title[:160],
            'url': f,
            'date': date,
            'text': text,
            'source': source['name'],
            'source_type': source['type'],
            'source_priority': source['priority'],
            'evidence_level': source['evidence'],
            'freshness_score': freshness,
            'source_category': source['category'],
        })
    return rows


def classify(title, body, fallback):
    s = f'{title} {body}'
    t = norm(title)
    # 特殊品类先判定，避免“纪念币+银币”被错投到纸币或泛资讯。
    if text_has(s, ('纸币', '纸钞', '冠号', '水印')) and not text_has(s, FIFTH_RMB_TERMS):
        return '纸币研究'
    if text_has(s, ('袁大头', '孙小头', '银元', '龙洋', '鹰洋', '船洋', '坐洋', '银圆', '黎元洪')):
        return '银元研究'
    if text_has(s, ('机制币', '铜元', '铜板', '机制银币')):
        return '机制币研究'
    if text_has(s, ('古钱币', '古钱', '秦半两', '五铢', '开元通宝', '宋钱', '清钱', '布币', '刀币')):
        return '钱币知识'
    if text_has(s, ('金银币', '金币', '银币', '贵金属币')):
        return '金银币资讯'
    if text_has(s, ('纪念币', '纪念章')):
        return '纪念币资讯'
    if text_has(s, ('福建', '泉州', '厦门', '漳州', '福州')):
        return '地域收藏'
    if text_has(t, ('评级', '人口报告', 'population report', 'auction central')):
        return '评级与市场资料'
    return fallback or '收藏研究'


def score(row):
    title, body = row['title'], row['text']
    s = f'{title} {body}'
    score = row['source_priority'] + row['freshness_score']
    if text_has(title, COIN_TERMS):
        score += 20
    score += min(24, sum(3 for x in RESEARCH_CUES if x in s))
    if len(body) >= 500:
        score += 12
    if len(body) >= 1200:
        score += 8
    if blocked(title) or blocked(body):
        score -= 100
    # 标题越像一句完整研究主题，越容易在前台形成有效阅读入口。
    if 12 <= len(title) <= 70:
        score += 8
    return score


def summary(title, text, category):
    sentences = [norm(x) for x in re.split(r'(?<=[。！？])', text) if len(norm(x)) >= 30]
    sentences = [x for x in sentences if not blocked(x)]
    chosen = sentences[:4]
    if not chosen:
        return f'本条资料围绕“{title}”整理，归入{category}。重点关注发行事实、钱币特征、研究背景与可核验来源。'
    return ' '.join(chosen)[:900]


def research_note(category, body):
    s = body
    if category == '银元研究':
        return '研究时优先核对年份、版别、钱文细节、边齿、压力与包浆；涉及成交时，必须同时记录成交日期、评级、拍卖平台与具体品种。'
    if category == '机制币研究':
        return '重点记录版式、模具特征、铸造工艺、齿边和局部细节，并尽量与可靠图录或同版图片交叉比对。'
    if category == '纸币研究':
        return '重点核对冠号、水印、版式、印刷工艺、纸张与保存状态；涉及版本判断时不要把年份名称直接等同于版别。'
    if category == '纪念币资讯':
        return '优先记录发行日期、材质、规格、发行量、正反面设计与铸造单位，事实与市场观点分开。'
    if category == '金银币资讯':
        return '优先核对材质、重量、成色、规格、发行量与主题，并区分官方发行信息和市场交易信息。'
    if category == '评级与市场资料':
        return '评级与成交资料应作为证据使用，记录机构、分数、成交时间和拍卖平台，不用单条记录推导整体行情。'
    if category == '地域收藏':
        return '福建地域资料优先连接历史流通背景、地方铸币、钱币实物与收藏文化，形成可继续扩展的区域知识节点。'
    return '先确认对象、时代和品类，再把公开来源中的可观察事实逐项对应，避免单一关键词直接下结论。'


def make_item(row):
    category = classify(row['title'], row['text'], row['source_category'])
    key_material = (row['url'] + '|' + re.sub(r'[^\w\u4e00-\u9fff]+', '', row['title'])).encode('utf-8')
    key = hashlib.sha1(key_material).hexdigest()[:16]
    return {
        'id': 'hz-' + key,
        'date': row['date'],
        'title': re.sub(r'[!！?？]+$', '', norm(row['title']))[:80],
        'category': category,
        'keywords': [x for x in COIN_TERMS if x in row['title'] + row['text']][:12],
        'summary': summary(row['title'], row['text'], category),
        'analysis': research_note(category, row['text']),
        'source': row['source'],
        'source_type': row['source_type'],
        'evidence_level': row['evidence_level'],
        'source_url_internal': row['url'],
        'quality_score': score(row),
        'editorial_status': 'published',
        'editorial_method': 'evidence-first-collect-filter-dedupe-classify-edit',
    }


def collect_and_edit():
    candidates = []
    source_status = []
    for source in SOURCES:
        try:
            rows = discover_source(source)
            candidates.extend(rows)
            source_status.append({'name': source['name'], 'records': len(rows), 'error': None})
        except Exception as exc:
            source_status.append({'name': source['name'], 'records': 0, 'error': type(exc).__name__})

    # URL + 标题双重去重，防止同一条资料被多个栏目入口重复抓取。
    dedup = {}
    for row in candidates:
        key = hashlib.sha1((row['url'].split('#')[0] + '|' + norm(row['title']).lower()).encode('utf-8')).hexdigest()
        old = dedup.get(key)
        if old is None or score(row) > score(old):
            dedup[key] = row

    rows = sorted(dedup.values(), key=score, reverse=True)
    published = []
    seen_titles = set()
    for row in rows:
        title_key = re.sub(r'[^\w\u4e00-\u9fff]+', '', norm(row['title']))[:80]
        if title_key in seen_titles:
            continue
        seen_titles.add(title_key)
        item = make_item(row)
        # 质量门槛：必须有明确钱币主题、正文与来源证据。
        if item['quality_score'] < 125 or len(row['text']) < 220:
            continue
        published.append(item)
        if len(published) >= 16:
            break

    if len(published) < 3:
        raise RuntimeError('本轮高质量资料不足3条，拒绝更新，避免低质量内容覆盖现有资料。')

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    output = {
        'updated_at': now,
        'policy': '证据优先；权威公告/评级机构优先；正文抽取；营销与第五套人民币过滤；标题与正文双重相关性；URL与标题去重；质量门槛；分类后再发布。',
        'published_count': len(published),
        'source_count': len({x['source'] for x in published}),
        'source_status': source_status,
        'items': published,
    }
    (DATA / 'editorial.json').write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')

    realtime = {
        'updated_at': now,
        'mode': 'research-first-curation',
        'notice': '前台只展示经过筛选、编辑与证据分级的公开收藏研究资料。',
        'items': [
            {
                'id': x['id'], 'date': x['date'], 'title': x['title'], 'category': x['category'],
                'keywords': x['keywords'][:8], 'summary': x['summary'], 'analysis': x['analysis'],
                'source': x['source'], 'evidence_level': x['evidence_level'],
                'quality_score': x['quality_score'], 'source_url': x['source_url_internal']
            }
            for x in published[:12]
        ]
    }
    (DATA / 'realtime_ai.json').write_text(json.dumps(realtime, ensure_ascii=False, indent=2), encoding='utf-8')

    (DATA / 'editorial_status.json').write_text(json.dumps({'updated_at': now, 'sources': source_status, 'published_count': len(published), 'source_count': output['source_count']}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('high_quality_published=', len(published), 'sources=', output['source_count'])
    for s in source_status:
        print(s)


if __name__ == '__main__':
    collect_and_edit()
