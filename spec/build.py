"""feature-spec.md + api-spec.md → spec.html

원본은 마크다운 두 개다. 표를 고친 뒤  python3 build.py  로 다시 만든다.
기능 ID 와 API 경로가 서로 링크로 이어지고, 인쇄하면 A4 가로 문서가 된다.
"""
import html
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRI_NAME = {"P0": "핵심", "P1": "주요", "P2": "편의"}


# ── 마크다운 읽기 (이 문서에 쓰는 만큼만) ─────────────────────
def parse(md: str):
    notes, groups, cur = [], [], None
    for line in md.splitlines():
        s = line.strip()
        if s.startswith("> "):
            m = re.match(r"\*\*(.+?)\*\*\s*(.*)", s[2:])
            if m:
                notes.append((m.group(1), m.group(2)))
        elif s.startswith("## "):
            cur = {"name": s[3:], "head": None, "rows": []}
            groups.append(cur)
        elif s.startswith("|") and cur is not None:
            if re.fullmatch(r"\|[\s|:-]+\|", s):
                continue
            cells = [c.strip() for c in s.strip("|").split(" | ")]
            if cur["head"] is None:
                cur["head"] = cells
            else:
                cur["rows"].append(cells)
    return notes, groups


def inline(t: str) -> str:
    t = html.escape(t, quote=False).replace("&lt;br&gt;", "<br>")
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", t)


def api_key(method: str, path: str, ai: bool = False) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", f"{method}-{path}".lower()).strip("-")
    return ("ai-" if ai else "api-") + slug


METHOD_RE = re.compile(r"^(AI\s+)?(GET|POST|PUT|PATCH|DELETE|WS)\s+([^\s]+)\s*(.*)$")


def method(m: str) -> str:
    return f'<span class="mt mt-{m.lower()}">{m}</span>'


def meter(p: str) -> str:
    n = {"P0": 3, "P1": 2, "P2": 1}[p]
    bars = "".join(f'<i class="{"on" if i < n else ""}"></i>' for i in range(3))
    return (f'<span class="pri pri-{p.lower()}" title="{p} {PRI_NAME[p]}"><span class="bars">{bars}</span>'
            f'<span class="pt">{p}</span></span>')


def api_refs(cell: str, known: set) -> str:
    out = []
    for part in cell.split("<br>"):
        raw = part.strip().replace("`", "")
        m = METHOD_RE.match(raw)
        if not m:
            out.append(f'<span class="none">{inline(raw)}</span>')
            continue
        ai, mth, path, rest = bool(m.group(1)), m.group(2), m.group(3), m.group(4)
        key = api_key(mth, path, ai)
        body = (('<span class="tag-ai">AI 서버</span>' if ai else "") + method(mth)
                + f'<code class="path">{html.escape(path)}</code>')
        if rest:
            body += f'<span class="aside">{html.escape(rest.strip("()"))}</span>'
        tag = "a" if key in known else "span"
        href = f' href="#{key}"' if key in known else ""
        out.append(f'<{tag} class="ep"{href}>{body}</{tag}>')
    return "".join(out)


def feature_refs(cell: str, known: set) -> str:
    ids = [x.strip() for x in cell.split("·") if x.strip() and x.strip() != "—"]
    if not ids:
        return '<span class="none">—</span>'
    return ", ".join(f'<a class="fref" href="#f-{i}">{i}</a>' if f"f-{i}" in known else html.escape(i) for i in ids)


def lines(cell: str) -> str:
    """'A · B' 나열을 줄로 나눈다."""
    parts = [p.strip() for p in re.split(r"\s+·\s+", cell) if p.strip()]
    return "<br>".join(inline(p) for p in parts)


def notes_html(notes) -> str:
    rows = "".join(f"<dt>{html.escape(k)}</dt><dd>{inline(v)}</dd>" for k, v in notes)
    return f'<dl class="notes">{rows}</dl>'


def group_head(name: str):
    m = re.match(r"([A-Z])\.\s*(.*)", name)
    return (m.group(1), m.group(2)) if m else ("", name)


def main():
    f_notes, f_groups = parse((HERE / "feature-spec.md").read_text(encoding="utf-8"))
    a_notes, a_groups = parse((HERE / "api-spec.md").read_text(encoding="utf-8"))

    api_keys = {api_key(r[0], r[1].strip("`"), g["name"].startswith("AI")) for g in a_groups for r in g["rows"]}
    feat_keys = {f"f-{r[0]}" for g in f_groups for r in g["rows"]}
    n_feat = sum(len(g["rows"]) for g in f_groups)
    n_api = sum(len(g["rows"]) for g in a_groups if not g["name"].startswith("AI"))
    n_ai = sum(len(g["rows"]) for g in a_groups if g["name"].startswith("AI"))
    pc = {p: sum(1 for g in f_groups for r in g["rows"] if r[3] == p) for p in PRI_NAME}

    # ── 기능 명세 ──
    fp = []
    for g in f_groups:
        letter, gname = group_head(g["name"])
        rows = "".join(
            f'<tr id="f-{r[0]}" data-p="{r[3]}"><th scope="row" class="c-id">{r[0]}</th>'
            f'<td class="c-name">{inline(r[1])}</td><td class="c-desc">{inline(r[2])}</td>'
            f'<td class="c-pri">{meter(r[3])}</td><td class="c-screen">{lines(r[4])}</td>'
            f'<td class="c-api">{api_refs(r[5], api_keys)}</td></tr>' for r in g["rows"])
        fp.append(
            f'<section class="grp"><header class="gh"><span class="gl">{letter}</span><h2>{inline(gname)}</h2>'
            f'<span class="gn">{len(g["rows"])}개</span></header>'
            f'<div class="tw"><table class="ft"><colgroup><col class="w-id"><col class="w-name"><col>'
            f'<col class="w-pri"><col class="w-screen"><col class="w-api"></colgroup>'
            f'<thead><tr><th>ID</th><th>기능명</th><th>설명</th><th>우선순위</th><th>화면</th><th>API</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></div></section>')

    # ── API 명세 ──
    ap = []
    for g in a_groups:
        ai = g["name"].startswith("AI")
        rows = []
        for mth, path, desc, auth, req, resp, fids in g["rows"]:
            p = path.strip("`")
            cls = {"필수": "au-req", "선택": "au-opt", "없음": "au-no"}.get(auth, "au-int")
            rows.append(
                f'<tr id="{api_key(mth, p, ai)}"><td class="c-ep">{method(mth)}<code class="path">{html.escape(p)}</code>'
                f'<span class="ep-desc">{inline(desc)}</span></td>'
                f'<td class="c-auth"><span class="au {cls}">{auth}</span></td>'
                f'<td class="c-req">{inline(req)}</td><td class="c-resp">{inline(resp)}</td>'
                f'<td class="c-fid">{feature_refs(fids, feat_keys)}</td></tr>')
        ap.append(
            f'<section class="grp"><header class="gh"><span class="gl gl-api">{"AI" if ai else ""}</span>'
            f'<h2>{inline(g["name"])}</h2><span class="gn">{len(g["rows"])}개</span></header>'
            f'<div class="tw"><table class="at"><colgroup><col class="w-ep"><col class="w-auth"><col>'
            f'<col class="w-resp"><col class="w-fid"></colgroup>'
            f'<thead><tr><th>엔드포인트</th><th>인증</th><th>요청과 파라미터</th><th>응답</th><th>기능</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table></div></section>')

    page = TEMPLATE
    for k, v in {
        "F_NOTES": notes_html(f_notes), "A_NOTES": notes_html(a_notes), "F_BODY": "".join(fp), "A_BODY": "".join(ap),
        "N_FEAT": n_feat, "N_API": n_api, "N_AI": n_ai, "P0": pc["P0"], "P1": pc["P1"], "P2": pc["P2"],
        "N_GROUPS": len(f_groups), "M_P0": meter("P0"), "M_P1": meter("P1"), "M_P2": meter("P2"),
    }.items():
        page = page.replace("{{" + k + "}}", str(v))
    (HERE / "spec.html").write_text(page, encoding="utf-8")
    print(f"spec.html · 기능 {n_feat} (P0 {pc['P0']} · P1 {pc['P1']} · P2 {pc['P2']}) · API {n_api} + AI {n_ai}")


TEMPLATE = r"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>찾았다 기능 명세서</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans+KR:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
:root {
  --desk: #e9ecf1;
  --paper: #ffffff;
  --ink: #1c2633;
  --ink-2: #3d4a5a;
  --muted: #6b7686;
  --rule: #dde2ea;
  --rule-soft: #eef1f5;
  --head: #f5f7fa;
  --navy: #1d4f91;
  --navy-soft: #e8eef8;
  --sans: "IBM Plex Sans KR", "Apple SD Gothic Neo", sans-serif;
  --mono: "IBM Plex Mono", Menlo, monospace;
  --get: #18794e; --post: #1d5fc4; --put: #a1590a; --patch: #6d45c2; --delete: #c13a2f; --ws: #1b7489;
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
body { margin: 0; background: var(--desk); color: var(--ink); font: 400 14px/1.65 var(--sans); }
a { color: inherit; }
:focus-visible { outline: 2px solid var(--navy); outline-offset: 2px; border-radius: 2px; }

.sheet { max-width: 1400px; margin: 32px auto 64px; background: var(--paper); border-radius: 4px;
  box-shadow: 0 1px 2px rgba(28, 38, 51, .06), 0 8px 28px rgba(28, 38, 51, .07); }

/* 머리 */
.doc-head { display: grid; grid-template-columns: 1fr auto; gap: 32px; align-items: end; padding: 48px 56px 28px;
  border-bottom: 2px solid var(--ink); }
.doc-head .proj { font-size: 15px; font-weight: 600; color: var(--navy); margin: 0 0 6px; }
.doc-head h1 { font-size: 34px; font-weight: 700; line-height: 1.2; letter-spacing: -0.01em; margin: 0; }
.doc-head .basis { color: var(--muted); margin: 10px 0 0; }
.facts { width: auto; table-layout: auto; border-collapse: collapse; font-size: 13px; }
.facts th { text-align: left; font-weight: 500; color: var(--muted); padding: 3px 18px 3px 0; white-space: nowrap; }
.facts td { text-align: right; font-weight: 600; padding: 3px 0; font-variant-numeric: tabular-nums; white-space: nowrap; }
.facts td small { font-weight: 400; color: var(--muted); font-size: 12px; margin-left: 6px; }

/* 도구 줄 */
.tools { position: sticky; top: 0; z-index: 4; background: var(--paper); display: flex; align-items: center; gap: 28px;
  padding: 0 56px; border-bottom: 1px solid var(--rule); }
.tab { appearance: none; border: 0; background: none; font: 600 15px var(--sans); color: var(--muted); padding: 16px 0 14px;
  border-bottom: 2px solid transparent; margin-bottom: -1px; cursor: pointer; }
.tab span { font-weight: 400; margin-left: 4px; }
.tab[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--navy); }
.filter { display: flex; gap: 4px; margin-left: 12px; }
.filter button { appearance: none; border: 1px solid transparent; background: none; font: 500 13px var(--sans);
  color: var(--ink-2); padding: 5px 10px; border-radius: 4px; cursor: pointer; display: inline-flex; align-items: center; gap: 6px; }
.filter button:hover { background: var(--rule-soft); }
.filter button[aria-pressed="true"] { border-color: var(--ink); color: var(--ink); }
.find { margin-left: auto; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid var(--rule); padding: 4px 0; }
.find input { border: 0; outline: 0; font: 400 14px var(--sans); width: 240px; background: none; color: var(--ink); }
.find svg { color: var(--muted); flex: none; }
.find:focus-within { border-bottom-color: var(--navy); }

/* 본문 */
.panel { padding: 28px 56px 56px; }
.panel-title { display: none; font-size: 22px; font-weight: 700; margin: 0 0 16px; }
.notes { display: grid; grid-template-columns: max-content 1fr; gap: 6px 24px; margin: 0 0 40px 72px; padding: 18px 22px;
  background: var(--head); border-radius: 4px; font-size: 13px; color: var(--ink-2); }
.notes dt { font-weight: 600; color: var(--ink); }
.notes dd { margin: 0; }
.notes code { font: 500 12.5px var(--mono); color: var(--ink); }

.grp { display: grid; grid-template-columns: 64px 1fr; column-gap: 8px; margin-bottom: 44px; }
.gh { grid-column: 1 / -1; display: grid; grid-template-columns: 64px auto 1fr; column-gap: 8px; align-items: baseline;
  margin-bottom: 12px; }
.gl { font-size: 44px; font-weight: 700; line-height: 1; color: var(--navy); }
.gl-api { font-size: 15px; font-weight: 600; }
.gh h2 { font-size: 19px; font-weight: 700; margin: 0; }
.gn { color: var(--muted); font-size: 13px; margin-left: 10px; }
.tw { grid-column: 2; overflow-x: auto; }

table { width: 100%; border-collapse: collapse; table-layout: fixed; }
thead th { text-align: left; font-size: 12.5px; font-weight: 600; color: var(--muted); padding: 9px 14px;
  background: var(--head); border-top: 1px solid var(--ink); border-bottom: 1px solid var(--rule); white-space: nowrap; }
tbody th, tbody td { padding: 13px 14px; vertical-align: top; border-bottom: 1px solid var(--rule-soft); text-align: left;
  font-weight: 400; color: var(--ink-2); }
tbody tr:last-child > * { border-bottom: 1px solid var(--rule); }
tbody tr:target > * { background: var(--navy-soft); }

.ft { min-width: 1080px; }
.w-id { width: 58px; } .w-name { width: 168px; } .w-pri { width: 92px; } .w-screen { width: 168px; } .w-api { width: 300px; }
.c-id { font-weight: 700; color: var(--navy); font-variant-numeric: tabular-nums; }
.c-name { font-weight: 600; color: var(--ink); }
.c-desc code { font: 500 12.5px var(--mono); color: var(--ink); }
.c-screen { font-size: 13px; }

.pri { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 600; white-space: nowrap; }
.bars { display: inline-flex; gap: 2px; }
.bars i { width: 6px; height: 12px; border-radius: 1px; background: var(--rule); }
.pri-p0 .bars i.on { background: var(--navy); }
.pri-p1 .bars i.on { background: #5b82bd; }
.pri-p2 .bars i.on { background: #9db3d3; }
.pri-p0 .pt { color: var(--navy); } .pri-p1 .pt { color: #3f669f; } .pri-p2 .pt { color: var(--muted); }

.mt { display: inline-block; width: 52px; flex: none; font: 600 11.5px/1.6 var(--mono); letter-spacing: .02em; }
.mt-get { color: var(--get); } .mt-post { color: var(--post); } .mt-put { color: var(--put); }
.mt-patch { color: var(--patch); } .mt-delete { color: var(--delete); } .mt-ws { color: var(--ws); }
.path { font: 500 13px var(--mono); color: var(--ink); overflow-wrap: anywhere; }
.ep { display: flex; flex-wrap: wrap; align-items: baseline; padding: 2px 0; text-decoration: none; }
a.ep:hover .path { color: var(--navy); text-decoration: underline; text-underline-offset: 3px; }
.ep .aside { flex-basis: 100%; padding-left: 52px; font-size: 12px; color: var(--muted); }
.tag-ai { font-size: 11px; font-weight: 600; color: #a1590a; margin-right: 6px; }
.none { color: var(--muted); font-size: 13px; }
.none code { font: 400 12.5px var(--mono); }

.at { min-width: 1080px; }
.w-ep { width: 330px; } .w-auth { width: 70px; } .w-resp { width: 34%; } .w-fid { width: 92px; }
.c-ep .path { font-weight: 600; }
.ep-desc { display: block; padding-left: 52px; margin-top: 4px; font-size: 13px; color: var(--ink-2); }
.c-req, .c-resp { font-size: 13px; }
.c-req code, .c-resp code { font: 400 12.5px/1.6 var(--mono); color: var(--ink); overflow-wrap: break-word; }
.au { font-size: 13px; font-weight: 600; white-space: nowrap; }
.au-req { color: var(--delete); } .au-opt { color: var(--post); } .au-no { color: var(--muted); font-weight: 500; }
.au-int { color: #a1590a; }
.c-fid { font-size: 13px; }
a.fref { color: var(--navy); font-weight: 600; text-decoration: none; }
a.fref:hover { text-decoration: underline; text-underline-offset: 3px; }

.empty { color: var(--muted); padding: 24px 0 0 72px; }
[hidden] { display: none !important; }
.doc-foot { padding: 20px 56px 28px; border-top: 1px solid var(--rule); color: var(--muted); font-size: 12px; }
.doc-foot code { font-family: var(--mono); }

@media (max-width: 900px) {
  .sheet { margin: 0; border-radius: 0; box-shadow: none; }
  .doc-head { grid-template-columns: 1fr; padding: 28px 16px 20px; }
  .tools { padding: 0 16px; gap: 18px; flex-wrap: wrap; }
  .filter { margin-left: 0; }
  .find { margin-left: 0; width: 100%; } .find input { width: 100%; }
  .panel { padding: 20px 16px 40px; }
  .grp { grid-template-columns: 1fr; }
  .gh { grid-template-columns: auto auto 1fr; column-gap: 10px; }
  .gl { font-size: 28px; }
  .tw { grid-column: 1; }
  .notes { grid-template-columns: 1fr; margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
@media print {
  @page { size: A4 landscape; margin: 11mm 12mm; }
  body { background: #fff; font-size: 10.5px; }
  .sheet { margin: 0; max-width: none; box-shadow: none; }
  .tools, .empty { display: none !important; }
  .doc-head { padding: 0 0 14px; }
  .panel { display: block !important; padding: 18px 0 0; }
  .panel + .panel { break-before: page; }
  .panel-title { display: block; }
  .ft, .at { min-width: 0; }
  .grp { margin-bottom: 22px; }
  .gh { break-after: avoid; }
  tr { break-inside: avoid; }
  thead { display: table-header-group; }
  tbody th, tbody td { padding: 6px 8px; }
  thead th { padding: 5px 8px; }
  .doc-foot { padding: 12px 0 0; }
  a { text-decoration: none !important; }
}
</style>
</head>
<body>
<article class="sheet">
  <header class="doc-head">
    <div>
      <p class="proj">찾았다, 한양대 자취</p>
      <h1>기능 명세서와 API 명세서</h1>
      <p class="basis">2026년 11월 8일 기준으로 frontend, backend, ai-server 코드를 직접 읽고 정리했습니다.</p>
    </div>
    <table class="facts">
      <tr><th>기능</th><td>{{N_FEAT}}개<small>{{N_GROUPS}}개 영역</small></td></tr>
      <tr><th>우선순위</th><td>P0 {{P0}} / P1 {{P1}} / P2 {{P2}}</td></tr>
      <tr><th>백엔드 API</th><td>{{N_API}}개<small>WebSocket 포함</small></td></tr>
      <tr><th>AI 서버 API</th><td>{{N_AI}}개<small>내부 호출</small></td></tr>
    </table>
  </header>

  <nav class="tools" aria-label="문서 도구">
    <div role="tablist" style="display:flex;gap:28px">
      <button class="tab" role="tab" aria-selected="true" aria-controls="p-feat" data-tab="feat">기능 명세<span>{{N_FEAT}}</span></button>
      <button class="tab" role="tab" aria-selected="false" aria-controls="p-api" data-tab="api">API 명세<span>{{N_API}}</span></button>
    </div>
    <div class="filter" id="filter" aria-label="우선순위로 거르기">
      <button aria-pressed="true" data-p="">전체</button>
      <button aria-pressed="false" data-p="P0">{{M_P0}}</button>
      <button aria-pressed="false" data-p="P1">{{M_P1}}</button>
      <button aria-pressed="false" data-p="P2">{{M_P2}}</button>
    </div>
    <label class="find"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input id="q" type="search" placeholder="기능, 경로, 화면으로 찾기" aria-label="찾기"></label>
  </nav>

  <main>
    <section class="panel" id="p-feat" role="tabpanel">
      <h2 class="panel-title">기능 명세</h2>
      {{F_NOTES}}
      {{F_BODY}}
      <p class="empty" id="e-feat" hidden>조건에 맞는 기능이 없습니다. 검색어나 우선순위를 바꿔 보세요.</p>
    </section>
    <section class="panel" id="p-api" role="tabpanel" hidden>
      <h2 class="panel-title">API 명세</h2>
      {{A_NOTES}}
      {{A_BODY}}
      <p class="empty" id="e-api" hidden>조건에 맞는 API 가 없습니다. 검색어를 바꿔 보세요.</p>
    </section>
  </main>
  <footer class="doc-foot">원본은 <code>docs/spec/feature-spec.md</code>, <code>docs/spec/api-spec.md</code> 입니다. 고친 뒤 <code>python3 build.py</code> 로 다시 만듭니다.</footer>
</article>
<script>
(() => {
  const tabs = [...document.querySelectorAll('.tab')];
  const filter = document.getElementById('filter');
  const q = document.getElementById('q');
  let tab = 'feat', pri = '';
  function show(t) {
    tab = t;
    tabs.forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === t)));
    document.getElementById('p-feat').hidden = t !== 'feat';
    document.getElementById('p-api').hidden = t !== 'api';
    filter.hidden = t !== 'feat';
    apply();
  }
  function apply() {
    const s = q.value.trim().toLowerCase();
    const panel = document.getElementById('p-' + tab);
    let any = false;
    panel.querySelectorAll('.grp').forEach(sec => {
      let n = 0;
      sec.querySelectorAll('tbody tr').forEach(tr => {
        const ok = (!s || tr.textContent.toLowerCase().includes(s)) && (tab !== 'feat' || !pri || tr.dataset.p === pri);
        tr.hidden = !ok; if (ok) n++;
      });
      sec.hidden = n === 0; if (n) any = true;
    });
    document.getElementById('e-' + tab).hidden = any;
  }
  function setPri(p) {
    pri = p;
    filter.querySelectorAll('button').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.p === p)));
  }
  tabs.forEach(b => b.addEventListener('click', () => show(b.dataset.tab)));
  filter.addEventListener('click', e => { const b = e.target.closest('button'); if (b) { setPri(b.dataset.p); apply(); } });
  q.addEventListener('input', apply);
  function follow() {
    const id = decodeURIComponent(location.hash.slice(1));
    const el = id && document.getElementById(id);
    if (!el) return;
    q.value = ''; setPri('');
    show(el.closest('#p-api') ? 'api' : 'feat');
    requestAnimationFrame(() => el.scrollIntoView({ block: 'center' }));
  }
  window.addEventListener('hashchange', follow);
  window.addEventListener('beforeprint', () => { q.value = ''; setPri('');
    document.querySelectorAll('.panel [hidden]').forEach(x => { if (!x.classList.contains('empty')) x.hidden = false; }); });
  window.addEventListener('afterprint', () => show(tab));
  follow();
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
