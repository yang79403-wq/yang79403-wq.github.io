from datetime import datetime, timezone
from pathlib import Path
import json
import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
HEADERS = {"User-Agent": "HongshengJicang/3.0 (+public-source-index; educational-use)"}
BLOCKED_HOST_HINTS = ("tcmb.culture.tw", ".tw/", ".tw")
NEWS_SOURCES = [
    {"name": "中国金币网", "url": "https://www.chngc.net/common/homep", "category": "纪念币与行业资讯"},
    {"name": "爱藏收藏新闻", "url": "https://news.airmb.com/", "category": "收藏行业资讯"},
]
KEYWORDS = ["钱币收藏","古钱币","银元","袁大头","机制币","纸币","人民币","纪念币","金银币","钱币版别","钱币鉴赏","钱币拍卖","钱币展会","泉州钱币","福建钱币"]

def mainland_allowed(url: str) -> bool:
    u = (url or "").lower()
    return not any(h in u for h in BLOCKED_HOST_HINTS)

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def inspect(item):
    out = dict(item)
    url = item.get("url", "")
    if not mainland_allowed(url):
        out.update({"status": "blocked_non_mainland", "image_count": 0, "checked_at": now()})
        return out
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        imgs = []
        for img in soup.find_all("img"):
            src = img.get("src") or img.get("data-src")
            if src:
                imgs.append(urljoin(r.url, src))
        out.update({"status": "ok", "page_title": soup.title.get_text(" ", strip=True)[:180] if soup.title else item.get("name", ""), "image_count": len(imgs), "image_index": imgs[:30], "checked_at": now()})
    except Exception as e:
        out.update({"status": f"error:{type(e).__name__}", "image_count": 0, "image_index": [], "checked_at": now()})
    return out

def keyword_match(text):
    return [k for k in KEYWORDS if k in (text or "")]

def collect_news():
    records, seen = [], set()
    for source in NEWS_SOURCES:
        try:
            r = requests.get(source["url"], headers=HEADERS, timeout=25)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            for a in soup.find_all("a", href=True):
                title = " ".join(a.get_text(" ", strip=True).split())
                href = urljoin(r.url, a["href"])
                if not title or len(title) < 6 or len(title) > 120 or not mainland_allowed(href) or href in seen:
                    continue
                if not any(k in title for k in KEYWORDS):
                    continue
                seen.add(href)
                parent_text = a.parent.get_text(" ", strip=True) if a.parent else ""
                date_match = re.search(r"20\d{2}[-/.年]\d{1,2}[-/.月]\d{1,2}", parent_text)
                date = date_match.group(0).replace("年", "-").replace("月", "-").replace("日", "") if date_match else datetime.now().strftime("%Y-%m-%d")
                records.append({"id": f"news-{len(records)+1}-{abs(hash(href))}","date": date[:10],"title": title,"summary": f"公开来源：{source['name']}。本站保留标题、来源与链接，供收藏研究者继续核验。","source": source["name"],"url": href,"category": source["category"],"keywords": keyword_match(title)})
                if len(records) >= 80:
                    break
        except Exception as e:
            print(f"news source failed: {source['name']}: {type(e).__name__}")
    records.sort(key=lambda x: (x.get("date", ""), x.get("title", "")), reverse=True)
    unique, urls = [], set()
    for x in records:
        if x["url"] not in urls:
            urls.add(x["url"])
            unique.append(x)
        if len(unique) >= 80:
            break
    payload = {"updated_at": now(),"policy": "保存公开来源标题、日期、摘要、分类、关键词和原始链接；不整篇镜像受版权保护文章。","items": unique}
    (DATA / "news.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"news_records={len(unique)}")

def run():
    sources_file = DATA / "fujian_sources.json"
    src = json.loads(sources_file.read_text(encoding="utf-8"))
    checked = [inspect(x) for x in src.get("sources", []) if mainland_allowed(x.get("url", ""))]
    status = {"updated_at": now(),"policy": "中国大陆公开来源优先；受版权保护图片不直接复制；自动任务以来源索引和公开信息整理为主。","sources": checked}
    (DATA / "source_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
    f = json.loads((DATA / "fujian.json").read_text(encoding="utf-8"))
    f["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    f["source_status_count"] = len(checked)
    f["collection_note"] = "自动任务检查公开来源并建立资料/图片索引；授权不明确时只保留来源，不镜像图片。"
    f["records"] = [r for r in f.get("records", []) if mainland_allowed(r.get("source_url", ""))]
    (DATA / "fujian.json").write_text(json.dumps(f, ensure_ascii=False, indent=2), encoding="utf-8")
    collect_news()
    print(f"checked={len(checked)}, fujian_records={len(f['records'])}")

if __name__ == "__main__":
    run()
