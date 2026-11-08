# 기능 명세서·API 명세서를 읽어 슬라이드용 HTML 조각을 만든다 (index.html 의 <!--SPEC-->, <!--API--> 자리에 넣음)
import re, html, pathlib, sys
root = pathlib.Path(__file__).resolve().parents[2]
CORE = {  # 핵심 기능 4개에 쓰이는 기능 ID → 핵심 기능 번호
  'D1':1,'D2':1,'D3':1,'D4':1,'X1':1,'X5':1,
  'X2':2,'E1':2,'B8':2,
  'B1':3,'B2':3,'B5':3,'B7':3,'C3':3,'C4':3,
  'G1':4,'G2':4,'A1':4,
}
spec = (root/'spec/feature-spec.md').read_text()
rows = []
for m in re.finditer(r'^## ([A-Z])\. (.+?)\n(.*?)(?=^## |\Z)', spec, re.M|re.S):
    letter, name, body = m.groups()
    feats = re.findall(r'^\| ([A-Z]\d+) \| ([^|]+?) \|[^|]+\| (P\d) \|', body, re.M)
    pc = {p: sum(1 for f in feats if f[2]==p) for p in ('P0','P1','P2')}
    items = []
    for fid, fname, pr in feats:
        cls = f' class="core c{CORE[fid]}"' if fid in CORE else ''
        items.append(f'<span{cls}><b>{fid}</b> {html.escape(fname.strip())}</span>')
    rows.append(f'<tr><th>{html.escape(name.split(" (")[0])}</th><td class="n">{len(feats)}</td>'
                f'<td class="n">{pc["P0"] or ""}</td><td class="n">{pc["P1"] or ""}</td><td class="n">{pc["P2"] or ""}</td>'
                f'<td class="items">{"".join(items)}</td></tr>')
(root/'ppt/build/spec.html').write_text('\n'.join(rows))

api = (root/'spec/api-spec.md').read_text()
HOT = {'/auth/google','/listings','/listings/{id}/price-check','/listings/{id}/nearby','/walk','/floorplans/{id}','/floorplans/estimate','/reviews','/v1/rent/estimate','/v1/floorplan/estimate','/v1/floorplan/estimate-from-meta','/ws/world'}
groups = []
for m in re.finditer(r'^## (.+?)\n(.*?)(?=^## |\Z)', api, re.M|re.S):
    gname, body = m.groups()
    eps = re.findall(r'^\| (GET|POST|PUT|PATCH|DELETE|WS) \| `([^`]+)` \| ([^|]+?) \|', body, re.M)
    if not eps: continue
    lis = []
    seen = set()
    for meth, path, desc in eps:
        hot = path in HOT and (meth, path) not in seen and not (path=='/reviews' and False)
        seen.add((meth, path))
        lis.append(f'<li{" class=hot" if path in HOT else ""}><i class="m {meth.lower()}">{meth}</i><code>{html.escape(path)}</code></li>')
    groups.append(f'<div class="apig"><h4>{html.escape(gname.split(" (")[0])} <small>{len(eps)}</small></h4><ul>{"".join(lis)}</ul></div>')
(root/'ppt/build/api.html').write_text('\n'.join(groups))
print(len(rows), 'spec rows;', len(groups), 'api groups')
