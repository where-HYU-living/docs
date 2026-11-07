# Harness ledger

원장 위치: `docs` 레포 `harness/progress.md` (작업 루트 기준 `docs/harness/progress.md`). 기능명세서는 `docs` 레포 `docs/spec-v0.5.md`.
레포: frontend · backend · campus-data · docs (각자 git, 원격 where-HYU-living/*). 작업 루트는 git 아님.

## Phases
- Phase 0: 원장 생성 (2026-11-08)
- Phase 1: complete — docs `spec-v0.5.md` 4-S 구현 상태 표(전 기능 ID·프론트/백엔드 상태·개선점). 테스트: 문서 단계라 없음(코드 대조로 확인)
- Phase 2-1: complete — backend `27c14ef`(신규 API 8묶음+알림 잡, `CommunityApiTest` 5건). 테스트: backend `gradlew test` 293/293 통과, 로컬 서버 스모크(검색·후기 201·내 집·리포트·알림) 통과
- Phase 2-2: complete — frontend `efed957` + I19 커밋(관리비 필터·양도 글 고치기·내 집 달 선택·지난 기록·전환율 4.6%·외형 문구·내 집 대비). 테스트: vitest 343/343, tsc 0
- Phase 2-3: complete — backend 초대 `expiresAt`. 테스트: WorldSocketIT 통과. K2 외부 저장소는 보류(범위 밖)
- Phase 3-1: complete — frontend `ddb3f0d`. 테스트: vitest 347/347, `scripts/labels-check.mjs`(전 최대 862m·겹침 2쌍 → 후 70m·0쌍), `scripts/tour-check.mjs`(12동네×3항목 36/36, h2 전체 63/63, 캠퍼스 안 63/63)
- Phase 3-2: complete — frontend 상단바 커밋. 테스트: vitest 347/347, `scripts/topbar-check.mjs` 4개 폭 OK

### 3-2 상단바 전/후 (로그인 상태, `scripts/topbar-check.mjs`)
| 폭 | 전: 보이는 컨트롤·필요 폭·문제 | 후: 바로 보이는 컨트롤·폭·도달 |
|---|---|---|
| 1920 | 14 · 1436px · 탭 6개 높이 32px(<40), 슬라이더 포커스 표시 없음 | 12 · 1888 안에 맞음 · 15/15(⋯·계정 메뉴 경유 5) |
| 1440 | 14 · 1436px(바 1408) → `로그아웃` 잘림 | 12 · 잘림 0 · 15/15 |
| 1280 | 14 · 1436px(바 1248) → `내 계정`·`로그아웃` 잘림 | 12 · 잘림 0 · 15/15 |
| 390 | 11 보임, `지도로 보기`·`내 계정`·`로그아웃` 접근 불가, `내 집 기록` 잘림, 바 높이 198px(5줄) | 4(검색·메뉴·⋯·계정) · 높이 44px 한 줄 · 15/15(메뉴 경유 13) |
- 위계: 상단 = 검색·탭 6·지도/3D·찜·알림·계정 / `⋯` = 시간대·캐릭터 꾸미기·초대 / 계정 메뉴 = 내 정보·로그아웃 / 760px 이하 = `메뉴`(현재 탭 이름 표시) 안에 탭·지도·찜·알림.
- 현재 메뉴: 탭 `aria-selected`(패널 열림은 배경, 닫힘은 밑줄), 메뉴 항목 `aria-current`. 클릭 영역 최소 40px(탭 40, 버튼 44). Tab 포커스 링 전 컨트롤(누락 1→0). Esc 로 닫고 연 버튼으로 포커스 복귀.
- Phase 3-3: complete — frontend 지도 모드 커밋. 테스트: vitest 352/352(`landing.test.ts` 5), `scripts/map-check.mjs` 6/6

### 3-3 지도 모드 결과 (`scripts/map-check.mjs`)
| 검색 | 카드 | 계획 | 도착 | 계획점까지 | y / 지면 | 범위 안 · 건물 안 |
|---|---|---|---|---|---|---|
| 장한평역 → 장한평역 5호선 | 3D 가능 · 장한평역 힐데스하임 | inside h5 (1709,-603) | h5 | 0m | 1.97 / 1.97 | true · false |
| 한양대학교 → 역사관 | 3D 가능 · 캠퍼스 | inside campus (37,15) | campus | 25m(빈자리) | 30.65 / 30.65 | true · false |
| 마장역 → 마장역 5호선 | 3D 가능 · 마장역 한영스테이 | inside h2 | h2 | 0m | 3.82 / 3.82 | true · false |
| 서울숲역 | 지원 밖 · 캠퍼스까지 1.2km | outside campus (36,209) | campus + 안내 문구 | 25m | 9.41 / 9.41 | true · false |
| 뚝섬역 | 지원 밖 · 캠퍼스까지 776m | outside campus (269,209) | campus + 안내 문구 | 0m | 6.10 / 6.10 | true · false |
- 마커 화면 중심 오차 0px(5건 모두). 상태 유지: 고른 곳 카드·필터(월세 60만)·3D 위치(변화 0.000m)·지도 중심/확대 모두 유지.
- 함께 고친 것: 카카오 장소 검색이 디바운스 중 이전 검색어 결과를 보여 줘 엉뚱한 곳을 누르던 문제, 거리순 정렬 때문에 '장한평역' 에 역 대신 근처 가게가 먼저 나오던 문제(정확도순).
- Phase 3-4: complete — frontend `fc4b6da`. 테스트: vitest 353/353, `scripts/perf-check.mjs 5`, `scripts/load-check.mjs`(vite preview)

### 3-4 성능 전/후
| 항목 | 전 | 후 | 방법 |
|---|---|---|---|
| 월드 전환 왕복(캠퍼스↔l6)당 증가 | geometry +22 · texture +8 | **0 · 0** (5왕복 291/143 고정) | 원인 3개: `PMREMGenerator` 미해제(평면 geometry·재질), PMREM 결과 렌더 타깃(`texture.dispose()` 로는 GL 텍스처가 안 지워짐 — `gl.createTexture` 추적으로 찾음), 조명 그림자 맵(`light.dispose()` 누락). 원본 HDR 도 해제 |
| 첫 로딩(20Mbps·40ms, 캐시 없음) → `__ready` | 5.92s | **4.82s** (−19%) | |
| 첫 로딩 내려받는 양 | 13,987KB (폰트 4,605KB) | **10,158KB** (폰트 348KB) | Pretendard 6굵기 전체 → 동적 서브셋(unicode-range) |
| JS 청크 | index 1,529KB(gzip 455) 한 덩어리 | index 254 · vendor-react 426 · vendor-three 774 (첫 화면 합 1,453KB, gzip 425) + 지연: InteriorScene 62 · KakaoMap 11 | `React.lazy` + `manualChunks` (라이브러리 청크는 재배포 때 캐시 유지) |
| 프레임 시간 p50 / p95 (q=med, 헤드리스) | 16.7 / 18.7ms | 16.6 / 18.9ms | 60fps 상한, 변화 없음 |
| 다시 방문(캐시) 로딩 | 2.2s | 2.3s | 월드 생성(CPU)이 대부분 — 그대로 |
- 남은 큰 덩어리: jpg 텍스처 4.5MB·HDR 1.4MB·world.json 1.0MB (텍스처 예산 12MB 는 테스트가 지킴).
- Phase 3-5: complete — frontend `d0802ce`. 테스트: vitest 355/355(소켓 재접속·전환 중 move 억제 2건 추가), `scripts/mp-check.mjs --restart-cmd=…` 12/12

### 3-5 멀티플레이 검증 (브라우저 컨텍스트 3~4개, 로컬 백엔드 /ws/world)
| 항목 | 결과 |
|---|---|
| 입장 | A 가 B 를 보기까지 2ms, 인원 1명 반영 |
| 위치 동기화 | 순간이동 4번 오차 최대 0.000m, 지연 52~205ms (move 10Hz + 서버 tick 100ms) |
| 걷기 | 상대에게 a=walk → 멈춘 뒤 idle, 멈춘 위치 오차 0.004m |
| 캠퍼스→동네(l6) 전환 | 연결 유지(selfId 같음), B 가 본 위치 = 실제 (322.1,-397.9), 전환 중에도 B 가 A 를 계속 봄 |
| 동네에서 초대 | 받은 C 가 l6 월드로 바뀌고 A 와 1.50m |
| 캠퍼스 초대 | D 가 캠퍼스에서 A 와 1.50m |
| 퇴장 | 창 닫고 156ms 뒤 사라짐 |
| 새로고침 재접속 | 새 id 등장·옛 id 제거 1ms |
| 연결 끊김(오프라인+소켓 끊김) | 상태 closed → 온라인 후 104ms 재접속, 3D 유지, 초대 자리로 다시 안 끌려감 |
| 중복 접속(같은 닉네임 2창) | 각자 id, 인원 3 |
| 서버 재시작 | 끊김 감지 52ms, 재기동 포함 15.1s 뒤 전원 재접속, 서로 다시 보임 4ms, 페이지 오류 0 |
- 고친 것: `useMultiplayer` 가 `api` 에 의존해 월드 전환마다 소켓 재접속(상대에게 퇴장·입장) → 연결 하나 유지, 전환 중엔 move 안 보냄 / 동네에서 아예 끊던 것 → 동네도 공유 / 초대한 사람이 동네면 받은 사람이 캠퍼스 월드 밖 들판에 서던 것 → 그 동네로 전환 / 재접속(같은 invite URL)마다 초대 자리로 끌려가던 것 → 첫 welcome 만.
- Phase 4: complete — frontend F6 커밋. 테스트: vitest 360/360(`routeLogic.test.ts` 5), `scripts/route-check.mjs` 16/16(목), 실서버 `/walk` 5곳 대조

### 4 집 → 학과 건물 경로 검증
프론트(목 서버, IT/BT관 305) — `scripts/route-check.mjs`
| 집 | 경로 길이 / 응답 거리 | 분: 버튼 = 응답 = 길 막대 | 시작↔집 · 끝↔건물 | 3D (월드 · 바닥 점·화살표 · 보이는+밖) | 캠퍼스로 이동 | 지도 폴리라인 |
|---|---|---|---|---|---|---|
| 4 | 651 / 651m | 8=8=8 | 0.0 · 0.0m | campus · 326·54 · 650+0m | - | 651m |
| 6 | 761 / 761m | 10=10=10 | 0.0 · 0.0m | campus · 381·63 · 759+0m | - | 761m |
| 10 | 1132 / 1132m | 14=14=14 | 0.0 · 0.0m | l4 · 492·81 · 982+148m | 캠퍼스 442m, 끝↔건물 0.0m | 1133m |
| 18 | 531 / 531m | 7=7=7 | 0.0 · 0.0m | l6 · 217·36 · 432+98m | 캠퍼스 530m, 끝↔건물 0.0m | 531m |
| 20 | 712 / 712m | 9=9=9 | 0.0 · 0.0m | campus · 268·44 · 533+177m | (이미 캠퍼스) | 712m |
| 학과 미설정 | - | - | - | '학과 고르기' 안내 표시 | - | - |

백엔드 실서버(TMAP) `/walk` 같은 5곳 (실매물 id)
| 집 | 목록 walkMin / walk 분 | 응답 거리 / 경로 길이 | 시작↔집 · 끝↔IT/BT관 | m/분 |
|---|---|---|---|---|
| 4 사근동 신축 분리형 | 14 / 14 | 1047 / 1047m (0.0%) | 4.6 · 21.6m | 75 |
| 6 사근동 풀옵션 원룸 | 11 / 11 | 804 / 804m (0.0%) | 8.0 · 21.6m | 73 |
| 10 행당동 분리형 원룸 | 20 / 20 | 1469 / 1468m (0.1%) | 25.4 · 21.6m | 73 |
| 18 마장동 분리형 원룸 | 16 / 16 | 1286 / 1287m (0.1%) | 4.3 · 21.6m | 80 |
| 20 마장동 1.5룸 | 26 / 26 | 2012 / 2012m (0.0%) | 7.5 · 21.6m | 77 |
- Phase 5-1: complete — 명세서 4-S 재갱신(Q8 추가, 커밋 기준 갱신, 상태·개선점 반영)
- Phase 5-2: complete — `scripts/final-qa.mjs` 로 4-S 80줄 실행: 프론트 통과 72·부분 3·미구현 2·해당없음 3, 백엔드 통과 49·미구현 2·해당없음 29. 실패 7건 한 번 고침(제품 버그 B4·K4 → frontend `300f19b`, 나머지 스크립트) → 실패 0
- Phase 5-3: complete — `harness/final-qa.md`
- Phase 5-4: 전체 테스트 backend 293/293 · frontend vitest 360/360 · tsc 0 · build OK · campus-data 11/11 → main 푸시·배포 확인 — 진행 중

### 3-1 결과
| 버그 | 회귀 원인 | 수정 | 전 | 후 |
|---|---|---|---|---|
| A 먼 라벨 | 110f243 의 거리 숨김(`style.display`)을 R3F `Post` 의 `CSS2DRenderer.render` 가 매 프레임 덮어씀(three r180 은 display 를 직접 씀). 이식 전엔 렌더 순서가 달라 가려져 있었음 | `src/world/labelCull.ts pickLabels` — 거리(말풍선 60m·이름표 90m)·화면 안·우선순위(내 집·과 건물 3, 입구 2, 랜드마크 1)·겹침 제거·최대 14개, `object.visible` 로 숨김 (0.1초마다) | 사자상 앞 보임 11·최대 862m·겹침 2 / 본관 사이 8·691m·1 / 동쪽 2·420m | 1·13m·0 / 0 / 0 / 말풍선 앞 2·70m·0 |
| B 동네→캠퍼스 투어 | `CampusTourPanel` 이 지금 월드(동네)의 `api.goToPlace` 에 캠퍼스 좌표를 넘김(빈자리 못 찾음). 지도 캠퍼스 핀도 같음 | `goTo.ts useGoToCampus` — 동네면 `useArea.goTo('campus', x, z)` → 도착 후 `NeighborhoodHud` 가 이동 | h2/l18 에서 120초 동안 이동 없음 | 36/36·63/63 통과, 건물까지 25m, 전환 1.5~1.8초 |


### 2-1 프론트↔백엔드 어긋남 표
| # | 항목 | 프론트 | 백엔드(이전) | 판단 기준 | 결과 |
|---|---|---|---|---|---|
| 1 | `GET /search` | 호출 | 없음(404) | 계약 5-3 | 백엔드 구현 (DB 매물→단지→기숙사→양도→건물, 모자라면 ADDRESS, 주소 실패해도 200) |
| 2 | `GET/POST /reviews` | 호출 | 없음 | 계약 5-8 | 백엔드 구현 (대상 존재 확인, pin [x,y,z] 검증, 평균 소수 1자리) |
| 3 | `/me/home`·`/me/payments`·`/me/utilities`·`/me/report` | 호출 | 없음 | 계약 5-9 | 백엔드 구현 (같은 달 덮어씀, 리포트 규칙 계약대로) |
| 4 | `/me/home/alerts` CRUD | 호출 | 없음 | 계약 5-9 | 백엔드 구현 |
| 5 | `/me/notifications`, `PATCH …/read` | 호출 | 없음 | 계약 5-10 | 백엔드 구현 + `NotificationJob`(매일 09:00 KST·기동 시, D-7/D-1/당일·만료 daysBefore, dedupe) |
| 6 | 단지·기숙사 `favorited` 제거(df59c0d) | 타입에 원래 없음, 하트는 `/me/favorites` 기준 | 제거됨 | 계약 5-6 | 일치, 변경 없음 |
| 7 | 양도 `title`·사진 업로드 | `TransferBody.title`, `POST /uploads` multipart | 있음 | 계약 5-7 | 일치 |
| 8 | FloorPlanLinker 매물 평면도 101~107 | `neighborhoodSites.json` l4→103 … l20→106 | 같은 값 | 데이터 | 7건 모두 일치(로컬 API 대조) |
| 9 | 양도 `floorplanId` | `WorldEffects` 가 있으면 문 마커 | 필드 없음 | 계약에 없음 | 보류 — 양도 글엔 평면도 개념 없음, 프론트 분기는 무해 |
| 10 | 초대 응답 `expiresAt` | 안 씀 | 없음 | 계약 5-10 | 보류(프론트 미사용) |
| 11 | 일시 형식 | `Date` 로 파싱 | `Instant` → `…Z` | 계약은 `+09:00` | 보류 — 프론트 파싱 문제 없음 |
| 12 | `GET /walk` | 안 씀 | 있음(path 포함) | 계약 5-2 | 4단계 F6 에서 사용 |
| 13 | 캐릭터 외형 공유 | 안내 문구가 "다른 접속자에게 안 보여요" | `look` 중계 구현 | 계약 6장 | 2-2 에서 문구 수정 |


## Findings
- 목 서버의 매물 id 4·6·10·18·20 은 실서버 같은 id 와 주소가 다르다(예: 목 10 = 성수동). `world/neighborhood.ts siteForListing` 은 실서버 id 기준이라 목 모드의 '주변 걸어보기' 는 엉뚱한 동네로 갈 수 있음(실서버는 정상).
- 실서버 TMAP 경로 끝점은 IT/BT관 좌표에서 21.6m(건물 입구 쪽 도로로 스냅) — 허용.
- 프론트 환산 월세 미리보기(`forms/calc.ts`)가 전환율 6% 로 서버(4.6%)와 달랐음 → 2-2 에서 맞춤.
- 프로덕션 API = `https://api-production-8811.up.railway.app` (Vercel 번들에서 확인). 로컬 DB 는 청년안심주택 0건(수집 잡 꺼짐)·실거래 없음 → 등급 전부 PENDING. 프로덕션은 단지 5·기숙사 5·등급 계산됨.
- 로컬 QA 토큰: 메일 로그 모드 → `scratchpad/token.sh <메일>`.
- 백엔드에 없는 API(프론트는 호출): `/search`, `/reviews`, `/me/home`, `/me/payments`, `/me/utilities`, `/me/report`, `/me/home/alerts`, `/me/notifications`. 실서버에선 해당 화면이 항상 오류.
- 라벨 겹침(3-1 A) 원인 후보: R3F 이식 후 `Post` 가 매 프레임 `CSS2DRenderer.render` 를 부르는데 three r180 CSS2DRenderer 가 `element.style.display` 를 매번 덮어써, `buildWorld.js frame()` 의 거리 숨김(LABEL_NEAR 90·MARKER_NEAR 60, 커밋 110f243)이 무효.
- 3-1 B 원인 후보: `CampusTourPanel.go` 가 지금 월드(동네)의 `api.goToPlace` 에 캠퍼스 좌표를 넘김 → 동네 월드 안에서 빈자리 못 찾거나 엉뚱한 곳.
- 멀티플레이: `useMultiplayer` effect 가 `api` 에 의존 → 월드 전환마다 소켓 재접속(상대에게 퇴장·입장). 초대자가 동네 월드면 받은 사람은 캠퍼스 월드에서 그 좌표로 이동(월드 밖).
- docs 레포의 미커밋 `api-contract.md` 변경(`look` 메시지, max-players 30)은 백엔드 `WorldService`/`WorldPlayer` 구현과 일치.

## Rulings
- Ruling: 원장 경로 `docs/harness/progress.md` 를 작업 루트 기준으로 해석해 docs 레포 `harness/progress.md` 에 둔다. 이유: 명세서 경로 `docs/docs/` 도 같은 기준이라야 둘 다 성립. 틀리면 비용: 파일 이동 1회.
- Ruling: 서브에이전트·todo 도구가 없으므로 이 원장의 Phases/할 일 목록을 todo 로 쓴다. 틀리면 비용: 없음.
- Ruling: 기능명세서 개편은 기존 4장 표(제품 설명)를 두고 4-S 상태 표를 새로 붙이는 방식. 이유: 기존 우선순위·담당 열을 보존하면서 프론트/백엔드 상태·개선점 열을 한 표에 모음. 틀리면 비용: 표 합치기 1회.
- Ruling: 남이 남긴 미커밋 `api-contract.md`·`backend-request-world-look.md` 를 함께 커밋. 이유: 백엔드 코드와 대조해 내용이 맞음. 틀리면 비용: revert 1회.
- Ruling: 백엔드에 없는 8개 API 는 계약 문서(기준 문서)에 이미 정의돼 있으므로 백엔드를 계약대로 구현(프론트를 바꾸지 않음). 틀리면 비용: 백엔드 담당과 필드 협의 1회.
- Ruling: 새 테이블은 JPA 엔티티 없이 JdbcTemplate(기존 DormService 방식). 이유: ddl validate 부담·코드량 감소. 틀리면 비용: 엔티티 전환 시 리팩터 1회.
- Ruling: 양도 사진 외부 저장소(S3 등) 전환은 외부 서비스 설정이라 하지 않고 보류로 기록. 틀리면 비용: 재배포 때 데모 사진 재업로드.
- Ruling: 3-1 B '12개 동네 전부에서 각 항목' 은 동네마다 첫·가운데·마지막 3항목 + 신고된 h2 는 63항목 전부 + 캠퍼스 안 63항목 전부로 검증. 이유: 항목 이동 로직은 항목과 무관하게 같은 경로(useGoToCampus)라 표본으로 충분, 전수는 12×63 월드 로드(약 40분). 틀리면 비용: `node scripts/tour-check.mjs --items=63` 한 번.
- Ruling: 말풍선 최대 거리 60m·이름표 90m 는 110f243 의 원래 값을 유지하고 최대 14개·겹침 제거를 더함. 틀리면 비용: 상수 2개 조정.
- Ruling: 상단바에서 시간대·의상·초대를 '⋯' 로 접음(사용 빈도 낮음, 데모 핵심 흐름은 검색·탭·지도·찜). 틀리면 비용: 버튼 하나를 바깥으로 꺼내는 CSS·JSX 몇 줄.
- Ruling: 지도 모드 '3D로 가기' 는 서비스 안이면 그 지점에 바로 서고(못 서면 25~90m 빈자리), 밖이면 가장 가까운 월드(캠퍼스는 범위 40m 안쪽으로 당긴 점, 동네는 집 앞 기본 자리) + 안내 문구. 틀리면 비용: `world/landing.ts` 규칙 수정.
- Ruling: 지도 이동 허용 범위를 캠퍼스만 → 캠퍼스+동네 12곳+매물+검색한 곳(최대 축소 level 8)으로 넓힘. 이유: 장한평 등 검색 결과가 범위 밖이면 지도가 되돌아감. 틀리면 비용: 상수 2개.
- Ruling: 성능 병목 3개를 (1) 월드 전환 누수 (2) 폰트 4.6MB (3) 단일 번들 순으로 고름. 근거: 전환 누수는 알려진 결함, 폰트는 첫 로딩 바이트의 33%, 번들은 캐시 효율. 프레임 시간은 이미 60fps 상한이라 손대지 않음. 틀리면 비용: 텍스처·HDR 축소 추가 작업.
- Ruling: '동네 둘러보기는 혼자(v1)' 였던 것을 바꿔 동네 월드에서도 공유 월드 연결을 유지. 이유: 좌표계가 같아 위치가 그대로 맞고, 스펙 B7·초대(B8)가 '같이 걷기'. 틀리면 비용: `enabled` 한 줄.
- Ruling: `/walk` 실패(로컬처럼 TMAP 키 없음)는 계약대로 서버 502 를 두고, 프론트가 직선 추정(1.25배·80m/분)으로 대신 그리되 '직선 추정' 표시. 틀리면 비용: 서버 fallback 추가.
- Ruling: 경로 3D 는 '집이 있는 월드' 로 가서 그 월드 범위 안 구간만 그리고, 나머지는 길 막대에 '밖으로 이어지는 길 ○m(약 ○분)' + '캠퍼스로 이동'(경로가 캠퍼스에 처음 들어가는 점). 틀리면 비용: RouteHud 문구·버튼.
