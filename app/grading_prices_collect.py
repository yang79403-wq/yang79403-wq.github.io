from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urljoin, urlparse
import json, re, requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; DATA.mkdir(parents=True,exist_ok=True)
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; HongshengJicang-GradingPriceBot/2.0; +public-verified-data)'}
SOURCES=[
 {'grader':'PCGS','url':'https://www.pcgs.com/auctionprices'},
 {'grader':'NGC','url':'https://www.ngccoin.com/auction-central/world/china-provincial-scid-76-denom-all'},
 {'grader':'PMG','url':'https://www.pmgnotes.com/news/'},
 {'grader':'华夏评级','url':'https://www.huaxiapj.com/'},
 {'grader':'华夏古泉','url':'https://www.hxguquan.com/'}
]
BLOCK=('第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币')
PRICE_RE=re.compile(r'(?:¥|￥|RMB|CNY|HK\$|HKD|US\$|USD|SGD)\s*[0-9][0-9,]*(?:\.\d+)?|[0-9][0-9,]*(?:\.\d+)?\s*(?:元|人民币|港币|美元|新币)',re.I)
GRADE_RE=re.compile(r'\b(?:PMG|PCGS|NGC)\s*(?:[A-Z]{1,8}\s*)?(?:\d{1,2}(?:\.\d)?(?:\+)?|PR|PF|MS|AU|XF|VF|F|UNC|EPQ|Details|Plus|Choice|Gem|Uncirculated|About Uncirculated|Extremely Fine|Very Fine|Fine|Good)[A-Z0-9+ .-]*',re.I)
DATE_RE=re.compile(r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}|20\d{2}年\d{1,2}月\d{1,2}日')

def norm(s):return re.sub(r'\s+',' ',str(s or '')).strip()
def blocked(s):return any(x in norm(s) for x in BLOCK)
def fetch(url):
 try:
  r=requests.get(url,headers=HEADERS,timeout=25,allow_redirects=True);r.raise_for_status();r.encoding=r.apparent_encoding or r.encoding;return r.url,r.text
 except Exception:return '', ''
def recent(date):
 if not date:return True
 try:return datetime.strptime(date,'%Y-%m-%d').date()>=(datetime.now().date()-timedelta(days=365*2))
 except Exception:return True
def norm_date(s):
 m=DATE_RE.search(s or '')
 if not m:return ''
 return m.group(0).replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-')[:10]
def parse_price(s):
 m=PRICE_RE.search(norm(s));return m.group(0) if m else ''
def parse_grade(s,grader):
 t=norm(s)
 if grader in ('PCGS','NGC','PMG'):
  m=GRADE_RE.search(t);return norm(m.group(0)) if m else ''
 if grader=='华夏评级':
  m=re.search(r'(?:华夏评级|评级|分数|等级)\s*[:：]?\s*[A-Za-z0-9+.-]{1,20}',t,re.I);return norm(m.group(0)) if m else ''
 return ''

def discover(src):
 final,html=fetch(src['url']);
 if not html:return []
 root=urlparse(final);queue=[(final,html,0)];seen={final};docs=[]
 while queue and len(docs)<50:
  url,body,depth=queue.pop(0);docs.append((url,body));soup=BeautifulSoup(body,'html.parser')
  if depth>=1:continue
  for a in soup.find_all('a',href=True):
   href=urljoin(url,a.get('href',''));label=norm(a.get_text(' ',strip=True));p=urlparse(href)
   if p.netloc!=root.netloc or href in seen:continue
   low=(href+' '+label).lower()
   if src['grader']=='PMG' and '/news/article/' not in href:continue
   if src['grader']=='NGC' and '/auction-central/world/china' not in href:continue
   if src['grader']=='PCGS' and 'auctionprices' not in low:continue
   if src['grader']=='华夏评级' and not any(k in low for k in ('成交','拍卖','评级','auction','detail','goods-detail')):continue
   seen.add(href);f,h=fetch(href)
   if h:queue.append((f,h,1))
 return docs

def collect():
 rows=[];status=[];seen=set()
 for src in SOURCES:
  docs=discover(src);count=0
  for url,html in docs:
   soup=BeautifulSoup(html,'html.parser');page=norm(soup.get_text(' ',strip=True))
   if blocked(page):continue
   if not re.search(r'(?:realized|realized:|price realized|sold|sale|成交|结标|中标|已售|拍卖)',page,re.I):continue
   blocks=[]
   for node in soup.find_all(['article','li','tr','p','div']):
    text=norm(node.get_text(' ',strip=True))
    if 20<=len(text)<=1000 and re.search(r'(?:realized|price realized|sold|成交|结标|中标|已售|拍卖)',text,re.I):blocks.append(text)
   if not blocks:blocks=[page[:1500]]
   for text in blocks:
    price=parse_price(text);grade=parse_grade(text,src['grader'])
    if not price or not grade:continue
    date=norm_date(text) or norm_date(page)
    if not recent(date):continue
    # PCGS/NGC/PMG 只接受明确的已实现/成交语义；华夏评级同样不接受指导价。
    if not re.search(r'(?:realized|price realized|sold|成交|结标|中标|已售)',text,re.I):continue
    item=norm(text[:360]);key=(src['grader'],item,price,grade,date)
    if key in seen:continue
    seen.add(key);count+=1
    rows.append({'date':date or datetime.now().strftime('%Y-%m-%d'),'grader':src['grader'],'item':item,'grade':grade,'realized_price':price,'price_type':'实际成交/已实现价格','source':src['grader'],'source_url_internal':url,'verified':True})
    if count>=100:break
  status.append({'grader':src['grader'],'pages_scanned':len(docs),'records':count,'error':None})
 out={'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'policy':'只发布可核验的评级币实际成交/已实现价格；PCGS Price Guide 指导价、NGC/PMG估值或预展价均不作为成交价；第五套人民币继续过滤。','graders':['PMG','PCGS','NGC','华夏评级'],'items':rows[:250]}
 (DATA/'grading_prices.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 (DATA/'grading_prices_status.json').write_text(json.dumps({'updated_at':out['updated_at'],'total_records':len(rows),'sources':status},ensure_ascii=False,indent=2),encoding='utf-8')
 print('grading_price_records=',len(rows))
 for s in status:print(s)
if __name__=='__main__':collect()
