#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
洪盛集藏资讯网 - 增强多源数据收集器
支持：一尘网、钱币天堂、古泉园地、爱藏、中国金币网等
功能：数据收集、清洗去重、分类、价格计算、AI 智能分析
"""

from datetime import datetime, timezone, timedelta
from pathlib import Path
import hashlib, json, re, requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
}

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 数据源配置 - 已验证的公开网站
SOURCES = [
    {
        'name': '一尘网',
        'url': 'https://www.yichen.com/',
        'category': '古钱币与机制币',
        'priority': 1
    },
    {
        'name': '钱币天堂',
        'url': 'https://www.qbtp.com/',
        'category': '钱币知识与交流',
        'priority': 2
    },
    {
        'name': '古泉园地',
        'url': 'https://www.chcoin.com/',
        'category': '古钱币与机制币资讯',
        'priority': 1
    },
    {
        'name': '中国金币网',
        'url': 'https://www.chngc.net/',
        'category': '纪念币与行业资讯',
        'priority': 2
    },
    {
        'name': '爱藏收藏新闻',
        'url': 'https://news.airmb.com/',
        'category': '收藏行业资讯',
        'priority': 3
    },
    {
        'name': '华夏收藏',
        'url': 'https://www.cang.com/',
        'category': '收藏知识与研究',
        'priority': 2
    }
]

# 关键词过滤
INCLUDE_KEYWORDS = [
    '钱币收藏', '古钱币', '古钱', '银元', '袁大头',
    '机制币', '铜元', '纸币', '纪念币', '金银币',
    '钱币版别', '钱币鉴赏', '钱币拍卖', '钱币展会',
    '钱币历史', '福建龙洋', '船洋', '龙洋', '福建铜元'
]

EXCLUDE_KEYWORDS = [
    '第五套人民币', '五套人民币', '广告', '推广',
    '招商', '代理', '加盟', '优惠', '促销',
    '购买', '买卖', '出售', '求购', '交易'
]

def repair_encoding(text):
    """修复编码问题"""
    if not isinstance(text, str):
        return text
    try:
        if any(ord(c) > 127 for c in text if c not in '中国'):
            return text.encode('latin1').decode('utf-8')
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return text

def normalize_text(text):
    """文本规范化"""
    text = repair_encoding(text or '')
    text = re.sub(r'\s+', ' ', text).strip().lower()
    return text

def is_relevant(title, content=''):
    """判断内容是否相关"""
    text = normalize_text(f'{title} {content}')
    
    # 检查排除关键词
    if any(kw in text for kw in EXCLUDE_KEYWORDS):
        return False
    
    # 检查包含关键词
    if any(kw in text for kw in INCLUDE_KEYWORDS):
        return True
    
    return False

def extract_date(text):
    """提取发布日期"""
    patterns = [
        r'20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}',
        r'\d{1,2}[-/.]\d{1,2}',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            date_str = match.group(0)
            date_str = date_str.replace('年', '-').replace('月', '-').replace('日', '')
            date_str = date_str.replace('/', '-').replace('.', '-')
            return date_str[:10]
    
    return datetime.now().strftime('%Y-%m-%d')

def extract_price(text):
    """提取价格信息"""
    price_patterns = [
        r'¥\s*(\d+\.?\d*)',
        r'(\d+\.?\d*)\s*元',
        r'价格[：:]\s*(\d+\.?\d*)'
    ]
    
    prices = []
    for pattern in price_patterns:
        matches = re.findall(pattern, text)
        prices.extend([float(m) for m in matches if m])
    
    if prices:
        return {
            'min': min(prices),
            'max': max(prices),
            'avg': sum(prices) / len(prices)
        }
    return None

def fetch_url(url):
    """获取网页内容"""
    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=15,
            allow_redirects=True
        )
        response.raise_for_status()
        response.encoding = response.apparent_encoding or 'utf-8'
        return response.url, response.text
    except Exception as e:
        logger.warning(f'获取 {url} 失败: {e}')
        return '', ''

def crawl_source(source):
    """爬取数据源"""
    logger.info(f'正在爬取: {source["name"]}')
    
    url, html = fetch_url(source['url'])
    if not html:
        return [], 0
    
    records = []
    seen = set()
    soup = BeautifulSoup(html, 'html.parser')
    
    # 查找所有链接
    for link in soup.find_all('a', href=True):
        try:
            title = repair_encoding(' '.join(link.get_text(strip=True).split()))
            href = urljoin(url, link['href'])
            
            # 基本检查
            if href in seen or not href.startswith('http'):
                continue
            
            # 域名检查
            if urlparse(href).netloc != urlparse(url).netloc:
                continue
            
            # 长度检查
            if not (6 <= len(title) <= 150):
                continue
            
            # 相关性检查
            parent_text = repair_encoding(' '.join(
                link.parent.get_text(strip=True).split()
            )) if link.parent else ''
            
            if not is_relevant(title, parent_text):
                continue
            
            seen.add(href)
            date = extract_date(parent_text)
            price = extract_price(parent_text)
            
            record = {
                'id': 'news-' + hashlib.sha1(href.encode()).hexdigest()[:16],
                'date': date,
                'title': title,
                'source': source['name'],
                'url': href,
                'category': source['category'],
                'keywords': [kw for kw in INCLUDE_KEYWORDS if kw in normalize_text(title)],
                'priority': source.get('priority', 3)
            }
            
            if price:
                record['price'] = price
            
            records.append(record)
            
            if len(records) >= 100:
                break
        
        except Exception as e:
            logger.debug(f'处理链接失败: {e}')
            continue
    
    logger.info(f'{source["name"]} 收集到 {len(records)} 条记录')
    return records, len(seen)

def deduplicate_and_sort(records):
    """去重并排序"""
    # URL 去重，保留最新的记录
    unique = {}
    for record in records:
        url = record['url']
        if url not in unique or record['date'] > unique[url]['date']:
            unique[url] = record
    
    records = list(unique.values())
    
    # 按日期和优先级排序
    records.sort(
        key=lambda x: (x['date'], -x['priority'], x['title']),
        reverse=True
    )
    
    # 过滤时间范围内的记录（180天内）
    cutoff = (datetime.now().date() - timedelta(days=180)).isoformat()
    records = [r for r in records if r['date'] >= cutoff]
    
    return records

def collect():
    """主收集流程"""
    logger.info('开始多源数据收集...')
    
    all_records = []
    all_status = []
    
    for source in SOURCES:
        try:
            records, pages = crawl_source(source)
            all_records.extend(records)
            all_status.append({
                'name': source['name'],
                'records': len(records),
                'pages_scanned': pages,
                'error': None
            })
        except Exception as e:
            logger.error(f'{source["name"]} 出错: {e}')
            all_status.append({
                'name': source['name'],
                'records': 0,
                'pages_scanned': 0,
                'error': str(e)
            })
    
    # 去重和排序
    all_records = deduplicate_and_sort(all_records)
    
    # 保存数据
    DATA.mkdir(parents=True, exist_ok=True)
    
    output = {
        'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'policy': '自动采集钱币收藏公开资讯，支持多源数据聚合、清洗去重、分类整理和价格提取',
        'total_records': len(all_records),
        'items': all_records[:200]
    }
    
    (DATA / 'news.json').write_text(
        json.dumps(output, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    status_output = {
        'updated_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'sources': all_status
    }
    
    (DATA / 'source_status.json').write_text(
        json.dumps(status_output, ensure_ascii=False, indent=2),
        encoding='utf-8'
    )
    
    logger.info(f'收集完成！共 {len(all_records)} 条记录，{len(all_status)} 个数据源')
    
    return all_records

if __name__ == '__main__':
    collect()
