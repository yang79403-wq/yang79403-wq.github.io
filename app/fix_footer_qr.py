from pathlib import Path
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / 'index.html'
QR = '/static/qr-service.png'


def replace_box(soup, box):
    box.clear()
    img = soup.new_tag('img', src=QR, alt='微信客服二维码')
    img['style'] = 'width:110px;height:110px;object-fit:contain;background:#fff;border:0;border-radius:4px;display:block'
    box.append(img)
    p = soup.new_tag('div')
    p.string = '📱 微信二维码'
    p['style'] = 'margin-top:8px;font-size:12px;color:#e8cf9a;text-align:center;white-space:nowrap'
    box.append(p)


def main():
    soup = BeautifulSoup(INDEX.read_text(encoding='utf-8'), 'html.parser')

    # 删除同步脚本曾经插入到页脚中间的二维码，不改变原页脚布局。
    generated = soup.find(id='hongsheng-footer-qr')
    if generated:
        generated.decompose()

    # 只使用原版“联系我们”下面那个写着“微信二维码”的白色占位框。
    contact = soup.find(class_='footer-contact')
    box = contact.find(class_='qr-box') if contact else soup.find(class_='qr-box')
    if box:
        replace_box(soup, box)

    # 首页主视觉二维码也统一使用真实二维码图片资源。
    hero = soup.find(id='hongsheng-hero-qr')
    if hero:
        img = hero.find('img')
        if img:
            img['src'] = QR

    INDEX.write_text(str(soup), encoding='utf-8')


if __name__ == '__main__':
    main()
