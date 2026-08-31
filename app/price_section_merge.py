from pathlib import Path
import json
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; PR=DATA/'prices'; SE=DATA/'sections'
CATS=['ancient','silver','machine','banknote','commemorative','gold']

def load(p,default):
    try:return json.loads(p.read_text(encoding='utf-8'))
    except:return default

def merge_file(path, incoming, record_type):
    existing=load(path,[]); rows=[]; seen=set()
    for r in incoming+existing:
        if not isinstance(r,dict): continue
        rid=r.get('id') or r.get('title')
        if rid in seen: continue
        seen.add(rid); y=dict(r); y['section']='market'; y['record_type']=record_type
        rows.append(y)
    rows.sort(key=lambda x:(x.get('date',''),x.get('title',x.get('item',''))),reverse=True)
    path.write_text(json.dumps(rows[:600],ensure_ascii=False,indent=2),encoding='utf-8')

for cat in CATS:
    prices=load(PR/f'{cat}.json',[])
    for r in prices:
        r['note']=f"成交价：¥{r.get('price_display','')}。{r.get('note','')}"
    merge_file(SE/f'market_{cat}.json',prices,'成交价格')

# 评级币成交必须同时进入对应行情板块，按评级公司保留字段。
grading=load(DATA/'grading_prices.json',{}).get('items',[])
for r in grading:
    text=' '.join(str(r.get(k,'')) for k in ('item','title','note'))
    if any(x in text for x in ('银元','袁大头','龙洋')): cat='silver'
    elif any(x in text for x in ('机制币','铜元','铜币')): cat='machine'
    elif any(x in text for x in ('纸币','钞票','冠号','水印')): cat='banknote'
    elif '纪念币' in text: cat='commemorative'
    elif any(x in text for x in ('金币','银币','金银币')): cat='gold'
    elif any(x in text for x in ('古钱','通宝','重宝','元宝','秦半两','五铢')): cat='ancient'
    else: continue
    y=dict(r); y['category']=cat; y['category_title']={'ancient':'古钱币','silver':'银元','machine':'机制币','banknote':'纸币','commemorative':'纪念币','gold':'金银币'}[cat]
    y['title']=r.get('item','评级币成交'); y['price_display']=r.get('realized_price',''); y['price_type']='实际成交/已实现价格'; y['note']=f"{r.get('grader','')} {r.get('grade','')} · 实际成交/已实现价格：{r.get('realized_price','')}"
    path=SE/f'market_{cat}.json'; merge_file(path,[y],'评级币成交价格')

(DATA/'price-section-status.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'rule':'每日实际成交记录与评级币实际成交记录直接归档到对应钱币品类行情板块；直接显示成交价，不计算均价，不跨品类复制。'},ensure_ascii=False,indent=2),encoding='utf-8')
print('price section merge complete; grading records=',len(grading))
