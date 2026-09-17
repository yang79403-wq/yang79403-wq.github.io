from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, mimetypes, re
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
SECTIONS = DATA / 'sections'
ASSETS = ROOT / 'assets' / 'collected'
ASSETS.mkdir(parents=True, exist_ok=True)
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; HongshengJicang-ContentBot/2.0; +educational-research)'}
FIFTH = ('第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币')

def norm(s):
    return re.sub(r'\s+', ' ', str(s or '')).strip()

def blocked(s):
    t = norm(s)
    return any(x in t for x in FIFTH)

def safe_name(s):
    return re.sub(r'[^a-zA-Z0-9_-]+', '_', str(s))[:48]

def svg_fallback(path, title, category):
    title = norm(title)[:22].replace('&', '与')
    category = norm(category)[:14].replace('&', '与')
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#32150f"/><stop offset="1" stop-color="#8a2118"/></linearGradient></defs><rect width="1200" height="760" fill="#f5eddd"/><rect x="38" y="38" width="1124" height="684" rx="30" fill="url(#g)"/><circle cx="600" cy="330" r="190" fill="#c89a43" opacity=".96"/><circle cx="600" cy="330" r="145" fill="#e9c978"/><circle cx="600" cy="330" r="112" fill="#bd8d35"/><text x="600" y="350" text-anchor="middle" font-size="78" font-family="serif" fill="#fff4d2">洪盛集藏</text><text x="600" y="610" text-anchor="middle" font-size="34" font-family="sans-serif" fill="#f7dfad">{category} · 研究资料图</text><text x="600" y="665" text-anchor="middle" font-size="26" font-family="sans-serif" fill="#f7ead0">{title}</text></svg>'''
    path.write_text(svg, encoding='utf-8')

def collect_image(url, key, title, category):
    fallback = ASSETS / f'{key}.svg'
    if not url or blocked(title):
        svg_fallback(fallback, title, category)
        return '/assets/collected/' + fallback.name, 'generated'
    try:
        r = requests.get(url, headers=HEADERS, timeout=18, stream=True)
        r.raise_for_status()
        ctype = (r.headers.get('content-type') or '').split(';')[0].lower()
        if not ctype.startswith('image/'):
            raise ValueError('not-image')
        ext = mimetypes.guess_extension(ctype) or '.jpg'
        if ext in ('.jpe', '.jpeg'):
            ext = '.jpg'
        out = ASSETS / f'{key}{ext}'
        total = 0
        with out.open('wb') as f:
            for chunk in r.iter_content(65536):
                if not chunk:
                    continue
                total += len(chunk)
                if total > 2_000_000:
                    raise ValueError('image-too-large')
                f.write(chunk)
        if total < 3000:
            raise ValueError('image-too-small')
        return '/assets/collected/' + out.name, 'source-image'
    except Exception:
        svg_fallback(fallback, title, category)
        return '/assets/collected/' + fallback.name, 'generated'

def source_image(page_url):
    if not page_url:
        return ''
    try:
        r = requests.get(page_url, headers=HEADERS, timeout=18)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        for attrs in ({'property': 'og:image'}, {'name': 'twitter:image'}):
            x = soup.find('meta', attrs=attrs)
            if x and x.get('content'):
                return x['content']
    except Exception:
        return ''
    return ''

def make_analysis(item):
    title = norm(item.get('title'))
    category = norm(item.get('category') or '收藏研究')
    summary = norm(item.get('summary'))
    existing = norm(item.get('analysis'))
    kws = item.get('keywords') or []
    focus = '、'.join(kws[:8]) or '钱币特征、历史背景、公开证据'
    if category == '银元研究':
        observe = '研究时优先核对年份、版别、钱文细节、边齿、压力、磨损与包浆，并记录具体资料来源。'
    elif category == '机制币研究':
        observe = '重点观察版式、模具特征、压力、齿边与局部细节，尽量与可靠图录或同版图片交叉比对。'
    elif category == '纸币研究':
        observe = '重点核对冠号、水印、版式、印刷工艺、纸张与保存状态，不把年份名称直接等同于版别。'
    elif category == '纪念币资讯':
        observe = '优先核对发行日期、材质、规格、发行量、设计与铸造单位，事实与市场观点分开记录。'
    elif category == '金银币资讯':
        observe = '优先核对材质、重量、成色、规格、发行量和主题，官方发行信息与市场交易信息分开。'
    elif category == '评级与市场资料':
        observe = '市场资料应记录机构、分数、成交时间和拍卖平台，不用单条记录推导整体行情。'
    else:
        observe = '先确认对象、时代和品类，再把公开来源中的可观察事实逐项对应，避免单一关键词直接下结论。'
    return {
        '智能导读': summary[:900] or f'洪盛集藏围绕“{title}”整理公开研究资料，重点涉及{focus}。',
        '核心分析': existing or f'研究关键词：{focus}。先区分事实、来源和分析，再进行交叉核验。',
        '鉴赏观察': observe,
        '收藏提示': '公开资料存在来源差异，市场信息具有时效性与个体差异。本页用于学习、研究与收藏交流参考，不替代专业鉴定、评级或交易结论。',
        '证据等级': item.get('evidence_level') or 'C',
        '来源': item.get('source') or '公开资料',
    }

def main():
    try:
        raw = json.loads((DATA / 'editorial.json').read_text(encoding='utf-8'))
    except Exception:
        raw = {'items': []}
    items = [x for x in raw.get('items', []) if isinstance(x, dict) and x.get('editorial_status') == 'published' and not blocked(json.dumps(x, ensure_ascii=False))]
    enriched = []
    image_count = 0
    for x in items[:40]:
        title = norm(x.get('title'))
        key = 'img-' + hashlib.sha1((title + x.get('source_url_internal', '')).encode()).hexdigest()[:16]
        img = source_image(x.get('source_url_internal', ''))
        image, kind = collect_image(img, key, title, x.get('category', '收藏资料'))
        if kind == 'source-image':
            image_count += 1
        y = dict(x)
        y['image'] = image
        y['image_type'] = kind
        y['analysis_card'] = make_analysis(x)
        y['display_mode'] = 'research-card'
        enriched.append(y)

    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    (DATA / 'intelligent_content.json').write_text(
        json.dumps({
            'updated_at': now,
            'policy': '证据优先、智能摘要、研究提示、来源与证据等级；第五套人民币过滤；前台优先展示研究资料。',
            'count': len(enriched),
            'source_images': image_count,
            'items': enriched,
        }, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )

    realtime = {
        'updated_at': now,
        'mode': 'research-first-curation',
        'notice': '只展示通过主题相关性、正文质量、来源优先级、去重和质量门槛的公开研究资料。',
        'items': [
            {
                'id': x.get('id'),
                'date': x.get('date'),
                'title': x.get('title'),
                'category': x.get('category'),
                'keywords': (x.get('keywords') or [])[:8],
                'summary': norm(x.get('summary')),
                'analysis': norm(x.get('analysis')),
                'source': x.get('source'),
                'evidence_level': x.get('evidence_level', 'C'),
                'quality_score': x.get('quality_score', 0),
                'source_url': x.get('source_url_internal', ''),
                'image': x.get('image', ''),
            }
            for x in enriched[:12]
        ],
    }
    (DATA / 'realtime_ai.json').write_text(json.dumps(realtime, ensure_ascii=False, indent=2), encoding='utf-8')

    # 同步已有板块资料中的图片和研究卡片，不改变板块本身的路由规则。
    for p in SECTIONS.glob('*.json'):
        try:
            rows = json.loads(p.read_text(encoding='utf-8'))
        except Exception:
            continue
        if not isinstance(rows, list):
            continue
        byid = {x.get('id'): x for x in enriched if x.get('id')}
        out = []
        for r in rows:
            y = dict(r)
            src = byid.get(r.get('id'))
            if src:
                y['image'] = src['image']
                y['image_type'] = src['image_type']
                y['analysis'] = src['analysis_card']
                y['evidence_level'] = src.get('evidence_level', 'C')
                y['display_mode'] = 'research-card'
            elif 'image' not in y:
                key = 'local-' + hashlib.sha1((str(r.get('id')) + str(r.get('title'))).encode()).hexdigest()[:16]
                path = ASSETS / f'{key}.svg'
                svg_fallback(path, r.get('title', '专题资料'), r.get('category_title') or r.get('category') or '钱币收藏')
                y['image'] = '/assets/collected/' + path.name
                y['image_type'] = 'generated'
                y['analysis'] = make_analysis(r)
                y['display_mode'] = 'research-card'
            out.append(y)
        p.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
    print('intelligent_content=', len(enriched), 'source_images=', image_count, 'realtime_ai=', min(12, len(enriched)))

if __name__ == '__main__':
    main()
