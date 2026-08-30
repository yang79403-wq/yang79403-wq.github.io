from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'

NAV = '<a href="#fujian">🏮 福建钱币</a>'
SECTION = '''<section class="section" id="fujian"><h2>🏮 福建钱币</h2><div class="grid"><article class="card"><h3>福建钱币总览</h3><p>集中整理福建钱币历史、流通、地方铸币、机制币、银元及收藏文化资料。</p><a href="/knowledge/areas/fujian.html">进入福建钱币 →</a></article><article class="card"><h3>福建钱币历史</h3><p>整理福建历史时期的钱币流通、地方经济与钱币文化研究资料。</p><a href="/knowledge/areas/fujian.html">查看历史研究 →</a></article><article class="card"><h3>泉州 · 厦门 · 漳州 · 福州</h3><p>集中整理福建主要城市及周边地域的钱币历史与收藏研究资料。</p><a href="/knowledge/areas/fujian.html">进入地域研究 →</a></article><article class="card"><h3>福建地域研究</h3><p>地方钱币、贸易流通、机制币、银元、钱文与版别研究统一归档。</p><a href="/knowledge/areas/fujian.html">查看研究资料 →</a></article></div></section>'''


def main():
    html = INDEX.read_text(encoding='utf-8')

    # 导航只保留一个福建入口。
    if NAV not in html:
        html = html.replace('<a href="#knowledge">📚 钱币知识库</a>', '<a href="#knowledge">📚 钱币知识库</a>' + NAV)

    # 删除其他板块中旧的“福建收藏”卡片，避免地域内容重复展示。
    html = re.sub(r'<article class="card"><h3>福建收藏</h3>.*?</article>', '', html, flags=re.S)

    # 删除旧的福建收藏卡片残留造成的空白格，并插入唯一福建板块。
    if 'id="fujian"' not in html:
        marker = '<section class="section" id="collection">'
        html = html.replace(marker, SECTION + marker, 1)

    # 搜索提示词明确福建专区是独立入口。
    html = html.replace('搜索：袁大头 / 古钱币 / 纪念币 / 泉州钱币 / 版别', '搜索：袁大头 / 古钱币 / 纪念币 / 福建钱币 / 版别')

    INDEX.write_text(html, encoding='utf-8')
    print('福建UI整理完成：新增唯一福建钱币板块，移除其他板块福建重复入口。')


if __name__ == '__main__':
    main()
