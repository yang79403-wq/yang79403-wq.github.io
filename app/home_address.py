from pathlib import Path

p = Path(__file__).resolve().parent.parent / 'index.html'
s = p.read_text(encoding='utf-8')
address = '📍 地址：福建省泉州鲤城区后城旅游文化街179号'

if address in s:
    print('homepage address already present')
    raise SystemExit(0)

# Prefer injecting into an existing footer. Do not depend on one exact legacy template.
if '</footer>' in s:
    footer_start = s.rfind('<footer')
    footer_end = s.find('</footer>', footer_start)
    if footer_start >= 0 and footer_end >= 0:
        footer = s[footer_start:footer_end]
        insert = '<br>' + address
        s = s[:footer_end] + insert + s[footer_end:]
        p.write_text(s, encoding='utf-8')
        print('homepage address added before </footer>')
        raise SystemExit(0)

# Fall back to inserting before </body> so redesigned pages do not break the pipeline.
if '</body>' in s:
    s = s.replace('</body>', '<footer style="text-align:center;padding:18px;color:#71817f;font-size:12px">' + address + '</footer></body>', 1)
    p.write_text(s, encoding='utf-8')
    print('homepage address added before </body>')
    raise SystemExit(0)

raise SystemExit('cannot find safe insertion point in homepage')
