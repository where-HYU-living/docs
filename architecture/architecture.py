"""찾았다, 한양대 자취 — 아키텍처 그림 2장 (mingrammer/diagrams).

실행:  <venv>/bin/python architecture.py   (Graphviz `dot` 필요: brew install graphviz)
결과:  01-service-architecture.png, 02-ai-pipeline.png
아이콘: icons/ (Simple Icons 브랜드 로고 + Lucide 일반 아이콘, PNG 변환본)
"""
from pathlib import Path

from diagrams import Cluster, Diagram, Edge
from diagrams.custom import Custom
from diagrams.onprem.client import Users
from diagrams.onprem.database import Postgresql

HERE = Path(__file__).resolve().parent
ICON = HERE / "icons"
FONT = "Apple SD Gothic Neo"


def I(name: str) -> str:
    return str(ICON / f"{name}.png")


GRAPH = {
    "fontname": FONT, "fontsize": "28", "labelloc": "t", "pad": "0.6",
    "nodesep": "0.55", "ranksep": "1.1", "splines": "spline", "dpi": "180",
    "bgcolor": "white",
}
NODE = {"fontname": FONT, "fontsize": "13", "fontcolor": "#1f2937"}
EDGE = {"fontname": FONT, "fontsize": "11", "color": "#475569", "fontcolor": "#334155", "penwidth": "1.4"}


def box(color: str, fill: str, dashed: bool = False, size: str = "16") -> dict:
    """첨부 예시처럼 색 테두리 + 옅은 바탕 + 왼쪽 위 제목."""
    return {
        "fontname": FONT, "fontsize": size, "fontcolor": color, "labeljust": "l",
        "pencolor": color, "bgcolor": fill, "penwidth": "1.8",
        "style": "dashed,rounded" if dashed else "rounded", "margin": "18",
    }


# 색 (클라우드별)
VERCEL = ("#111827", "#f8fafc")
RAILWAY = ("#7c3aed", "#faf5ff")
BACK = ("#15803d", "#f0fdf4")
AI = ("#c2410c", "#fff7ed")
DB = ("#1d4ed8", "#eff6ff")
EXT = ("#64748b", "#f8fafc")
HF = ("#b45309", "#fffbeb")
OFF = ("#94a3b8", "#ffffff")

REST = Edge(color="#2563eb", penwidth="2.0")          # 실시간 요청
BUILD = dict(style="dashed", color="#94a3b8")           # 빌드·데이터 준비 (실행 중 아님)


# ─────────────────────────────────────────────────────────────
# 1. 서비스 아키텍처
# ─────────────────────────────────────────────────────────────
with Diagram("찾았다, 한양대 자취 — 서비스 아키텍처", filename=str(HERE / "01-service-architecture"),
             show=False, direction="TB", outformat="png", graph_attr={**GRAPH, "nodesep": "0.8", "ranksep": "0.9", "compound": "true"}, node_attr=NODE, edge_attr=EDGE):

    user = Users("사용자\n(웹 브라우저)")

    with Cluster("브라우저 SDK", graph_attr=box(*EXT, size="13")):
        kakao_sdk = Custom("Kakao Maps JS SDK\n지도·주소 검색", I("kakao"))
        gsi = Custom("Google Identity\nServices (로그인)", I("google"))

    with Cluster("Vercel  ·  where-hyu-living.xyz", graph_attr=box(*VERCEL)):
        spa = Custom("React 18 SPA\nVite 6 · TS 5\nTanStack Query\nZustand", I("react"))
        world3d = Custom("3D 캠퍼스·동네·실내\nthree.js 0.180\nR3F 8", I("threedotjs"))
        static = Custom("정적 데이터 (CDN)\nworld.json\n동네 12곳", I("l-file-json"))

    with Cluster("Railway", graph_attr=box(*RAILWAY, size="18")):
        with Cluster("Backend  ·  Spring Boot 3.5 / Java 21", graph_attr=box(*BACK)):
            api = Custom("REST API /api/v1\nSecurity + JWT\nCaffeine · Swagger", I("springboot"))
            ws = Custom("WebSocket\n/ws/world\n멀티플레이 30명", I("l-monitor-smartphone"))
            jobs = Custom("스케줄러\n06시 청년주택 수집\n09시 알림", I("l-clock"))
            disk = Custom("양도 사진\n서버 저장소", I("l-hard-drive"))

        with Cluster("Database", graph_attr=box(*DB)):
            db = Postgresql("PostgreSQL 16\nFlyway V1~V11")

        with Cluster("AI Server  ·  FastAPI / Python 3.11 (Docker)", graph_attr=box(*AI)):
            fastapi = Custom("FastAPI + Uvicorn\n/v1/floorplan\n/v1/rent", I("fastapi"))
            seg = Custom("CubiCasa5K\n평면도 분할\nPyTorch CPU", I("pytorch"))
            ocr = Custom("PaddleOCR\nPP-OCRv5 한국어", I("paddlepaddle"))
            gbm = Custom("적정 월세\nGBM 분위 회귀\nscikit-learn", I("scikitlearn"))

    with Cluster("모델 저장소 (빌드 시 다운로드)", graph_attr=box(*HF)):
        hf = Custom("Hugging Face\nchatatda-models\n가중치 209MB", I("huggingface"))
        gh = Custom("GitHub\nCubiCasa5K 코드", I("github"))

    with Cluster("외부 API", graph_attr=box(*EXT)):
        molit = Custom("국토교통부\n실거래가 API", I("l-landmark"))
        soco = Custom("서울시\n청년안심주택 수집", I("l-building-2"))
        tmap = Custom("TMAP\n보행자 경로", I("l-footprints"))
        kakao_api = Custom("카카오 로컬 API\n주소·좌표", I("kakao"))
        google = Custom("Google OAuth\nJWKS 토큰 검증", I("google"))

    with Cluster("campus-data  ·  자료 정리 (배포 안 함)", graph_attr=box(*OFF, dashed=True)):
        osm = Custom("OpenStreetMap\n길·건물 윤곽", I("openstreetmap"))
        ngii = Custom("국토지리정보원\n수치지도·지형", I("l-mountain"))
        ledger = Custom("건축물대장·브이월드\n건물 84곳", I("l-landmark"))
        build = Custom("Node 빌드 스크립트\nbuild-world.mjs", I("l-shapes"))

    # 보조선(점선)은 배치 계산에서 뺀다 → 주 흐름만으로 층이 정해짐
    AUX = dict(style="dotted", color="#94a3b8", constraint="false")

    # 사용자 흐름
    user >> Edge(label="HTTPS", color="#2563eb", penwidth="2.0") >> spa
    spa >> Edge(**AUX) >> world3d
    static >> Edge(label="로드", **AUX) >> world3d
    spa >> Edge(**AUX) >> kakao_sdk
    spa >> Edge(**AUX) >> gsi

    spa >> Edge(label="REST (JSON)", color="#2563eb", penwidth="2.0") >> api
    spa >> Edge(label="WebSocket", color="#7c3aed", penwidth="2.0") >> ws

    # 백엔드 내부·DB
    api >> Edge(label="JPA", color="#1d4ed8", penwidth="1.8") >> db
    jobs >> db
    api >> disk

    # 백엔드 → AI
    api >> Edge(label="평면도 · 적정 월세", color="#c2410c", penwidth="2.0") >> fastapi
    fastapi >> [seg, ocr, gbm]

    # 모델 받기 (빌드 시)
    hf >> Edge(label="빌드 시 가중치 다운로드", **BUILD) >> seg
    gh >> Edge(label="git clone", **BUILD) >> seg

    # 외부 API
    api >> Edge(label="외부 API 호출", lhead="cluster_외부 API") >> kakao_api
    jobs >> Edge(label="크롤링 (Jsoup)", style="dashed") >> soco

    # 오프라인 데이터 → 정적 데이터
    [osm, ngii, ledger] >> Edge(**BUILD) >> build
    build >> Edge(label="frontend/public 복사", **BUILD) >> static


# ─────────────────────────────────────────────────────────────
# 2. 평면도 파이프라인 (AI 서버 → 실내 3D)
# ─────────────────────────────────────────────────────────────
SUB = lambda: box("#b45309", "#ffffff", size="14")
with Diagram("평면도 → 실내 3D 파이프라인", filename=str(HERE / "02-floorplan-pipeline"),
             show=False, direction="LR", outformat="png",
             graph_attr={**GRAPH, "ranksep": "0.75", "nodesep": "0.6"}, node_attr=NODE, edge_attr=EDGE):

    req = Custom("Spring Boot\n평면도 추정 요청", I("springboot"))
    hf = Custom("Hugging Face\n분할 모델 가중치\n(빌드 시 다운로드)", I("huggingface"))

    with Cluster("AI Server  ·  FastAPI (Railway)", graph_attr=box(*AI, size="18")):
        with Cluster("루트 A · 평면도 이미지  /v1/floorplan/estimate", graph_attr=SUB()):
            img = Custom("평면도 이미지", I("l-images"))
            seg = Custom("CubiCasa5K 분할\n방 12종 · 아이콘 11종\nPyTorch", I("pytorch"))
            ocr = Custom("PaddleOCR\n한국어 방 이름", I("l-scan-text"))
            vec = Custom("벡터화\n방 폴리곤 · 벽\nOpenCV · Shapely", I("opencv"))
            opn = Custom("문 · 창 배치\n문 열림 방향", I("l-house"))
        with Cluster("루트 B · 도면 없음  /v1/floorplan/estimate-from-meta", graph_attr=SUB()):
            meta = Custom("면적 · 방 수", I("l-file-spreadsheet"))
            tmpl = Custom("템플릿 33종\n선택 · 스케일", I("l-layout-template"))
        check = Custom("보정 · 검수\n/v1/floorplan/validate", I("l-check-check"))

    fp = Custom("FloorPlan JSON\n방 · 벽 · 문 · 창", I("l-file-json"))

    with Cluster("Backend  ·  Spring Boot", graph_attr=box(*BACK)):
        db = Postgresql("PostgreSQL\n평면도 저장")
        get = Custom("GET /floorplans/{id}", I("springboot"))

    front = Custom("실내 3D 방 투어\nthree.js · R3F", I("threedotjs"))

    hf >> Edge(**BUILD) >> seg
    req >> Edge(label="이미지", color="#c2410c", penwidth="2.0") >> img
    req >> Edge(label="면적 · 방 수", color="#c2410c", penwidth="2.0") >> meta
    img >> seg >> vec >> opn >> check
    img >> ocr >> Edge(label="방 이름") >> check
    meta >> tmpl >> check
    check >> fp
    fp >> Edge(label="저장") >> db >> get
    get >> Edge(color="#2563eb", penwidth="2.0") >> front


# ─────────────────────────────────────────────────────────────
# 3. 적정 월세 모델 (학습 → 배포 → 추론)
# ─────────────────────────────────────────────────────────────
with Diagram("적정 월세 AI — 학습에서 판결까지", filename=str(HERE / "03-rent-model"),
             show=False, direction="LR", outformat="png",
             graph_attr={**GRAPH, "ranksep": "0.8", "nodesep": "0.7"}, node_attr=NODE, edge_attr=EDGE):

    with Cluster("모델 학습 (로컬)", graph_attr=box(*OFF, dashed=True)):
        deals = Custom("국토부 실거래\n동·면적·보증금·월세\n계약월·층·준공연도", I("l-landmark"))
        kakao = Custom("카카오 로컬 API\n가장 가까운 지하철역", I("kakao"))
        bus = Custom("버스 정류장\n500m 안 개수", I("l-map-pinned"))
        dongf = Custom("동 단위 피처\nbuild_dong_features.py", I("l-file-spreadsheet"))
        train = Custom("train_rent.py\nHistGradientBoosting\n분위 회귀 25·50·75%", I("scikitlearn"))

    hf = Custom("Hugging Face\nrent/model.joblib", I("huggingface"))

    with Cluster("AI Server  ·  FastAPI (Railway)", graph_attr=box(*AI, size="18")):
        ep = Custom("POST /v1/rent/estimate", I("fastapi"))
        model = Custom("GBM 분위 회귀\n㎡당 환산 월세 추정", I("scikitlearn"))

    with Cluster("Backend  ·  Spring Boot", graph_attr=box(*BACK)):
        svc = Custom("AiRentService\n적정가 요청", I("springboot"))
        rule = Custom("룰 기반 판정\n실거래 동 중앙값\n보증금 환산 4.6%", I("l-check-check"))
        verdict = Custom("적정가 + 범위\n판결 등급", I("l-landmark"))

    front = Custom("매물 상세\n판결 카드", I("react"))

    [deals, kakao, bus] >> Edge(**BUILD) >> dongf >> Edge(**BUILD) >> train
    train >> Edge(label="hf upload", **BUILD) >> hf
    hf >> Edge(label="빌드 시 다운로드", **BUILD) >> model
    svc >> Edge(color="#c2410c", penwidth="2.0") >> ep >> model
    model >> Edge(label="fairRent · low · high", color="#c2410c") >> verdict
    rule >> verdict
    verdict >> Edge(color="#2563eb", penwidth="2.0") >> front

