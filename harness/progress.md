# Harness ledger

원장 위치: `docs` 레포 `harness/progress.md` (작업 루트 기준 `docs/harness/progress.md`). 기능명세서는 `docs` 레포 `docs/spec-v0.5.md`.
레포: frontend · backend · campus-data · docs (각자 git, 원격 where-HYU-living/*). 작업 루트는 git 아님.

## Phases
- Phase 0: 원장 생성 (2026-11-08)
- Phase 1: complete — docs `spec-v0.5.md` 4-S 구현 상태 표(전 기능 ID·프론트/백엔드 상태·개선점). 테스트: 문서 단계라 없음(코드 대조로 확인)
- Phase 2-1: complete — backend `27c14ef`(신규 API 8묶음+알림 잡, `CommunityApiTest` 5건). 테스트: backend `gradlew test` 293/293 통과, 로컬 서버 스모크(검색·후기 201·내 집·리포트·알림) 통과
- Phase 2-2: 프론트 개선 — 진행 중

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
