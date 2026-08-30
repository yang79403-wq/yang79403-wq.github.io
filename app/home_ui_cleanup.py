from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'


def main():
    html = INDEX.read_text(encoding='utf-8')

    # 删除首页新增的“实时收藏资讯 AI”展示板块，同时移除导航入口。
    html = re.sub(r'<a href="/ai-news\.html">🤖 实时资讯AI</a>', '', html)
    html = re.sub(r'<section class="section"><div class="ai-section">.*?</div></section>', '', html, count=1, flags=re.S)

    # 客服二维码只在用户明确需要服务时弹出，避免首页重复堆放二维码。
    if 'id="customerQrModal"' not in html:
        modal = '''<div id="customerQrModal" style="display:none;position:fixed;inset:0;z-index:100;background:rgba(20,10,6,.68);align-items:center;justify-content:center;padding:20px"><div style="position:relative;width:min(360px,92vw);background:#fffdf8;border:2px solid #d7b45a;border-radius:18px;padding:24px;text-align:center;box-shadow:0 18px 60px #0006"><button id="customerQrClose" aria-label="关闭" style="position:absolute;right:10px;top:8px;border:0;background:transparent;font-size:26px;color:#741712;cursor:pointer">×</button><h2 style="margin:4px 0 8px;color:#741712">📱 联系洪盛集藏客服</h2><p style="margin:0 0 14px;color:#766657;line-height:1.7">扫码添加客服微信<br>免费鉴定 · 评估 · 收藏咨询 · 面对面交流预约</p><img src="/assets/customer-contact.svg" alt="洪盛集藏客服微信二维码" style="width:230px;height:230px;max-width:75vw;border:1px solid #e3d6bf;border-radius:12px;padding:5px;background:#fff"><div style="font-size:23px;font-weight:900;color:#741712;margin-top:12px">📞 13799875350</div><p style="font-size:12px;color:#927d6c;margin:6px 0 0">需要相关服务时扫码联系即可</p></div></div>'''
        script = '''<script>(function(){function openQR(){var m=document.getElementById('customerQrModal');if(m)m.style.display='flex'}function closeQR(){var m=document.getElementById('customerQrModal');if(m)m.style.display='none'}document.addEventListener('click',function(e){var a=e.target.closest('a');if(!a)return;var t=(a.textContent||'').replace(/\\s/g,'');if(/免费鉴定|在线估价|立即咨询|评级服务|收藏顾问|回收寄卖/.test(t)){e.preventDefault();openQR()}});document.addEventListener('DOMContentLoaded',function(){var c=document.getElementById('customerQrClose');var m=document.getElementById('customerQrModal');if(c)c.onclick=closeQR;if(m)m.addEventListener('click',function(e){if(e.target===m)closeQR()});document.addEventListener('keydown',function(e){if(e.key==='Escape')closeQR()})});window.openCustomerQR=openQR})()</script>'''
        html = html.replace('</body>', modal + script + '</body>')

    # 去掉首页文案中对前台实时资讯AI的展示性描述，保留后台自动处理能力。
    html = html.replace('知识、行情、鉴赏、版别研究、评级服务、收藏顾问、藏品展示与收藏资讯统一入口。后台持续整理公开资料并进行筛选、摘要、分类。', '知识、行情、鉴赏、版别研究、评级服务、收藏顾问、藏品展示与收藏资讯统一入口。')

    INDEX.write_text(html, encoding='utf-8')
    print('首页清理完成：删除实时资讯AI展示板块；服务入口改为按需弹出客服微信二维码。')


if __name__ == '__main__':
    main()
