from pathlib import Path
import json
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; PR=DATA/'prices'; SE=DATA/'sections'
CATS=['ancient','silver','machine','banknote','commemorative','gold']

def load(p,default):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return default

for cat in CATS:
    prices=load(PR/f'{cat}.json',[])
    existing=load(SE/f'market_{cat}.json',[])
    # 价格记录作为市场板块的一等内容，直接显示成交价，不计算均价。
    rows=[]; seen=set()
    for r in prices+existing:
        rid=r.get('id') or r.get('title')
        if rid in seen: continue
        seen.add(rid)
        if r in prices:
            r=dict(r); r['section']='market'; r['record_type']='成交价格'; r['note']=f"成交价：¥{r.get('price_display','')}。{r.get('note','')}"
        rows.append(r)
    rows.sort(key=lambda x:(x.get('date',''),x.get('record_type',''),x.get('title','')),reverse=True)
    (SE/f'market_{cat}.json').write_text(json.dumps(rows[:600],ensure_ascii=False,indent=2),encoding='utf-8')

(DATA/'price-section-status.json').write_text(json.dumps({'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'rule':'每日实际成交记录直接归档到对应钱币品类的行情板块；直接显示成交价，不计算均价，不跨品类复制。'},ensure_ascii=False,indent=2),encoding='utf-8')
print('price section merge complete')
