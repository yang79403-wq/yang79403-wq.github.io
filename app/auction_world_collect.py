from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib, json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; HongshengJicang-AuctionIndexer/1.1; +public-source-index)'}
SOURCES = [
 {'name': "Stack's Bowers", 'seeds': ['https://stacksbowers.com/', 'https://auctions.stacksbowers.com/'], 'category': '国际拍卖·中国钱币'},
 {'name': 'Spink', 'seeds': ['https://www.spink.com/auctions/index?location_id=1', 'https://www.spink.com/'], 'category': '国际拍卖·中国钱币'},
 {'name': 'MDC Monaco', 'seeds': ['https://mdc.mc/fr/ventes-aux-encheres-numismatiques-a-venir/', 'https://mdc.mc/fr/ventes-aux-encheres-numismatiques-passees/'], 'category': '国际拍卖·中国钱币'},
 {'name': 'Taisei Coins', 'seeds': ['https://www.taiseicoins.com/auction/', 'https://auctions.taiseicoins.com/'], 'category': '国际拍卖·中国钱币'},
 {'name': '泓盛拍卖 HOSANE', 'seeds': ['https://www.hosane.com/', 'https://www.hosane.com/auction/'], 'category': '中国拍卖·钱币与收藏'}
]
CN_TERMS = ['china','chinese','ching','qing','yuan shikai','yuan shi kai','sun yat-sen','sun yat sen','empire of china','republic of china','kiangnan','kiang nan','peiyang','peiyang province','kwang-tung','kwangtung','hupeh','hu-peh','fengtien','feng-tien','yunnan','szechuan','sichuan','kansu','kansu province','hunan','chekiang','tientsin','tianjin','dragon dollar','dollar','cash coin','tael','中国','中华民国','大清','光绪','宣统','袁世凯','孙中山','江南','北洋','广东','湖北','奉天','云南','四川','湖南','浙江','天津','龙洋','银元','铜元','机制币','古钱','钱币']
NOISE_TERMS = ['privacy','terms','contact','login','register','newsletter','cookie','buy now','sell directly','consign','gold investment','jewellery','招聘','广告','优惠','商城','库存','下单','购物']
DATE_RE = re.compile(r'(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})|([A-Za-z]+\s+\d{1,2},\s+20\d{2})')
LOT_RE = re.compile(r'\b(?:lot|LOT)\s*[#:№]?\s*(\d{1,5})\b')
PRICE_RE = re.compile(r'(?:€|EUR|£|GBP|\$|USD|¥|JPY)\s?[0-9][0-9,]*(?:\.\d+)?')

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def norm(s): return re.sub(r'\s+', ' ', (s or '').strip())
def fetch(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=25, allow_redirects=True); r.raise_for_status(); r.encoding = r.apparent_encoding or r.encoding
        return r.url, r.text
    except Exception: return '', ''
def relevant(text):
    t = norm(text).lower(); return any(k in t for k in CN_TERMS) and not all(k in t for k in NOISE_TERMS)
def parse_date(text):
    m = DATE_RE.search(text or '')
    if not m: return datetime.now().strftime('%Y-%m-%d')
    if m.group(1): return f'{m.group(1)}-{int(m.group(2)):02d}-{int(m.group(3)):02d}'
    try: return datetime.strptime(m.group(4), '%B %d, %Y').strftime('%Y-%m-%d')
    except Exception: return datetime.now().strftime('%Y-%m-%d')
def extract_lot(text):
    m = LOT_RE.search(text or ''); return m.group(1) if m else ''
def extract_price(text):
    m = PRICE_RE.search(text or ''); return m.group(0) if m else ''
def title_ok(title, context):
    title = norm(title); return 8 <= len(title) <= 180 and relevant(f'{title} {context}')
def crawl_source(source):
    queue=[(u,0) for u in source['seeds']]; seen=set(); rows=[]; scanned=0; cutoff=(datetime.now().date()-timedelta(days=365)).isoformat()
    while queue and len(rows)<160:
        url,depth=queue.pop(0)
        if url in seen: continue
        seen.add(url); final,html=fetch(url); scanned+=1
        if not html: continue
        root=urlparse(final); soup=BeautifulSoup(html,'html.parser'); page_text=norm(soup.get_text(' ',strip=True))
        if relevant(page_text[:8000]):
            heading=''
            for tag in soup.find_all(['h1','h2','h3'],limit=8):
                c=norm(tag.get_text(' ',strip=True))
                if c and len(c)>=8: heading=c; break
            if heading and title_ok(heading,page_text[:3000]): rows.append(make_row(source,final,heading,page_text[:2000],page_text))
        for a in soup.find_all('a',href=True):
            href=urljoin(final,a['href'])
            if href in seen: continue
            p=urlparse(href)
            if p.netloc!=root.netloc: continue
            label=norm(a.get_text(' ',strip=True)); parent=norm(a.parent.get_text(' ',strip=True)) if a.parent else ''; context=f'{label} {parent}'
            if not (relevant(context) or any(x in href.lower() for x in ('auction','lot','archive','china','results','realised','realized','pai-mai','拍卖','钱币'))): continue
            if depth<2 and len(queue)<140: queue.append((href,depth+1))
            if title_ok(label,context):
                rows.append(make_row(source,href,label,context[:800],page_text))
                if len(rows)>=160: break
    uniq={r['url']:r for r in rows}; rows=[r for r in uniq.values() if r['date']>=cutoff]; rows.sort(key=lambda x:(x['date'],x['title']),reverse=True)
    return rows[:120],scanned
def make_row(source,url,title,context,page_text):
    title=norm(title); lot=extract_lot(f'{title} {context}'); price=extract_price(f'{title} {context}')
    return {'id':'auction-'+hashlib.sha1(url.encode()).hexdigest()[:18],'date':parse_date(f'{context} {page_text[:1000]}'),'title':title,'summary':f'公开来源：{source["name"]}。系统仅提取与中国钱币/收藏相关的公开拍卖资讯标题、拍卖线索与原始链接，详细信息请回到来源页面核验。','source':source['name'],'url':url,'category':source['category'],'lot':lot,'public_price_hint':price,'content_type':'auction_information','keywords':[k for k in CN_TERMS if k.lower() in (title+' '+context).lower()][:12]}
def collect():
    DATA.mkdir(parents=True,exist_ok=True); all_rows=[]; status=[]
    for source in SOURCES:
        try:
            rows,scanned=crawl_source(source); all_rows.extend(rows); status.append({'name':source['name'],'records':len(rows),'pages_or_links_seen':scanned,'error':None})
        except Exception as e: status.append({'name':source['name'],'records':0,'pages_or_links_seen':0,'error':type(e).__name__})
    uniq={x['url']:x for x in all_rows}; rows=list(uniq.values()); rows.sort(key=lambda x:(x['date'],x['title']),reverse=True)
    payload={'updated_at':now(),'policy':'自动采集公开国际/中国拍卖页面中与中国钱币相关的资讯；不复制整篇正文；保留来源链接；不以公开报价替代真实成交；最终以原始来源为准。','items':rows[:250]}
    (DATA/'china_auction_news.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    (DATA/'china_auction_source_status.json').write_text(json.dumps({'updated_at':now(),'sources':status},ensure_ascii=False,indent=2),encoding='utf-8')
    print('china_auction_records=',len(rows))
    for s in status: print(s)
if __name__=='__main__': collect()
