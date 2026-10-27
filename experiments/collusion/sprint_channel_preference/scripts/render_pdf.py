"""Render APART_REPORT.md to a paper-styled HTML (figure embedded) for printing to PDF."""
import base64,re
from pathlib import Path
import markdown

md=Path('outputs/APART_REPORT.md').read_text(encoding='utf-8-sig')
img=base64.b64encode(Path('outputs/figure1_whisper_not_erase.png').read_bytes()).decode()
md=md.replace('](figure1_whisper_not_erase.png)','](data:image/png;base64,'+img+')')
md=md.replace('Independent Researcher\n**Apart','Independent Researcher\n\n**Apart')
body=markdown.markdown(md,extensions=['tables'])
# Title block: first h1 + author/sprint paragraphs centred.
body=re.sub(r'^(<h1>.*?</h1>\s*<p>.*?</p>\s*<p>.*?</p>)',r'<header>\1</header>',body,count=1,flags=re.S)
css='''
@page{size:Letter;margin:0.75in 0.8in}
:root{--ink:#1a1a1a;--muted:#555;--accent:#1c5cab;--rule:#d7dbe2;--head:#eef3fa}
body{font-family:"Charter","Georgia","Cambria",serif;font-size:10.5pt;line-height:1.42;color:var(--ink);margin:0}
header{text-align:center;margin-bottom:14pt;padding-bottom:10pt;border-bottom:1.5px solid var(--accent)}
header h1{font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;font-size:19pt;line-height:1.2;margin:0 0 6pt;color:var(--ink)}
header p{margin:2pt 0;color:var(--muted);font-size:10pt}
h2{font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;font-size:12.5pt;color:var(--accent);margin:14pt 0 4pt;padding-bottom:2pt;border-bottom:1px solid var(--rule)}
h3{font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;font-size:11pt;margin:10pt 0 3pt}
p{margin:4pt 0 6pt;text-align:justify}
ul,ol{margin:3pt 0 6pt;padding-left:18pt}li{margin:1.5pt 0}
table{border-collapse:collapse;margin:6pt auto 9pt;font-size:9pt;page-break-inside:avoid;width:auto}
th{background:var(--head);font-family:"Segoe UI",Arial,sans-serif;font-weight:600;text-align:left}
td,th{border-bottom:1px solid var(--rule);padding:3pt 7pt;vertical-align:top}
tr:first-child th{border-top:1.5px solid var(--accent)}tr:last-child td{border-bottom:1.5px solid var(--accent)}
img{display:block;max-width:82%;margin:8pt auto 2pt}
p:has(> img)+p em,p:has(> img)+p{font-size:9pt;color:var(--muted);text-align:center}
blockquote{margin:6pt 12pt;padding:4pt 10pt;border-left:3px solid var(--accent);background:#f6f8fb;font-style:italic}
blockquote p{margin:2pt 0}
code{font-size:8.5pt;background:#f2f2f2;padding:0 2pt}
h2:first-of-type+p{font-size:10pt}
'''
Path('outputs/APART_REPORT.html').write_text('<!doctype html><meta charset=utf-8><title>Whisper, Don\'t Erase</title><style>'+css+'</style>'+body,encoding='utf-8')
print('ok')
