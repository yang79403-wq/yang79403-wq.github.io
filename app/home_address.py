from pathlib import Path
p=Path(__file__).resolve().parent.parent/'index.html'
s=p.read_text(encoding='utf-8')
address='📍 地址：福建省泉州鲤城区后城旅游文化街179号'
if address not in s:
    old='<footer class="footer"><div class="wrap"><strong>🏮 洪盛集藏</strong>｜钱币收藏综合信息与服务平台<br>知识 · 行情 · 鉴赏 · 研究 · 服务 · 资讯<br>公开资料整理｜学习交流参考</div></footer>'
    new='<footer class="footer"><div class="wrap"><strong>🏮 洪盛集藏</strong>｜钱币收藏综合信息与服务平台<br>知识 · 行情 · 鉴赏 · 研究 · 服务 · 资讯<br>'+address+'<br>公开资料整理｜学习交流参考</div></footer>'
    if old not in s:
        raise SystemExit('footer template not found')
    p.write_text(s.replace(old,new,1),encoding='utf-8')
    print('homepage address added')
else:
    print('homepage address already present')
