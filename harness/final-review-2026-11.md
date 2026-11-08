# 최종 리뷰: 명세 대조 · 코드 리뷰 · 동시성 · 성능 · 반응성 (2026-11-08)

기준 문서: `docs/spec/feature-spec.md`(기능 ID A1~X5), `docs/spec/api-spec.md`.
범위 밖: AI 서버(`ai-server/`)와 AI 호출 경로. AI 모드는 꺼진 상태(`AI_ENABLED=false`)가 맞고, AI 적정가는 `backend/src/main/resources/fixtures/ai-rent.json` 에서 온다(판결 카드 표시까지는 확인함).
확인 방법: 화면 캡처 없이 DOM·좌표·응답 코드·시간만 잰다. 로컬 = docker 백엔드(최신 코드 + V12) + vite dev, 운영 = 읽기 전용(GET 만, 쓰기 요청은 브라우저에서 막음).

## 0. 요약

| | 전 | 후 |
|---|---|---|
| 백엔드 테스트 (`./gradlew test`) | 321 통과 | **334 통과** (회귀 13개 추가) |
| 프론트 단위 테스트 (`vitest`) | 413 통과 | **423 통과** (회귀 10개 추가) |
| `tsc` | 0 | 0 |
| 새 E2E `scripts/qa-final.mjs local` | 58/107 (스크립트 오탐 포함) | **120/120** (4폭 × 탭 8개 레이아웃·반응, 상세·판결·지도·실내·폼 5종, 상단바 8폭) |
| 기존 E2E `scripts/final-qa.mjs` | 실패 9 (화면 개편 뒤 선택자 낡음 + `MOCK` 정의 누락) | **통과 121**, 실패 0 (부분 3 = 구글 실제 로그인·3D 핀 좌표·가로등 품질, 자동화 한계 / 미구현 1 = F3 경로 고도) |
| 멀티플레이 `scripts/mp-check.mjs` | 11/11 | 11/11 (동네 초대 26m 어긋남을 찾아 고친 뒤) |
| 도보 계산 동시 요청 14개 (캐시 없음) | **30.3초 멈춤, 4개 500**, 그동안 다른 API 도 멈춤 | 15개(TMAP 60번) 모두 200, 1.8초. 그동안 다른 API 10~24ms |
| 첫 화면을 막는 CSS | 606KB (gzip 196KB) | 134KB (gzip 30KB) |
| `vendor-react` 번들 | gzip 136KB | gzip 112KB (`react-dom/server` 제거) |
| `/listings` 응답 | 6.6KB | 1.2KB (gzip 켬) |
| 운영 읽기 전용 E2E `qa-final.mjs prod` | — | **78/78**, 운영으로 나간 쓰기 요청 0 |

P0 1건(DB 연결 고갈로 API 전체 정지), P1 15건, P2 30여 건을 고쳤다. 고치지 않고 결정이 필요한 것은 4장.

## 1. 기능 ID 추적표

판정: **일치** · **고침**(이번에 어긋남을 고침) · **명세 낡음**(코드가 맞음, 3장에 수정안) · **부분**.
프론트 경로는 `frontend/src/`, 백엔드 경로는 `backend/src/main/java/com/chatatda/api/` 기준.

| ID | 프론트 | 백엔드 | 테스트 | 판정 | 비고 |
|---|---|---|---|---|---|
| A1 | `app/LoginModal.tsx`, `app/auth/`, `state/session.ts` | `auth/GoogleAuthController.java:17`, `auth/AccountService.java` | AuthApiTest, final-qa A1·A8 | 고침 | 첫 로그인 연타 500 → 계정 하나만 (upsert). 만료 토큰 저장 요청이면 로그인 창 다시 띄움. 늦게 온 401 이 새 로그인 내보내던 경합 고침 |
| A2 | `app/ProfileModal.tsx`, `DepartmentPicker.tsx`, `BuildingPicker.tsx` | `user/ProfileController.java:15`, `user/ProfileService.java:41` | qa-final A2, FinalQaFixesTest | 고침 | 예산 지우기 안 되던 것, 동시 저장 500(행 잠금), 첫 로그인 안내가 새 창마다 다시 뜨던 것(localStorage) |
| B1 | `world/WorldCanvas.tsx`, `buildWorld.js`, `player.js` | — | final-qa B1·B2 | 고침 | 입력칸·글상자에서 WASD 치면 캐릭터가 걷던 것 (`lib/keys.ts`) |
| B2 | `app/NeighborhoodButton.tsx`, `app/visit.ts` | — | neighborhood.test, qa-final D2 | 고침 | 동네 집 빛 기둥이 단지 표시 토글 때 사라지던 것 (빛 기둥 묶음 분리) |
| B3 | `buildWorld.js` 미니맵 | — | final-qa M4 | 일치 | 건물 위 두 번 누름은 막고 안내 |
| B4 | `world/timeOfDay.ts`, `TopBar.tsx` | — | effects.test | 일치 | |
| B5 | `ListingMarkers.tsx`, `PlaceMarkers.tsx`, `TransferMarkers.tsx` | 목록 API | qaFixes·favorites.test | 고침 | 청년안심주택·양도 말풍선을 누르면 앞서 연 다른 상세가 열리던 것 |
| B6 | `WorldEffects.tsx` | `/housing`, `/buildings`, `/me/profile` | effects.test | 일치 | |
| B7 | `WorldEffects.tsx` | `listing/ListingController.java:66` | final-qa | 일치 | |
| B8 | `world/doors.ts`, `worldExtras.js` | `/dorms`, `/housing/{id}` | final-qa | 일치 | |
| B9 | `app/map/LandingNotice.tsx`, `world/serviceArea.ts` | — | final-qa B4 | 일치 | |
| C1 | `TopBar.tsx`, `features/search.ts` | `search/SearchController.java:26` | final-qa A5 | 부분 | 고른 뒤 패널을 닫고 3D 로 감(상세는 선택만) → 4장 결정 |
| C2 | `app/map/KakaoMap.tsx` | 목록 API | qa-final C2 | 일치 | 지도 전환 18~506ms |
| C3 | `app/route/` | `geo/GeoController.java:24`, `geo/WalkService.java` | WalkServiceTest, FinalQaFixesTest | 고침 | P0: 도보 계산이 DB 연결을 쥔 채 TMAP 을 기다려 연결 고갈. 잘못된 좌표 3번에 TMAP 이 모두에게 60초 꺼지던 것 |
| C4 | `CampusTourPanel.tsx` | — | CampusTourPanel.test | 일치 | |
| D1 | `ListingsPanel.tsx`, `features/listings.ts` | `listing/ListingController.java:23` | ListingsPanel.test | 고침 | 필터 한 글자마다 요청·깜빡임 → 250ms 기다렸다 받고 앞 결과 유지. 큰 page 500 → 400 |
| D2 | `ListingDetailView.tsx` | `listing/ListingController.java:60` | final-qa D1, qa-final | 일치 | 목록 클릭은 정보만, 3D 이동은 [3D에서 보기] (명세 낡음) |
| D3 | `VerdictCard.tsx`, `dossier/PriceLineup.tsx` | `pricing/PriceCheckService.java` | VerdictCard.test, qa-final X1·D3 | 명세 낡음 | 근거(표본 수·기간) 줄은 화면에서 뺐다. AI 적정가 표시 확인(로컬·운영 20/20) |
| D4 | `dossier/WantedFlyer.tsx` | price-check | VerdictCard.test | 일치 | |
| D5 | `dossier/CompareSection.tsx` | `compare/AlternativeService.java` | qaFixes | 명세 낡음 | '근처'가 아니라 가장 싼 3곳, 더 싼 자취방은 현재 필터 결과에서 |
| E1 | `interior/` | `floorplan/FloorPlanController.java:39` | interior 테스트, qa-final E1 | 고침 | 핀 후기 쓰다 Esc 누르면 실내에서 튕겨 나가 글을 잃던 것 |
| G1 | `ReviewSection.tsx` | `review/ReviewController.java:33` | CommunityApiTest, qa-final G1 | 고침 | 항목 별점을 빨리 누르면 앞 것이 지워지던 것(이전 값 기준 갱신). 별점 4.7 을 4로 받던 것 → 400 |
| G2 | `interior/PinPanel.tsx`, `pins.ts` | 같은 API | interiorLogic.test | 부분 | 매물 실내에서는 핀 후기를 못 남김(기숙사·단지만) → 4장 |
| F1 | `HeartButton.tsx`, `features/favorites.ts` | `favorite/FavoriteController.java:20` | favorites.test | 고침 | 로그아웃·계정 바꾸기 뒤 앞사람 찜이 하트·3D 말풍선에 남던 것. 하트 이름표에 집 이름 |
| F2 | `FavoritesPanel.tsx` | 같은 API | favorites.test | 고침 | 고른 종류의 마지막 찜을 풀면 칩이 사라지고 빈 목록에 갇히던 것 |
| I1 | `HousingPanel.tsx` | `housing/HousingController.java:21` | panels.test | 일치 | |
| I2 | `HousingPanel.tsx` | `housing/HousingController.java:41` | panels.test | 고침 | 면적 없는 주택형이 "null㎡", 관리비 없음이 "-" |
| I3 | `HousingPanel.tsx` | `housing/HousingController.java:53` | CommunityApiTest | 고침 | 구독 버튼 연타·구독 때 단지 상세 30개를 다시 받던 것 |
| I4 | `HousingPanel.tsx` 캘린더 | `housing/HousingController.java:47` | panels.test | 일치 | |
| P1 | `DormPanel.tsx` | `dorm/DormController.java:13` | FinalQaFixesTest, DormApiTest | 고침 | `GET /dorms` 가 도보 분을 늘 null 로 줘 기숙사 탭에 도보가 안 나왔다 → buildingId·로그인 사용자 기준으로 계산 |
| K1 | `TransferPanel.tsx` | `transfer/TransferController.java:27` | TransferApiTest | 일치 | |
| K2 | `TransferPanel.tsx`, `AddressPicker.tsx`, `forms/` | `transfer/TransferController.java`, `UploadController.java` | more.test, qa-final K2 | 고침 | 사진 올리는 중에 올리기를 누르면 사진이 빠지던 것. 국외 좌표 저장되던 것 → 400 |
| K3 | `TransferPanel.tsx` | `transfer/TransferController.java:62·67` | TransferApiTest | 고침 | 고치기와 양도 완료가 동시에 오면 완료가 조용히 되돌아가던 것(@Version, 409). 양도 완료는 한 번 더 묻기 |
| H1 | `MyHomePanel.tsx` | `home/HomeController.java:44·49` | CommunityApiTest, qa-final H1 | 일치 | 달력이 화면·패널 안에 들어옴(1280·380) |
| H2 | `MyHomePanel.tsx` RentRow | `home/HomeController.java:59` | qa-final H2 | 일치 | |
| H3 | `MyHomePanel.tsx` UtilityRows | `home/HomeController.java:70` | final-qa H3 | 고침 | 공과금 칸을 빨리 고치면 앞 칸이 지워지던 것, 다 비어 있으면 "0만" |
| H4 | `MyHomePanel.tsx` ReportCard | `home/HomeService.java:169` | qaFixes, CommunityApiTest | 고침 | 적정가보다 싼 집이 "-12만 원 더 냈어요". 계약이 끝난 뒤 달은 누적이 계약 기간보다 커지던 것 |
| H5 | `MyHomePanel.tsx` 알림 | `home/HomeController.java:81` | FinalQaFixesTest | 고침 | 같은 '며칠 전' 알림이 연타로 여러 개 생기던 것 (V12 고유 인덱스 + upsert) |
| Q1 | `InboxPanel.tsx`, `TopBar.tsx` | `notification/NotificationController.java:19` | CommunityApiTest | 일치 | |
| M1 | `net/`, `interior/IndoorPeers.tsx` | `world/WorldService.java` | net.test, mp-check | 일치 | 실내 room 은 명세에 반영됨 |
| M2 | `WorldChat.tsx` | `world/WorldService.java` | mp-check | 일치 | |
| M3 | `InviteButton.tsx`, `net/useRoomInvite.ts` | `world/InviteController.java:16`, `InviteService.java` | FinalQaFixesTest | 고침 | 나간 사람의 초대 토큰이 24시간 남아 토큰 자리를 차지하던 것 |
| M4 | `app/avatar/`, `world/avatar.ts` | `world/WorldService.java` (look) | mp-check | 일치 | CLAUDE.md 의 "내 화면에만" 문장이 낡아 고침 |
| S1 | `gfx.ts`, `quality.ts`, `WorldCanvas.tsx` | — | gfx-check | 고침 | 품질이 바뀔 때마다 GTAO 렌더 타깃이 GPU 에 남던 것, AO 끈 품질에서도 후처리 타깃을 만들던 것 |
| S2 | `App.tsx` | — | — | 일치 | |
| S3 | `TopBar.tsx`, `app.css` | — | qa-final S3 | 고침 | 1024 폭에서 계정 버튼이 화면 밖으로 10px 나가던 것 |
| X1 | `VerdictCard.tsx` | `pricing/`, fixtures | qa-final X1 | 일치 | AI 꺼짐 → fixture 값, 로컬·운영 20/20 |
| X2 | — | `floorplan/` | (AI 범위 밖) | 해당없음 | |
| X3 | — | `housing/HousingIngestJob.java` | HousingIngestTest | 고침 | 06시 수집이 도는 동안 예약 스레드 1개를 다 써서 멀티플레이 틱이 멈추던 것 (스케줄 스레드 4개) |
| X4 | — | `notification/NotificationJob.java` | CommunityApiTest | 일치 | 중복 방지 키로 여러 인스턴스에서도 한 번 |
| X5 | — | `listing/ListingGradeJob.java` | — | 고침 | 서버를 다시 켜지 않으면 달이 바뀌어도 목록 등급이 옛 창으로 남던 것 → 매달 1일 다시 계산 |

## 2. 발견 목록

심각도: **P0** 기능 깨짐·데이터 오류·보안 / **P1** 흐름 막힘·잘못된 표시·실제로 일어날 경합·눈에 띄는 누수 / **P2** 다듬기.
위치: `BE` = `backend/src/main/java/com/chatatda/api/`, `FE` = `frontend/src/`. 모두 고쳤고, 검증 열의 테스트·수치로 다시 확인했다.

### P0

| # | 문제 | 위치 | 재현 (전) | 고친 방법 | 검증 (후) |
|---|---|---|---|---|---|
| 1 | 도보 시간 캐시에 없는 요청이 몰리면 DB 연결이 바닥나 **API 전체가 30초 멈춤** | BE `geo/WalkCacheStore.java`, `geo/WalkService.java`, `listing/ListingService.java:73`, `housing/HousingService.java`, `transfer/TransferService.java:66`, `dorm/DormService.java` | 비로그인 `GET /listings?buildingId=107&size=1` 14개 동시 → 전부 30.3초, 4개 500 (`HikariPool … Connection is not available`), 그동안 다른 API 도 멈춤. 저장 실패가 TMAP 실패로 세어져 TMAP 이 60초 꺼짐 | 읽기 트랜잭션이 연결을 쥔 채 TMAP(3초)을 기다리고, 캐시 저장이 `REQUIRES_NEW` 로 연결을 하나 더 빌려 서로 막혔다 → ① 목록 API 는 DB 읽기와 도보 계산을 나눔(연결을 돌려준 뒤 TMAP) ② 트랜잭션 안의 캐시 저장은 별도 한 줄 스레드로(밀리면 버림) ③ 같은 자리·건물은 TMAP 한 번만(동시 요청 합침) ④ 저장 실패는 TMAP 실패로 안 셈 ⑤ 연결 20개·대기 5초 | 캐시 없는 `maxWalkMin` 목록 15개 동시(TMAP 60번) → 전부 200, 1.8초. 그동안 `/departments` 10~24ms. `FinalQaFixesTest.sameWalkKey_atOnce_callsTmapOnce` |

### P1

| # | 문제 | 위치 | 재현 (전) | 고친 방법 | 검증 |
|---|---|---|---|---|---|
| 2 | 메일 코드 로그인 대입·경합: 재전송마다 틀린 횟수가 0으로(분당 5번), 틀린 횟수 동시 갱신으로 5번 넘게 평가, 첫 전송 동시 요청 10통 발송 | BE `auth/EmailCodeService.java`, `auth/EmailCodeRepository.java`, `auth/AuthController.java` | 틀린 코드 40개 동시 → 10개 평가. 첫 전송 10개 동시 → 메일 10통, 500 7개 | 행 잠금(`findForUpdate`)으로 한 줄씩, 다 틀려 잠기면 15분 뒤에야 새 코드, 첫 전송 경합은 429. `EMAIL_LOGIN_ENABLED` 스위치 추가(운영 끄기 권장, 4장) | `wrongCodes_atOnce_countEveryTry`(12개 동시 → 5), `emailSend_atOnce_mailsOnce`, `AuthApiTest` |
| 3 | 잘못된 좌표 요청 3번이면 TMAP 이 모두에게 60초 꺼짐. 국외 좌표 양도 글·내 집이 저장됨 | BE `geo/WalkService.java`, `transfer/TransferDtos.java:25`, `home/HomeService.java:36` | `/walk?fromLat=999&fromLng=-999` ×3 → 정상 좌표도 502 | 서비스 지역 밖 좌표는 TMAP 을 부르지 않음(`/walk` 는 400), 저장 DTO 에 위경도 범위 검증 | `badCoordinates_…`, `transferCoordinates_outsideKorea_are400` |
| 4 | `GET /dorms` 가 도보 분을 늘 null → 기숙사 탭에 도보가 안 나옴 (로컬·운영 둘 다) | BE `dorm/DormController.java`, `dorm/DormService.java` | `/dorms?buildingId=101` → walkMin 전부 null | buildingId·로그인 사용자 첫 건물 기준으로 계산 (트랜잭션 밖) | `dormList_hasWalkMin_whenBuildingGiven`, 로컬 `[11,13,14,11,16]` |
| 5 | 업로드 사진 주소가 프록시 뒤에서 `http://` | BE `application.yml` | `X-Forwarded-Proto: https` 무시 | `server.forward-headers-strategy: framework` | (컨테이너 디스크 문제는 4장) |
| 6 | 로그아웃·다른 계정 로그인 뒤 앞사람 찜이 하트·3D 말풍선에 남고, 로그인해도 도보 분이 '정보 없음'으로 남음. 내 정보 저장 뒤 상세·판결의 도보·예산이 옛 값 | FE `app/features/personal.ts`(새), `App.tsx`, `features/catalog.ts` | 토큰이 바뀌어도 아무 쿼리도 무효화하지 않았다. 찜 키가 `['favorites', !!token]` | 토큰이 바뀌면 /me 기록 삭제 + 사람마다 다른 쿼리 다시 받기, 찜 덮어쓰기 초기화, 찜 키에 토큰 | `qaFixes.test` 로그아웃·계정 바꾸기 |
| 7 | 예산을 비워 저장해도 지워지지 않음 | FE `ProfileModal.tsx:49` | 둘 다 비우면 `budget: undefined` → 서버가 건너뜀 | 늘 `{rentCap, depositCap}` 를 보냄(null 이면 지움) | 서버 `Budget` null 허용 확인 |
| 8 | 적정가보다 싼 집 리포트가 "−12만 원 더 냈어요", 계약 끝난 달은 누적이 계약 기간보다 큼 | FE `MyHomePanel.tsx` `excessPhrase`, BE `home/HomeService.java:187` | 2030-01 리포트 누적 25.4M (24개월 최대 12.97M) | 부호에 따라 더/덜, 1만 원 안쪽은 '거의 같아요', 지난 달 수를 계약 기간 안으로 자름 | `qaFixes.test` excessPhrase |
| 9 | 면적 없는 주택형이 "null㎡" | FE `api/types.ts:79`, `HousingPanel.tsx:54` | 서버 `exclusiveAreaM2` nullable | `number \| null`, '면적 정보 없음' | tsc |
| 10 | 후기·설명을 쓰다 WASD·방향키를 치면 캐릭터가 걷고, 실내에서 핀 후기 쓰다 Esc 면 튕겨 나가 글을 잃음 | FE `player.js:108`, `interior/Walker.tsx:67`, `interior/InteriorScene.tsx:110`, `lib/keys.ts`(새) | INPUT 만 걸렀다 | 입력칸·글상자·선택 상자·편집 요소는 무시, Esc 는 입력칸에서 빠져나오기만, 로그인 창·핀 후기 쓰기가 열려 있으면 안 나감 | `qaFixes.test` isTypingTarget |
| 11 | 3D 청년안심주택·양도 말풍선을 누르면 앞서 연 다른 상세가 열림 | FE `PlaceMarkers.tsx:33`, `TransferMarkers.tsx:20` | 탭만 바꿨다 | 그 단지·글을 선택하고 탭 열기 | 코드 확인 |
| 12 | 오류 경계가 없어 새 배포 뒤 옛 탭에서 지도·실내를 열면 앱 전체(3D 포함)가 하얗게 사라짐 | FE `ErrorBoundary.tsx`(새), `App.tsx`, `api/client.ts` | 지운 코드 조각 404 → React 루트 해제 | 패널·지도·실내를 경계로 감싸 그 자리만 안내(새 버전이면 새로고침 권함), 2xx 인데 JSON 아니면 오류로 | `qaFixes.test` 경계 2개 |
| 13 | 품질이 바뀔 때마다(자동 낮추기·메뉴) GTAO 렌더 타깃이 GPU 에 남음, AO 끈 품질에서도 후처리 타깃을 만듦 | FE `world/WorldCanvas.tsx:69`, `interior/InteriorPost.tsx` | `EffectComposer.dispose` 는 붙인 패스를 안 푼다 | 패스마다 dispose, AO 끄면 composer 를 안 만듦 | perf-check (5장) |
| 14 | 시간대 슬라이더를 끌면 열린 패널(카드 100장)이 매 틱 다시 그려짐 | FE `SidePanel.tsx:24`, `ListingsPanel.tsx` | 스토어 전체 구독 | 필드별 구독 | 코드 확인 |
| 15 | 1024 폭에서 상단바 계정 버튼이 화면 밖으로 10px (E2E 로 찾음) | FE `app/app.css` | 닉네임이 보이면 탭 6개 + 버튼들이 넘침 | 1100px 이하에선 계정은 아이콘만, 긴 닉네임은 … | qa-final `S3:상단바 폭별 넘침` (761~1440, 25자 닉네임) |
| 16 | 동네에서 초대 링크로 들어온 사람이 가끔 초대한 사람과 26m 떨어져 섬 (mp-check 2번 연속 실패로 찾음) | FE `NeighborhoodButton.tsx` | 초대 자리(옆 1.5m, 방향 무작위)가 벽에 걸리면 곧장 '그 지점이 보이는 자리'(30m 밖)로 | 바로 둘레 1~3m 빈자리부터 찾음 | `neighborhood.test` 새 테스트, mp-check |

### P2 (고침)

| 문제 | 위치 | 고친 방법 · 검증 |
|---|---|---|
| 양도 글 고치기와 양도 완료가 동시에 오면 완료가 조용히 되돌아감 (40/40) | BE `transfer/Transfer.java`, V12 | `@Version` + 409 `CONFLICT` |
| 내 정보 동시 저장 500 (10개 중 5~7개) | BE `user/ProfileService.java`, `UserRepository.findForUpdate` | 행 잠금. `profileSaves_atOnce_allSucceed` |
| 첫 로그인 연타 500 (6개 중 5개) | BE `auth/AccountService.java` | `insert … on conflict do nothing` 후 다시 읽기. `firstLogin_doubleSubmit_makesOneAccount` |
| 06시 청년안심주택 수집 동안 멀티플레이 틱·핑 멈춤 (예약 스레드 1개) | BE `application.yml` | 예약 스레드 4개 |
| 나간 사람 초대 토큰이 24시간 남음 → 5000개 차면 모두 429 | BE `world/InviteService.java`, `WorldService.leave` | 나가면 바로 회수. `inviteToken_isRevoked_whenHostLeaves` |
| 같은 '며칠 전' 만료 알림이 연타로 여러 개 | BE `home/HomeService.java`, V12 | 고유 인덱스 + upsert. `sameAlertTwice_staysOne` |
| 아주 큰 page → 500, multipart 아닌 업로드 → 500 | BE `ListingController`, `TransferController`, `GlobalExceptionHandler` | 400. 제약 위반은 전역 409 |
| 별점 4.7 을 4로 받음 | BE `application.yml` | `accept-float-as-int: false` → 400 |
| 달이 바뀌어도 서버를 다시 켜기 전엔 목록 등급이 옛 12개월 창 | BE `listing/ListingGradeJob.java` | 매달 1일 04:10 다시 계산 |
| 목록 사진 지연 컬렉션 N+1, 업로드 사진 `no-store`, JSON 압축 없음, 검색의 카카오 호출 매번 | BE `application.yml`, `UploadConfig.java`, `SearchController.java` | 100개씩 묶어 읽기, 사진 1년 immutable, gzip(6.6KB→1.2KB), 카카오 결과 10분 캐시 |
| 인덱스 없음: 단지 구독자·내 양도 글·내 후기 | V12 | 인덱스 3개 |
| `gradlew` 실행 권한 없이 커밋됨 | backend git | `git update-index --chmod=+x` |
| 늦게 온 401 이 새로 로그인한 사람을 내보냄, 저장 중 만료면 말없이 실패 | FE `api/client.ts` | 같은 토큰일 때만 로그아웃, 쓰기 요청이면 로그인 창. `qaFixes.test` 2개 |
| 4xx 도 한 번 더 요청(없는 매물 '찾을 수 없어요'가 1초 늦음) | FE `App.tsx` | 네트워크·5xx 만 재시도 |
| 새로고침 뒤 닉네임이 사라져 '내 계정'·같이 걷기 '손님####' | FE `App.tsx` NicknameSync | 내 정보 닉네임으로 채움 |
| 동네 집 빛 기둥이 단지 표시 토글 때 사라짐 | FE `buildWorld.js` setBeacons, `NeighborhoodButton.tsx` | 빛 기둥 묶음(group) 분리 |
| 구독 한 번에 단지 상세 30개를 다시 받음, 구독 버튼 연타 | FE `features/catalog.ts`, `HousingPanel.tsx` | 목록 + 그 단지만 무효화, 처리 중엔 버튼 끔 |
| 필터 한 글자마다 요청·목록 깜빡·3D 말풍선 지웠다 다시 | FE `features/listings.ts` | 250ms 기다렸다 받기 + 앞 결과 유지 |
| 첫 화면을 막는 글꼴 CSS 606KB(@font-face 828개), 550·650·750 굵기는 흉내 | FE `app/main.tsx` 외 6곳 글꼴 이름 | Pretendard 가변 글꼴 → 134KB |
| `react-dom/server` 가 첫 화면 번들에 (SVG 문자열 몇 개 때문) | FE `app/icons.tsx` | 떼어 낸 요소에 한 번 그려 문자열만 → vendor-react gzip 136→112KB |
| 사진 올리는 중에 올리기 → 사진 빠짐. 양도 완료는 되묻지 않고 실패도 안 보임 | FE `TransferPanel.tsx` | 올리는 동안 버튼 끔, 한 번 더 묻기, 실패 안내 |
| 관리비 없음 '-', 공과금 전부 비면 '0만' | FE `HousingPanel.tsx`, `MyHomePanel.tsx` | '정보 없음' / '기록 없음' |
| 찜 종류 칩의 마지막 찜을 풀면 빈 목록에 갇힘 | FE `FavoritesPanel.tsx` | 전체로 돌아감 |
| 후기 항목 별점·공과금 칸을 빨리 고치면 앞 값이 지워짐 | FE `ReviewSection.tsx`, `MyHomePanel.tsx` | 이전 값 기준 갱신 |
| 로그인·내 정보 창: Esc·초점·`aria-modal` 없음 / 하트 100개가 모두 '찜하기' | FE `useModal.ts`(새), `LoginModal.tsx`, `ProfileModal.tsx`, `HeartButton.tsx` | Esc·Tab 가두기·닫으면 초점 복귀, 하트 이름표 '<집 이름> 찜' + `aria-pressed` |
| 첫 로그인 안내가 새 창마다 다시 열림 | FE `ProfileModal.tsx` | localStorage |
| 380 폭 등급 칩 줄에서 '범인'·'판정 보류'가 화면 밖인데 단서가 없음 | FE `ListingsPanel.tsx`, `venue.css` | 더 있으면 그쪽 끝을 흐리게 |
| 기숙사 '지도에서 보기'가 실제론 3D 이동 | FE `DormPanel.tsx` | '3D에서 보기' |
| 점검 스크립트: `final-qa.mjs` 의 `MOCK` 정의 누락으로 로그인 뒤 전부 실패, 화면 개편 뒤 선택자 9곳 낡음 | FE `scripts/final-qa.mjs` | 고침 + 미니맵 두 번 누름은 건물 위면 다른 자리로 |

## 3. 명세서 수정안

코드가 맞고 명세가 낡은 문장. (명세 파일은 고치지 않았다 — 아래를 그대로 옮기면 된다)

**기능 명세서 `docs/spec/feature-spec.md`**

| ID | 지금 문장 | 고칠 문장 |
|---|---|---|
| A1 | 로그아웃은 토큰 삭제 | 로그아웃은 토큰 삭제(앞사람 기록·찜 표시도 지움). 저장 중 토큰이 만료되면 로그인 창을 다시 띄운다 |
| A2 | 첫 로그인 때 한 번 자동으로 열린다 | 첫 로그인 때 한 번 자동으로 열린다(닫으면 이 브라우저에선 다시 저절로 열지 않음) |
| B5 | 누르면 상세가 열린다 | 매물·청년안심주택·양도는 누르면 그 상세가, 기숙사는 기숙사 탭이 열린다. 하트는 표시만(찜은 목록·상세에서) |
| C1 | 고르면 3D 에서 그곳으로 이동하고 상세가 열린다 | 고르면 3D 에서 그곳으로 이동하고 상세를 골라 둔다(패널은 접어 3D 를 보여 줌, 탭을 누르면 그 상세) — 4장 결정에 따라 |
| D1 | 카드에 등급·환산 월세·도보 분 | 카드에 등급·환산 월세·도보 분. 누르면 상세만 열리고 3D 이동은 상세의 [3D에서 보기] |
| D3 | AI 적정가 범위, 근거(표본 수·기간), 내 예산 초과도 함께 보여 준다 | 실거래 적정가·AI 적정가 범위·이 집을 한 눈금자에 놓고, 내 예산 초과도 보여 준다(표본 수·기간은 API 에만) |
| D5 | 근처 기숙사·청년안심주택과 … 같은 예산의 더 싼 자취방(최대 3개) | 기숙사·청년안심주택 중 환산 월세가 싼 3곳과 … 지금 필터 결과 중 더 싼 자취방(최대 3개). 표로 2년 차이 |
| K2 | 사진(최대 6장) | 사진(화면 최대 6장, 서버는 10장까지) |
| K3 | 내 글이 양도 중일 때만 고치기·양도 완료가 보인다 | 내 글이 양도 중일 때만 고치기·양도 완료(한 번 더 확인)가 보인다. 동시에 고치면 늦은 쪽은 409 |
| H5 | 켜기·끄기·삭제 | 켜기·끄기·삭제. 같은 '며칠 전'은 하나만 |
| M4 | (그대로) | 일치. frontend/CLAUDE.md 의 '내 화면에만' 문장은 낡아서 고쳤다 |
| P1 | API `GET /dorms` (인증 없음) | `GET /dorms` (인증 선택, `buildingId`?) — 도보 분 포함 |
| X5 | 서버 시작 시 | `INGEST_ENABLED=true` 일 때 서버 시작 시 수집, 등급은 시작 시 + 매달 1일 다시 계산 |

**API 명세서 `docs/spec/api-spec.md`**

| 곳 | 지금 | 고칠 것 |
|---|---|---|
| 머리말 오류 코드 | VALIDATION_FAILED … WORLD_FULL | `CODE_MISMATCH(400)`, `CODE_EXPIRED(400)`, `METHOD_NOT_ALLOWED(405)`, `CONFLICT(409, 동시 수정)` 추가 |
| `/listings` | `grade[]`, `page`=0 | `grade`(반복 또는 쉼표 구분), `page` 0~10000, `size` 최대 100. `maxWalkMin` 은 buildingId 나 로그인 사용자의 건물이 없으면 무시 |
| `/transfers` | page | `page` 0~10000. 항목에 `thumbnailUrl` 도 있다 |
| `/walk` | 200 `{ minutes, distanceM, path, gateId }` | `gateId` 는 늘 null(빼거나 구현). 서비스 지역 밖 좌표는 400 |
| `/dorms` | 인증 없음, 파라미터 — | 인증 선택, query `buildingId`?, 응답에 `walkMin`. `GET /dorms/{id}` 도 추가 |
| `/housing/{id}` | `floorLayoutImageUrl` | 수집이 채우지 않아 늘 null — 빼거나 `housing_floorplan_images` 에서 채움 |
| price-check | (설명 없음) | `monthlyExcess`·`totalExcess`·`excessRate` 는 음수 가능(적정가보다 쌈), PENDING 이면 `fairRent`·초과액 null, `budget` 은 비로그인·미설정이면 null, `aiEstimate` 없으면 null(양도 글 판결은 늘 null) |
| `/me/profile` | budget | `budget` 은 미설정이면 null, PUT 에 `{rentCap:null, depositCap:null}` 이면 지움 |
| `/reviews` | 응답 | `items` 는 최근 100건, `average`·`count` 는 전체. 항목별 평균은 API 에 없음(화면이 계산) |
| `/me/payments`, `/me/utilities` | POST 201 | 같은 달이면 덮어씀(upsert) |
| `/me/home/alerts` | POST 201 | 같은 `daysBefore` 면 그 알림을 고쳐 돌려줌(하나만) |
| `/me/report` | `excess` | `cumulative` 는 계약 기간 안의 지난 달 수 × 월 초과액(음수 가능) |
| `/transfers` POST·PUT, `/me/home` PUT | lat, lng | 국내 범위(위도 33~39, 경도 124~132) 밖이면 400. PUT·PATCH 동시 수정은 409 |
| `/search` | `limit`=10 | `q` 2자 이상, `limit` 최대 30 |
| `/listings/{id}/nearby` | `radius`=300 | 최대 500 |
| `/floorplans/estimate` | AI 서버 호출 | AI 꺼짐이면 저장된 평면도 그대로(없으면 404) |
| 빠진 엔드포인트 | — | `POST /auth/email/send`·`/verify`: 점검·테스트용, `EMAIL_LOGIN_ENABLED=false` 면 없음 |

## 4. 고치지 않고 남긴 것 · 결정이 필요한 것

### 운영 설정 (코드 밖, 직접 해야 함)

1. **Railway 에 `EMAIL_LOGIN_ENABLED=false`** (권장). 화면 로그인은 구글뿐이라 쓰는 사람이 없는데 켜져 있으면 코드 대입 표면이 남는다(이번에 잠금·속도 제한은 넣었다). `MAIL_MODE=log` 면 코드가 Railway 로그에 그대로 찍히니 그것도 확인. 끄면 운영에서 `final-qa` 의 메일 로그인은 못 쓴다(로컬은 그대로).
2. **업로드 사진 저장소**: 지금은 컨테이너 디스크(`/app/uploads`) → 재배포마다 양도 사진이 지워진다. Railway 볼륨을 `UPLOAD_DIR` 에 붙이거나 S3 호환 저장소로. (운영엔 아직 사진 있는 글이 없다: 3건 모두 thumbnailUrl 없음)
3. 이번 백엔드 변경에는 **V12 마이그레이션**이 있다(`transfers.version`, 알림 중복 정리 + 고유 인덱스, 인덱스 3개). 배포하면 자동 적용.

### 결정이 필요한 것 (고치지 않음)

| # | 무엇 | 선택지 | 추천 |
|---|---|---|---|
| 1 | Swagger·`/v3/api-docs` 가 운영에 공개 | 그대로 / `SWAGGER_ENABLED` 로 운영만 끄기 | 끄기 (메일 로그인 경로 등 내부 경로가 다 보임) |
| 2 | 구글 로그인에서 `hd`(학교 도메인) 클레임을 요구할지 | 지금처럼 이메일 도메인만 / `hd=hanyang.ac.kr` 도 요구 | 학교가 구글 워크스페이스면 요구. 아니면 그대로 |
| 3 | `?mock=1` 이 운영 주소에서도 켜짐(가짜 매물·판결이 진짜 도메인에 보이는 링크를 만들 수 있음) | 그대로(시연용) / 개발 서버·`VITE_USE_MOCK` 일 때만 | 개발에서만 |
| 4 | 패널을 열면 왼쪽 아래 채팅 줄이 패널 밑에 가려진다(데스크톱). 멀티플레이 중 채팅을 못 봄 | 그대로 / 패널이 열리면 채팅을 패널 오른쪽으로 옮김 | 옮기기 — 다만 예전에 HUD 가 옆으로 밀리는 걸 싫어했으니 확인 받고 |
| 5 | 청년안심주택 목록 클릭은 아직 3D 로 바로 이동(매물은 정보만) | 그대로 / 매물처럼 정보만 + [3D에서 보기] | 매물과 같게 |
| 6 | 통합 검색(C1)에서 고르면 패널을 접는다(명세는 '상세가 열린다') | 접기 유지 / 상세를 연 채로 3D 이동 | 동네 HUD 가 없는 집(동네 밖)은 상세를 연 채로 |
| 7 | 매물 실내(문 앞·'실내 보기')에서는 핀 후기를 못 남김(기숙사·단지만) | 그대로 / 매물도 허용 | 허용(후기 API 는 LISTING 지원) |
| 8 | 같은 사람이 같은 집에 후기를 여러 개 쓸 수 있음(서버에서 10개 동시 → 10개) | 그대로 / 한 사람 한 집 한 후기(고치기) | 한 개 + 고치기 |

### 기술 부채 (이번엔 안 고침)

- `/me/favorites` 30개에 SQL 134번(항목마다 상세 서비스를 통째로). 종류별로 묶어 읽기 필요.
- `buildWorld.js` 라벨 가리기(`cullLabels`)가 100ms 마다 모든 라벨 `offsetWidth` 를 읽어 강제 레이아웃.
- 월드를 짓는 중에 키보드로 '캠퍼스로'를 누르면 두 월드가 한 장면에 섞일 수 있음(`buildWorld` 에 중단 신호 없음).
- 카카오 지도 이벤트 리스너를 지도마다 해제하지 않음.
- 접근성 잔여: 상단 검색 결과 `listbox` 안 `option` 역할, 달력 `grid` 의 행·칸 역할, 주택형 '실내 보기' 버튼 이름, 머리색 견본 이름이 색 코드, 미니맵 키보드 조작.
- CSS 이름 규칙(`ui-` 접두사) 위반: `.empty .fold .ghost .glass .grow .iconbtn .mapswitch .primary .search .suggest .tabs .textbtn .tod .topbar`, `.span2`, `.tone-*`, 실내 `.area .name`. `.loading-*`·`.suggest` 는 `style.css` 와 실제로 겹침.
- 검증 오류 메시지 일부가 영어 기본값("must be greater than …").

## 5. 전후 수치

**반응 시간** (클릭 → 화면이 바뀐 다음 프레임까지, 페이지 안에서 잼. 로컬 dev 서버 + q=low)

| 동작 | 1280 | 1024 | 760 | 380 | 운영 1280 |
|---|---|---|---|---|---|
| 탭 → 패널 내용 (32번 중앙값 / 최대) | 25ms / 391ms(첫 매물 찾기) | | | | 6~488ms |
| 목록 카드 → 판결 카드 숫자 | 116ms | 30ms | 30ms | 30ms | 353ms |
| 3D에서 보기 (동네 월드 전환 포함) | 521ms | 15ms* | 12ms* | 11ms* | — |
| 지도로 보기 | 273ms | 27ms | 34ms | 28ms | 224ms |
| 실내 진입 / 나가기 | 64 / 28ms | | | 28 / 25ms | 360ms |
| 내 정보 저장 · 내 집 등록 · 월세 한 번 · 양도 올리기 · 후기 등록 | 71 · 74 · 52 · 244 · 78ms | | | | (쓰기 안 함) |

\* 이미 받아 둔 동네라 다시 짓지 않음. 300ms 를 넘은 것은 첫 화면(369ms), 처음 여는 매물 찾기(391ms, 목록 첫 요청), 동네 월드를 처음 짓는 3D에서 보기(521ms) 셋뿐.

**레이아웃** (1280·1024·760·380): 가로 스크롤 0, 화면 밖 조작 요소 0, 같은 영역 버튼 겹침 0, 판결 눈금자 이름표 겹침 0, 달력은 화면·패널 안. 남은 것은 24px 보다 작은 누름 영역 3개(760·380: 검색칸 높이 23px — 감싼 칸 44px 이 실제 누름 영역, 하단 개인정보처리방침·약관 링크 13px).

**3D 성능** (`perf-check.mjs 5`, q=med): 캠퍼스↔동네 5번 왕복 뒤 geometry 289 → 289, texture 143 → 143, 셰이더 34 → 34 (누수 없음). 프레임 p50 16.7ms / p95 18.5ms, 왕복 뒤 p50 18.5 / p95 26.6ms.

**번들·전송** (운영 배포본 → 이번 빌드): 첫 화면 CSS 606KB(gzip 196KB) → 134KB(gzip 30KB), vendor-react gzip 136KB → 112KB, `/listings` JSON 6.6KB → gzip 1.2KB.

**백엔드 부하** (로컬): 캐시 없는 도보 계산 동시 15개 1.8초 전부 200(전: 14개 30.3초·500 4개). 운영 GET 은 서버 처리 약 10ms, 나머지는 네트워크(Railway sin1 왕복 약 0.3초). 로컬·운영 GET 22개 응답 필드 집합 같음.

## 재현

- 프론트: `cd frontend && npx tsc --noEmit && npx vitest run && npm run build`
- 백엔드: `cd backend && ./gradlew test` (gradlew 실행 권한을 git 에 기록함)
- E2E 로컬: `docker logs -f chatatda-api > api.log &` 후 `MAIL_LOG=api.log node scripts/qa-final.mjs local out.json`
- E2E 운영(읽기만): `node scripts/qa-final.mjs prod out.json`
- 기존: `MAIL_LOG=api.log node scripts/final-qa.mjs out.json`, `node scripts/mp-check.mjs`
