from pathlib import Path
import json,re
from datetime import datetime,timezone

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; CATS=DATA/'categories'; OUT=DATA/'sections'
OUT.mkdir(parents=True,exist_ok=True)

CONFIG=json.loads((DATA/'section-config.json').read_text(encoding='utf-8'))
CAT=json.loads((DATA/'category-config.json').read_text(encoding='utf-8')).get('taxonomy',{})
RULES={
'market':['拍卖','成交','市场','行情','价格','发行资讯','流通'],
'appraisal':['真伪','真假','鉴赏','品相','边齿','包浆','形制','特征'],
'research':['版别','版式','钱文','字体','书体','铸造','工艺','模具','历史','研究'],
'services':['评级','收藏咨询','评估','顾问','藏品档案','收藏服务'],
'collection':['藏品','收藏','研究笔记','专题']
}

def dump(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return []

def hit(section,r):
 s=json.dumps(r,ensure_ascii=False)
 return any(k in s for k in RULES[section])

for cat,cfg in CONFIG['categories'].items():
    rows=dump(CATS/f'{cat}.json')
    for section,subs in cfg['sections'].items():
        arr=[dict(r,section=section,category=cat,category_title=cfg['title']) for r in rows if hit(section,r)]
        seen=set(); clean=[]
        for r in arr:
            key=r.get('id') or r.get('title')
            if key in seen: continue
            seen.add(key); clean.append(r)
        clean.sort(key=lambda x:(x.get('date',''),x.get('title','')),reverse=True)
        (OUT/f'{section}_{cat}.json').write_text(json.dumps(clean[:100],ensure_ascii=False,indent=2),encoding='utf-8')

(DATA/'section-routing-status.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'rule':'功能板块与钱币品类双重隔离，每条资料先归品类，再归功能板块；不跨品类复制。'},ensure_ascii=False,indent=2),encoding='utf-8')
print('section routing complete')
