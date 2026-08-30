from pathlib import Path
import json, re

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'; SRC=DATA/'content'; OUT=DATA/'categories'

TAXONOMY={
'ancient':{'title':'古钱币','intro':'只收录古钱币相关历史、钱文、形制、铸造、版别与鉴赏资料。','subs':['朝代与时代','钱文与书体','形制与穿郭','铸造工艺','版别研究','真伪鉴赏','品相保存','历史文化']},
'silver':{'title':'银元','intro':'只收录银元及近代银币相关品种、版别、压力、边齿、包浆、真伪与品相资料。','subs':['银元品种','版别研究','字体与图案','压力与细节','边齿与包浆','真伪鉴赏','品相与评级','收藏研究']},
'machine':{'title':'机制币','intro':'只收录机制币相关铜元、机制银币、模具、铸造、版别、边齿与品相资料。','subs':['铜元','机制银币','版别研究','模具与铸造','边齿研究','真伪鉴赏','品相保存','历史研究']},
'banknote':{'title':'纸币','intro':'只收录历史纸币相关冠号、水印、版别、印刷工艺、纸张与品相资料。第五套人民币内容不进入资讯库。','subs':['历史纸币','冠号研究','水印研究','版别研究','印刷工艺','纸张研究','品相保存','发行背景']},
'commemorative':{'title':'纪念币','intro':'只收录纪念币发行事实、主题、设计、规格、材质与收藏研究资料。','subs':['发行资讯','发行主题','图案设计','规格与材质','发行背景','收藏研究']},
'gold':{'title':'金银币','intro':'只收录金银币及贵金属纪念币的发行、材质、工艺、规格与主题资料。','subs':['金币','银币','材质与规格','铸造工艺','发行主题','收藏研究']},
'fujian':{'title':'福建钱币','intro':'福建地域资料统一入口，按地区与研究主题归档，不再散落到全国品类目录。','subs':['福建钱币总览','福建历史','泉州','厦门','漳州','福州','福建地域研究','福建收藏文化']}
}

EXCLUDE=['第五套人民币','第五版人民币','第五套 人民币','买卖','收购','求购','回收广告','招商','推广','加微信','联系方式']

def text(x): return ' '.join(str(x or '').split())
def load(p):
 try:return json.loads(p.read_text(encoding='utf-8'))
 except:return []
def classify(r):
 s=text(json.dumps(r,ensure_ascii=False))
 if any(k in s for k in EXCLUDE): return None
 if any(k in s for k in ['福建','泉州','厦门','漳州','福州','莆田','宁德','南平','三明','龙岩','晋江','石狮','闽南','闽东','闽北','闽西']): return 'fujian'
 if any(k in s for k in ['银元','袁大头','龙洋','孙像银币','站洋','鹰洋']): return 'silver'
 if any(k in s for k in ['机制币','铜元','铜板','机制银币']): return 'machine'
 if any(k in s for k in ['纸币','冠号','水印','纸钞']) and not any(k in s for k in ['第五套人民币','第五版人民币']): return 'banknote'
 if '纪念币' in s: return 'commemorative'
 if any(k in s for k in ['金币','金银币','贵金属币']): return 'gold'
 if any(k in s for k in ['古钱币','古钱','秦半两','五铢','开元通宝','宋钱','清钱']): return 'ancient'
 return None

def subcategory(kind,r):
 s=text(json.dumps(r,ensure_ascii=False)); title=text(r.get('title'))
 if kind=='ancient':
  if any(k in s for k in ['真伪','真假']): return '真伪鉴赏'
  if any(k in s for k in ['品相','包浆','磨损']): return '品相保存'
  if any(k in s for k in ['版别','版式']): return '版别研究'
  if any(k in s for k in ['钱文','字体','书体']): return '钱文与书体'
  if any(k in s for k in ['铸造','铸法','铸工']): return '铸造工艺'
  if any(k in s for k in ['秦汉','唐','宋','元','明','清','先秦']): return '朝代与时代'
  return '历史文化'
 if kind=='silver':
  if any(k in s for k in ['真伪','真假']): return '真伪鉴赏'
  if any(k in s for k in ['评级','品相','磨损']): return '品相与评级'
  if any(k in s for k in ['边齿','齿边','包浆']): return '边齿与包浆'
  if any(k in s for k in ['版别','版式']): return '版别研究'
  if any(k in s for k in ['字体','图案']): return '字体与图案'
  if any(k in s for k in ['压力','打制']): return '压力与细节'
  return '银元品种'
 if kind=='machine':
  if any(k in s for k in ['铜元','铜板']): return '铜元'
  if any(k in s for k in ['边齿','齿边']): return '边齿研究'
  if any(k in s for k in ['模具','钢模','铸造','铸工']): return '模具与铸造'
  if any(k in s for k in ['真伪','真假']): return '真伪鉴赏'
  if any(k in s for k in ['品相','磨损']): return '品相保存'
  if any(k in s for k in ['版别','版式']): return '版别研究'
  return '历史研究'
 if kind=='banknote':
  if any(k in s for k in ['冠号','冠字']): return '冠号研究'
  if '水印' in s:return '水印研究'
  if any(k in s for k in ['版别','版式']): return '版别研究'
  if any(k in s for k in ['印刷','凹印','胶印']): return '印刷工艺'
  if '纸张' in s:return '纸张研究'
  if any(k in s for k in ['品相','磨损']): return '品相保存'
  if any(k in s for k in ['发行','发行史']): return '发行背景'
  return '历史纸币'
 if kind=='commemorative':
  if any(k in s for k in ['发行','公告','发行计划']): return '发行资讯'
  if any(k in s for k in ['主题','纪念']): return '发行主题'
  if any(k in s for k in ['图案','设计']): return '图案设计'
  if any(k in s for k in ['规格','材质']): return '规格与材质'
  if '背景' in s:return '发行背景'
  return '收藏研究'
 if kind=='gold':
  if '金币' in s:return '金币'
  if '银币' in s:return '银币'
  if any(k in s for k in ['材质','规格']): return '材质与规格'
  if any(k in s for k in ['铸造','工艺']): return '铸造工艺'
  if any(k in s for k in ['发行','主题']): return '发行主题'
  return '收藏研究'
 if kind=='fujian':
  for city in ['泉州','厦门','漳州','福州']:
   if city in s:return city
  if any(k in s for k in ['历史','流通']):return '福建历史'
  if any(k in s for k in ['研究','版别','钱文','机制币','银元']):return '福建地域研究'
  if '收藏文化' in s:return '福建收藏文化'
  return '福建钱币总览'
 return None

def main():
 OUT.mkdir(parents=True,exist_ok=True); buckets={k:[] for k in TAXONOMY}
 for p in SRC.glob('*.json'):
  for r in load(p):
   if not isinstance(r,dict) or r.get('status') not in (None,'published'): continue
   k=classify(r)
   if k:buckets[k].append(dict(r,subcategory=subcategory(k,r)))
 for k in buckets:
  seen=set(); clean=[]
  for r in buckets[k]:
   key=r.get('id') or r.get('title')
   if key not in seen:seen.add(key);clean.append(r)
  clean.sort(key=lambda x:(x.get('date',''),x.get('title','')),reverse=True)
  (OUT/f'{k}.json').write_text(json.dumps(clean[:100],ensure_ascii=False,indent=2),encoding='utf-8')
 config={'updated_at':NOW,'taxonomy':TAXONOMY,'rule':'一篇资料只进入一个钱币主品类；地域资料优先进入福建钱币；第五套人民币及商业导流内容排除。'}
 (DATA/'category-config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2),encoding='utf-8')
 print('category routing complete:',{k:len(v) for k,v in buckets.items()})
if __name__=='__main__':main()
