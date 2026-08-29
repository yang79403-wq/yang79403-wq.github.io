from datetime import datetime, timezone
from pathlib import Path
import json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'
HEADERS={'User-Agent':'HongshengJicang/5.0 (+public-source-index; educational-use)'}
SOURCES=[
 {'name':'中国金币网','url':'https://www.chngc.net/common/homep','category':'纪念币与行业资讯'},
 {'name':'爱藏收藏新闻','url':'https://news.airmb.com/','category':'收藏行业资讯'}
]
# 只收集知识、新闻、发行、研究类公开信息；商业广告、交易导流、价格营销全部拒绝。
KEYWORDS=['钱币收藏','古钱币','银元','袁大头','机制币','纸币','人民币','纪念币','金银币','钱币版别','钱币鉴赏','钱币拍卖','钱币展会','钱币历史','钱币文化','钱币研究','泉州钱币','福建钱币']
# 第五套人民币一律不进入站内资讯，无论是否出现“买卖”字样。
FIFTH_RMB_TERMS=['第五套人民币','五套人民币','第五版人民币','五版人民币','第五套 人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币']
# 广告、出售、求购、价格导流、联系方式、招商等商业内容全部过滤。
AD_TERMS=['广告','推广','招商','代理','加盟','优惠','促销','购买','买入','买卖','出售','求购','收购','回收','寄卖','出手','转让','报价','价格表','今日价格','最新价格','多少钱','值多少钱','高价','低价','批发','零售','现货','库存','联系微信','加微信','微信号','扫码','二维码','电话咨询','客服电话','私聊','私信','公众号','小程序','直播带货','带货','店铺','商城','下单','订单','商品','卖家','买家','拍下','付款','招商加盟']

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def textnorm(s): return re.sub(r'\s+',' ',s or '').strip().lower()
def is_fifth_rmb(text):
    t=textnorm(text)
    return any(k.lower() in t for k in FIFTH_RMB_TERMS)
def is_ad(text):
    t=textnorm(text)
    return any(k.lower() in t for k in AD_TERMS)
def allowed_url(url):
    u=textnorm(url)
    return '.tw' not in u and 'taobao.' not in u and 'jd.com' not in u and 'shop' not in u
def matched_keywords(text): return [k for k in KEYWORDS if k in (text or '')]
def clean_title(title, context):
    if not title or len(title)<6 or len(title)>120: return False
    combined=f'{title} {context}'
    if is_fifth_rmb(combined) or is_ad(combined): return False
    return bool(matched_keywords(title))

def collect():
    records=[]; seen=set()
    for source in SOURCES:
        try:
            r=requests.get(source['url'],headers=HEADERS,timeout=25); r.raise_for_status()
            soup=BeautifulSoup(r.text,'html.parser')
            for a in soup.find_all('a',href=True):
                title=' '.join(a.get_text(' ',strip=True).split())
                href=urljoin(r.url,a['href'])
                context=' '.join(a.parent.get_text(' ',strip=True).split()) if a.parent else ''
                if href in seen or not allowed_url(href) or not clean_title(title,context): continue
                seen.add(href)
                m=re.search(r'20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}',context)
                date=(m.group(0).replace('年','-').replace('月','-').replace('日','') if m else datetime.now().strftime('%Y-%m-%d'))[:10]
                records.append({'id':f'news-{len(records)+1}-{abs(hash(href))}','date':date,'title':title,'summary':f'公开来源：{source["name"]}。仅保存标题、日期、分类、关键词和原始链接，供收藏研究者核验。','source':source['name'],'url':href,'category':source['category'],'keywords':matched_keywords(title)})
                if len(records)>=100: break
        except Exception as e:
            print('source failed:',source['name'],type(e).__name__)
    records.sort(key=lambda x:(x['date'],x['title']),reverse=True)
    # 二次总过滤，防止后续字段变化把广告或第五套人民币带入结果。
    records=[x for x in records if not is_fifth_rmb(x['title']) and not is_ad(x['title']) and allowed_url(x['url'])]
    (DATA/'news.json').write_text(json.dumps({'updated_at':now(),'policy':'严格过滤商业广告、买卖/收购/出售/求购及价格导流内容；第五套人民币相关内容一律不收集。仅保留公开知识、新闻、发行、历史与研究资讯索引。','items':records[:80]},ensure_ascii=False,indent=2),encoding='utf-8')
    (DATA/'source_status.json').write_text(json.dumps({'updated_at':now(),'policy':'商业广告与交易导流过滤；第五套人民币过滤；公开资料索引，不整篇镜像文章。','sources':[{'name':s['name'],'url':s['url'],'category':s['category']} for s in SOURCES]},ensure_ascii=False,indent=2),encoding='utf-8')
    print('news_records=',min(len(records),80))

if __name__=='__main__': collect()
