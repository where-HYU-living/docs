# 집 주변 동네 3D (Neighborhood Worlds) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 실내 3D 평면도가 있는 매물 7곳·청년안심주택 단지 5곳 주변을 캠퍼스처럼 걸어 다닐 수 있는 3D 동네(건물·도로·공원·지형)로 만든다.

**Architecture:** 캠퍼스 월드를 만드는 `campus-data` 파이프라인(OSM+지형 → `world.json`)을 "중심점+반경" 입력으로 일반화해 동네마다 `neighborhoods/<siteId>.json`(같은 스키마, 같은 원점)을 만든다. 프론트는 `buildWorld` 에 동네 모드를 넣고, 상세 패널의 "주변 걸어보기"로 캠퍼스 월드 대신 동네 월드를 띄웠다가 "캠퍼스로"로 돌아온다(실내 3D 가 동네 Canvas 를 멈췄다 되살리는 방식과 같은 패턴).

**Tech Stack:** Node(ESM, `node --test`) 빌드 스크립트, Overpass(OSM), AWS Terrarium 지형 타일, Vite/React/R3F/three 0.180, Vitest, Playwright(`playwright-core`, 숫자만 확인).

**Spec:** 별도 문서 없음 — 이 대화의 요구("기숙사 6·매물 7·청년안심주택 단지는 월드 밖이어도 그 집 주변을 걸어 볼 수 있게, `campus-data` 파이프라인을 제대로 확장")가 명세다. 아래 "확정한 결정"이 해석이다.

## 확정한 결정 (사실 확인 결과)

- 기숙사는 캠퍼스 안이라 동네 조각은 필요 없지만 **건물 자체를 고도화**한다(Task 6b). 평면도 201–206 은 호실 유형 6개이고 건물은 801~806(+807·809·810)이다. `dorms.json` 에는 801·804·805·806·810 이 들어 있다. 캠퍼스 폴더에 `appearance.json`·로드뷰 사진·대장이 이미 있고, 신뢰도는 801 중간·802 낮음·803 낮음·804 높음·805 중간·806 낮음이다(낮은 건 사진을 다시 보고 보강).
- 청년안심주택 평면도 20개는 **건물 20동이 아니라 단지 5곳의 주택형 20개**다. 건물별 좌표가 있는 건 이 5동(위 좌표)이며 운영 API 에서 받았다.
- 동네 12곳은 서로 멀어(최소 158m, 대부분 300m 이상) 합치지 않고 **전부 따로** 만든다.
- 대상 건물(매물 7동 + 단지 5동 = 12동)은 외관을 제대로 만든다: 카카오 로드뷰 사진 → 외관 조사(`APPEARANCE-BRIEF.md` 방식) → `appearance.json` → 3D. **주변 건물은 상자로 세워 두기만 하면 된다**(속성 정밀도에 공을 들이지 않는다).
- 가로등: OSM `highway=street_lamp` 노드가 있으면 그 자리에, 없는 도로에는 30m 간격으로 도로 가장자리에 세운다(기존 `streetlamps.ts`·품질 프리셋 `streetlamps` 재사용).
- 월드 지형 범위는 x −268~598, z −426~250 (사자상 원점, 동+·남+). 매물 7곳 중 6곳, 단지 5곳 모두 범위 밖. 대상은 **동네 12곳**(매물 7 + 단지 5).
  - 매물(`fixtures/listings.json` 중 floorplanId 가 있는 7건 — **site id 는 평면도 id 가 아니라 매물 id**: `l4 l6 l10 l17 l18 l19 l20`): 데모용 가짜 매물이고 주소만 실제 지번이다(실제 그 건물이 아님). 평면도는 청년안심주택 도면을 빌려 왔다.
    | 매물 id | 평면도 | 주소 | 월드 좌표(x,z) |
    |---|---|---|---|
    | 6 | 101 | 사근동 187 | (325,−404) — 캠퍼스 월드 가장자리 |
    | 4 | 103 | 사근동 171 | (155,−455) — 월드 바로 밖 |
    | 10 | 107 | 행당동 379 | (−499,−115) |
    | 17 | 102 | 행당동 349 | (−729,136) |
    | 18 | 105 | 마장동 811 | (237,−1106) |
    | 19 | 104 | 마장동 829 | (135,−1220) |
    | 20 | 106 | 마장동 817 | (−372,−1107) |
  - 단지(운영 API `/api/v1/housing`): 1 청량리역 퀸즈W(583,−2704) 2 마장역 한영스테이(7,−1128) 3 왕십리역 라봄성동(−205,−805) 4 왕십리역 청아진(−841,−991) 5 장한평역 힐데스하임(1832,−536).
- 동네 월드는 **캠퍼스와 같은 원점(사자상)** 을 쓴다 → `toLocal`/`toLatLng`·마커·텔레포트 좌표를 바꾸지 않는다. 한 동네 = 중심에서 반경 350m 정사각 조각 한 장(`bounds` 로 벽).
- 지형은 Terrarium(z15, 약 3.7m/px)을 평활화해 격자 step 4 로 만든다. 수치지도(NGII)는 재배포 금지·도엽 2장뿐이라 쓰지 않는다. 건물 속성은 `campus-data` 에 이미 있는 API 를 동네에도 쓴다(키는 `campus/tools/.env` 의 `DATA_GO_KR_KEY`·`VWORLD_KEY`):
  1. **브이월드 GIS건물통합정보(`LT_C_BLDGINFO`)** 를 동네 BOX 로 받아 건물 윤곽마다 지상층수·용도·사용승인연도를 OSM 건물에 윤곽 겹침으로 붙인다(캠퍼스 README 의 경고 — 한 필지에 85동이 몰린 곳은 속성이 다른 도형에 붙어 어긋남 — 은 필지가 잘게 나뉜 주거지에는 해당하지 않을 가능성이 크지만 **가정이므로 Task 4 에서 OSM 층수와의 일치율로 검증**한다).
  2. **건축HUB 건축물대장**(`getBrTitleInfo`)은 대상 건물(매물·단지) 한 동에만 쓴다: 주소(지번)로 조회해 층수·용도·사용승인일을 확정하고 `site.target.ledger` 에 넣어 상세 패널의 건물 정보와 맞춘다.
  3. 우선순위: 대장(대상 건물) > 브이월드 층수 > OSM `height`/`building:levels` > 기본 3층. 색은 용도(주거/상업/업무)별 팔레트에서 건물 id 해시로 고른다.
  4. **카카오 장소검색**(`search.map.kakao.com`, 팀 내부 참고용)으로 반경 안 편의점·카페·마트·지하철역 이름을 받아 3D 라벨/POI 로 쓴다(캠퍼스 `landmarks` 와 같은 형식).
- v1 은 **솔로**(동네에서는 멀티플레이 접속·초대 없음). 동네 월드는 캠퍼스 전용 구역(사자상·hero·zones·노천극장·출입구)을 만들지 않는다.
- 해석이 갈릴 수 있는 한 가지: "로드맵 걸어보기"를 **집 주변 보행**으로 해석했다. 집→캠퍼스 도보 경로선(Tmap, `walkMin`)은 Task 7 에 선택 과제로 분리했다.

## Global Constraints

- 좌표: 원점 = 사자상(위도 37.5561486, 경도 127.044341), x 동, z 남(m). 변환은 프론트 `src/app/map/geo.ts` 의 `toLocal`/`toLatLng` 와 같은 식만 쓴다.
- 3D 확인은 스크린샷 금지, 숫자(draw call·삼각형·에러 로그·좌표)로만.
- 메뉴 층 CSS 는 `ui-` 접두사·`--ui-*` 변수, 카드에 왼쪽 컬러 막대 금지, `.ui-primary` 등 파란 버튼 글자색은 `inkFor`/기존 규칙을 따를 것.
- 조각 JSON 은 gzip 전 1.5MB 이하, 한 동네 draw call 은 캠퍼스(`scripts/perf-baseline.json`)의 절반 이하.
- 출처 표기: OSM(ODbL)·AWS Terrain Tiles·브이월드·건축HUB·카카오맵(팀 내부 참고용)을 `attribution` 필드와 `campus-data/README.md` 에 적는다. 카카오 POI 는 라벨 텍스트만 쓰고 원본 응답은 git 에 올리지 않는다.
- 키: `campus/tools/.env`(git 제외) 만 읽고 로그·JSON 에 출력하지 않는다.
- 비밀 값(TMAP 등)은 코드·JSON 에 넣지 않는다.

## Review Focus

- 브이월드가 건물 속성을 다른 도형에 붙여 층수가 엉뚱한 건물(캠퍼스에서 실제로 28/38 어긋남): 일치율 게이트(Task 4)가 막는다.
- 대장 조회가 키 미활성·번지 불일치로 실패: 동네 빌드는 계속되고 `ledger:null` 로 표시된다.
- 중심점 반경 안에 OSM 건물이 거의 없는 곳(공원·강변): 빈 조각이 아니라 도로·녹지는 그려지고 에러 없이 뜬다.
- Overpass 가 일부 미러에서 실패·타임아웃: 재시도 후에도 실패하면 어느 동네인지 알려 주고 이미 만든 조각은 지우지 않는다.
- 건물 윤곽이 조각 경계를 넘는 경우: 잘라내지 않고 중심이 안에 있는 건물만 넣거나 통째로 제외한다(반쪽 건물 금지).
- 건물 높이가 `"12 m"`, `"3;4"`, 비숫자인 OSM 태그: 파싱 실패해도 기본 높이로 그린다.
- 동네에서 캠퍼스로 돌아올 때 들어가기 전 캠퍼스 위치·시간대가 그대로 복원된다.
- 동네 월드에서 `?invite=`·소켓 위치 전송이 새어 나가지 않는다.
- 같은 동네를 여러 번 열고 닫아도 WebGL 자원이 쌓이지 않는다(`dispose`).

## File Structure

| 파일 | 역할 |
|---|---|
| `campus-data/neighborhoods/sites.json` | 동네 12곳 목록(id, kind, name, lat, lng, x, z) — 손으로 갱신하는 단일 출처 |
| `campus-data/campus/tools/fetch-neighborhood.mjs` | 동네 하나의 OSM·지형 타일·브이월드 건물·카카오 POI·(대상 건물) 대장 받기 → `data/neighborhoods/<id>/` |
| `campus-data/world/lib/geo.mjs` | 위경도↔월드 좌표, 지형 격자 만들기(공용) |
| `campus-data/world/lib/classify.mjs` | OSM 태그 → 건물/도로/면(`cls`,`sub`) 분류·높이 파싱 (build-world 에서 뽑아냄) |
| `campus-data/world/build-neighborhood.mjs` | 위 부품으로 `frontend/public/neighborhoods/<id>.json` 생성 |
| `frontend/src/world/neighborhood.ts` | 동네 목록·조회·타입 (`neighborhoodForListing`, `neighborhoodForHousing`, URL 규칙) |
| `frontend/src/world/buildWorld.js` | 동네 모드(`world.site` 있으면 캠퍼스 전용 구역 생략) |
| `frontend/src/app/state/area.ts` | 현재 월드(`campus` / `{site}`)와 캠퍼스 복귀 지점 |
| `frontend/src/app/NeighborhoodButton.tsx` | 상세 패널의 "주변 걸어보기", 동네의 "캠퍼스로" 버튼 |

---

### Task 1: 동네 목록 단일 출처

**Files:**
- Create: `campus-data/neighborhoods/sites.json`, `campus-data/world/lib/geo.mjs`
- Test: `campus-data/test/sites.test.mjs`

**Interfaces:**
- Produces: `sites.json` = `Site[]`, `Site = { id: string /* 'l6' | 'h3' */, kind: 'listing'|'housing', ref: number, name: string, lat: number, lng: number, x: number, z: number }`; `geo.mjs`: `toLocal(lat: number, lng: number): [x: number, z: number]`, `ORIGIN`.

- [ ] **Step 1: Write the failing test** `sites.test.mjs`: 12개이고 id 유일; 각 `x,z` 가 `toLocal(lat,lng)` 와 1m 이내; `l6`=(325,−404)±2, `h5`=(1832,−536)±2; 매물 ref 집합이 {4,6,10,17,18,19,20} 이고 `backend/.../fixtures/listings.json` 에서 floorplanId 가 있는 매물과 같다.
- [ ] **Step 2: Run** `cd campus-data && node --test test/sites.test.mjs` — Expected: FAIL (파일 없음).
- [ ] **Step 3: Implement** `geo.mjs`(`toLocal`: 프론트 `geo.ts` 와 같은 식; 두 식이 같은지 확인하는 단언을 테스트에 포함) 와 `sites.json`(매물 좌표는 listings.json, 단지는 위 5곳 — 단지 좌표는 운영 `GET /api/v1/housing` 값을 그대로 복사).
- [ ] **Step 4: Run test** — Expected: PASS.
- [ ] **Step 5: Commit** `feat(campus-data): 동네 12곳 목록과 좌표 변환`.

### Task 2: 동네 원본 받기 (OSM + 지형)

**Files:**
- Create: `campus-data/campus/tools/fetch-neighborhood.mjs`
- Test: `campus-data/test/fetch-neighborhood.test.mjs`

**Interfaces:**
- Consumes: `Site`, `toLocal` (Task 1).
- Produces: `bboxOf(site: Site, radiusM = 400): { s: number, w: number, n: number, e: number }`, `overpassQuery(bb): string`, `vworldBuildings(bb, key, fetchFn): Promise<Feature[]>` (BOX 를 4×3 타일로 나눠 페이지 순회, `fetch-vworld-buildings.mjs` 의 요청 형식 그대로), `kakaoPois(site, fetchFn): Promise<Poi[]>` (카테고리 CS2·CE7·MT1·SW8), `ledgerFor(site, key, fetchFn): Promise<Ledger | null>` (주소→법정동코드+번지; 실패하면 null), 저장 위치 `data/neighborhoods/<id>/{osm.json, vworld.json, pois.json, ledger.json, terrain_<z>_<x>_<y>.png}`. CLI: `node campus/tools/fetch-neighborhood.mjs [siteId…]` (인자 없으면 전부, 이미 받은 것은 건너뜀, `--force` 로 재수신).

- [ ] **Step 1: Write the failing test**: `bboxOf(l6)` 가 중심을 포함하고 폭·높이가 800m±5m; `overpassQuery` 에 `building`, `highway`, `leisure`, `landuse`, `natural` 이 모두 들어간다; `vworldBuildings` 는 `status!=='OK'` 페이지에서 멈추고 키가 없으면 `Error('VWORLD_KEY')`; `ledgerFor` 는 응답이 JSON 이 아니면 null(키 활성화 전) 이고 예외를 던지지 않는다; 미러 3개가 모두 실패하면 `Error` 메시지에 site id 가 들어간다(fetch 를 주입 가능한 인자로 받는다).
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** — 반경은 필요한 350m 에 여유 50m. 재시도·미러 순환은 `fetch-site-data.mjs` 방식 그대로(최대 6회). 일부 동네만 실패해도 나머지는 저장하고 마지막에 실패 목록을 출력, 종료 코드 1.
- [ ] **Step 4: Run test** — Expected: PASS. 그다음 실제로 `node campus/tools/fetch-neighborhood.mjs l6 h3` 를 돌려 `osm.json` 에 `building` way 가 1개 이상, `vworld.json` 에 feature 가 1개 이상, `pois.json` 이 비어 있지 않은지 확인. 하나라도 비면 그 소스는 건너뛰고 경고(나머지로 계속).
- [ ] **Step 5: Commit** `feat(campus-data): 동네 OSM·지형 받기`.

### Task 3: 월드 빌드 부품 분리 (회귀 없이)

**Files:**
- Create: `campus-data/world/lib/classify.mjs`
- Modify: `campus-data/world/build-world.mjs` (분류·높이 파싱을 `classify.mjs` 로 이동, 동작 불변)
- Test: `campus-data/test/classify.test.mjs`, `campus-data/test/world-regression.test.mjs`

**Interfaces:**
- Produces: `parseHeight(tags: Record<string,string>): number | null` (`"12 m"`, `"12"`, `"3;4"`→null 아닌 첫 값, 비숫자→null), `levelsToHeight(levels: number): number` (층고 3.2m + 지붕 1m), `classifyWay(tags): { kind: 'building'|'road'|'area'|null, cls?: string, sub?: string, hw?: string, w?: number }`.

- [ ] **Step 1: Write the failing tests**: `classify.test.mjs` — `parseHeight({height:'12 m'})===12`, `{height:'abc'}`→null, `{'building:levels':'5'}` 는 `levelsToHeight(5)`, `classifyWay({highway:'residential'})` 가 road, `{leisure:'pitch'}` 가 `{kind:'area',cls:'leisure',sub:'pitch'}`. `world-regression.test.mjs` — **리팩터링 전 현재** `world.json` 의 건물 수·도로 수·areas 수와 `heightAt` 샘플 5점을 고정값으로 박아 두고, `npm run world` 결과가 같다(수치지도 파일이 없는 환경이면 테스트를 skip 하고 이유를 출력).
- [ ] **Step 2: Run** — Expected: classify FAIL, regression PASS(리팩터링 전 기준선).
- [ ] **Step 3: Implement** — 함수를 이동만 하고 `build-world.mjs` 가 import. 새 로직 추가 금지.
- [ ] **Step 4: Run** `npm test` — Expected: 모두 PASS (regression 이 여전히 같은 값).
- [ ] **Step 5: Commit** `refactor(campus-data): OSM 분류·높이 파싱을 lib 로 분리`.

### Task 4: 동네 조각 만들기

**Files:**
- Create: `campus-data/world/build-neighborhood.mjs`, `campus-data/world/lib/terrain.mjs`
- Output: `frontend/public/neighborhoods/<id>.json` ×12
- Test: `campus-data/test/build-neighborhood.test.mjs`

**Interfaces:**
- Consumes: Task 1~3 의 `Site`, `classifyWay`, `parseHeight`, `toLocal`.
- Produces: `terrain.mjs` `terrariumToGrid(pngs, bounds, step = 4): { step, w, h, minX, minZ, data: number[] }` (3×3 평활화, 값은 절대 높이 m); `build-neighborhood.mjs` `buildNeighborhood(site: Site, osm, grid): NeighborhoodWorld`.
- `NeighborhoodWorld` = `world.json` 과 같은 키(`origin, bounds, terrain, buildings, roads, areas, landmarks:[], exits:[], retaining:[], stairs:[], attribution`) + `site: { id, kind, ref, name, target: { x, z, buildingId: string | null } }`. `buildings[i]` = `{ id, name, kind, h, floors, use, pts, look? }` (캠퍼스 건물과 같은 필드 + 층수·용도), `landmarks` 는 카카오 POI(캠퍼스 `landmarks` 형식, 라벨용), `site.target.ledger` 는 대장 결과 또는 null. `target.buildingId` = 매물/단지 좌표를 포함하거나 가장 가까운(30m 이내) 건물.

- [ ] **Step 1: Write the failing tests** (합성 OSM 입력 사용): 중심이 조각 밖인 건물은 제외되고 중심이 안인 건물은 윤곽이 `bounds` 를 넘어도 통째로 유지되지 않고 **제외**된다(반쪽 금지 결정 — 중심이 안이고 모든 꼭짓점이 `bounds`+20m 안일 때만 포함); `height:'12 m'` 는 h=12, 태그 없으면 h=9.6(3층); `target.buildingId` 가 좌표를 포함하는 건물 id; 건물이 0개인 입력에서도 `terrain`·`roads` 가 비어 있지 않고 에러 없음; 브이월드 feature(층수 7)와 겹치는 OSM 건물(층수 태그 없음)은 `floors===7`, 둘 다 있고 다르면 브이월드 우선이지만 `|차이|>3` 이면 `suspect:true`; 대상 건물에 대장이 있으면 대장 층수가 이긴다; 모든 JSON 이 1.5MB 미만(실데이터 12개에 대한 별도 테스트, 데이터가 있을 때만).
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** — 도로 폭은 캠퍼스 `roads` 와 같은 표(`hw`→w)를 `classify.mjs` 에서 가져온다. 지형은 조각 `bounds` 에서 건물 윤곽 안쪽 높이를 주변 평균으로 눌러 "건물 높이가 섞이는" 문제(README 에 적힌 평균 8m 오차)를 줄인다. `attribution` 에 OSM·AWS 문구.
- [ ] **Step 4: Run** `node --test` 후 `node world/build-neighborhood.mjs` 로 12개 생성, 각 파일의 건물 수·크기·브이월드 결합률·OSM↔브이월드 층수 일치율(±1층 이내 비율)을 표로 출력. **게이트:** 일치율이 70% 미만인 동네는 브이월드 속성을 쓰지 않고 OSM 만 쓰도록 `site.look.useVworld=false` 로 표시하고 그 사실을 사용자에게 보고한다(캠퍼스에서 일어난 어긋남이 동네에서도 있는지 데이터로 확인).
- [ ] **Step 5: Commit** (campus-data) `feat: 동네 월드 조각 생성`, (frontend) `data: 동네 월드 12곳`.

### Task 4b: 대상 건물 12동 외관 (로드뷰 → appearance.json)

**Files:**
- Create: `campus-data/campus/tools/make-roadview-links-sites.mjs`, `campus-data/neighborhoods/<siteId>/appearance.json` ×12, 사진은 `campus-data/neighborhoods/<siteId>/photos/`(git 제외, 재배포 안 함)
- Modify: `campus-data/world/build-neighborhood.mjs` (대상 건물에 `look` 주입)
- Test: `campus-data/test/appearance.test.mjs`

**Interfaces:**
- Produces: `roadviewLinks(site: Site, bearings = [0, 120, 240]): { url: string, bearing: number }[]` (`https://map.kakao.com/link/roadview/<lat>,<lng>` 형식 — 캠퍼스 `make-roadview-links.mjs` 와 같은 형식), `lookFromAppearance(a: Appearance): Look` (외벽 재질 → `wall`/`walls`, 지붕 색·모양 → `roofColor`, 창 패턴 → `window`; 캠퍼스 `world.buildings[i].look` 와 같은 키).

- [ ] **Step 1: Write the failing test**: `roadviewLinks` 가 방위 수만큼 URL 을 내고 위경도가 URL 에 들어간다; `lookFromAppearance` 가 `{외벽:[{재질:'붉은 벽돌',색:'#a85'}]}` 에서 `look.wall==='#aa5500…'`(색을 그대로 쓰고 hex 형식 검증), 모르는 재질은 `null` 이 아니라 기본 회색 도장; `appearance.json` 12개가 `APPEARANCE-BRIEF.md` 형식(필수 키 `형태, 지붕, 외벽, 출처, 신뢰도`)을 만족한다.
- [ ] **Step 2: Run** `node --test test/appearance.test.mjs` — Expected: FAIL.
- [ ] **Step 3: Implement** — 링크를 만들고 `capture-roadview.mjs` 방식으로 사진 저장(사이트당 2~3장). 그다음 사진을 직접 보고 `APPEARANCE-BRIEF.md` 지침대로 `appearance.json` 을 쓴다(모르면 null, 지어내지 않음; 로드뷰가 옆 건물을 찍었으면 "다른 건물로 보임"). 단지 5동은 단지 이름으로 웹 검색해 외관 사진·기사 출처를 보탠다. 사진 원본은 저장소에 올리지 않고 `appearance.json` 의 파생 정보만 올린다.
- [ ] **Step 4: Run test** — Expected: PASS. 신뢰도 '낮음' 인 건물 목록을 사용자에게 보고.
- [ ] **Step 5: Commit** `feat(campus-data): 대상 건물 12동 외관 조사`.

### Task 5: 프론트 동네 모드 로딩

**Files:**
- Create: `frontend/src/world/neighborhood.ts`, `frontend/src/app/state/area.ts`
- Modify: `frontend/src/world/buildWorld.js`, `frontend/src/world/WorldCanvas.tsx`, `frontend/src/main.d.ts` (필요 시), `frontend/src/world/buildWorld.d.ts`
- Test: `frontend/src/world/neighborhood.test.ts`, `frontend/src/app/state/area.test.ts`, `frontend/e2e` 대신 `scripts/neighborhood-check.mjs`(숫자 확인)

**Interfaces:**
- Produces (`neighborhood.ts`): `type SiteId = string`; `siteForListing(listingId: number): SiteId | null` (`'l'+listingId`, 평면도 있는 매물 7건만), `siteForHousing(id: number): SiteId | null` (`'h'+id`), `neighborhoodUrl(site: SiteId): string` (`/neighborhoods/<id>.json`), `loadNeighborhood(site: SiteId): Promise<World>`.
- Produces (`area.ts`, zustand): `useArea: { area: 'campus' | { site: SiteId }, returnPose: { x, z, yaw } | null, enter(site: SiteId, from: Pose): void, leave(): void }`.
- `WorldCanvas` 는 `area` 가 바뀌면 현재 장면을 `dispose()` 하고 해당 월드로 다시 만든다.

- [ ] **Step 1: Write the failing tests**: `siteForListing(6)==='l6'`, `siteForListing(1)===null`, `siteForHousing(9)===null`; `useArea.enter('l6', pose)` 후 `area` 가 `{site:'l6'}`, `returnPose` 가 pose 와 같고, `leave()` 후 `'campus'` 와 `returnPose` 유지 후 소비됨; 동네 모드에서는 `useMultiplayer` 가 소켓을 열지 않는다(훅 테스트: area 가 동네면 `connect` 호출 0회).
- [ ] **Step 2: Run** `npx vitest run src/world/neighborhood.test.ts src/app/state/area.test.ts` — Expected: FAIL.
- [ ] **Step 3: Implement** — `buildWorld.js`: `world.site` 가 있으면 사자상 flatten, hero, zones, 노천극장, 출입구, 랜드마크 라벨, hero props, 고정 소나무를 건너뛰고 지형·도로·건물·나무·가로등·시간대 조명만 만든다(건너뛴 항목 목록을 코드 주석에 남김). 플레이어 시작점은 `site.target`(집 좌표) 앞 도로 쪽 5m. `Player` 의 `bounds` 는 조각 `bounds`.
- [ ] **Step 4: Run** 위 vitest PASS, 그리고 `npm run typecheck`, `npm run build`. `node scripts/neighborhood-check.mjs l6 h5` — dev 서버에서 `?area=l6` 로 열어 `window.__ready`, 콘솔 에러 0건, draw call·삼각형 출력(Global Constraints 의 절반 이하).
- [ ] **Step 5: Commit** `feat(world): 동네 월드 모드와 area 상태`.

### Task 6: 진입·복귀 UI와 집 표시

**Files:**
- Create: `frontend/src/app/NeighborhoodButton.tsx`
- Modify: `frontend/src/app/ListingsPanel.tsx`, `frontend/src/app/HousingPanel.tsx`, `frontend/src/app/venue.css`(또는 해당 css), `frontend/src/app/WorldEffects.tsx`
- Test: `frontend/src/app/neighborhood.test.tsx`

**Interfaces:**
- Consumes: `siteForListing/Housing`, `useArea` (Task 5), `api.getPose()`, `api.teleport`.
- Produces: `<NeighborhoodButton kind="listing"|"housing" id={number} />` — 사이트가 없으면 렌더하지 않음. 동네에서는 우상단에 "캠퍼스로" 버튼.

- [ ] **Step 1: Write the failing tests**: 매물 6 상세에 "주변 걸어보기" 가 있고 매물 1(평면도 없음)에는 없다; 클릭하면 `useArea.area` 가 `{site:'l6'}`; 동네에서 "캠퍼스로" 클릭 시 `area==='campus'` 이고 `teleport` 가 저장해 둔 `returnPose` 로 한 번 호출됨; 동네에서는 초대 버튼이 비활성+안내("동네에서는 초대할 수 없어요").
- [ ] **Step 2: Run** — Expected: FAIL.
- [ ] **Step 3: Implement** — 동네에서 집 건물 위에 기존 빔(`api.setBeacons`)을 세워 위치를 알린다. 이미 있는 "실내 보기"는 동네에서 집 문 앞(`doors.ts` 방식) 또는 패널 버튼 그대로 쓴다 — 어느 쪽이 자연스러운지 코드를 보고 기존 패턴을 따른다. 버튼 글자색은 `inkFor` 규칙.
- [ ] **Step 4: Run** `npx vitest run`, `npm run typecheck`, `npm run build` — Expected: 모두 PASS.
- [ ] **Step 5: Commit** `feat(app): 주변 걸어보기·캠퍼스로 버튼`.

### Task 6b: 기숙사 건물 고도화 (캠퍼스 구역 플러그인)

**Files:**
- Create: `frontend/src/zones/dorm.js`, `frontend/src/world/dormLook.ts`(순수 계산), 데이터는 `campus-data/campus/80x-*/appearance.json` 에서 `world.json` 빌드 때 건물 `look` 에 이미 들어가는지 먼저 확인
- Test: `frontend/src/world/dormLook.test.ts`

**Interfaces:**
- Consumes: 구역 계약 `export default async ({THREE, world, heightAt, lm, scene, renderer, prior}) => ({group, skipIds, footprints, clear})` (`src/zones/README.md`), `world.buildings[i].look`.
- Produces: `dormSpec(b: WorldBuilding, appearance: Appearance | null): { floors: number, wall: string, roof: string, bays: number, entrance: 'S'|'N'|'E'|'W' | null }` (순수 함수).

- [ ] **Step 1: Write the failing test**: `dormSpec` 가 `appearance` 가 null 이면 층수는 `b.floors`, 색은 `look.wall` 로 떨어지고 예외가 없다; 외벽이 2종이면 큰 비율이 `wall`; 입구 방향 한글('남')을 'S' 로 바꾼다.
- [ ] **Step 2: Run** `npx vitest run src/world/dormLook.test.ts` — Expected: FAIL.
- [ ] **Step 3: Implement** — 신뢰도 낮은 802·803·806 은 로드뷰 사진을 다시 보고 `appearance.json` 을 먼저 보강(Task 4b 와 같은 지침). `dorm.js` 는 801~806 의 현재 상자 건물을 `skipIds` 로 빼고 `dormSpec` 대로 층 줄눈·창 띠·옥상 난간·입구 캐노피가 있는 건물을 직접 세운다(`hill.js` 의 `wallsGeo`·`groundRange` 패턴 복사). 성능: 재질 공유·`merge` 기본값 유지.
- [ ] **Step 4: Run** vitest·typecheck·build PASS, `?go=801`~`?go=806` 으로 이동해 구역이 에러 없이 로드되는지(`zone ../zones/dorm.js: Nms`, 콘솔 에러 0건)와 draw call 증가량을 숫자로 기록.
- [ ] **Step 5: Commit** `feat(zones): 기숙사 801~806 고도화`.

### Task 7 (선택): 집→캠퍼스 도보 경로선

**Files:**
- Create: `backend` 쪽 `GET /api/v1/route/walk?from=…` 가 없으면 만들지 않고 이 과제를 건너뛴다. 있으면 `frontend/src/world/routeLine.ts`
- 전제: Railway 에 `TMAP_KEY` 가 들어 있다(2026-11-08 설정). 백엔드에 Tmap 보행자 경로 클라이언트가 이미 있는지 먼저 확인(`external.tmap`).

- [ ] **Step 1:** 백엔드의 도보 시간(`walkMin`) 산출 코드가 Tmap 경로 좌표를 이미 받는지 확인하고, 받는다면 좌표 목록을 내려 주는 엔드포인트 추가 여부를 사용자에게 한 줄로 확인한다. 아니면 이 과제는 보류.
- [ ] **Step 2~5:** 확정되면 별도 계획으로 분리한다(이 계획의 범위 밖).

### Task 8: 성능·배포 확인

**Files:** `frontend/scripts/perf-baseline.json`(동네 항목 추가), `campus-data/README.md`(파이프라인·출처 절 추가)

- [ ] **Step 1:** `node scripts/perf.mjs "q=med&area=l6"` 와 `h5`(건물 많은/적은 동네 각각)를 돌려 draw call·삼각형·프레임을 baseline 에 기록. 기준 위반이면 건물 병합·나무 수를 조절하는 수정을 먼저 한다.
- [ ] **Step 2:** `public/neighborhoods` 합계와 가장 큰 파일 크기를 출력해 1.5MB(개별) 이하임을 확인, `npm test` 가 이 한도를 지키게 테스트 추가(`neighborhoodSize.test.ts`).
- [ ] **Step 3:** 동네 12곳을 열고 닫기 20회 반복하는 스크립트로 `renderer.info.memory.geometries/textures` 가 증가하지 않는지 확인(Review Focus 마지막 항목).
- [ ] **Step 4:** `npx vitest run`, `npm run typecheck`, `npm run build` 통과 확인 후 main 에 푸시(Vercel 자동 배포).
- [ ] **Step 5:** 배포 후 `https://…/?area=l6` 을 열어 콘솔 에러 0건을 확인하고 결과를 사용자에게 보고.

---

## Self-Review

- **Spec coverage:** 매물 7·단지 5 동네(Task 4·5·6)와 대상 건물 외관(4b), 기숙사 고도화(6b), 도로·가로등·주변 건물(Task 4·5), 캠퍼스 파이프라인 확장(Task 3·4), 걸어 다니기(Task 5), 돌아오기(Task 6). "로드맵" 해석은 결정에 명시, 경로선은 Task 7 선택.
- **Type consistency:** `Site`/`SiteId`(`'l6'`,`'h3'`), `NeighborhoodWorld.site.target`, `useArea.enter/leave` 이름이 Task 1·4·5·6 에서 동일.
- **Proportion:** 코드 본문은 시그니처·테스트 단언·수치만 적었다.
- **리스크:** Task 5 의 `buildWorld` 동네 모드는 캠퍼스 전용 코드가 `landmarks`·`zones` 부재에서 깨지는 곳을 실제로 돌려 봐야 정확히 알 수 있다 — 그래서 Step 4 가 숫자 확인 스크립트를 포함한다.
