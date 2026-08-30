from datetime import datetime, timezone
from pathlib import Path
import json, hashlib

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
CONTENT = DATA / 'content'
MARKET = DATA / 'market'
NOW = datetime.now(timezone.utc).isoformat(timespec='seconds')

SECTIONS = {
    'knowledge': {
        'title': '钱币知识库',
        'subtitle': '自动整理公开历史、钱文、形制与收藏知识，持续补充古钱币、银元、机制币、纸币、纪念币、金银币资料。',
        'items': [('knowledge_ancient','古钱币'),('knowledge_silver','银元'),('knowledge_machine','机制币'),('knowledge_banknote','纸币'),('knowledge_commemorative','纪念币'),('knowledge_gold','金银币')]
    },
    'appraisal': {
        'title': '在线鉴赏',
        'subtitle': '以公开资料和可观察特征为基础，自动整理鉴赏、真伪研究与品相分析知识，仅作学习交流参考。',
        'items': [('appraisal_features','特征观察'),('appraisal_auth','真伪研究'),('appraisal_grade','品相分析')]
    },
    'research': {
        'title': '版别研究',
        'subtitle': '持续建立钱文、版式、铸造工艺、边齿与地域资料索引。',
        'items': [('research_text','钱文与字体'),('research_variety','版式研究'),('research_edge','边齿与工艺'),('research_region','地域研究')]
    },
    'services': {
        'title': '收藏服务',
        'subtitle': '整理评级、收藏咨询、品相评估与藏品流通相关的公开知识，不发布交易导流广告。',
        'items': [('service_grading','评级服务交流'),('service_advisor','收藏顾问'),('service_flow','收藏品流通')]
    },
    'collection': {
        'title': '藏品展示',
        'subtitle': '以文字资料、版别记录和收藏研究笔记为主，逐步形成可检索的藏品资料库。',
        'items': [('collection_records','藏品资料'),('collection_fujian','福建收藏'),('collection_notes','收藏研究笔记')]
    },
}


def norm(x):
    return ' '.join(str(x or '').split())


def stable_id(prefix, title, extra=''):
    return prefix + hashlib.sha1((title + extra).encode('utf-8')).hexdigest()[:12]


def load_editorial():
    p = DATA / 'editorial.json'
    if not p.exists():
        return []
    try:
        obj = json.loads(p.read_text(encoding='utf-8'))
        return obj.get('items', []) if isinstance(obj, dict) else []
    except Exception:
        return []


def make_record(title, note, category, date=None, source='洪盛集藏资料库', source_url=''):
    return {
        'id': stable_id(category + '-', title, source_url),
        'date': date or datetime.now().strftime('%Y-%m-%d'),
        'title': norm(title),
        'note': norm(note),
        'category': category,
        'source': source,
        'source_url': source_url,
        'images': [],
        'status': 'published',
        'disclaimer': '公开资料整理，仅供学习、研究与收藏交流参考。'
    }


def seed_records():
    return {
        'knowledge_ancient': [make_record('古钱币：钱文、形制与时代识别', '从钱文、穿制、轮廓、铸造方式和历史背景建立基础观察框架。', '古钱币')],
        'knowledge_silver': [make_record('银元：版式、压力与边齿观察', '银元研究重点包括图文细节、压力表现、边齿状态、磨损和包浆等可观察特征。', '银元')],
        'knowledge_machine': [make_record('机制币：铸造工艺与版别基础', '关注模具、压力、齿边、文字布局和局部细节，结合可靠资料进行对照。', '机制币')],
        'knowledge_banknote': [make_record('老纸币：冠号、水印与版别资料', '围绕冠号、水印、印刷工艺、纸张和版式建立研究索引；第五套人民币不进入本站资讯。', '纸币')],
        'knowledge_commemorative': [make_record('纪念币：发行主题与收藏资料', '整理发行背景、主题、规格与公开资料，区分官方信息和民间观点。', '纪念币')],
        'knowledge_gold': [make_record('金银币：材质、规格与主题研究', '整理金银币公开发行资料、主题信息和收藏研究线索。', '金银币')],
        'appraisal_features': [make_record('钱币鉴赏：先看哪些特征？', '从钱文、形制、铸造工艺、边齿、包浆、磨损和整体状态建立观察顺序。', '在线鉴赏')],
        'appraisal_auth': [make_record('真伪研究：为什么要多维交叉核验', '单一特征不能作为真伪结论，应结合版式、工艺、尺寸重量、边齿和可靠图录进行综合判断。', '真伪研究')],
        'appraisal_grade': [make_record('品相分析：磨损与保存状态', '关注高点磨损、划痕、磕碰、清洗痕迹、包浆与保存状态，不以单一描述替代专业评级。', '品相分析')],
        'research_text': [make_record('钱文与字体研究', '比较字体结构、笔画、布局和时代特征，建立可检索的文字研究笔记。', '版别研究')],
        'research_variety': [make_record('版式研究：从整体到局部', '记录版式差异、文字位置、图案细节和常见变体，形成版别索引。', '版别研究')],
        'research_edge': [make_record('边齿与铸造工艺研究', '边齿、压力、坯饼和铸造细节是机制币研究的重要观察维度。', '版别研究')],
        'research_region': [make_record('福建钱币与地域收藏研究', '逐步整理福建、泉州、厦门、福州等地区的钱币历史与收藏文化资料。', '地域研究')],
        'service_grading': [make_record('评级服务交流：了解评级逻辑', '整理公开评级知识，介绍评级标签、品相概念和送评前的资料准备思路。', '评级服务交流')],
        'service_advisor': [make_record('收藏顾问：建立自己的收藏体系', '从兴趣方向、预算、品种结构、资料积累和风险意识等方面建立收藏记录。', '收藏顾问')],
        'service_flow': [make_record('收藏品流通：认识公开市场信息', '仅整理收藏品流通相关知识和公开信息，不发布买卖、收购、求购或价格导流内容。', '收藏品流通')],
        'collection_records': [make_record('藏品资料库建设规则', '每件藏品逐步记录名称、年代、版别、尺寸、重量、状态、来源说明和研究备注。', '藏品资料')],
        'collection_fujian': [make_record('福建收藏文化资料', '围绕福建钱币历史、地方铸币与收藏文化建立地域资料索引。', '福建收藏')],
        'collection_notes': [make_record('收藏研究笔记', '持续沉淀观察记录、资料出处和研究结论，方便后续检索与复核。', '研究笔记')],
    }


def route_editorial(items):
    buckets = {k: [] for g in SECTIONS.values() for k, _ in g['items']}
    for x in items:
        title = norm(x.get('title'))
        text = norm(json.dumps(x, ensure_ascii=False))
        if not title or x.get('editorial_status') != 'published':
            continue
        kws = set(x.get('keywords', []))
        date = x.get('date')
        note = norm((x.get('content') or {}).get('内容摘要') or (x.get('content') or {}).get('导读'))
        source = x.get('source', '公开资料')
        srcurl = x.get('source_url_internal', '')
        rec = make_record(title, note or '洪盛集藏对公开资料进行筛选、整理和结构化，供收藏研究者参考。', x.get('category','收藏资讯'), date, source, srcurl)
        if any(k in text or k in kws for k in ['古钱币']): buckets['knowledge_ancient'].append(rec)
        if any(k in text or k in kws for k in ['银元','袁大头']): buckets['knowledge_silver'].append(rec)
        if any(k in text or k in kws for k in ['机制币','铜元']): buckets['knowledge_machine'].append(rec)
        if '纸币' in text or '人民币' in kws and '第五套人民币' not in text: buckets['knowledge_banknote'].append(rec)
        if '纪念币' in text: buckets['knowledge_commemorative'].append(rec)
        if '金银币' in text: buckets['knowledge_gold'].append(rec)
        if any(k in text for k in ['鉴赏','真伪','品相']): buckets['appraisal_features'].append(rec)
        if any(k in text for k in ['版别','钱文','字体']): buckets['research_variety'].append(rec)
        if any(k in text for k in ['边齿','铸造','机制']): buckets['research_edge'].append(rec)
        if any(k in text for k in ['福建','泉州']): buckets['research_region'].append(rec)
    return buckets


def build_market(items):
    out = [make_record('钱币市场观察：公开资讯动态', '自动汇总公开资讯中的发行、拍卖、展会、评级与收藏研究动态。这里是信息观察，不等同于实时成交价。', '市场行情')]
    for x in items:
        text = norm(json.dumps(x, ensure_ascii=False))
        if any(k in text for k in ['拍卖','成交','评级','市场','行情']):
            title = norm(x.get('title'))
            note = norm((x.get('content') or {}).get('内容摘要') or '公开市场信息整理，具体成交结果应以原始记录和实际交易为准。')
            out.append(make_record(title, note, '市场观察', x.get('date'), x.get('source','公开资料'), x.get('source_url_internal','')))
    return out[:30]


def main():
    CONTENT.mkdir(parents=True, exist_ok=True)
    MARKET.mkdir(parents=True, exist_ok=True)
    editorial = load_editorial()
    buckets = seed_records()
    routed = route_editorial(editorial)
    for k, arr in routed.items():
        # 自动资料优先，同时保留最小种子内容，防止某次来源失败导致页面空白。
        merged = arr + buckets.get(k, [])
        seen = set(); final = []
        for x in merged:
            if x['id'] in seen: continue
            seen.add(x['id']); final.append(x)
        final.sort(key=lambda z: (z.get('date',''), z.get('title','')), reverse=True)
        (CONTENT / f'{k}.json').write_text(json.dumps(final[:40], ensure_ascii=False, indent=2), encoding='utf-8')
    market = build_market(editorial)
    (MARKET / 'market_overview.json').write_text(json.dumps(market, ensure_ascii=False, indent=2), encoding='utf-8')
    groups = {}
    for gid, g in SECTIONS.items():
        groups[gid] = {'title': g['title'], 'subtitle': g['subtitle'], 'items': [{'id': i, 'name': n, 'enabled': True} for i, n in g['items']]}
    groups['market'] = {'title': '钱币行情', 'subtitle': '自动整理公开市场资讯、拍卖与成交观察。数字价格仅在具备可靠公开来源时单独收录，默认不将宣传报价当作市场价格。', 'items': [{'id':'market_overview','name':'市场观察','enabled':True}]}
    config = {'siteName':'洪盛集藏','updated_at':NOW,'groups':groups,'serviceSections':[],'policy':'不采集第五套人民币资讯；过滤商业广告、买卖导流、联系方式和价格营销；图片不使用外部图床。'}
    (DATA / 'site-config.json').write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding='utf-8')
    print('section_pipeline: generated', len(buckets), 'section datasets; editorial=', len(editorial))

if __name__ == '__main__':
    main()
