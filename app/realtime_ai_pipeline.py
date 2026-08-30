from datetime import datetime, timezone
from pathlib import Path
import hashlib, json, os, re, requests
from bs4 import BeautifulSoup

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'
HEADERS={'User-Agent':'HongshengJicang-RealtimeAI/1.0'}
FIFTH=['第五套人民币','五套人民币','第五版人民币','五版人民币','1999年版人民币','2005年版人民币','2015年版人民币','2019年版人民币','2020年版人民币','第五套纸币']
BLOCK=['广告','推广','招商','代理','加盟','优惠','促销','购买','买入','买卖','出售','求购','收购','回收','寄卖','转让','报价','价格表','今日价格','最新价格','多少钱','值多少钱','高价','低价','批发','零售','现货','库存','加微信','微信号','扫码','二维码','电话咨询','客服电话','私聊','私信','公众号','小程序','直播带货','店铺','商城','下单','订单','商品','卖家','买家','付款']
TOPICS=['古钱币','银元','袁大头','机制币','铜元','老纸币','纪念币','金银币','钱币版别','钱币鉴赏','钱币历史','钱币文化','钱币研究','钱币展会','钱币发行','泉州钱币','福建钱币']
SOURCES=[
 {'name':'中国金币网','url':'https://www.chngc.net/common/homep','category':'发行资讯'},
 {'name':'中国人民银行','url':'https://www.pbc.gov.cn/','category':'官方资讯'},
 {'name':'中国国家博物馆','url':'https://www.chnmuseum.cn/','category':'历史文化'}
]

def norm(s): return re.sub(r'\s+',' ',s or '').strip()
def blocked(s):
    t=norm(s).lower()
    return any(x.lower() in t for x in FIFTH+BLOCK)
def topics(s): return [x for x in TOPICS if x in s]
def fetch(url):
    try:
        r=requests.get(url,headers=HEADERS,timeout=20); r.raise_for_status()
        soup=BeautifulSoup(r.text,'html.parser')
        for x in soup(['script','style','nav','footer','header','form','aside']): x.decompose()
        out=[]
        for a in soup.find_all('a',href=True):
            title=norm(a.get_text(' ',strip=True)); parent=norm(a.parent.get_text(' ',strip=True)) if a.parent else ''
            if 8<=len(title)<=100 and not blocked(title+' '+parent) and topics(title):
                out.append((title,parent))
        return out[:40]
    except Exception as e:
        print('source failed',url,type(e).__name__); return []

def local_ai(title, context, category):
    kws=topics(title+' '+context)
    focus='、'.join(kws[:5]) or '钱币收藏与历史文化'
    return {
      '摘要':f'围绕{focus}整理公开资讯，重点提取与收藏知识、历史背景、发行信息和研究价值有关的内容。',
      '分析':f'本条资料归入“{category}”。建议重点关注资料中的历史事实、发行信息和可核验的研究线索，不将宣传性或市场营销表述作为结论。',
      '关键词':kws[:8]
    }

def main():
    rows=[]; seen=set()
    for s in SOURCES:
        for title,ctx in fetch(s['url']):
            key=hashlib.sha256(title.encode()).hexdigest()[:16]
            if key in seen: continue
            seen.add(key)
            ai=local_ai(title,ctx,s['category'])
            rows.append({'id':'rt-'+key,'date':datetime.now().strftime('%Y-%m-%d'),'title':title,'category':s['category'],'summary':ai['摘要'],'analysis':ai['分析'],'keywords':ai['关键词'],'source':s['name'],'ai_status':'filtered-edited','published_at':datetime.now(timezone.utc).isoformat(timespec='seconds')})
            if len(rows)>=30: break
        if len(rows)>=30: break
    rows.sort(key=lambda x:x['title'])
    DATA.mkdir(exist_ok=True)
    payload={'updated_at':datetime.now(timezone.utc).isoformat(timespec='seconds'),'mode':'realtime-ai-filter-edit','notice':'网站前台只显示经过筛选与编辑的内容，不显示原文跳转链接。商业广告、交易导流和第五套人民币相关内容一律拒绝。','items':rows[:30]}
    (DATA/'realtime_ai.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print('realtime_ai=',len(rows))

if __name__=='__main__': main()
