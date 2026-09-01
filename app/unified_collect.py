from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib, json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

ROOT=Path(__file__).resolve().parent.parent; DATA=ROOT/'data'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; HongshengJicang-ContentBot/2.0; +public-source-index)'}
SOURCES=[
 {'name':'中国金币网','url':'https://www.chngc.net/','category':'纪念币与行业资讯'},
 {'name':'爱藏收藏新闻','url':'https://news.airmb.com/','category':'收藏行业资讯'},
 {'name':'古泉园地','url':'https://www.chcoin.com/','category':'古钱币与机制币资讯'}
]
KEYWORDS=['钱币收藏','古钱币','古钱','银元','袁大头','机制币','铜元','纸币','纪念币','金银币','钱币版别','钱币鉴赏','钱币拍卖','钱币展会','钱币历史','钱币文化','钱币研究','泉州钱币','福建钱币']
FIFTH_RMB_TERMS=['第五套人民币','五套人民币','第五版人民币','五版人民币','第五套 人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币']
AD_TERMS=['广告','推广','招商','代理','加盟','优惠','促销','购买','买入','买卖','出售','求购','收购','回收','寄卖','出手','转让','报价','价格表','今日价格','最新价格','多少钱','值多少钱','高价','低价','批发','零售','现货','库存','联系微信','加微信','微信号','扫码','二维码','电话咨询','客服电话','私聊','私信','公众号','小程序','直播带货','带货','店铺','商城','下单','订单','商品','卖家','买家','拍下','付款','招商加盟']


def repair(s):
 if not isinstance(s,str): return s
 if not any(x in s for x in ('Ã','Â','æ','ç','å','é','è','ä','�')): return s
 try:
  fixed=s.encode('latin1').decode('utf-8'); marks=('Ã','Â','æ','ç','å','é','è','ä','�')
  return fixed if sum(fixed.count(x) for x in marks)<sum(s.count(x) for x in marks) else s
 except (UnicodeEncodeError,UnicodeDecodeError): return s

def repair_tree(v):
 if isinstance(v,dict): return {k:repair_tree(x) for k,x in v.items()}
 if isinstance(v,list): return [repair_tree(x) for x in v]
 return repair(v)

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def textnorm(s): return repair(re.sub(r'\s+',' ',s or '').strip().lower())
def is_fifth_rmb(text): return any(k.lower() in textnorm(text) for k in FIFTH_RMB_TERMS)
def is_ad(text): return any(k.lower() in textnorm(text) for k in AD_TERMS)
def allowed_url(url):
 u=textnorm(url); return '.tw' not in u and 'taobao.' not in u and 'jd.com' not in u and 'shop' not in u

def matched_keywords(text): return [k for k in KEYWORDS if k in (text or '')]
def clean_title(title, context):
 title=repair(title); combined=f'{title} {repair(context)}'
 return 6<=len(title)<=120 and not is_fifth_rmb(combined) and not is_ad(combined) and bool(matched_keywords(title))

def fetch(url):
 try:
  r=requests.get(url,headers=HEADERS,timeout=25,allow_redirects=True); r.raise_for_status(); r.encoding=r.apparent_encoding or r.encoding
  return r.url,r.text
 except Exception: return '', ''

def page_date(text):
 m=re.search(r'20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}',text)
 if not m: return datetime.now().strftime('%Y-%m-%d')
 return m.group(0).replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-')[:10]

def crawl_source(source):
 final,html=fetch(source['url'])
 if not html: return [],0
 root=urlparse(final); queue=[(final,html,0)]; seen={final}; records=[]
 while queue and len(records)<120:
  url,body,depth=queue.pop(0); soup=BeautifulSoup(body,'html.parser')
  for a in soup.find_all('a',href=True):
   title=repair(' '.join(a.get_text(' ',strip=True).split())); href=urljoin(url,a['href']); context=repair(' '.join(a.parent.get_text(' ',strip=True).split()) if a.parent else '')
   if href in seen or not allowed_url(href): continue
   p=urlparse(href)
   if p.netloc!=root.netloc: continue
   if not clean_title(title,context): continue
   seen.add(href)
   date=page_date(context)
   if depth<2 and len(queue)<80: queue.append((href,'',depth+1))
   records.append({'id':'news-'+hashlib.sha1(href.encode()).hexdigest()[:16],'date':date,'title':title,'summary':f'公开来源：{source["name"]}。采集后进入洪盛集藏自动筛选与编辑流程。','source':source['name'],'url':href,'category':source['category'],'keywords':matched_keywords(title)})
   if len(records)>=120: break
  # queue中的空body在这里抓取，避免一次性并发过多
  if queue and not queue[0][1]:
   u,_,d=queue.pop(0); f,h=fetch(u)
   if h: queue.insert(0,(f,h,d))
 records=repair_tree(records)
 cutoff=(datetime.now().date()-timedelta(days=180)).isoformat()
 records=[x for x in records if x['date']>=cutoff and not is_fifth_rmb(x['title']) and not is_ad(x['title']) and allowed_url(x['url'])]
 return records, len(seen)

def collect():
 records=[]; status=[]
 for source in SOURCES:
  try:
   rows,scanned=crawl_source(source); records.extend(rows); status.append({'name':source['name'],'records':len(rows),'pages_or_links_seen':scanned,'error':None})
  except Exception as e: status.append({'name':source['name'],'records':0,'pages_or_links_seen':0,'error':type(e).__name__})
 # URL 去重，优先最新资料。
 uniq={x['url']:x for x in records}; records=list(uniq.values()); records.sort(key=lambda x:(x['date'],x['title']),reverse=True)
 DATA.mkdir(parents=True,exist_ok=True)
 payload={'updated_at':now(),'policy':'自动采集公开收藏资讯，过滤商业广告、交易导流和第五套人民币；仅保留近180天候选资料；随后自动抓取正文、编辑、分类和图片化。','items':records[:120]}
 (DATA/'news.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
 (DATA/'source_status.json').write_text(json.dumps({'updated_at':now(),'sources':status},ensure_ascii=False,indent=2),encoding='utf-8')
 print('news_records=',len(records),'encoding=repair-enabled')
 for s in status: print(s)
if __name__=='__main__': collect()
