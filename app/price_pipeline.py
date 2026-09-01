from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
import hashlib, json, re, requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; OUT=DATA/'prices'; OUT.mkdir(parents=True,exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; HongshengJicang-PriceBot/2.0; +public-collection-data)'}
SOURCES=[
 {'name':'华夏古泉','url':'https://www.hxguquan.com/','kind':'auction'},
 {'name':'古泉园地','url':'https://www.chcoin.com/','kind':'auction'},
 {'name':'钱币天堂','url':'https://www.yy11.com/','kind':'auction'},
 {'name':'一尘网','url':'http://www.xx007.com/','kind':'market'},
 {'name':'钱币价格查','url':'https://www.qianbicha.com/','kind':'aggregator'}
]
CATS={
 'ancient':['古钱币','先秦','秦','汉','唐','宋','元','明','清','通宝','重宝','元宝','布币','刀币','花钱'],
 'silver':['银元','袁大头','孙小头','船洋','龙洋','北洋龙','大清银币','光绪元宝','鹰洋','坐洋','孙像'],
 'machine':['机制币','铜元','铜币','龙版','宣统三年','大清铜币','光绪元宝机制','样币'],
 'banknote':['纸币','钞','人民币','民国纸币','解放区纸币','连体钞','纪念钞'],
 'commemorative':['纪念币','生肖币','流通纪念币','贺岁币','纪念钞'],
 'gold':['金银币','金币','银币','熊猫金银币','生肖金银币','金锭','银锭']
}
BLOCK=['第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币']
PRICE_RE=re.compile(r'(?:成交价|成交|结标价|落槌价|已售|售出|中标|最终价|落槌)[^￥¥\d]{0,24}[￥¥]?\s*([\d,]+(?:\.\d+)?)\s*(?:元)?|[￥¥]\s*([\d,]+(?:\.\d+)?)\s*元?',re.I)
DATE_RE=re.compile(r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}|20\d{2}年\d{1,2}月\d{1,2}日')
LINK_HINTS=('goods-detail','goods-list','detail','exhibit','auction','pai','chengjiao','history','成交','结标','中标','拍卖')


def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def blocked(s): return any(k in norm(s) for k in BLOCK)
def classify(title):
 t=norm(title)
 if blocked(t): return None
 scores={k:sum(1 for x in vs if x in t) for k,vs in CATS.items()}
 best=max(scores,key=scores.get)
 return best if scores[best] else None

def price_value(m):
 for g in m.groups():
  if g: return float(g.replace(',',''))
 return None

def normalize_date(s):
 s=norm(s).replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-')
 m=re.search(r'(20\d{2}-\d{1,2}-\d{1,2})',s)
 return m.group(1) if m else ''

def recent_enough(date_text):
 d=normalize_date(date_text)
 if not d: return True
 try:
  return datetime.strptime(d,'%Y-%m-%d').date() >= (datetime.now().date()-timedelta(days=365))
 except Exception:
  return True

def fetch(url):
 try:
  r=requests.get(url,headers=HEADERS,timeout=25,allow_redirects=True); r.raise_for_status()
  r.encoding=r.apparent_encoding or r.encoding
  return r.url,r.text
 except Exception:
  return '', ''

def discover_pages(source):
 root=urlparse(source['url'])
 final,html=fetch(source['url'])
 pages=[]
 if html: pages.append((final,html))
 if not html: return pages
 soup=BeautifulSoup(html,'html.parser')
 links=[]
 for a in soup.find_all('a',href=True):
  href=urljoin(final,a.get('href',''))
  p=urlparse(href)
  label=norm(a.get_text(' ',strip=True))
  if p.netloc!=root.netloc: continue
  if not any(h in (href.lower()+' '+label.lower()) for h in LINK_HINTS): continue
  if href in {x[0] for x in pages} or href in links: continue
  links.append(href)
 for href in links[:45]:
  f,h=fetch(href)
  if h: pages.append((f,h))
 return pages

def parse_document(source,url,html):
 rows=[]
 soup=BeautifulSoup(html,'html.parser')
 # 只处理明确有成交/结标/中标语义的页面文本，绝不把起拍价、当前价当成交价。
 page_text=norm(soup.get_text(' ',strip=True))
 if not re.search(r'成交价|结标价|落槌价|已售|售出|中标|最终价|落槌',page_text,re.I): return []
 title=''
 h=soup.find(['h1','h2'])
 if h: title=norm(h.get_text(' ',strip=True))
 if not title and soup.title: title=norm(soup.title.get_text(' ',strip=True))
 blocks=[]
 for node in soup.find_all(['article','li','tr','p','div']):
  txt=norm(node.get_text(' ',strip=True))
  if len(txt)<12 or len(txt)>900: continue
  if re.search(r'成交价|结标价|落槌价|已售|售出|中标|最终价|落槌',txt,re.I): blocks.append(txt)
 seen=set()
 for txt in blocks:
  m=PRICE_RE.search(txt)
  if not m: continue
  price=price_value(m)
  if price is None or price<=0: continue
  # 排除明显的当前价、起拍价、估价等非成交数字。
  if re.search(r'起拍价|当前价格|当前价|预展|估价|参考价',txt,re.I) and not re.search(r'成交价|结标价|落槌价|已售|售出|中标|最终价|落槌',txt,re.I): continue
  pre=txt[:m.start()].strip(' -|:：')
  candidate=norm(pre[-160:])
  candidate=re.sub(r'^(Image|图片)\s*','',candidate,flags=re.I)
  # 页面标题通常比价格前的导航碎片更可靠。
  coin_title=title if classify(title) else candidate
  cat=classify(coin_title)
  if not cat: cat=classify(candidate)
  if not cat: continue
  date_match=DATE_RE.search(txt) or DATE_RE.search(page_text)
  date=normalize_date(date_match.group(0) if date_match else '') or datetime.now().strftime('%Y-%m-%d')
  if not recent_enough(date): continue
  key=hashlib.sha1((source['name']+url+coin_title+str(price)+date).encode()).hexdigest()[:16]
  if key in seen: continue
  seen.add(key)
  rows.append({'id':'deal-'+key,'date':date,'category':cat,'category_title':{'ancient':'古钱币','silver':'银元','machine':'机制币','banknote':'纸币','commemorative':'纪念币','gold':'金银币'}[cat],'title':coin_title[:180],'price':price,'price_display':f'{price:,.2f}'.rstrip('0').rstrip('.'),'currency':'CNY','source':source['name'],'source_kind':source['kind'],'status':'成交','source_url_internal':url,'note':'公开成交记录整理；本站直接显示该笔成交价，不计算均价。'})
 return rows

def main():
 allrows=[]; status=[]
 for source in SOURCES:
  source_rows=[]; pages=0; err=None
  try:
   docs=discover_pages(source); pages=len(docs)
   for url,html in docs: source_rows.extend(parse_document(source,url,html))
  except Exception as e: err=type(e).__name__
  # 同一来源内去重
  uniq={r['id']:r for r in source_rows}
  source_rows=list(uniq.values())
  allrows.extend(source_rows)
  status.append({'source':source['name'],'pages_scanned':pages,'records':len(source_rows),'error':err})
 seen=set(); clean=[]
 for r in sorted(allrows,key=lambda x:(x['date'],x['source'],x['title']),reverse=True):
  if r['id'] in seen: continue
  seen.add(r['id']); clean.append(r)
 for cat in CATS:
  arr=[r for r in clean if r['category']==cat]
  (OUT/f'{cat}.json').write_text(json.dumps(arr[:500],ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'all.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'policy':'仅保存可核验的成交/结标/已售/中标记录；直接显示成交价，不计算均价；第五套人民币过滤；前台不显示外部链接。','items':clean[:2000]},ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'status.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'total_records':len(clean),'sources':status},ensure_ascii=False,indent=2),encoding='utf-8')
 print('price_records=',len(clean))
 for s in status: print(s)
if __name__=='__main__': main()
