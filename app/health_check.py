#!/usr/bin/env python3
"""洪盛集藏生产健康检查：验证核心页面、静态资源和数据文件。"""
from __future__ import annotations
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://yang79403-wq.github.io"
PAGES = ["/", "/index.html"]
ASSETS = ["/app.css", "/app.js"]
DATA = ["/data/news.json", "/data/editorial.json", "/data/grading_prices.json"]
TIMEOUT = 20


def fetch(url: str) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers={"User-Agent": "HongshengJicang-HealthCheck/1.0"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.read()


def check_url(path: str) -> tuple[bool, str]:
    try:
        status, body = fetch(BASE + path)
        if status != 200:
            return False, f"HTTP {status}"
        if not body:
            return False, "empty response"
        return True, f"HTTP {status}, {len(body)} bytes"
    except Exception as exc:
        return False, str(exc)


def local_json(path: str) -> tuple[bool, str]:
    p = ROOT / path.lstrip("/")
    if not p.exists():
        return False, "file missing"
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(obj, dict) and "items" in obj and not isinstance(obj["items"], list):
            return False, "items is not a list"
        return True, f"valid JSON, {p.stat().st_size} bytes"
    except Exception as exc:
        return False, f"invalid JSON: {exc}"


def main() -> int:
    failures = 0
    warnings = 0
    print("=== 洪盛集藏 AI 生产健康检查 ===")
    print(f"Base: {BASE}")
    print("\n[公网页面]")
    for path in PAGES + ASSETS + DATA:
        ok, detail = check_url(path)
        print(f"{'PASS' if ok else 'FAIL'} {path} -> {detail}")
        failures += not ok

    print("\n[本地数据完整性]")
    for path in DATA:
        ok, detail = local_json(path)
        print(f"{'PASS' if ok else 'FAIL'} {path} -> {detail}")
        failures += not ok

    index = ROOT / "index.html"
    if index.exists():
        text = index.read_text(encoding="utf-8", errors="replace")
        required = ["洪盛集藏", "AI", "app.css", "app.js"]
        missing = [x for x in required if x not in text]
        if missing:
            print(f"FAIL /index.html required markers missing: {missing}")
            failures += 1
        else:
            print("PASS /index.html required markers present")
    else:
        print("FAIL /index.html missing")
        failures += 1

    # Health check itself is intentionally conservative: warnings do not block publishing.
    if failures:
        print(f"\nHEALTH=FAIL failures={failures} warnings={warnings}")
        return 1
    print(f"\nHEALTH=PASS failures={failures} warnings={warnings}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
