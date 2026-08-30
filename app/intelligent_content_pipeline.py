from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, re, mimetypes
import requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; SECTIONS=DATA/'sections'; ASSETS=ROOT/'assets'/'collected'
ASSETS.mkdir(parents=True,exist_ok=True)
HEADERS={'User-Agent':'HongshengJicang-ContentBot/1.0 (+educational-use)'}
FIFTH=('第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币')

def norm(s): return re.sub(r'\s+',' ',str(s or '')).strip()
def blocked(s):
 t=norm(s); return any(x in t for x in FIFTH)
def safe_name(s): return re.sub(r'[^a-zA-Z0-9_-]+','_',s)[:48]
def svg_fallback(path,title,category):
 title=norm(title)[:22]; category=norm(category)[:14]
 svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="760" viewBox="0 0 1200 760"><defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#32150f"/><stop offset="1" stop-color="#8a2118"/></linearGradient></defs><rect width="1200" height="760" fill="#f5eddd"/><rect x="38" y="38" width="1124" height="684" rx="30" fill="url(#g)"/><circle cx="600" cy="330" r="190" fill="#c89a43" opacity=".96"/><circle cx="600" cy="330" r="145" fill="#e9c978"/><circle cx="600" cy="330" r="112" fill="#bd8d35"/><text x="600" y="350" text-anchor="middle" font-size="78" font-family="serif" fill="#fff4d2">洪盛集藏</text><text x="600" y="610" text-anchor="middle" font-size="34" font-family="sans-serif" fill="#f7dfad">{category} · 智能资料图</text><text x="600" y="665" text-anchor="middle" font-size="26" font-family="sans-serif" fill="#f7ead0">{title}</text></svg>'''
 path.write_text(svg,encoding='utf-8')

def collect_image(url,key,title,category):
 fallback=ASSETS/f'{key}.svg'
 if not url or blocked(title):
  svg_fallback(fallback,title,category); return '/assets/collected/'+fallback.name,'generated'
 try:
  r=requests.get(url,headers=HEADERS,timeout=18,stream=True); r.raise_for_status()
  ctype=(r.headers.get('content-type') or '').split(';')[0].lower()
  if not ctype.startswith('image/'):
   svg_fallback(fallback,title,category); return '/assets/collected/'+fallback.name,'generated'
  ext=mimetypes.guess_extension(ctype) or '.jpg'
  if ext in ('.jpe','.jpeg'): ext='.jpg'
  out=ASSETS/f'{key}{ext}'
  total=0
  with out.open('wb') as f:
   for chunk in r.iter_content(65536):
    if not chunk: continue
    total+=len(chunk)
    if total>2_000_000: raise ValueError('image-too-large')
    f.write(chunk)
  if total<3000: raise ValueError('image-too-small')
  return '/assets/collected/'+out.name,'source-image'
 except Exception:
  svg_fallback(fallback,title,category); return '/assets/collected/'+fallback.name,'generated'

def source_image(page_url):
 try:
  r=requests.get(page_url,headers=HEADERS,timeout=18); r.raise_for_status()
  soup=BeautifulSoup(r.text,'html.parser')
  for attrs in ({'property':'og:image'},{'name':'twitter:image'}):
   x=soup.find('meta',attrs=attrs)
   if x and x.get('content'): return x['content']
  for img in soup.find_all('img',src=True):
   src=img.get('src','')
   if src.startswith(('http://','https://')): return src
 except Exception: pass
 return ''

def make_analysis(item):
 c=item.get('content') or {}; title=norm(item.get('title')); cat=norm(item.get('category') or '收藏资料'); kws=item.get('keywords') or []
 focus='、'.join(kws[:6]) or '钱币形制、历史背景、收藏研究'
 overview=norm(c.get('内容摘要')) or f'本专题围绕“{title}”展开，重点整理{focus}。'
 if cat in ('银元研究','银元'): observe='优先观察图文布局、压力细节、边齿、磨损、包浆与整体状态，并与同版可靠图录进行对照。'
 elif cat in ('古钱币','钱币知识'): observe='优先观察钱文、轮廓、穿制、铸造痕迹、锈色与时代特征，再结合历史资料交叉判断。'
 elif cat in ('机制币研究','机制币'): observe='重点观察模具特征、压力、齿边、文字细节、坯饼与局部修整痕迹。'
 elif cat in ('纸币研究','纸币'): observe='重点观察版式、冠号、水印、印刷细节、纸张状态及保存痕迹。'
 elif cat in ('纪念币资讯','金银币资讯'): observe='重点核对发行背景、主题、材质、规格及公开发行资料，区分事实与市场观点。'
 elif '福建' in cat or '地域' in cat: observe='结合福建地域历史、流通背景、地方铸币与收藏文化进行交叉研究。'
 else: observe='从历史背景、钱币特征、版别差异和保存状态四个层面建立观察框架。'
 return {'智能导读':f'洪盛集藏智能编辑：{overview[:420]}','核心分析':f'本条资料的研究关键词为“{focus}”。阅读时先确认对象、时代和品类，再把可观察特征与可靠资料逐项对应，避免只凭单一特征下结论。','鉴赏观察':observe,'收藏提示':'公开资料存在来源差异，市场说法、图片状态和个体差异均可能影响判断。本页用于学习、研究与收藏交流参考，不替代专业鉴定、评级或交易结论。','图片说明':'图片优先采用公开页面可获取的图片并保存为站内资料图；无法稳定取得时使用洪盛集藏本地专题图，前台不跳转外部图片链接。'}

def main():
 try: raw=json.loads((DATA/'editorial.json').read_text(encoding='utf-8'))
 except Exception: raw={'items':[]}
 items=[x for x in raw.get('items',[]) if not blocked(json.dumps(x,ensure_ascii=False))]
 enriched=[]; image_count=0
 for x in items[:80]:
  title=norm(x.get('title')); key='img-'+hashlib.sha1((title+x.get('source_url_internal','')).encode()).hexdigest()[:16]
  img=source_image(x.get('source_url_internal',''))
  image,kind=collect_image(img,key,title,x.get('category','收藏资料'))
  if kind=='source-image': image_count+=1
  y=dict(x); y['image']=image; y['image_type']=kind; y['analysis']=make_analysis(x); y['display_mode']='internal-content'
  # 外部链接只保留在后台数据，前台模板不得渲染。
  enriched.append(y)
 (DATA/'intelligent_content.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'policy':'智能筛选、分类、摘要、分析与本地图片化；前台不显示外部原文链接。第五套人民币内容继续过滤。','count':len(enriched),'source_images':image_count,'items':enriched},ensure_ascii=False,indent=2),encoding='utf-8')
 byid={x['id']:x for x in enriched}
 for p in SECTIONS.glob('*.json'):
  try: rows=json.loads(p.read_text(encoding='utf-8'))
  except Exception: continue
  if not isinstance(rows,list): continue
  out=[]
  for r in rows:
   y=dict(r); src=byid.get(r.get('id'))
   if src:
    y['image']=src['image']; y['image_type']=src['image_type']; y['analysis']=src['analysis']; y['display_mode']='internal-content'
   elif 'image' not in y:
    key='local-'+hashlib.sha1((str(r.get('id'))+str(r.get('title'))).encode()).hexdigest()[:16]
    path=ASSETS/f'{key}.svg'; svg_fallback(path,r.get('title','专题资料'),r.get('category_title') or r.get('category') or '钱币收藏'); y['image']='/assets/collected/'+path.name; y['image_type']='generated'; y['analysis']=make_analysis(r); y['display_mode']='internal-content'
   out.append(y)
  p.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
 print('intelligent_content=',len(enriched),'source_images=',image_count)

if __name__=='__main__': main()
