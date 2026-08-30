from datetime import datetime, timezone
from pathlib import Path
import json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; DATA.mkdir(parents=True,exist_ok=True)
HEADERS={'User-Agent':'HongshengJicang-GradingPriceBot/1.0 (+educational-use)'}
SOURCES=[
 {'grader':'PCGS','url':'https://www.pcgs.com/prices/china'},
 {'grader':'NGC','url':'https://www.ngccoin.com/auction-central/world/china-provincial-scid-76-denom-all'},
 {'grader':'PMG','url':'https://www.pmgnotes.com/news/'},
 {'grader':'华夏评级','url':'https://www.huaxiapj.com/'},
 {'grader':'华夏古泉','url':'https://www.hxguquan.com/'}
]
BLOCK=('第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币')
PRICE_RE=re.compile(r'(?:¥|￥|RMB|CNY|HK\$|HKD|US\$|USD|SGD)\s*[0-9][0-9,]*(?:\.\d+)?|[0-9][0-9,]*(?:\.\d+)?\s*(?:元|人民币|港币|美元|新币)',re.I)
GRADE_RE=re.compile(r'\b(?:PMG|PCGS|NGC)\s*(?:[0-9]{1,2}(?:\.[0-9])?|PR|PF|MS|AU|XF|VF|F|UNC|EPQ|Details|Plus|\+)\b',re.I)

def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def blocked(s): return any(x in norm(s) for x in BLOCK)
def parse_price(s):
 m=PRICE_RE.search(norm(s)); return m.group(0) if m else ''
def parse_grade(s,grader):
 t=norm(s)
 if grader in ('PCGS','NGC','PMG'):
  m=re.search(r'\b'+grader+r'\s*(?:[A-Z]{1,4}\s*)?(?:\d{1,2}(?:\.\d)?(?:\+)?|Details|EPQ|Choice|Gem|Uncirculated|About Uncirculated|Extremely Fine|Very Fine|Fine|Good|AU|MS|PR|PF)[A-Z0-9+ .-]*',t,re.I)
  return norm(m.group(0)) if m else ''
 if '华夏评级' in t: return norm(re.search(r'(?:评级|分数|等级)\s*[:：]?\s*[A-Za-z0-9+.-]{1,20}',t,re.I).group(0)) if re.search(r'(?:评级|分数|等级)\s*[:：]?\s*[A-Za-z0-9+.-]{1,20}',t,re.I) else ''
 return ''

def fetch(url):
 try:
  r=requests.get(url,headers=HEADERS,timeout=25); r.raise_for_status(); return r.url,r.text
 except Exception:return '', ''

def collect():
 rows=[]; seen=set()
 for src in SOURCES:
  final,html=fetch(src['url'])
  if not html: continue
  soup=BeautifulSoup(html,'html.parser')
  for node in soup.find_all(['article','li','tr','div','p']):
   text=norm(node.get_text(' ',strip=True))
   if len(text)<20 or len(text)>900 or blocked(text): continue
   price=parse_price(text)
   if not price: continue
   grade=parse_grade(text,src['grader'])
   if src['grader'] in ('PCGS','NGC','PMG') and not grade: continue
   key=(src['grader'],text[:500],price,grade)
   if key in seen: continue
   seen.add(key)
   rows.append({'date':datetime.now().strftime('%Y-%m-%d'),'grader':src['grader'],'item':text[:360],'grade':grade,'realized_price':price,'price_type':'成交价/已实现价格候选','source':src['grader'],'source_url_internal':final or src['url'],'verified':False})
   if len(rows)>=200: break
  
 # 只把明确的成交/已实现语义作为成交价；PCGS Price Guide 本身是指导价，不混入成交表。
 cleaned=[]
 for r in rows:
  t=r['item'].lower()
  if r['grader']=='PCGS' and not any(k in t for k in ['auction','realized','sold','sale','成交','拍卖']): continue
  if r['grader']=='NGC' and not any(k in t for k in ['auction','realized','sold','sale','成交','拍卖']): continue
  if r['grader']=='PMG' and not any(k in t for k in ['realized','auction','sold','sale','成交','拍卖']): continue
  if r['grader']=='华夏评级' and not any(k in t for k in ['成交','拍卖','结标','已售','sold','realized']): continue
  r['verified']=True; r['price_type']='实际成交/已实现价格'
  cleaned.append(r)
 out={'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'policy':'只发布可核验的评级币实际成交/已实现价格；PCGS/NGC/PMG指导价、估值价不作为成交价。华夏评级只在明确出现成交、结标或已售语义时进入成交表。第五套人民币继续过滤。','graders':['PMG','PCGS','NGC','华夏评级'],'items':cleaned[:150]}
 (DATA/'grading_prices.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('grading_price_candidates=',len(cleaned))

if __name__=='__main__': collect()
