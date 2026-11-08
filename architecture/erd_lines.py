"""06 ERD 관계선 버전 — erd.py 의 마이그레이션 파싱·카드 그리기를 그대로 쓰고, 선만 직접 배치한다.

선은 열 사이 통로(gutter)와 맨 위 통로로만 다닌다 → 테이블 카드 위로 지나가지 않는다.
같은 통로의 선은 차선을 나누고, 교차가 적어지는 순서로 차선을 정한다.
  실선(그룹 색) = FK 제약 · 회색 점선 = 논리 참조(FK 없음)
  자식 쪽 까마귀발(N) · 부모 쪽 ─┤(1)

실행:  python3 erd_lines.py      결과: 06-erd-relations.svg / .png  (rsvg-convert 필요)
"""
import subprocess

import erd
from erd import GROUPS, HERE, esc, load

erd.CARD_W = 330
W = erd.CARD_W
GW = 130          # 열 사이 통로 폭
LANE = 13         # 차선 간격
LEFT, TOP = 60, 250
VGAP = 30

# 열 배치: 연결된 테이블이 옆 열에 오도록 (users 가 허브)
COLUMNS = [
    ["my_homes", "home_payments", "home_utilities", "home_alerts", "notifications", "user_buildings"],
    ["users", "departments", "department_buildings", "buildings", "walk_cache", "email_codes"],
    ["reviews", "favorites", "housing_subscriptions", "transfers"],
    ["housing", "transfer_photos"],
    ["housing_unit_types", "housing_floorplan_images", "announcements", "announcement_events"],
    ["floorplans", "listings"],
    ["listing_options", "listing_photos", "dorm_room_types", "dorms", "real_deals"],
]
# 세로 위치 맞춤: 이 테이블은 최소 이 y 부터 (선이 짧아지게)
MIN_Y = {"transfer_photos": "transfers", "dorms": None}

out = erd.out
COLOR = {n: c for _, c, ns in GROUPS for n in ns}
GROUP_OF = {n: g for g, _, ns in GROUPS for n in ns}


def row_y(pos, t, col):
    i = next(k for k, c in enumerate(t["cols"]) if c["name"] == col)
    return pos[t["name"]][1] + erd.HEAD_H + i * erd.ROW_H + 14.5


def rounded(pts, r=9):
    """직각 꺾임을 둥글게."""
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        (x0, y0), (x1, y1), (x2, y2) = pts[i - 1], pts[i], pts[i + 1]
        l1 = max(abs(x1 - x0), abs(y1 - y0))
        l2 = max(abs(x2 - x1), abs(y2 - y1))
        rr = min(r, l1 / 2, l2 / 2)
        if rr < 1:
            d += f" L{x1:.1f},{y1:.1f}"
            continue
        ax = x1 - (rr if x1 > x0 else -rr if x1 < x0 else 0)
        ay = y1 - (rr if y1 > y0 else -rr if y1 < y0 else 0)
        bx = x1 + (rr if x2 > x1 else -rr if x2 < x1 else 0)
        by = y1 + (rr if y2 > y1 else -rr if y2 < y1 else 0)
        d += f" L{ax:.1f},{ay:.1f} Q{x1:.1f},{y1:.1f} {bx:.1f},{by:.1f}"
    d += f" L{pts[-1][0]:.1f},{pts[-1][1]:.1f}"
    return d


def crow(x, y, d, color):
    """자식 쪽 N: 카드 테두리(x,y)에서 바깥(d=+1 오른쪽, -1 왼쪽)으로."""
    tip = x + d * 15
    out.append(f'<path d="M{tip},{y} L{x},{y - 7} M{tip},{y} L{x},{y} M{tip},{y} L{x},{y + 7}" '
               f'stroke="{color}" stroke-width="2" fill="none" stroke-linecap="round"/>')


def tee(x, y, d, color):
    bx = x + d * 9
    out.append(f'<path d="M{bx},{y - 7} L{bx},{y + 7}" stroke="{color}" stroke-width="2.4" stroke-linecap="round"/>')


def main():
    tables = load()
    assert sorted(n for c in COLUMNS for n in c) == sorted(tables), "COLUMNS 와 테이블 목록이 다름"

    # ── 카드 위치 ──
    pos = {}
    for ci, names in enumerate(COLUMNS):
        x = LEFT + ci * (W + GW)
        y = TOP
        for n in names:
            anchor = MIN_Y.get(n)
            if anchor and anchor in pos:
                y = max(y, pos[anchor][1])
            pos[n] = (x, y, ci)
            y += erd.card_height(tables[n]) + VGAP
    col_of = {n: p[2] for n, p in pos.items()}
    width = LEFT * 2 + len(COLUMNS) * W + (len(COLUMNS) - 1) * GW
    height = max(p[1] + erd.card_height(tables[n]) for n, p in pos.items()) + 60

    # ── 선 목록 ──
    edges = []
    for n, t in tables.items():
        for c in t["cols"]:
            target = c["fk"] or (c["ref"] if c["ref"] in tables else None)
            if target:
                pk = next(x["name"] for x in tables[target]["cols"] if x["pk"])
                edges.append({"child": n, "col": c["name"], "parent": target, "pk": pk, "ref": bool(c["ref"])})

    # 통로별 반쪽 선(segment): gutter g 는 열 g 와 g+1 사이. side: 'L'=왼쪽 열 카드, 'R'=오른쪽 열 카드, 'T'=맨 위 통로
    CH_Y = TOP - 48
    segs: dict[int, list] = {}

    def add(g, e, a, b):
        segs.setdefault(g, []).append({"e": e, "a": a, "b": b})  # a,b = (side, y)

    for e in edges:
        cc, cp = col_of[e["child"]], col_of[e["parent"]]
        yc = row_y(pos, tables[e["child"]], e["col"])
        yp = row_y(pos, tables[e["parent"]], e["pk"])
        e["yc"], e["yp"] = yc, yp
        if cp == cc + 1:
            add(cc, e, ("L", yc), ("R", yp)); e["route"] = [("seg", cc)]
        elif cp == cc - 1:
            add(cp, e, ("R", yc), ("L", yp)); e["route"] = [("seg", cp)]
        elif cp == cc:
            g = cc if cc < len(COLUMNS) - 1 else cc - 1
            side = "L" if g == cc else "R"
            add(g, e, (side, yc), (side, yp)); e["route"] = [("seg", g)]
        else:  # 먼 열: 맨 위 통로로 넘어간다
            step = 1 if cp > cc else -1
            g1 = cc if step == 1 else cc - 1
            g2 = cp - 1 if step == 1 else cp
            add(g1, e, ("L" if step == 1 else "R", yc), ("T", CH_Y))
            add(g2, e, ("T", CH_Y), ("R" if step == 1 else "L", yp))
            e["route"] = [("seg", g1), ("seg", g2)]

    # ── 차선 정하기: 교차 수가 줄어드는 쪽으로 이웃 교환 ──
    def crossings(order, g):
        gl = LEFT + g * (W + GW) + W
        n = len(order)
        xs = {id(s): gl + GW / 2 + (i - (n - 1) / 2) * LANE for i, s in enumerate(order)}
        cnt = 0
        for s in order:
            for f in order:
                if s is f:
                    continue
                fx = xs[id(f)]
                fy0, fy1 = sorted((f["a"][1], f["b"][1]))
                for side, y in (s["a"], s["b"]):
                    if side == "T":
                        continue
                    x0, x1 = (gl, xs[id(s)]) if side == "L" else (xs[id(s)], gl + GW)
                    if x0 < fx < x1 and fy0 < y < fy1:
                        cnt += 1
        return cnt

    lane_x = {}
    for g, lst in segs.items():
        order = sorted(lst, key=lambda s: (s["a"][1] + s["b"][1]) / 2)
        best = crossings(order, g)
        improved = True
        while improved:
            improved = False
            for i in range(len(order) - 1):
                cand = order[:i] + [order[i + 1], order[i]] + order[i + 2:]
                c = crossings(cand, g)
                if c < best:
                    order, best, improved = cand, c, True
        gl = LEFT + g * (W + GW) + W
        for i, s in enumerate(order):
            lane_x[id(s)] = gl + GW / 2 + (i - (len(order) - 1) / 2) * LANE

    # ── 바탕 · 머리 ──
    out.append(f'<rect x="24" y="24" width="{width - 48}" height="{height - 40}" rx="22" fill="#f8fafc" '
               f'stroke="#cbd5e1" stroke-width="1.5"/>')
    erd.text(56, 72, "POSTGRESQL 16 · CHATATDA — 테이블 관계도", size=22, color="#334155", weight=700)
    n_fk = sum(not e["ref"] for e in edges)
    n_ref = sum(e["ref"] for e in edges)
    erd.text(56, 104, f"테이블 {len(tables)}개 · FK {n_fk}개(실선) · 논리 참조 {n_ref}개(점선) · "
                      f"찜·후기·알림의 target_id 는 type 따라 대상이 달라 선 생략", size=15, color="#64748b")
    # 그룹 색 칩
    gx = 56
    for gname, color, names in GROUPS:
        out.append(f'<rect x="{gx}" y="134" width="14" height="14" rx="3" fill="{color}"/>')
        erd.text(gx + 20, 146, gname, size=15, color="#334155", weight=600)
        gx += 48 + sum(15 if "\uac00" <= ch <= "\ud7a3" else 4.5 if ch in " ·" else 8.5 for ch in gname)
    # 기호 설명
    lx = width - 520
    out.append(f'<path d="M{lx},{140} L{lx + 70},{140}" stroke="#475569" stroke-width="2"/>')
    crow(lx, 140, 1, "#475569")
    tee(lx + 70, 140, -1, "#475569")
    erd.text(lx + 84, 146, "N : 1 (FK)", size=15, color="#334155")
    lx += 200
    out.append(f'<path d="M{lx},{140} L{lx + 70},{140}" stroke="#94a3b8" stroke-width="2" stroke-dasharray="7 5"/>')
    erd.text(lx + 84, 146, "논리 참조 (FK 없음)", size=15, color="#334155")

    # ── 카드 ──
    for n, (x, y, _) in pos.items():
        erd.card(x, y, tables[n], COLOR[n])

    # ── 선 ──
    for e in edges:
        color = "#94a3b8" if e["ref"] else COLOR[e["child"]]
        dash = ' stroke-dasharray="8 6"' if e["ref"] else ""
        cx, cy, cc = pos[e["child"]]
        px, py, pc = pos[e["parent"]]
        seg_list = [s for g in (r[1] for r in e["route"]) for s in segs[g] if s["e"] is e]
        pts = []
        # 자식 쪽 시작점
        s0 = seg_list[0]
        side0 = s0["a"][0]
        start_x = cx + W if side0 == "L" else cx
        d0 = 1 if side0 == "L" else -1
        pts.append((start_x, e["yc"]))
        for s in seg_list:
            lx_ = lane_x[id(s)]
            pts.append((lx_, s["a"][1]))
            pts.append((lx_, s["b"][1]))
        sl = seg_list[-1]
        side1 = sl["b"][0]
        end_x = px if side1 == "R" else px + W
        d1 = -1 if side1 == "R" else 1
        pts.append((end_x, e["yp"]))
        # 같은 점 연속 제거
        clean = [pts[0]]
        for p in pts[1:]:
            if abs(p[0] - clean[-1][0]) > 0.1 or abs(p[1] - clean[-1][1]) > 0.1:
                clean.append(p)
        out.append(f'<path d="{rounded(clean)}" fill="none" stroke="{color}" stroke-width="2.2" '
                   f'stroke-linejoin="round" opacity="0.9"{dash}/>')
        crow(start_x, e["yc"], d0, color)
        tee(end_x, e["yp"], d1, color)

    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'viewBox="0 0 {width} {height}" font-family="{erd.FONT}"><rect width="{width}" height="{height}" '
           f'fill="white"/>' + "\n".join(out) + "</svg>")
    (HERE / "06-erd-relations.svg").write_text(svg, encoding="utf-8")
    subprocess.run(["rsvg-convert", "-z", "2", str(HERE / "06-erd-relations.svg"), "-o",
                    str(HERE / "06-erd-relations.png")], check=True)
    print(f"06-erd-relations: {width}x{height} · FK {n_fk} · REF {n_ref}")


if __name__ == "__main__":
    main()
