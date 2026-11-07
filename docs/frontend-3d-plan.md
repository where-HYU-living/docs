# 프론트·3D Implementation Plan (담당: 김준형)

> **현재 구현 상태 (2026-11-07 갱신):** 3D 층은 **R3F `<Canvas>`(`@react-three/fiber`) + 순수 three.js 장면 조립(`buildWorld`)** 으로 동작합니다. 아래 문서의 `ecctrl`·`@react-three/rapier`·`drei`는 **도입하지 않았습니다** (충돌은 `PolyIndex` 다각형 조회로 충분하고 wasm·물리 바디 비용만 늡니다). Task 4·5·17의 파일 구조(`src/world/Buildings.tsx` 등)는 계획이며 실제 구조와 다릅니다. 실제 구조·규칙은 `frontend/CLAUDE.md`, 성능 개선 이력은 `frontend/docs/superpowers/plans/2026-11-07-3d-perf-and-r3f-port.md` 를 보세요. 품질 프리셋(`?q=high|med|low`)이 있어 성능 목표(30fps·draw call)는 프리셋별로 측정합니다.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 행당·마장·답십리·왕십리·한양대 3D 공유 월드에서 매물·기숙사·청년안심주택을 걸어서 보고, 실내에 들어가고, 초과액 판정을 확인하는 웹 프론트를 백엔드 계약에 맞춰 만든다.

**Architecture:** React 앱 위에 R3F 캔버스 하나를 깔고, 그 위에 상단 검색·탭과 왼쪽 패널을 겹친다. 서버 데이터는 계약 문서 타입 그대로 TanStack Query로 받고, 백엔드가 준비되기 전에는 공유 픽스처를 MSW로 응답한다. 3D 좌표 변환·실내 생성·멀티플레이 메시지 처리는 순수 함수로 분리해 테스트한다.

**Tech Stack:** Vite, React 18, TypeScript, React Three Fiber, drei, @react-three/rapier, ecctrl, TanStack Query, Zustand, React Router, MSW, Vitest + Testing Library, 카카오맵 JS SDK, r3f-perf(개발용)

**Spec:** `docs/spec-v0.5.md` · **계약:** `docs/api-contract.md` (모든 요청·응답·WS 메시지 형식은 계약 문서가 정답. 프론트는 백엔드에 맞춘다)

## Global Constraints
- API 주소 `VITE_API_BASE` (기본 `http://localhost:8080`), 목 사용 여부 `VITE_USE_MOCK=true|false`
- 타입은 계약 문서와 **필드명·enum 값 그대로** (`src/api/types.ts` 한 곳에만 정의)
- 금액은 서버에서 원 단위 정수로 받고, 화면에서만 만원 단위로 변환
- `null` 값은 반드시 "정보 없음" 계열로 표시하고 숫자 0으로 바꾸지 않는다
- 좌표: ORIGIN과 변환식은 계약 4장 그대로, +x 동쪽 / +y 위 / −z 북쪽
- 등급 색·라벨·판결 문구는 계약 2-2장 그대로
- 게스트로 3D·검색·판정·멀티플레이 모두 가능, 로그인이 필요한 동작은 로그인 모달을 띄운다
- 멀티플레이: `move` 최대 10Hz, `ping` 15초, 초대 링크 파라미터 `?invite=`
- 3D 범위: 행당역·마장역·답십리역·왕십리역·한양대
- 목표 성능: 개발 노트북에서 30fps 이상, draw call 200 이하 (OKR 안 3)
- 평면도는 청년안심주택 공개 평면도를 손으로 옮긴 FloorPlan JSON만 사용 (스캔·추정·입력 도구 없음)

## Review Focus
- **판정 보류(`PENDING`)·`walkMin: null`·`budget: null`:** 숫자 대신 "판정 보류", "도보 시간 정보 없음"이 보여야 하고 `NaN`·`0만`이 보이면 안 된다 → Task 6, 8 테스트
- **게스트가 찜·후기·양도 쓰기를 누름:** 로그인 모달이 뜨고 화면이 깨지지 않아야 한다 → Task 11 테스트
- **WebSocket 끊김:** 자동 재접속, 재접속 후 사라진 플레이어는 지워져야 한다 → Task 16 테스트
- **지도 핀과 3D 위치 불일치:** 같은 매물이 2D 지도와 3D에서 같은 곳에 있어야 한다 → Task 2, 7 테스트
- **실내에서 나왔을 때 위치:** 그 건물 문 앞으로 돌아와야 한다 (정문으로 튀면 안 됨) → Task 9 테스트

---

## 파일 구조
```
frontend/
├── .env.example                 # VITE_API_BASE, VITE_USE_MOCK, VITE_KAKAO_JS_KEY, VITE_WS_BASE
├── public/data/
│   ├── buildings.geojson        # OSM 건물 윤곽(5개 역 범위) 사전 추출본
│   └── roads.geojson            # 도로·보행로 (선택)
├── scripts/extract-osm.mjs      # Overpass → geojson 추출 (1회 실행)
└── src/
    ├── api/        client.ts, types.ts, queries/*.ts (도메인별 훅)
    ├── mocks/      handlers.ts, browser.ts, fixtures/ → contract/fixtures 복사본
    ├── lib/        geo.ts, money.ts, grade.ts
    ├── state/      session.ts (토큰·프로필), ui.ts (탭·선택 대상·지도 모드·실내 여부)
    ├── app/        App.tsx, Layout.tsx, routes.tsx, LoginModal.tsx
    ├── world/      WorldCanvas.tsx, buildBuildings.ts, Buildings.tsx, Ground.tsx, Player.tsx, spawn.ts,
    │               Markers.tsx, NearbyIcons.tsx, Lighting.tsx, Minimap.tsx, RemotePlayers.tsx
    ├── interior/   buildInterior.ts, InteriorScene.tsx
    ├── net/        worldReducer.ts, interpolate.ts, worldSocket.ts, useWorld.ts
    └── features/   search/, listings/, map2d/, detail/, favorites/, dorm/, housing/, transfer/, reviews/, auth/, home/, notifications/
```
> 포크 세션에서 만든 한양대 3D 시제품(`~/maindesktop/chatatda-hanyang/proto`)의 OSM 추출 데이터와 건물 압출 코드는 Task 4에서 참고·이관 가능 (시제품은 검증용이므로 코드를 그대로 가져오지 말고 아래 인터페이스에 맞춰 옮긴다)

---

### Task 1: 프로젝트 골격 · API 클라이언트 · 계약 타입 · 목 서버

**Files:**
- Create: `package.json`, `vite.config.ts`, `src/api/client.ts`, `src/api/types.ts`, `src/mocks/handlers.ts`, `src/mocks/browser.ts`, `src/mocks/fixtures/*.json`, `src/main.tsx`
- Test: `src/api/client.test.ts`, `src/mocks/handlers.test.ts`

**Interfaces:**
- Produces:
  - `types.ts`: 계약 3장·5장의 모든 객체와 2장 enum (`Grade`, `RoomType`, `FavoriteType` …), `Page<T>`, `ListingSummary`, `ListingDetail`, `PriceCheck`, `Alternative`, `FloorPlan`, `Housing`, `Dorm`, `Transfer`, `Review`, `Report` 등
  - `class ApiError extends Error { code: string; status: number; details: unknown }`
  - `api<T>(path: string, init?: { method?, body?, query? }): Promise<T>` — `/api/v1` 접두사 자동, 토큰 있으면 `Authorization` 헤더, 실패 응답을 `ApiError`로 변환, `204`는 `undefined`
  - MSW 핸들러: 계약 5장 GET 전부 + 쓰기 요청은 메모리에 저장하는 수준

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('adds bearer token when logged in', ...)      // session.setToken('t') → 요청 헤더 Authorization: Bearer t
test('parses error body into ApiError', ...)       // 404 {code:'NOT_FOUND'} → rejects ApiError code 'NOT_FOUND', status 404
test('builds query string without null/undefined', ...) // query {maxRent: 500000, grade: undefined} → '?maxRent=500000'
test('mock listings return contract page shape', ...)    // GET /listings → items.length 20, page 0, total 20
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/api src/mocks` → FAIL
- [ ] **Step 3: 구현** — `npm create vite@latest frontend -- --template react-ts`, 의존성 설치. `VITE_USE_MOCK=true`면 `main.tsx`에서 MSW 워커 시작 후 렌더
- [ ] **Step 4: 통과 확인** — 같은 명령 → PASS, `npm run dev` 후 `http://localhost:5173` 빈 화면 오류 없음
- [ ] **Step 5: 커밋** — `git commit -m "chore: bootstrap vite app, api client, contract types, msw mocks"`

### Task 2: 좌표 · 금액 · 등급 유틸

**Files:**
- Create: `src/lib/geo.ts`, `src/lib/money.ts`, `src/lib/grade.ts`
- Test: `src/lib/geo.test.ts`, `src/lib/money.test.ts`, `src/lib/grade.test.ts`

**Interfaces:**
- Produces:
  - `ORIGIN: { lat: number; lng: number }` (계약 4장 값, 확정되면 여기 한 곳만 수정)
  - `toLocal(lat: number, lng: number): [x: number, z: number]`, `toLatLng(x: number, z: number): [lat: number, lng: number]`
  - `manwon(won: number | null): string` — `550000 → "55만"`, `1_000_000_0 → "1,000만"`, `555000 → "55.5만"`, `null → "-"`
  - `GRADE_META: Record<Grade, { color: string; label: string; verdict: (totalExcessWon: number | null) => string }>`

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('origin maps to 0,0', () => expect(toLocal(ORIGIN.lat, ORIGIN.lng)).toEqual([0, 0]))
test('north is -z', () => expect(toLocal(ORIGIN.lat + 0.001, ORIGIN.lng)[1]).toBeCloseTo(-110.54, 1))
test('east is +x', () => expect(toLocal(ORIGIN.lat, ORIGIN.lng + 0.001)[0]).toBeCloseTo(111.32 * Math.cos(ORIGIN.lat * Math.PI / 180), 1))
test('roundtrip within 1cm', ...)   // toLatLng(...toLocal(37.5612, 127.0371)) 오차 < 1e-7
test('manwon formats', ...)         // 550000→'55만', 555000→'55.5만', 10000000→'1,000만', null→'-'
test('verdict text', ...)           // GRADE_META.CULPRIT.verdict(3936000) === '찾았다. 2년간 393.6만 원을 써버릴 놈'
test('pending verdict has no number', ...) // GRADE_META.PENDING.verdict(null) === '비교할 거래가 부족해요'
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/lib` → FAIL
- [ ] **Step 3: 구현** — 계약 4장 식 그대로, 색·문구는 계약 2-2장 그대로
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(lib): geo projection, money and grade formatting"`

### Task 3: 앱 골격 · 상단 검색 · 탭 · 왼쪽 패널 · 상태

**Files:**
- Create: `src/app/App.tsx`, `src/app/Layout.tsx`, `src/app/routes.tsx`, `src/state/ui.ts`, `src/state/session.ts`, `src/features/search/SearchBar.tsx`, `src/api/queries/search.ts`
- Test: `src/app/Layout.test.tsx`, `src/features/search/SearchBar.test.tsx`

**Interfaces:**
- Consumes: Task 1 `api`, MSW
- Produces:
  - `useUi` (Zustand): `tab: 'home' | 'dorm' | 'housing' | 'transfer' | 'myhome'`, `mapMode: '3d' | '2d'`, `target: { type: SearchType | FavoriteType; id: number | null; lat: number; lng: number } | null`, `indoor: { floorplanId: number; returnTo: [number, number, number] } | null`, 액션 `setTab`, `setMapMode`, `focus(target)`, `enterIndoor(...)`, `exitIndoor()`
  - `useSession`: `token`, `profile`, `setToken`, `logout`, `requireLogin(): boolean` (게스트면 로그인 모달 열고 `false`)
  - 레이아웃: 캔버스 전체 화면 + 상단(검색·탭 [집 찾기][기숙사][청년안심주택][양도][내 집 기록]) + 왼쪽 패널(탭별 내용) + 오른쪽 아래 미니맵 자리

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('tabs switch left panel', ...)      // '기숙사' 클릭 → 패널 heading '기숙사'
test('search shows results after 2 chars', ...) // '청' 입력 → 요청 없음, '청아' → 결과 목록에 '왕십리역 청아진'
test('selecting result focuses target', ...)    // 결과 클릭 → useUi.getState().target.lat === 결과 lat
test('requireLogin opens modal for guest', ...) // 토큰 없음 → requireLogin() false, 모달 표시
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/app src/features/search` → FAIL
- [ ] **Step 3: 구현** — 검색 입력 300ms 디바운스
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(app): layout, search bar, tabs, ui and session state"`

### Task 4: 3D 동네 (건물 · 지면)

**Files:**
- Create: `scripts/extract-osm.mjs`, `public/data/buildings.geojson`, `src/world/buildBuildings.ts`, `src/world/Buildings.tsx`, `src/world/Ground.tsx`, `src/world/WorldCanvas.tsx`
- Test: `src/world/buildBuildings.test.ts`

**Interfaces:**
- Consumes: Task 2 `toLocal`
- Produces:
  - `extract-osm.mjs`: Overpass로 bbox(행당역·마장역·답십리역·왕십리역·한양대를 모두 포함) 건물 폴리곤 + `building:levels` + `name` 추출 → `buildings.geojson`
  - `buildBuildings(fc: GeoJSON.FeatureCollection): { geometry: THREE.BufferGeometry; footprints: Footprint[] }` — 모든 건물을 **하나의 병합 지오메트리**로(draw call 최소화), 높이 = `levels × 3m`, levels 없으면 3층
  - `type Footprint = { id: string; name?: string; polygon: [number, number][]; height: number; center: [number, number] }` (충돌체·말풍선 위치에 사용)

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('square footprint becomes box with level height', ...) // 10m×10m, levels 4 → bbox 높이 12, 바닥 x/z 범위 10
test('missing levels defaults to 3 floors', ...)            // 높이 9
test('all buildings merged into one geometry', ...)         // 3개 feature → geometry 1개, footprints 3개
test('skips invalid polygons', ...)                         // 꼭짓점 2개 feature → footprints 에서 제외, 예외 없음
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/world/buildBuildings.test.ts` → FAIL
- [ ] **Step 3: 구현** — `THREE.Shape` + `ExtrudeGeometry` 후 `mergeGeometries`, 회전으로 y축을 높이로. 지면은 bbox 크기 평면(지형 고저는 Task 17에서 선택)
- [ ] **Step 4: 통과 확인** — 테스트 PASS. `npm run dev`에서 동네가 보이고 r3f-perf로 **draw call ≤ 200, 30fps 이상** 확인
- [ ] **Step 5: 커밋** — `git commit -m "feat(world): osm buildings extruded and merged, ground"`

### Task 5: 캐릭터 걷기 · 카메라 · 충돌 · 순간이동

**Files:**
- Create: `src/world/Player.tsx`, `src/world/spawn.ts`, `src/world/Colliders.tsx`
- Test: `src/world/spawn.test.ts`

**Interfaces:**
- Consumes: Task 3 `useUi.target`, Task 4 `Footprint`
- Produces:
  - `spawnInFrontOf(target: { lat: number; lng: number }, footprints: Footprint[]): [number, number, number]` — 대상 위치에서 가장 가까운 건물 외곽선 바깥 3m 지점, 건물이 없으면 대상 위치 그대로
  - `playerRef` 전역 접근: `getPlayerPose(): { p: [number, number, number]; r: number; a: 'idle' | 'walk' | 'run' }`, `teleport(p: [number, number, number])` (Task 16에서 사용)
  - 충돌체: 각 Footprint를 rapier 고정 박스(외곽 사각형 근사)로

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('spawn is outside the building', ...)  // 정사각형 건물 중심을 대상으로 → 결과가 폴리곤 밖, 외곽선과 거리 ≈ 3
test('no building → target point', ...)     // footprints [] → toLocal(target) 그대로, y 0
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/world/spawn.test.ts` → FAIL
- [ ] **Step 3: 구현** — ecctrl 3인칭 컨트롤러(WASD·Shift 달리기), 모바일은 ecctrl 조이스틱. `useUi.target`이 바뀌면 `teleport(spawnInFrontOf(...))`
- [ ] **Step 4: 통과 확인** — 테스트 PASS. 수동: 걸어서 건물을 통과하지 못함, 검색 결과 클릭 시 그 건물 앞으로 이동
- [ ] **Step 5: 커밋** — `git commit -m "feat(world): third-person player, building colliders, teleport"`

### Task 6: 건물 말풍선 (월세 · 등급 색 · 하트)

**Files:**
- Create: `src/world/Markers.tsx`, `src/world/MarkerLabel.tsx`, `src/api/queries/listings.ts`
- Test: `src/world/MarkerLabel.test.tsx`

**Interfaces:**
- Consumes: Task 1 `ListingSummary`, Task 2 `manwon`, `GRADE_META`, `toLocal`
- Produces:
  - `useListings(params: ListingParams)` (TanStack Query, 키 `['listings', params]`)
  - `<MarkerLabel item={{ rent, deposit, grade, favorited, kind: 'listing' | 'housing' | 'dorm' | 'transfer' }} />` — drei `Html`로 건물 위 표시, 클릭 시 `useUi.focus` + 상세 열기
  - 화면 부하 제한: 카메라 반경 400m 안의 말풍선만 렌더

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('shows deposit/rent in manwon', ...)  // deposit 10000000, rent 550000 → '1,000/55'
test('colored by grade', ...)              // grade HIGH → 배경색 '#F2994A'
test('pending is gray with label', ...)    // grade PENDING → '#9E9E9E', 텍스트 '판정 보류'
test('heart when favorited', ...)          // favorited true → aria-label '찜함'
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/world/MarkerLabel.test.tsx` → FAIL
- [ ] **Step 3: 구현** — 기숙사·청년안심주택 말풍선은 Task 10에서 같은 컴포넌트에 `kind`만 바꿔 재사용
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(world): listing markers with grade colors and hearts"`

### Task 7: 매물 목록 · 필터 · 2D 지도 전환

**Files:**
- Create: `src/features/listings/ListingPanel.tsx`, `src/features/listings/Filters.tsx`, `src/features/listings/buildListingParams.ts`, `src/features/map2d/KakaoMap.tsx`, `src/features/map2d/loadKakao.ts`
- Test: `src/features/listings/buildListingParams.test.ts`, `src/features/listings/ListingPanel.test.tsx`, `src/features/map2d/KakaoMap.test.tsx`

**Interfaces:**
- Consumes: Task 6 `useListings`, Task 3 `useUi`, `useSession.profile`
- Produces:
  - `type FilterState = { maxRent?: number; maxDeposit?: number; maxMgmtFee?: number; grades: Grade[]; maxWalkMin?: number; roomType?: RoomType; bbox?: [number, number, number, number] }`
  - `buildListingParams(f: FilterState, buildingId: number | null): Record<string, string>` — 금액은 화면 만원 입력 → 원으로 변환, `grades` → `grade=HIGH,CULPRIT`, 빈 값은 생략
  - `KakaoMap`: 매물 핀(등급 색), 핀 클릭 → 카드 → "3D로 들어가기" = `setMapMode('3d')` + `focus`

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('converts manwon inputs to won', ...)  // {maxRent: 60} → {maxRent: '600000'}
test('joins grades', ...)                   // grades ['HIGH','CULPRIT'] → grade 'HIGH,CULPRIT'
test('omits empty', ...)                    // {} → {}
test('walk filter needs building', ...)     // maxWalkMin 10, buildingId null → maxWalkMin 생략
test('walkMin null renders 정보 없음', ...)  // ListingPanel 항목 walkMin null → '도보 정보 없음'
test('pin and 3d use same coordinates', ...)// KakaoMap 핀 위경도 == 항목 lat/lng, 클릭 후 target.lat/lng 동일
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/listings src/features/map2d` → FAIL
- [ ] **Step 3: 구현** — 카카오 SDK는 `loadKakao()`로 동적 스크립트 로드(`autoload=false`), 테스트에서는 모듈 목킹. 목록 카드 클릭 → `focus`
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(listings): list panel, filters, kakao 2d map toggle"`

### Task 8: 용의자 파일 · 판결 카드 · 비교 (D · N1 · N3)

**Files:**
- Create: `src/features/detail/SuspectFile.tsx`, `src/features/detail/VerdictCard.tsx`, `src/features/detail/ComparePanel.tsx`, `src/api/queries/detail.ts`
- Test: `src/features/detail/VerdictCard.test.tsx`, `src/features/detail/SuspectFile.test.tsx`, `src/features/detail/ComparePanel.test.tsx`

**Interfaces:**
- Consumes: `GET /listings/{id}`, `/price-check`, `/alternatives`, `/nearby`, Task 2 `GRADE_META`, `manwon`
- Produces: `useListingDetail(id)`, `usePriceCheck(id)`, `useAlternatives(id)`; `SuspectFile`에 "실내 들어가기" 버튼(`floorplanId` 있을 때만) → Task 9 `enterIndoor`

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('verdict shows converted vs fair', ...)  // 환산 71.2만 · 적정 54.8만 · 판결 문구(HIGH)
test('pending hides numbers', ...)            // PENDING → '판정 보류', '적정' 숫자 없음, 'NaN' 없음
test('budget over shown when logged in', ...) // budget.overRent 112000 → '예산보다 월 11.2만 원 초과'
test('budget hidden for guest', ...)          // budget null → 예산 문구 없음
test('sample basis shown', ...)               // sample.count 23, scope ADJACENT → '행당동·사근동 거래 23건 기준'
test('compare lists housing and dorm diffs', ...) // twoYearDiff 5376000 → '2년 537.6만 원 차이'
test('indoor button only with floorplan', ...)    // floorplanId null → 버튼 없음
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/detail` → FAIL
- [ ] **Step 3: 구현** — 용의자 파일 레이아웃(사진·주소·면적·옵션·도보 시간·주변 시설 개수) + 판결 카드 + 비교 목록. 주변 시설 `[]`이면 "주변 정보 없음"
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(detail): suspect file, verdict card, comparison"`

### Task 9: 평면도 → 실내 3D · 실내 입장/퇴장

**Files:**
- Create: `src/interior/buildInterior.ts`, `src/interior/InteriorScene.tsx`
- Modify: `src/world/WorldCanvas.tsx` (`useUi.indoor`가 있으면 실내 씬, 없으면 동네)
- Test: `src/interior/buildInterior.test.ts`, `src/interior/indoorFlow.test.ts`

**Interfaces:**
- Consumes: `GET /floorplans/{id}` (계약 FloorPlan), Task 3 `enterIndoor/exitIndoor`, Task 5 `getPlayerPose`, `teleport`
- Produces:
  - `buildInterior(fp: FloorPlan): { wallPieces: Box[]; floor: Polygon[]; spawn: [number, number, number] }` — `type Box = { center: [number, number, number]; size: [number, number, number]; rotationY: number }`
  - 문·창 처리: 열린 곳이 있는 벽은 **열린 곳 좌우 벽 + 문 위(인방) + 창 아래·위** 조각으로 나눔
  - `spawn` = `entrance`에서 방 안쪽으로 0.8m
  - 입장 시 `enterIndoor({ floorplanId, returnTo: 현재 위치 })`, 퇴장 시 `exitIndoor()` 후 `teleport(returnTo)`
  - `glbUrl`이 있으면 GLB 로드로 대체

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('plain wall is one piece', ...)          // 벽 1개, 열린 곳 없음 → wallPieces 1개, 길이 2.6, 높이 2.4
test('door splits wall into sides + lintel', ...) // offset 0.3, width 0.9, height 2.1 → 3조각, 인방 높이 0.3
test('window splits into sides + below + above', ...) // sill 0.9, height 1.2 → 4조각
test('spawn is inside near entrance', ...)    // entrance [1.3, 0] → spawn [1.3, 0, 0.8]
test('exit returns to saved position', ...)   // enterIndoor(returnTo [5,0,-3]) → exit 후 teleport 호출 인자 [5,0,-3]
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/interior` → FAIL
- [ ] **Step 3: 구현** — 조각마다 `boxGeometry`, 바닥은 `rooms` 폴리곤 `ShapeGeometry`, 방 이름 라벨. 청아진 18·18A FloorPlan JSON을 공유 픽스처에 작성(첫날 체크리스트)
- [ ] **Step 4: 통과 확인** — 테스트 PASS. 수동: 청아진 18타입 실내에서 걸어 다니고 문으로 나오면 원래 건물 앞
- [ ] **Step 5: 커밋** — `git commit -m "feat(interior): floor plan to 3d interior, enter and exit"`

### Task 10: 기숙사 투어 · 청년안심주택 · 공고 캘린더

**Files:**
- Create: `src/features/dorm/DormPanel.tsx`, `src/features/dorm/DormCard.tsx`, `src/features/housing/HousingPanel.tsx`, `src/features/housing/HousingDetail.tsx`, `src/features/housing/AnnouncementCalendar.tsx`, `src/features/housing/groupEvents.ts`, `src/api/queries/housing.ts`, `src/api/queries/dorm.ts`
- Modify: `src/world/Markers.tsx` (기숙사·단지 말풍선, `recruiting` 단지 강조는 Task 17)
- Test: `src/features/housing/groupEvents.test.ts`, `src/features/housing/HousingDetail.test.tsx`, `src/features/dorm/DormCard.test.tsx`

**Interfaces:**
- Consumes: `/dorms`, `/housing`, `/housing/{id}`, `/housing/announcements`, `/housing/{id}/subscribe`, Task 9 실내 입장
- Produces: `groupEventsByMonth(anns: Announcement[]): Map<string /*YYYY-MM*/, { date: string; type: EventType; housingName: string; status: AnnouncementStatus }[]>` (날짜 오름차순)

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('groups events by month sorted', ...)      // 11-20, 11-05, 12-01 → '2026-11' [11-05, 11-20], '2026-12' [12-01]
test('status badge labels', ...)                // OPEN → '접수 중', ADDITIONAL → '추가모집'
test('subscribe as guest opens login', ...)     // 토큰 없음 'D-day 알림 받기' 클릭 → 로그인 모달, 요청 없음
test('subscribed toggles', ...)                 // 로그인 → 클릭 후 '알림 받는 중'
test('dorm card shows monthly cost and meal', ...) // monthlyCost 300000, mealIncluded true → '월 30만 원 (식비 포함)'
test('unit type has indoor button', ...)        // floorplanId 있음 → '실내 들어가기'
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/housing src/features/dorm` → FAIL
- [ ] **Step 3: 구현** — 캘린더는 월 단위 목록형(달력 그리드 라이브러리 없이), D-day 표시 = 오늘 기준 남은 일수
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(housing,dorm): dorm tour, housing detail, announcement calendar"`

### Task 11: 찜 · 찜 목록

**Files:**
- Create: `src/features/favorites/HeartButton.tsx`, `src/features/favorites/FavoritesPanel.tsx`, `src/api/queries/favorites.ts`
- Test: `src/features/favorites/HeartButton.test.tsx`, `src/features/favorites/FavoritesPanel.test.tsx`

**Interfaces:**
- Consumes: `/me/favorites`, Task 3 `requireLogin`
- Produces: `<HeartButton type={FavoriteType} targetId={number} favorited={boolean} />` — 낙관적 업데이트, 실패 시 되돌림, `409`는 성공으로 처리. 말풍선·목록 카드·상세·단지·기숙사·양도에 공통 사용

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('guest click opens login, no request', ...)
test('optimistic toggle then confirm', ...)      // 클릭 즉시 '찜함', 서버 201 후 유지
test('rollback on server error', ...)            // 500 → '찜하기'로 되돌림 + 안내 토스트
test('409 treated as favorited', ...)
test('favorites panel click focuses target', ...)// 항목 클릭 → useUi.target 해당 lat/lng
test('dorm favorite shows no grade', ...)        // grade null → 등급 배지 없음
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/favorites` → FAIL
- [ ] **Step 3: 구현** — 성공 시 `['listings']`, `['favorites']` 쿼리 무효화
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(favorites): heart button and favorites list"`

### Task 12: 로그인 · 온보딩 · 프로필

**Files:**
- Create: `src/features/auth/LoginModal.tsx` (Task 3 자리 채움), `src/features/auth/Onboarding.tsx`, `src/api/queries/profile.ts`
- Test: `src/features/auth/LoginModal.test.tsx`, `src/features/auth/Onboarding.test.tsx`

**Interfaces:**
- Consumes: `/auth/email/send`, `/auth/email/verify`, `/me/profile`, `/departments`
- Produces: 토큰은 `localStorage['chatatda.token']`(접근 실패 시 메모리만), 로그인 후 프로필 로드. 온보딩 순서: 학과 선택 → 예산(만원) 입력 → 완료. 학과·예산은 건너뛰기 가능

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('rejects non-hanyang email inline', ...)  // a@gmail.com → 서버 400 INVALID_EMAIL_DOMAIN → '한양대 메일만 가능해요'
test('resend cooldown message', ...)           // 429 → '1분 뒤 다시 보낼 수 있어요'
test('verify stores token and loads profile', ...)
test('onboarding saves department and budget in won', ...) // 예산 60(만) → PUT budget.rentCap 600000
test('skip onboarding keeps guest-friendly defaults', ...)
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/auth` → FAIL
- [ ] **Step 3: 구현** — 게스트로 시작해도 되고, 로그인은 필요한 순간에만 요구
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(auth): email login, onboarding with department and budget"`

### Task 13: 양도 게시판

**Files:**
- Create: `src/features/transfer/TransferPanel.tsx`, `src/features/transfer/TransferDetail.tsx`, `src/features/transfer/TransferForm.tsx`, `src/features/transfer/AddressSearch.tsx`, `src/api/queries/transfer.ts`
- Test: `src/features/transfer/TransferForm.test.tsx`, `src/features/transfer/TransferDetail.test.tsx`

**Interfaces:**
- Consumes: `/transfers*`, `/geo/address`, `/uploads`, Task 8 `VerdictCard`(판정 표시 재사용), Task 5 순간이동
- Produces: 폼 값 → 계약 `POST /transfers` 본문(금액 원 단위). 상세의 "3D로 보기" = `focus({type:'TRANSFER', ...})`

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('address selection fills lat/lng/dong', ...) // 주소 검색 결과 클릭 → 폼 숨은 값 lat, lng, dong 채워짐
test('requires address before submit', ...)
test('submits money in won', ...)                 // 월세 45(만) → body.rent 450000
test('detail shows verdict from priceCheck', ...) // VerdictCard 렌더, contractMonths 8 → '8개월간'
test('owner sees edit and done buttons', ...)     // mine true → '수정', '양도 완료'
test('3D view focuses building', ...)
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/transfer` → FAIL
- [ ] **Step 3: 구현** — 사진은 `/uploads`로 먼저 올리고 URL만 본문에. 판결 문구의 "2년간"은 `contractMonths`가 24가 아니면 "{n}개월간"으로
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(transfer): transfer board with address search and verdict"`

### Task 14: 후기

**Files:**
- Create: `src/features/reviews/ReviewList.tsx`, `src/features/reviews/ReviewForm.tsx`, `src/api/queries/reviews.ts`
- Test: `src/features/reviews/ReviewForm.test.tsx`, `src/features/reviews/ReviewList.test.tsx`

**Interfaces:**
- Consumes: `/reviews`, Task 3 `requireLogin`
- Produces: 상세(매물·단지·기숙사) 하단에 목록·작성. 실내 후기 핀(G4, P2)은 `pin` 필드만 지원하고 UI는 시간 남으면

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('empty state', ...)               // count 0, average null → '아직 후기가 없어요', 'NaN' 없음
test('validates rating and length', ...)// 별점 미선택 → 제출 불가, 501자 → 제출 불가
test('guest write opens login', ...)
test('submits scores 1-5', ...)
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/reviews` → FAIL
- [ ] **Step 3: 구현**
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(reviews): review list and form"`

### Task 15: 내 집 기록 · 월간 리포트 · 알림

**Files:**
- Create: `src/features/home/MyHomePanel.tsx`, `src/features/home/HomeForm.tsx`, `src/features/home/MonthlyInputs.tsx`, `src/features/home/ReportCard.tsx`, `src/features/home/AlertSettings.tsx`, `src/features/notifications/Inbox.tsx`, `src/api/queries/home.ts`
- Test: `src/features/home/ReportCard.test.tsx`, `src/features/home/AlertSettings.test.tsx`, `src/features/notifications/Inbox.test.tsx`

**Interfaces:**
- Consumes: `/me/home`, `/me/payments`, `/me/utilities`, `/me/home/alerts`, `/me/report`, `/me/notifications`
- Produces: 내 집 미등록(`404`)이면 등록 폼부터. 알림함은 상단 종 아이콘 + 안 읽은 개수

- [ ] **Step 1: 실패하는 테스트 작성**
```tsx
test('report totals and top increase', ...) // 계약 5-9 예시 → '이번 달 74.2만', '지난달보다 4.1만 ↑', '가스비 2.1만 ↑'
test('report without previous month', ...)  // prevTotal null → 비교 문구 없음
test('report cumulative excess', ...)       // excess.cumulative 1312000 → '지금까지 적정가보다 131.2만 원 더 냈어요'
test('report pending excess', ...)          // excess null → '판정 보류'
test('alert add/disable/delete', ...)       // 60일 추가 → 목록 '만료 60일 전', 끄기, 삭제
test('alert range validation', ...)         // 0, 366 → 추가 불가
test('inbox unread count and mark read', ...)
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/features/home src/features/notifications` → FAIL
- [ ] **Step 3: 구현** — 공과금 입력 칸은 비워 두면 `null`로 전송
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(home): my home records, monthly report, alerts, inbox"`

### Task 16: 멀티플레이 클라이언트 · 초대 · 이모트·채팅

**Files:**
- Create: `src/net/worldReducer.ts`, `src/net/interpolate.ts`, `src/net/worldSocket.ts`, `src/net/useWorld.ts`, `src/world/RemotePlayers.tsx`, `src/features/world/InviteButton.tsx`, `src/features/world/EmoteChatBar.tsx`
- Test: `src/net/worldReducer.test.ts`, `src/net/interpolate.test.ts`, `src/net/worldSocket.test.ts`

**Interfaces:**
- Consumes: 계약 6장 메시지, `POST /invites`, Task 5 `getPlayerPose`, `teleport`
- Produces:
  - `type WorldModel = { selfId: string | null; players: Record<string, { nickname: string; samples: { t: number; p: [number, number, number]; r: number }[]; a: string; emote?: { e: string; until: number }; chat?: { m: string; until: number } }> }`
  - `worldReducer(m: WorldModel, msg: ServerMsg, now: number): WorldModel` — `welcome`은 players 통째로 교체(재접속 시 사라진 사람 정리), `state`는 샘플 추가(최근 10개), `leave` 삭제, `emote`·`chat`은 3초·5초 표시
  - `interpolate(samples, renderTime): { p; r }` — 렌더 시각 = 현재 − 100ms, 두 샘플 사이 선형 보간, 샘플 하나면 그대로
  - `connectWorld({ nickname, invite }): WorldConnection` — 자동 재접속 1s → 2s → 4s → 최대 10s, `move` 10Hz 제한(위치 변화 없으면 미전송), `ping` 15초
  - 초대: `?invite=` 읽어서 접속 후 URL에서 제거. "초대하기" = `POST /invites {playerId: selfId}` → URL 복사

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('welcome replaces players', ...)       // 기존 a,b → welcome [c] → players 키 ['c'] (self 제외)
test('state appends samples capped at 10', ...)
test('leave removes player', ...)
test('chat expires after 5s', ...)
test('interpolates midpoint', ...)          // t0 p[0,0,0], t100 p[10,0,0], render 50 → p[5,0,0]
test('single sample returns it', ...)
test('reconnect backoff 1,2,4,8,10,10', ...) // 가짜 타이머로 끊김 반복 → 재시도 간격 확인
test('move throttled to 10Hz and skipped when still', ...)
test('invite param removed after join', ...)
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/net` → FAIL
- [ ] **Step 3: 구현** — 다른 플레이어 캐릭터는 같은 캐릭터 모델 + 닉네임 라벨, `useFrame`에서 `interpolate`. 서버 `error: WORLD_FULL` → "지금 사람이 너무 많아요, 혼자 둘러보기" 안내 후 오프라인 모드
- [ ] **Step 4: 통과 확인** — 테스트 PASS. 수동: 브라우저 창 2개로 서로 보이는지, 초대 링크로 들어온 창이 초대한 캐릭터 옆에 나타나는지, 서버 재시작 후 자동 재접속
- [ ] **Step 5: 커밋** — `git commit -m "feat(world): multiplayer client, interpolation, invites, emotes and chat"`

### Task 17: 미니맵 · 시간대 조명 · 주변 시설 · 모집 중 단지 강조

**Files:**
- Create: `src/world/Minimap.tsx`, `src/world/minimapProject.ts`, `src/world/Lighting.tsx`, `src/world/NearbyIcons.tsx`
- Modify: `src/world/Markers.tsx` (`recruiting` 단지에 빛 기둥·깃발)
- Test: `src/world/minimapProject.test.ts`, `src/world/Lighting.test.ts`

**Interfaces:**
- Consumes: Task 4 `footprints`, Task 5 `getPlayerPose`, `/listings/{id}/nearby`
- Produces:
  - `minimapProject(x: number, z: number, view: { centerX: number; centerZ: number; radiusM: number; sizePx: number }): [px: number, py: number] | null` — 반경 밖이면 `null`, 위쪽 = 북쪽
  - `LIGHT_PRESETS: Record<'day' | 'evening' | 'night', { sun: [number, number, number]; intensity: number; ambient: number; fog: string }>`, 상단 토글로 전환
  - 주변 시설 아이콘: 선택한 집 반경 300m, `nearby` 결과의 카테고리별 아이콘

- [ ] **Step 1: 실패하는 테스트 작성**
```ts
test('center maps to minimap center', ...)  // (centerX, centerZ) → [sizePx/2, sizePx/2]
test('north is up', ...)                    // z 감소(북쪽) → py 감소
test('outside radius is null', ...)
test('night is darker than day', ...)       // LIGHT_PRESETS.night.intensity < day.intensity
```
- [ ] **Step 2: 실패 확인** — `npx vitest run src/world/minimapProject.test.ts src/world/Lighting.test.ts` → FAIL
- [ ] **Step 3: 구현** — 미니맵은 2D 캔버스에 건물 외곽 + 나 + 다른 플레이어 + 찜한 집
- [ ] **Step 4: 통과 확인** — PASS, 수동으로 30fps 유지 재확인
- [ ] **Step 5: 커밋** — `git commit -m "feat(world): minimap, time-of-day lighting, nearby icons, recruiting highlight"`

### Task 18: 실서버 전환 · 데모 점검 · 배포

**Files:**
- Modify: `.env.production`, `src/mocks/handlers.ts` (계약 변경분 반영)
- Create: `src/contract.smoke.test.ts`, `DEMO.md` (데모 시나리오 체크리스트)

**Interfaces:**
- Consumes: 백엔드 Task 16 배포 주소

- [ ] **Step 1: 실패하는 테스트 작성** — `contract.smoke.test.ts`: `VITE_API_BASE`가 실서버일 때만 실행, 계약 5장 GET 엔드포인트를 호출해 응답이 `types.ts` 필수 필드를 갖는지 확인(필드 존재 검사 함수 `hasKeys(obj, keys)`)
- [ ] **Step 2: 실패 확인** — `VITE_API_BASE=<배포 주소> npx vitest run src/contract.smoke.test.ts` → 불일치가 있으면 FAIL (불일치는 계약 문서 기준으로 어느 쪽을 고칠지 백엔드와 합의)
- [ ] **Step 3: 구현** — 불일치 수정, Vercel 배포(`VITE_USE_MOCK=false`)
- [ ] **Step 4: 통과 확인** — 스모크 PASS. `DEMO.md`의 스펙 10장 데모 6단계를 배포 주소에서 두 브라우저로 끝까지 수행
- [ ] **Step 5: 커밋** — `git commit -m "chore: switch to live api, contract smoke test, deploy"`

---

## 이 계획에서 뺀 것 (스펙의 P2·△, 시간 남으면)
- B6 캐릭터 꾸미기(과잠·학과 색), F3 언덕·계단 보정, G4 실내 후기 핀 UI, H8 거주자 평면도 등록, M2 밤길 안전 레이어, N2 수배 전단, D8 대안 추천(비교 패널 N3로 대체)

## 진행 순서 (백엔드와 맞추는 지점)
| 순서 | 프론트 Task | 의존 |
|---|---|---|
| 1 | 1~5 | 목 데이터만으로 진행 (백엔드 불필요) |
| 2 | 6~9 | 목으로 개발 → 백엔드 Task 4~7 끝나면 실서버로 확인 |
| 3 | 16 | 백엔드 Task 15와 같은 시기에 붙여서 오래 시험 |
| 4 | 10~13 | 백엔드 Task 8~10 |
| 5 | 14·15·17 | 백엔드 Task 11~14 |
| 6 | 18 | 백엔드 Task 16 |
