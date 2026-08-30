from pathlib import Path
import json,re

ROOT=Path(__file__).resolve().parent.parent
DATA=ROOT/'data'
RULE='自动采集仅保留收藏知识、历史文化、发行资讯和研究价值的公开信息；广告推广、商业导流、买卖回收信息及第五套人民币相关内容不进入网站资讯库。'
# 仅清理前台可能误显示的内部规则文字；后台 policy 字段继续保留供程序使用。
TARGETS=[ROOT/'index.html',ROOT/'news.html',ROOT/'section.html',DATA/'editorial.json']

def clean_text(s):
    s=s.replace('**内容原则：**'+RULE,'').replace('内容原则：'+RULE,'')
    s=s.replace(RULE,'')
    s=s.replace('本站不是原文链接聚合页。','本站采用站内内容整理展示。')
    s=s.replace('公开资料经过筛选和重新编写后直接展示，前台不设置外部原文跳转。商业广告、交易导流及第五套人民币相关内容继续过滤。','公开资料经过智能整理后直接展示。')
    return s

for p in TARGETS:
    if not p.exists(): continue
    if p.suffix=='.json':
        try:
            obj=json.loads(p.read_text(encoding='utf-8'))
            # JSON 后台规则不删除，只保证异常前台模板文字不混入内容字段。
            p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
        except Exception: pass
    else:
        s=p.read_text(encoding='utf-8'); p.write_text(clean_text(s),encoding='utf-8')
print('public rules removed from frontend files')
