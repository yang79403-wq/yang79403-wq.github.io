from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import hashlib, json, re, requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; OUT=DATA/'prices'; OUT.mkdir(parents=True,exist_ok=True)
HEADERS={'User-Agent':'HongshengJicang-PriceBot/1.0 (+public-collection-data; educational-use)'}
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
PRICE_RE=re.compile(r'(?:成交价|成交|结标价|落槌价|已售|售出)[^￥¥\d]{0,18}[￥¥]?\s*([\d,]+(?:\.\d+)?)\s*(?:元)?|[￥¥]\s*([\d,]+(?:\.\d+)?)\s*元?')
DATE_RE=re.compile(r'20\d{2}[./-]\d{1,2}[./-]\d{1,2}|20\d{2}年\d{1,2}月\d{1,2}日')

def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def blocked(s): return any(k in norm(s) for k in BLOCK)
def classify(title):
 t=norm(title)
 if blocked(t): return None
 scores={k:sum(1 for x in vs if x in t) for k,vs in CATS.items()}; best=max(scores,key=scores.get)
 return best if scores[best] else None

def price_value(m):
 for g in m.groups():
  if g: return float(g.replace(',',''))
 return None

def parse_page(source):
 rows=[]
 try:
  r=requests.get(source['url'],headers=HEADERS,timeout=25); r.raise_for_status()
  soup=BeautifulSoup(r.text,'html.parser')
  # 以可见文本块为单位，只接受明确出现成交/结标/已售语义的记录，排除“当前价/预展价”。
  blocks=[]
  for node in soup.find_all(['article','li','tr','div']):
   txt=norm(node.get_text(' ',strip=True))
   if len(txt)<10 or len(txt)>700: continue
   if not re.search(r'成交价|结标价|落槌价|已售|售出',txt): continue
   if re.search(r'当前价|拍卖中|预展',txt) and not re.search(r'成交价|结标价|落槌价|已售|售出',txt): continue
   blocks.append(txt)
  seen=set()
  for txt in blocks:
   m=PRICE_RE.search(txt)
   if not m: continue
   price=price_value(m)
   if price is None or price<=0: continue
   # 去除过长前缀，寻找钱币标题。优先取价格前的最后一个较短片段。
   pre=txt[:m.start()].strip(' -|:：')
   title=pre[-120:].strip()
   title=re.sub(r'^(Image|图片)\s*','',title,flags=re.I)
   cat=classify(title)
   if not cat: continue
   d=DATE_RE.search(txt)
   date=d.group(0) if d else datetime.now().strftime('%Y-%m-%d')
   date=date.replace('年','-').replace('月','-').replace('日','').replace('/','-').replace('.','-')
   key=hashlib.sha1((source['name']+title+str(price)+date).encode()).hexdigest()[:16]
   if key in seen: continue
   seen.add(key)
   rows.append({'id':'deal-'+key,'date':date,'category':cat,'category_title':{'ancient':'古钱币','silver':'银元','machine':'机制币','banknote':'纸币','commemorative':'纪念币','gold':'金银币'}[cat],'title':title,'price':price,'price_display':f'{price:,.2f}'.rstrip('0').rstrip('.'),'currency':'CNY','source':source['name'],'source_kind':source['kind'],'status':'成交','source_url_internal':source['url'],'note':'公开成交记录整理；本站直接显示该笔成交价，不计算均价。'} )
 except Exception as e:
  return [], type(e).__name__
 return rows, None

def main():
 allrows=[]; status=[]
 for s in SOURCES:
  rows,err=parse_page(s); allrows.extend(rows); status.append({'source':s['name'],'url':s['url'],'records':len(rows),'error':err})
 # 去重并保留最近记录。价格表不做均价计算。
 seen=set(); clean=[]
 for r in sorted(allrows,key=lambda x:(x['date'],x['source'],x['title']),reverse=True):
  if r['id'] in seen: continue
  seen.add(r['id']); clean.append(r)
 for cat in CATS:
  arr=[r for r in clean if r['category']==cat]
  (OUT/f'{cat}.json').write_text(json.dumps(arr[:500],ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'all.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'policy':'仅保存可核验的成交/结标/已售记录；直接显示成交价，不计算均价；第五套人民币过滤；前台不显示外部链接。','items':clean[:2000]},ensure_ascii=False,indent=2),encoding='utf-8')
 (OUT/'status.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'sources':status},ensure_ascii=False,indent=2),encoding='utf-8')
 print('price_records=',len(clean))
 for s in status: print(s)
if __name__=='__main__': main()
