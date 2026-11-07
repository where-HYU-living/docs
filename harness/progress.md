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
- Phase 3-2: 상단바 — 진행 중

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
