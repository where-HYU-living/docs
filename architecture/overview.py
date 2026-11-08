"""04 종합 아키텍처 — 좌표를 직접 잡은 SVG (16:9 슬라이드용).

01 서비스 구성도를 뼈대로, AI 서버 안에 02(평면도)·03(적정 월세) 파이프라인을 펼쳐 넣었다.
  위 줄   : 모델 학습 · 모델 저장소
  가운데 줄: 사용자 → Vercel → Railway(Backend · AI Server · DB)
  아래 줄 : campus-data · 외부 API · 범례

실행:  python3 overview.py   (rsvg-convert 필요: brew install librsvg — graphviz 설치 때 같이 깔림)
결과:  04-overview.svg, 04-overview.png
"""
import base64
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ICON = HERE / "icons"
W, H = 3200, 1820
FONT = "Apple SD Gothic Neo, Pretendard, sans-serif"

C = {
    "ink": "#1f2937", "muted": "#64748b",
    "vercel": ("#111827", "#f8fafc"), "railway": ("#7c3aed", "#faf5ff"),
    "back": ("#15803d", "#f0fdf4"), "ai": ("#c2410c", "#fff7ed"), "sub": ("#b45309", "#ffffff"),
    "db": ("#1d4ed8", "#eff6ff"), "ext": ("#64748b", "#f8fafc"), "hf": ("#b45309", "#fffbeb"),
    "off": ("#94a3b8", "#ffffff"),
    "blue": "#2563eb", "purple": "#7c3aed", "orange": "#c2410c", "gray": "#94a3b8", "dark": "#475569",
}

out: list[str] = []
_icons: dict[str, str] = {}


def esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def icon_uri(name: str) -> str:
    if name not in _icons:
        _icons[name] = "data:image/png;base64," + base64.b64encode((ICON / f"{name}.png").read_bytes()).decode()
    return _icons[name]


def text(x, y, s, size=20, color=None, weight=400, anchor="middle", halo=False):
    h = ' stroke="white" stroke-width="7" stroke-linejoin="round" paint-order="stroke"' if halo else ""
    out.append(f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" fill="{color or C["ink"]}" '
               f'text-anchor="{anchor}"{h}>{esc(s)}</text>')


def box(x1, y1, x2, y2, title, col, sub=None, dashed=False, size=22):
    stroke, fill = col
    d = ' stroke-dasharray="10 7"' if dashed else ""
    out.append(f'<rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" rx="14" fill="{fill}" '
               f'stroke="{stroke}" stroke-width="2.4"{d}/>')
    text(x1 + 18, y1 + 32, title, size=size, color=stroke, weight=600, anchor="start")
    if sub:
        text(x1 + 18, y1 + 32 + size + 4, sub, size=size - 4, color=stroke, anchor="start")


def node(x, y, icon, lines, s=84, size=19):
    out.append(f'<image x="{x - s / 2}" y="{y - s / 2}" width="{s}" height="{s}" href="{icon_uri(icon)}" '
               f'preserveAspectRatio="xMidYMid meet"/>')
    for i, ln in enumerate(lines):
        text(x, y + s / 2 + 24 + i * 24, ln, size=size, weight=600 if i == 0 else 400,
             color=C["ink"] if i == 0 else "#374151")


def arrow(pts, color, kind="solid", width=3.0, label=None, at=None, anchor="middle", lsize=18):
    dash = {"solid": "", "dashed": ' stroke-dasharray="11 8"', "dotted": ' stroke-dasharray="3 7"'}[kind]
    d = "M" + " L".join(f"{x},{y}" for x, y in pts)
    mid = color.lstrip("#")
    out.append(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linejoin="round" '
               f'stroke-linecap="round"{dash} marker-end="url(#m{mid})"/>')
    if label:
        lx, ly = at
        text(lx, ly, label, size=lsize, color=color if color != C["gray"] else C["dark"], anchor=anchor,
             halo=True, weight=500)


# ── 머리 ──────────────────────────────────────────────
# ── 위 줄: 모델 학습 · 모델 저장소 ─────────────────────
box(1480, 100, 2560, 278, "적정 월세 모델 학습 (로컬)", C["off"], dashed=True, size=20)
node(1700, 186, "l-file-spreadsheet", ["국토부 실거래 + 동 단위 피처"], s=64)
node(2240, 186, "scikitlearn", ["train_rent.py · GBM 분위 회귀"], s=64)
box(2620, 100, 3160, 278, "모델 저장소", C["hf"], size=20)
node(2770, 180, "huggingface", ["Hugging Face", "chatatda-models"], s=64)
node(3010, 180, "github", ["GitHub", "CubiCasa5K 코드"], s=64)

# ── 가운데 줄 ─────────────────────────────────────────
node(200, 475, "users", ["사용자", "웹 브라우저"])

box(60, 640, 340, 1240, "브라우저 SDK", C["ext"], size=20)
node(200, 790, "kakao", ["Kakao Maps", "JS SDK"], s=76)
node(200, 1060, "google", ["Google 로그인", "(Identity Services)"], s=76)

box(400, 340, 860, 1240, "Vercel", C["vercel"], sub="where-hyu-living.xyz")
node(630, 475, "react", ["React 18 SPA", "Vite 6 · TypeScript 5", "TanStack Query · Zustand"])
node(630, 800, "threedotjs", ["3D 캠퍼스 · 동네 · 실내", "three.js 0.180 · R3F 8"])
node(630, 1100, "l-file-json", ["정적 데이터 (CDN)", "world.json · 동네 12곳"])

box(920, 300, 3160, 1420, "Railway", C["railway"], size=24)

box(960, 340, 1360, 1390, "Backend", C["back"], sub="Spring Boot 3.5 · Java 21")
node(1160, 475, "springboot", ["REST API /api/v1", "Security + JWT", "Caffeine · Swagger"])
node(1160, 800, "l-monitor-smartphone", ["WebSocket /ws/world", "멀티플레이 (최대 30명)"])
node(1160, 1110, "l-clock", ["스케줄러", "06시 청년주택 수집", "09시 알림"])

box(1480, 1150, 2140, 1390, "Database · Storage", C["db"], size=20)
node(1660, 1250, "postgresql", ["PostgreSQL 16", "Flyway V1~V11"], s=76)
node(1960, 1250, "l-hard-drive", ["양도 사진", "서버 저장소"], s=76)

box(1480, 340, 3120, 1115, "AI Server  ·  FastAPI · Python 3.11 · Docker", C["ai"], size=24)
#   평면도 AI
box(1510, 400, 3090, 895, "평면도 AI   /v1/floorplan", C["sub"], size=19)
node(1650, 520, "l-images", ["루트 A", "평면도 이미지"], s=76)
node(1960, 520, "pytorch", ["CubiCasa5K 분할", "방 12종 · 아이콘 11종"], s=76)
node(2280, 520, "opencv", ["벡터화 · 문·창 배치", "OpenCV · Shapely"], s=76)
node(1960, 680, "paddlepaddle", ["PaddleOCR", "한국어 방 이름"], s=60)
node(1650, 800, "l-file-spreadsheet", ["루트 B", "면적 · 방 수"], s=64)
node(1960, 800, "l-layout-template", ["템플릿 33종", "선택 · 스케일"], s=64)
node(2640, 680, "l-check-check", ["보정 · 검수", "/validate"], s=76)
node(2940, 680, "l-file-json", ["FloorPlan JSON", "→ 실내 3D 방 투어"], s=76)
#   적정 월세 AI
box(1510, 915, 3090, 1100, "적정 월세 AI   /v1/rent/estimate", C["sub"], size=19)
node(1650, 1000, "l-map-pinned", ["동 · 면적 · 층 · 연식", "계약 시점"], s=60)
node(1990, 1000, "l-file-spreadsheet", ["동 단위 피처 결합", "사자상 · 지하철 · 버스"], s=60)
node(2340, 1000, "scikitlearn", ["HistGradientBoosting", "분위 회귀 25 · 50 · 75%"], s=60)
node(2700, 1000, "l-landmark", ["적정 월세 + 범위", "→ 판결 등급"], s=60)

# ── 아래 줄 ───────────────────────────────────────────
box(40, 1470, 860, 1780, "campus-data · 3D 월드 데이터 (로컬)", C["off"], dashed=True, size=20)
node(150, 1560, "openstreetmap", ["OpenStreetMap"], s=56)
node(150, 1690, "l-mountain", ["수치지도 · 건축물대장"], s=56)
node(470, 1625, "l-shapes", ["build-world.mjs", "월드 JSON 생성"], s=64)

box(920, 1470, 2320, 1780, "외부 API", C["ext"], size=20)
for x, ic, lb in [(1060, "l-landmark", ["국토교통부", "실거래가"]), (1330, "l-building-2", ["서울시 청년안심주택", "(크롤링)"]),
                  (1600, "l-footprints", ["TMAP", "보행자 경로"]), (1870, "kakao", ["카카오 로컬 API", "주소 · 좌표"]),
                  (2140, "google", ["Google OAuth", "ID 토큰 검증"])]:
    node(x, 1600, ic, lb, s=72)

box(2380, 1470, 3160, 1780, "범례", C["ext"], size=20)
for i, (col, kind, lb) in enumerate([(C["blue"], "solid", "사용자 요청 (HTTPS · REST)"),
                                     (C["purple"], "solid", "WebSocket (실시간 멀티플레이)"),
                                     (C["orange"], "solid", "AI 호출 (백엔드 → AI 서버)"),
                                     (C["dark"], "solid", "DB · 외부 API"),
                                     (C["gray"], "dashed", "빌드 · 데이터 준비 (실행 중 아님)")]):
    y = 1530 + i * 50
    arrow([(2420, y), (2540, y)], col, kind)
    text(2565, y + 6, lb, size=19, anchor="start")

# ── 선 ────────────────────────────────────────────────
B, P, O, G, D = C["blue"], C["purple"], C["orange"], C["gray"], C["dark"]
# 사용자 · 프론트
arrow([(250, 475), (578, 475)], B, label="HTTPS", at=(330, 460))
arrow([(630, 595), (630, 748)], G, "dotted", width=2.4)
arrow([(630, 1052), (630, 905)], G, "dotted", width=2.4, label="로드", at=(660, 990), anchor="start")
arrow([(586, 500), (470, 500), (470, 920), (348, 920)], G, "dotted", width=2.4, label="SDK", at=(480, 700),
      anchor="start")
# 프론트 → 백엔드
arrow([(684, 475), (1108, 475)], B, label="REST (JSON)", at=(890, 458))
arrow([(684, 800), (1108, 800)], P, label="WebSocket", at=(890, 783))
# 백엔드 → AI
arrow([(1212, 475), (1602, 520)], O, label="평면도 이미지", at=(1420, 468))
arrow([(1212, 500), (1300, 500), (1300, 800), (1608, 800)], O, label="면적 · 방 수", at=(1420, 788))
arrow([(1300, 800), (1300, 1000), (1608, 1000)], O, label="적정가 요청", at=(1420, 988))
# 백엔드 → DB
arrow([(1360, 1250), (1610, 1250)], D, label="JPA", at=(1420, 1238))
# 평면도 AI 내부
arrow([(1690, 520), (1912, 520)], D, width=2.4)
arrow([(2000, 520), (2232, 520)], D, width=2.4)
arrow([(2320, 520), (2640, 520), (2640, 632)], D, width=2.4)
arrow([(1690, 548), (1925, 672)], D, width=2.4)
arrow([(1992, 680), (2594, 680)], D, width=2.4, label="방 이름", at=(2290, 668))
arrow([(1694, 800), (1918, 800)], D, width=2.4)
arrow([(2004, 800), (2540, 800), (2540, 712), (2594, 712)], D, width=2.4)
arrow([(2686, 680), (2892, 680)], D, width=2.4)
# 적정 월세 AI 내부
arrow([(1682, 1000), (1952, 1000)], D, width=2.4)
arrow([(2022, 1000), (2302, 1000)], D, width=2.4)
arrow([(2372, 1000), (2662, 1000)], D, width=2.4)
# 학습 · 모델 저장소
arrow([(1736, 186), (2200, 186)], G, "dashed", width=2.4)
arrow([(2276, 186), (2730, 180)], G, "dashed", width=2.4, label="hf upload", at=(2440, 170))
arrow([(2770, 262), (2770, 396)], G, "dashed", width=2.6, label="빌드 시 가중치 다운로드", at=(2786, 330),
      anchor="start")
arrow([(3010, 262), (3010, 396)], G, "dashed", width=2.6)
# 백엔드 → 외부 API
arrow([(1160, 1390), (1160, 1466)], D, label="외부 API 호출 · 청년주택 수집", at=(1176, 1446), anchor="start")
# campus-data → 정적 데이터
arrow([(182, 1560), (432, 1612)], G, "dashed", width=2.2)
arrow([(182, 1690), (432, 1640)], G, "dashed", width=2.2)
arrow([(506, 1625), (760, 1625), (760, 1100), (682, 1100)], G, "dashed", width=2.6, label="public 복사",
      at=(774, 1400), anchor="start")

# ── 조립 ──────────────────────────────────────────────
markers = "".join(
    f'<marker id="m{c.lstrip("#")}" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="5.5" markerHeight="5.5" '
    f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
    for c in {B, P, O, G, D})
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
       f'font-family="{FONT}"><defs>{markers}</defs><rect width="{W}" height="{H}" fill="white"/>'
       + "\n".join(out) + "</svg>")
(HERE / "04-overview.svg").write_text(svg, encoding="utf-8")
subprocess.run(["rsvg-convert", "-z", "1.5", str(HERE / "04-overview.svg"), "-o", str(HERE / "04-overview.png")],
               check=True)
print("04-overview.svg / 04-overview.png")
