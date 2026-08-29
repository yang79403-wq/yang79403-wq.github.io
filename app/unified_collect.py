from datetime import datetime, timezone
from pathlib import Path
import json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'
HEADERS={'User-Agent':'HongshengJicang/4.0 (+public-source-index; educational-use)'}
SOURCES=[
 {'name':'中国金币网','url':'https://www.chngc.net/common/homep','category':'纪念币与行业资讯'},
 {'name':'爱藏收藏新闻','url':'https://news.airmb.com/','category':'收藏行业资讯'}]
KEYWORDS=['钱币收藏','古钱币','银元','袁大头','机制币','纸币','人民币','纪念币','金银币','钱币版别','钱币鉴赏','钱币拍卖','钱币展会','泉州钱币','福建钱币']

def now(): return datetime.now(timezone.utc).isoformat(timespec='seconds')
def allowed(url): return '.tw' not in (url or '').lower()
def match(text): return [k for k in KEYWORDS if k in (text or '')]

def collect():
 records=[]; seen=set()
 for source in SOURCES:
  try:
   r=requests.get(source['url'],headers=HEADERS,timeout=25); r.raise_for_status()
   soup=BeautifulSoup(r.text,'html.parser')
   for a in soup.find_all('a',href=True):
    title=' '.join(a.get_text(' ',strip=True).split()); href=urljoin(r.url,a['href'])
    if not title or len(title)<6 or len(title)>120 or not allowed(href) or href in seen or not match(title): continue
    seen.add(href); text=' '.join(a.parent.get_text(' ',strip=True).split()) if a.parent else ''
    m=re.search(r'20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}',text)
    date=(m.group(0).replace('年','-').replace('月','-').replace('日','') if m else datetime.now().strftime('%Y-%m-%d'))[:10]
    records.append({'id':f'news-{len(records)+1}-{abs(hash(href))}','date':date,'title':title,'summary':f'公开来源：{source["name"]}。本站保存标题、日期、分类、关键词和原始链接，供收藏研究者继续核验。','source':source['name'],'url':href,'category':source['category'],'keywords':match(title)})
    if len(records)>=100: break
  except Exception as e: print('source failed:',source['name'],type(e).__name__)
 records.sort(key=lambda x:(x['date'],x['title']),reverse=True)
 (DATA/'news.json').write_text(json.dumps({'updated_at':now(),'policy':'保存公开来源标题、日期、摘要、分类、关键词和原始链接；不整篇镜像受版权保护文章。','items':records[:80]},ensure_ascii=False,indent=2),encoding='utf-8')
 (DATA/'source_status.json').write_text(json.dumps({'updated_at':now(),'sources':[{'name':s['name'],'url':s['url'],'category':s['category']} for s in SOURCES]},ensure_ascii=False,indent=2),encoding='utf-8')
 print('news_records=',min(len(records),80))

if __name__=='__main__': collect()
