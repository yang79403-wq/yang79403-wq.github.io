from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, re, requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
HEADERS = {'User-Agent': 'HongshengJicang-EditorialBot/1.2'}
FIFTH = ('第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币')
AD = ('广告','推广','招商','代理','加盟','优惠','促销','购买','买入','买卖','出售','求购','收购','回收','寄卖','出手','转让','报价','价格表','今日价格','最新价格','多少钱','值多少钱','高价','低价','批发','零售','现货','库存','加微信','微信号','扫码','二维码','电话咨询','客服电话','私聊','私信','公众号','小程序','直播带货','带货','店铺','商城','下单','订单','商品','卖家','买家','付款')
KEYWORDS = ('古钱币','银元','袁大头','机制币','铜元','纸币','人民币','纪念币','金银币','钱币版别','钱币鉴赏','钱币历史','钱币文化','钱币研究','钱币拍卖','钱币展会','泉州钱币','福建钱币')

def norm(s): return re.sub(r'\s+', ' ', s or '').strip()
def repair_mojibake(s):
    """Repair common UTF-8 decoded-as-Latin1/CP1252 Chinese mojibake without touching normal Chinese."""
    if not isinstance(s, str) or not s: return s
    markers=('Ã','Â','æ','ç','å','é','è','ä','ö','ð','ñ','â','ï','¤','�')
    if not any(m in s for m in markers): return s
    try:
        fixed=s.encode('latin1').decode('utf-8')
        bad=sum(s.count(m) for m in markers); good=sum(fixed.count(m) for m in markers)
        return fixed if good < bad else s
    except (UnicodeEncodeError,UnicodeDecodeError):
        return s

def repair_tree(v):
    if isinstance(v, dict): return {k: repair_tree(val) for k,val in v.items()}
    if isinstance(v, list): return [repair_tree(x) for x in v]
    return repair_mojibake(v)

def blocked(text):
    t = norm(text).lower()
    return any(x.lower() in t for x in FIFTH) or any(x.lower() in t for x in AD)
def keywords(text): return [k for k in KEYWORDS if k in text]
def category(text, fallback):
    rules = [('古钱币','钱币知识'),('银元','银元研究'),('袁大头','银元研究'),('机制币','机制币研究'),('铜元','机制币研究'),('纸币','纸币研究'),('人民币','纸币研究'),('纪念币','纪念币资讯'),('金银币','金银币资讯'),('版别','版别研究'),('鉴赏','鉴赏研究'),('福建','地域收藏'),('泉州','地域收藏')]
    for k, c in rules:
        if k in text: return c
    return fallback

def fetch_article(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20); r.raise_for_status()
        enc=r.apparent_encoding or r.encoding
        if enc: r.encoding=enc
        soup = BeautifulSoup(r.text, 'html.parser')
        for x in soup(['script','style','nav','footer','header','form','aside']): x.decompose()
        parts = [norm(repair_mojibake(x.get_text(' ', strip=True))) for x in soup.find_all(['h1','h2','p','li'])]
        parts = [x for x in parts if 20 <= len(x) <= 900 and not blocked(x)]
        return norm(' '.join(parts[:18]))[:6500]
    except Exception:
        return ''

def edit_title(title):
    title = repair_mojibake(title)
    title = re.sub(r'[!！?？]+', '', norm(title)); title = re.sub(r'^(震撼|重磅|速看|注意)[:： ]*', '', title)
    if len(title) > 54: title = title[:54].rstrip('，。,:：') + '｜收藏资料整理'
    return title

def edit_body(title, raw, cat, kws):
    sentences = re.split(r'(?<=[。！？])\s*', repair_mojibake(raw))
    useful = [norm(s) for s in sentences if len(norm(s)) >= 25 and not blocked(s)][:3]
    focus_text = '、'.join(kws[:4]) or '钱币收藏相关内容'
    overview = ' '.join(useful)[:520] if useful else f'本条资料围绕“{title}”展开，重点涉及{focus_text}。洪盛集藏按公开资料重新整理，便于收藏者从历史背景、钱币特征与研究线索等角度阅读。'
    focus = '、'.join(kws[:6]) or '钱币收藏、历史资料、鉴赏研究'
    return {'导读': f'这是一条{cat}资料。洪盛集藏对公开信息进行筛选、压缩和重新编排，仅保留与收藏研究直接相关的内容。','内容摘要': overview,'研究重点': f'关键词：{focus}。阅读时建议区分历史事实、作者观点和未经证实的市场说法，不把宣传性表述当作结论。','编辑说明': '本文为洪盛集藏资料整理稿，不转载原文全文，不提供买卖导流信息。'}

def collect_and_edit():
    raw = repair_tree(json.loads((DATA / 'news.json').read_text(encoding='utf-8')))
    candidates = raw.get('items', []) if isinstance(raw, dict) else raw
    published, rejected = [], 0; seen = set()
    for item in candidates[:100]:
        title, url = norm(item.get('title')), item.get('url', '')
        if not title or not url or blocked(title): rejected += 1; continue
        text = fetch_article(url); combined = f'{title} {text}'
        if blocked(combined) or len(text) < 80: rejected += 1; continue
        kws = keywords(combined)
        if not kws: rejected += 1; continue
        key = hashlib.sha256((title + url).encode('utf-8')).hexdigest()[:16]
        if key in seen: continue
        seen.add(key); cat = category(combined, item.get('category', '收藏资讯'))
        published.append({'id':'hz-'+key,'date':item.get('date') or datetime.now().strftime('%Y-%m-%d'),'title':edit_title(title),'category':cat,'keywords':kws[:10],'content':edit_body(title,text,cat,kws),'source':repair_mojibake(item.get('source','公开资料')),'source_url_internal':url,'editorial_status':'published','editorial_method':'filter-score-edit'})
        if len(published) >= 60: break
    published.sort(key=lambda x:(x['date'],x['title']), reverse=True); DATA.mkdir(parents=True, exist_ok=True)
    output={'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'policy':'后台规则：过滤商业广告、交易导流和第五套人民币；前台不显示后台规则。','published_count':len(published),'rejected_count':rejected,'items':published}
    (DATA / 'editorial.json').write_text(json.dumps(repair_tree(output),ensure_ascii=False,indent=2),encoding='utf-8')
    print('published=',len(published),'rejected=',rejected,'encoding=repair-enabled')

if __name__ == '__main__': collect_and_edit()
