"""05 ERD — Flyway 마이그레이션(backend/.../db/migration/V*.sql)을 읽어 테이블 카드 그림을 만든다.

마이그레이션이 바뀌면 다시 돌리기만 하면 된다 (컬럼·타입·PK·FK·UNIQUE 는 SQL 에서 자동 추출).
도메인 묶음(GROUPS)과 FK 없는 논리 참조(REFS)만 손으로 적는다.

실행:  python3 erd.py      결과: 05-erd.svg, 05-erd.png  (rsvg-convert 필요)
"""
import re
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
MIG = HERE.parents[1] / "backend" / "src" / "main" / "resources" / "db" / "migration"
FONT = "Apple SD Gothic Neo, Pretendard, sans-serif"

# 도메인 묶음 (이름, 색, 테이블들)
GROUPS = [
    ("사용자 · 인증", "#6366f1", ["users", "email_codes", "user_buildings"]),
    ("캠퍼스 · 학과", "#0d9488", ["buildings", "departments", "department_buildings", "walk_cache"]),
    ("매물 · 실거래", "#ea580c", ["listings", "listing_options", "listing_photos", "real_deals"]),
    ("청년안심주택", "#16a34a", ["housing", "housing_unit_types", "housing_floorplan_images", "announcements",
                            "announcement_events", "housing_subscriptions"]),
    ("기숙사", "#0891b2", ["dorms", "dorm_room_types"]),
    ("평면도 (실내 3D)", "#d97706", ["floorplans"]),
    ("양도", "#db2777", ["transfers", "transfer_photos"]),
    ("후기 · 찜", "#9333ea", ["reviews", "favorites"]),
    ("내 집 기록", "#2563eb", ["my_homes", "home_payments", "home_utilities", "home_alerts"]),
    ("알림", "#dc2626", ["notifications"]),
]
# FK 제약 없이 id 만 가리키는 논리 참조
REFS = {
    ("listings", "floorplan_id"): "floorplans", ("housing_unit_types", "floorplan_id"): "floorplans",
    ("dorm_room_types", "floorplan_id"): "floorplans", ("reviews", "floorplan_id"): "floorplans",
    ("walk_cache", "building_id"): "buildings",
    ("favorites", "target_id"): "type별 대상", ("reviews", "target_id"): "type별 대상",
    ("notifications", "target_id"): "type별 대상",
}


# ── SQL 읽기 ─────────────────────────────────────────
def split_top(s: str) -> list[str]:
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]


def norm_type(t: str) -> str:
    t = t.lower()
    return {"double precision": "double"}.get(t, t)


TYPE_RE = re.compile(r"^(\w+)\s+(double precision|\w+(?:\(\d+(?:,\s*\d+)?\))?)(.*)$", re.I | re.S)


def parse_column(table: dict, line: str, version: str):
    m = TYPE_RE.match(line.strip())
    name, typ, rest = m.group(1), norm_type(m.group(2)), m.group(3).lower()
    col = {"name": name, "type": typ, "pk": "primary key" in rest, "uq": bool(re.search(r"\bunique\b", rest)),
           "fk": None, "ref": None, "added": version if table["version"] != version else None}
    fk = re.search(r"references\s+(\w+)", rest)
    if fk:
        col["fk"] = fk.group(1)
    table["cols"].append(col)


def load() -> dict[str, dict]:
    tables: dict[str, dict] = {}
    files = sorted(MIG.glob("V*__*.sql"), key=lambda p: int(re.match(r"V(\d+)", p.name).group(1)))
    for f in files:
        ver = re.match(r"(V\d+)", f.name).group(1)
        sql = re.sub(r"--[^\n]*", "", f.read_text(encoding="utf-8"))
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            m = re.match(r"create table (\w+)\s*\((.*)\)\s*$", stmt, re.I | re.S)
            if m:
                t = {"name": m.group(1), "version": ver, "cols": []}
                tables[t["name"]] = t
                for part in split_top(m.group(2)):
                    low = part.lower()
                    if low.startswith("primary key"):
                        for c in re.findall(r"\w+", part[part.index("(") + 1:part.index(")")]):
                            next(x for x in t["cols"] if x["name"] == c)["pk"] = True
                    elif low.startswith("unique"):
                        for c in re.findall(r"\w+", part[part.index("(") + 1:part.index(")")]):
                            next(x for x in t["cols"] if x["name"] == c)["uq"] = True
                    elif low.startswith(("constraint", "check", "foreign key")):
                        continue
                    else:
                        parse_column(t, part, ver)
                continue
            m = re.match(r"alter table (\w+)\s+(.*)$", stmt, re.I | re.S)
            if m:
                for part in split_top(m.group(2)):
                    am = re.match(r"add column\s+(.*)$", part.strip(), re.I | re.S)
                    if am:
                        parse_column(tables[m.group(1)], am.group(1), ver)
    for (t, c), target in REFS.items():
        next(x for x in tables[t]["cols"] if x["name"] == c)["ref"] = target
    return tables


# ── 그리기 ───────────────────────────────────────────
CARD_W, HEAD_H, ROW_H, GAP, COL_GAP = 360, 38, 25, 26, 34
GROUP_HEAD = 46
out: list[str] = []


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size=15, color="#1f2937", weight=400, anchor="start", family=None):
    fam = f' font-family="{family}"' if family else ""
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color}" '
               f'text-anchor="{anchor}"{fam}>{esc(s)}</text>')


BADGE = {"PK": ("#fef3c7", "#b45309"), "FK": ("#dbeafe", "#1d4ed8"), "UQ": ("#dcfce7", "#15803d"),
         "REF": ("#f1f5f9", "#64748b")}
MONO = "SF Mono, Menlo, monospace"


def badge(x, y, kind):
    bg, fg = BADGE[kind]
    w = 34 if kind == "REF" else 26
    out.append(f'<rect x="{x}" y="{y - 13}" width="{w}" height="17" rx="4" fill="{bg}"/>')
    text(x + w / 2, y, kind, size=11, color=fg, weight=700, anchor="middle")
    return w


def card_height(t) -> int:
    return HEAD_H + len(t["cols"]) * ROW_H + 12


def card(x, y, t, color):
    h = card_height(t)
    out.append(f'<rect x="{x + 2}" y="{y + 3}" width="{CARD_W}" height="{h}" rx="9" fill="#0f172a" opacity="0.06"/>')
    out.append(f'<rect x="{x}" y="{y}" width="{CARD_W}" height="{h}" rx="9" fill="white" stroke="#e2e8f0"/>')
    out.append(f'<path d="M{x},{y + 9} a9,9 0 0 1 9,-9 h{CARD_W - 18} a9,9 0 0 1 9,9 v{HEAD_H - 9} h-{CARD_W} z" '
               f'fill="{color}"/>')
    text(x + 14, y + 25, t["name"], size=17, color="white", weight=700, family=MONO)
    pill = t["version"]
    out.append(f'<rect x="{x + CARD_W - 50}" y="{y + 10}" width="38" height="19" rx="9.5" fill="white" '
               f'opacity="0.9"/>')
    text(x + CARD_W - 31, y + 24, pill, size=12, color=color, weight=700, anchor="middle")
    for i, c in enumerate(t["cols"]):
        ry = y + HEAD_H + i * ROW_H + 19
        if i % 2 == 1:
            out.append(f'<rect x="{x + 1}" y="{ry - 17}" width="{CARD_W - 2}" height="{ROW_H}" fill="#f8fafc"/>')
        text(x + 14, ry, c["name"], size=14.5, color="#0f172a", weight=700 if c["pk"] else 400, family=MONO)
        # 오른쪽: 배지들, 그 왼쪽에 타입(또는 참조 대상)
        kinds = [k for k, on in (("PK", c["pk"]), ("FK", c["fk"]), ("UQ", c["uq"] and not c["pk"]),
                                 ("REF", c["ref"])) if on]
        bx = x + CARD_W - 12
        for k in reversed(kinds):
            bx -= (34 if k == "REF" else 26)
            badge(bx, ry, k)
            bx -= 4
        if c["fk"]:
            label, col = f'→ {c["fk"]}', "#1d4ed8"
        elif c["ref"]:
            label, col = f'→ {c["ref"]}', "#64748b"
        else:
            label, col = c["type"], "#94a3b8"
        text(bx - 6, ry, label, size=13, color=col, anchor="end", family=MONO)
        if c["added"]:
            text(x + 14 + len(c["name"]) * 8.9 + 8, ry, f'+{c["added"]}', size=11, color="#94a3b8")
    return h


def main():
    tables = load()
    grouped = {n for _, _, ts in GROUPS for n in ts}
    missing = set(tables) - grouped
    assert not missing, f"GROUPS 에 없는 테이블: {missing}"

    n_cols = 6
    col_h = [0] * n_cols
    placed = []  # (col, y, kind, payload)
    top = 150
    for gname, color, names in GROUPS:
        gh = GROUP_HEAD + sum(card_height(tables[n]) + GAP for n in names)
        c = min(range(n_cols), key=lambda i: col_h[i])
        y = top + col_h[c]
        placed.append((c, y, "group", (gname, color, len(names))))
        y += GROUP_HEAD
        for n in names:
            placed.append((c, y, "card", (tables[n], color)))
            y += card_height(tables[n]) + GAP
        col_h[c] += gh + 18

    left = 70
    width = left * 2 + n_cols * CARD_W + (n_cols - 1) * COL_GAP
    height = top + max(col_h) + 40
    # 바탕 영역 (예시의 DB 박스)
    out.append(f'<rect x="30" y="30" width="{width - 60}" height="{height - 50}" rx="22" fill="#f8fafc" '
               f'stroke="#cbd5e1" stroke-width="1.5"/>')
    text(62, 76, "POSTGRESQL 16 · CHATATDA  (Railway)", size=20, color="#334155", weight=700)
    n_cols_total = sum(len(t["cols"]) for t in tables.values())
    text(62, 108, f"테이블 {len(tables)}개 · 컬럼 {n_cols_total}개 · Flyway V1~V11", size=16, color="#64748b")
    # 범례
    for lx, k, desc in ((width - 742, "PK", "기본 키"), (width - 630, "FK", "외래 키 (→ 대상 테이블)"),
                        (width - 410, "UQ", "UNIQUE"), (width - 290, "REF", "논리 참조 (FK 없음)")):
        w = badge(lx, 98, k)
        text(lx + w + 8, 98, desc, size=14, color="#475569")
    text(width - 62, 70, "Vn = 처음 만든 마이그레이션 · +Vn = 나중에 추가된 컬럼", size=14, color="#94a3b8", anchor="end")

    for c, y, kind, payload in placed:
        x = left + c * (CARD_W + COL_GAP)
        if kind == "group":
            gname, color, cnt = payload
            out.append(f'<rect x="{x}" y="{y + 10}" width="12" height="12" rx="3" fill="{color}"/>')
            out.append(f'<text x="{x + 20}" y="{y + 21}" font-size="17" font-weight="700" fill="{color}">'
                       f'{esc(gname)}<tspan dx="8" font-size="15" font-weight="400" fill="#94a3b8">({cnt})</tspan>'
                       f'</text>')
        else:
            card(x, y, *payload)

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="{FONT}"><rect width="{width}" height="{height}" '
           f'fill="white"/>' + "\n".join(out) + "</svg>")
    (HERE / "05-erd.svg").write_text(svg, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-z", "2", str(HERE / "05-erd.svg"), "-o", str(HERE / "05-erd.png")], check=True)
    print(f"05-erd: 테이블 {len(tables)} · 컬럼 {n_cols_total} · {width}x{height}")


if __name__ == "__main__":
    main()
