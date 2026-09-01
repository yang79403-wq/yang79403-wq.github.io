from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, re, requests
from bs4 import BeautifulSoup
ROOT=Path(__file__).resolve().parent.parent; DATA=ROOT/'data'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; HongshengJicang-EditorialBot/2.1)'}
FIFTH=('第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币')
AD=('广告','推广','招商','代理','加盟','优惠','促销','购买','买入','买卖','出售','求购','收购','回收','寄卖','出手','转让','报价','价格表','今日价格','最新价格','多少钱','值多少钱','高价','低价','批发','零售','现货','库存','加微信','微信号','扫码','二维码','电话咨询','客服电话','私聊','私信','公众号','小程序','直播带货','带货','店铺','商城','下单','订单','商品','卖家','买家','付款')
KEYWORDS=('古钱币','古钱','秦半两','五铢','开元通宝','银元','袁大头','龙洋','机制币','铜元','纸币','冠号','水印','纪念币','金银币','金币','银币','钱币版别','钱币鉴赏','钱币历史','钱币文化','钱币研究','钱币拍卖','钱币展会','泉州钱币','福建钱币')
def norm(s):return re.sub(r'\s+',' ',s or '').strip()
def repair(s):
 if not isinstance(s,str) or not s:return s
 marks=('Ã','Â','æ','ç','å','é','è','ä','ö','ð','ñ','â','ï','¤','�')
 if not any(m in s for m in marks):return s
 try:
  fixed=s.encode('latin1').decode('utf-8');return fixed if sum(fixed.count(m) for m in marks)<sum(s.count(m) for m in marks) else s
 except (UnicodeEncodeError,UnicodeDecodeError):return s
def blocked(text):
 t=norm(text).lower();return any(x.lower() in t for x in FIFTH) or any(x.lower() in t for x in AD)
def keywords(text):return [k for k in KEYWORDS if k in text]
def category(text,fallback):
 t=norm(text);rules=[('福建钱币','地域收藏'),('泉州钱币','地域收藏'),('纸币','纸币研究'),('冠号','纸币研究'),('水印','纸币研究'),('人民币','纸币研究'),('银元','银元研究'),('袁大头','银元研究'),('龙洋','银元研究'),('机制币','机制币研究'),('铜元','机制币研究'),('纪念币','纪念币资讯'),('金银币','金银币资讯'),('金币','金银币资讯'),('银币','金银币资讯'),('版别','版别研究'),('鉴赏','鉴赏研究'),('古钱币','钱币知识'),('古钱','钱币知识'),('秦半两','钱币知识'),('五铢','钱币知识'),('开元通宝','钱币知识')]
 for k,c in rules:
  if k in t:return c
 return fallback
def fetch_article(url):
 try:
  r=requests.get(url,headers=HEADERS,timeout=8);r.raise_for_status();r.encoding=r.apparent_encoding or r.encoding;soup=BeautifulSoup(r.text,'html.parser')
  for x in soup(['script','style','nav','footer','header','form','aside']):x.decompose()
  parts=[norm(repair(x.get_text(' ',strip=True))) for x in soup.find_all(['h1','h2','h3','p','li'])]
  parts=[x for x in parts if 20<=len(x)<=900 and not blocked(x)]
  return norm(' '.join(parts[:20]))[:6500]
 except Exception:return ''
def edit_title(title):
 title=repair(title);title=re.sub(r'[!！?？]+','',norm(title));title=re.sub(r'^(震撼|重磅|速看|注意)[:： ]*','',title);return title[:58].rstrip('，。,:：')
def edit_body(title,raw,cat,kws):
 sentences=re.split(r'(?<=[。！？])\s*',repair(raw));useful=[norm(s) for s in sentences if len(norm(s))>=25 and not blocked(s)][:5];focus='、'.join(kws[:6]) or '钱币收藏、历史资料、鉴赏研究';overview=' '.join(useful)[:720] if useful else f'本条资料围绕“{title}”展开，重点涉及{focus}。洪盛集藏按公开资料重新整理，便于收藏者从历史背景、钱币特征与研究线索等角度阅读。'
 observe={'银元研究':'重点观察钱文、图案、边齿、压力细节、磨损和包浆，并与可靠图录或同版实物对照。','机制币研究':'重点观察版式、铸造或打制工艺、边齿和细节特征，避免单一特征下结论。','纸币研究':'重点核对版式、冠号、水印、印刷工艺、纸张状态和保存痕迹。','钱币知识':'从时代、钱文、形制、版式、工艺和历史背景建立交叉验证。','版别研究':'结合钱文、版式、细节、工艺和可靠图录进行多维比对。','地域收藏':'结合福建及泉州等地域历史、流通背景、地方铸币与收藏文化研究。'}.get(cat,'重点核对发行背景、规格材质、图案设计、历史资料和公开信息来源。')
 return {'智能导读':overview,'核心分析':f'关键词：{focus}。先确认对象、时代和品类，再将可观察特征与可靠资料逐项对应。','鉴赏观察':observe,'收藏提示':'公开资料存在来源差异，本页用于学习、研究与收藏交流参考。','编辑方式':'自动采集 → 正文抽取 → 广告与第五套人民币过滤 → 品类分类 → 智能摘要。'}
def collect_and_edit():
 try:raw=json.loads((DATA/'news.json').read_text(encoding='utf-8'))
 except Exception:raw={'items':[]}
 candidates=raw.get('items',[]) if isinstance(raw,dict) else raw;published=[];rejected=0;seen=set()
 for item in candidates[:30]:
  title,url=norm(item.get('title')),item.get('url','')
  if not title or not url or blocked(title):rejected+=1;continue
  text=fetch_article(url);combined=f'{title} {text}'
  if blocked(combined) or len(text)<120:rejected+=1;continue
  kws=keywords(combined)
  if not kws:rejected+=1;continue
  key=hashlib.sha256((title+url).encode()).hexdigest()[:16]
  if key in seen:continue
  seen.add(key);cat=category(combined,item.get('category','收藏资讯'));published.append({'id':'hz-'+key,'date':item.get('date') or datetime.now().strftime('%Y-%m-%d'),'title':edit_title(title),'category':cat,'keywords':kws[:10],'content':edit_body(title,text,cat,kws),'source':repair(item.get('source','公开资料')),'source_url_internal':url,'editorial_status':'published','editorial_method':'auto-collect-filter-edit'})
  if len(published)>=20:break
 published.sort(key=lambda x:(x['date'],x['title']),reverse=True);output={'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'policy':'自动采集、正文抽取、广告过滤、第五套人民币过滤、品类分类、智能摘要与研究提示；前台不显示外部原文链接。','published_count':len(published),'rejected_count':rejected,'items':published};(DATA/'editorial.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf-8');print('published=',len(published),'rejected=',rejected)
if __name__=='__main__':collect_and_edit()
