from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
import hashlib, json, re, requests

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
HEADERS = {'User-Agent': 'HongshengJicang/6.0 (+public-source-index; educational-use)'}
API = 'https://commons.wikimedia.org/w/api.php'

# 仅选择 Wikimedia Commons 中明确标注为公共领域或允许再利用的图片。
# 不下载原图到仓库，保存高清缩略图地址与署名/许可证信息，降低仓库体积并保留来源。
TOPICS = [
    ('古钱币', ['Chinese ancient coins', 'ancient Chinese coin', 'cash coin China']),
    ('银元', ['Chinese silver dollar', 'Yuan Shikai dollar', 'Chinese silver coin']),
    ('机制币', ['Chinese machine struck coin', 'Chinese coin mint', 'Chinese copper coin']),
    ('纸币', ['Chinese banknote', 'Republic of China banknote', 'Chinese paper money']),
    ('纪念币', ['Chinese commemorative coin', 'China commemorative coin']),
    ('金银币', ['Chinese gold coin', 'Chinese silver commemorative coin']),
    ('钱币鉴赏', ['coin collecting', 'coin grading', 'coin authentication']),
    ('版别研究', ['coin varieties', 'coin die variety', 'coin minting detail']),
    ('福建钱币', ['Fujian China history', 'Fujian coin', 'Quanzhou China history']),
    ('泉州收藏', ['Quanzhou China', 'Quanzhou old city', 'Quanzhou history']),
    ('收藏资讯', ['coin exhibition', 'numismatic exhibition', 'coin museum']),
    ('收藏文化', ['numismatics museum', 'coin collection museum', 'numismatic collection']),
]

ALLOWED_LICENSE = ('public domain', 'cc0', 'cc by', 'cc by-sa', 'creative commons attribution')
BLOCKED_TERMS = ('non-commercial', 'no derivatives', 'nc', 'nd')


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def clean_html(value):
    return re.sub(r'<[^>]+>', ' ', value or '').replace('&nbsp;', ' ').strip()


def license_ok(meta):
    license_name = clean_html(meta.get('LicenseShortName', {}).get('value', ''))
    low = license_name.lower()
    if not license_name or any(x in low for x in BLOCKED_TERMS):
        return False
    return any(x in low for x in ALLOWED_LICENSE)


def search_topic(topic, queries, limit_each=2):
    found = []
    seen = set()
    for q in queries:
        params = {
            'action': 'query', 'generator': 'search', 'gsrsearch': q,
            'gsrnamespace': 6, 'gsrlimit': limit_each, 'format': 'json',
            'prop': 'imageinfo',
            'iiprop': 'url|size|extmetadata', 'iiurlwidth': 1400,
        }
        try:
            r = requests.get(API, params=params, headers=HEADERS, timeout=25)
            r.raise_for_status()
            pages = r.json().get('query', {}).get('pages', {}).values()
            for page in pages:
                info = (page.get('imageinfo') or [{}])[0]
                width, height = int(info.get('width') or 0), int(info.get('height') or 0)
                if width < 900 or height < 500 or not info.get('thumburl') or not license_ok(info.get('extmetadata') or {}):
                    continue
                title = page.get('title', '').replace('File:', '').strip()
                key = hashlib.sha1(title.encode('utf-8')).hexdigest()[:12]
                if key in seen:
                    continue
                seen.add(key)
                meta = info.get('extmetadata') or {}
                author = clean_html(meta.get('Artist', {}).get('value', '')) or 'Wikimedia Commons contributor'
                license_name = clean_html(meta.get('LicenseShortName', {}).get('value', ''))
                description = clean_html(meta.get('ImageDescription', {}).get('value', ''))
                found.append({
                    'id': key,
                    'topic': topic,
                    'title': title,
                    'image': info['thumburl'],
                    'original': info.get('url'),
                    'width': width,
                    'height': height,
                    'author': author[:180],
                    'license': license_name[:100],
                    'source': 'Wikimedia Commons',
                    'source_url': 'https://commons.wikimedia.org/wiki/' + requests.utils.quote(page.get('title', ''), safe=':/'),
                    'description': description[:260],
                })
        except Exception as exc:
            print('image source failed:', q, type(exc).__name__)
    return found[:3]


def collect():
    items = []
    for topic, queries in TOPICS:
        items.extend(search_topic(topic, queries))
    DATA.mkdir(parents=True, exist_ok=True)
    payload = {
        'updated_at': now(),
        'source_policy': 'Wikimedia Commons reusable/public-domain images only; each image retains source, author and license metadata.',
        'image_width_target': 1400,
        'topics': [
            {'topic': topic, 'count': sum(1 for x in items if x['topic'] == topic)}
            for topic, _ in TOPICS
        ],
        'items': items,
    }
    (DATA / 'image-index.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print('image_records=', len(items))


if __name__ == '__main__':
    collect()
