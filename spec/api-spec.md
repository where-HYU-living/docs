# API 명세서 — 찾았다, 한양대 자취

> **Base URL** `https://api-production-8811.up.railway.app/api/v1`
> **인증** 필수는 `Authorization: Bearer <JWT>` 가 없으면 401. 선택은 토큰이 있으면 찜 여부, 예산, 도보 분을 내 기준으로 채운다. 없음은 누구나 호출할 수 있다.
> **목록 응답** `{ items, page, size, total }`
> **오류 응답** `{ code, message, details }`. code 는 VALIDATION_FAILED(400), INVALID_EMAIL_DOMAIN(400), UNAUTHORIZED(401), FORBIDDEN(403), NOT_FOUND(404), ALREADY_EXISTS(409), TOO_MANY_REQUESTS(429), INTERNAL_ERROR(500), UPSTREAM_FAILED(502), WORLD_FULL(503)
> **단위** 금액은 원, 면적은 ㎡, 좌표는 WGS84 위경도. `bbox` 는 `minLng,minLat,maxLng,maxLat`

## 인증과 내 정보

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| POST | `/auth/google` | 구글 ID 토큰 검증 후 로그인 (한양대 계정만) | 없음 | body `{ idToken }` | 200 `{ accessToken, expiresIn, user{ id, email, nickname } }` | A1 |
| GET | `/me/profile` | 내 정보 조회 | 필수 | — | 200 `{ id, email, nickname, departmentId, buildingIds[], budget{ rentCap, depositCap } }` | A2 · B6 · M4 |
| PUT | `/me/profile` | 학과·자주 가는 건물·예산 저장 | 필수 | body `{ departmentId, buildingIds[], budget{ rentCap, depositCap } }` | 200 내 정보 | A2 |
| GET | `/departments` | 학과 목록 (학과별 기본 건물 포함) | 없음 | — | 200 `[{ id, name, college, defaultBuildingIds[] }]` | A2 · M4 |
| GET | `/buildings` | 캠퍼스 건물 목록 | 없음 | query `type`? (CAMPUS · GATE · DORM) | 200 `[{ id, name, type, lat, lng }]` | A2 · B6 |

## 검색과 길 안내

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/search` | 통합 검색: 매물 → 청년안심주택 → 기숙사 → 양도 글 → 건물, 모자라면 카카오 주소 | 없음 | query `q`, `limit`=10 | 200 `[{ type, id, name, address, lat, lng }]` | C1 |
| GET | `/geo/address` | 주소 검색 (카카오) | 없음 | query `q` | 200 `[{ address, roadAddress, dong, lat, lng }]` · 502 외부 실패 | K2 · H1 |
| GET | `/walk` | 집 → 과 건물 보행 경로 (TMAP, 결과 캐시) | 없음 | query `fromLat`, `fromLng`, `buildingId` | 200 `{ minutes, distanceM, path[[lat,lng]], gateId }` | C3 |

## 매물과 판결

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/listings` | 매물 목록 · 필터 | 선택 | query `bbox`, `maxRent`, `maxDeposit`, `maxMgmtFee`, `grade[]`, `maxWalkMin`, `roomType`, `buildingId`, `page`=0, `size`=20 | 200 페이지 `{ id, title, address, dong, lat, lng, deposit, rent, mgmtFee, areaM2, floor, roomType, convertedRent, grade, walkMin, thumbnailUrl, favorited }` | D1 · B5 · C2 · D5 |
| GET | `/listings/{id}` | 매물 상세 | 선택 | query `buildingId`? | 200 목록 항목 + `options[], photos[], floorplanId, builtYear, description` · 404 | D2 |
| GET | `/listings/{id}/price-check` | 가격 판결: 환산 월세 · 적정가 · 초과액 · 등급 · AI 적정가 | 선택 | — | 200 `{ convertedRent, fairRent, monthlyExcess, contractMonths, totalExcess, excessRate, grade, conversionRate, sample{ count, scope, dongs, areaMinM2, areaMaxM2, from, to }, budget{ rentCap, depositCap, overRent, overDeposit }, aiEstimate{ fairRent, low, high } }` | D3 · D4 · X1 |
| GET | `/listings/{id}/alternatives` | 이 돈이면: 근처 청년안심주택·기숙사 비교 | 선택 | query `buildingId`? | 200 `{ housing[], dorms[] }` 각 `{ type, id, name, convertedRent, monthlyDiff, twoYearDiff, walkMin }` | D5 |
| GET | `/listings/{id}/nearby` | 주변 시설 (편의점·세탁방·버스정류장·지하철역) | 없음 | query `radius`=300 | 200 `[{ category, name, lat, lng, distanceM }]` | B7 |

## 평면도와 후기

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/floorplans/{id}` | 실내 3D 용 평면도 JSON (1시간 캐시) | 없음 | — | 200 FloorPlan JSON (방 · 벽 · 문 · 창) · 404 | E1 |
| POST | `/floorplans/estimate` | AI 평면도 추정 (AI 서버 호출) | 필수 | body `{ id, name, areaM2, rooms? }` | 200 FloorPlan JSON | X2 |
| GET | `/reviews` | 후기 목록 · 평균 | 없음 | query `targetType` (LISTING · HOUSING · DORM), `targetId` | 200 `{ average, count, items[{ id, rating, scores{ noise, light, bugs, landlord, depositReturn }, text, pin[x,y,z], floorplanId, authorNickname, createdAt }] }` | G1 · G2 |
| POST | `/reviews` | 후기 쓰기 (실내 핀 선택) | 필수 | body `{ targetType, targetId, rating 1~5, scores{ 5개 1~5 }, text ≤500, pin?[x,y,z], floorplanId? }` | 201 후기 | G1 · G2 |

## 찜

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/me/favorites` | 찜 목록 | 필수 | query `type`? (LISTING · HOUSING · DORM · TRANSFER) | 200 `[{ type, targetId, name, lat, lng, convertedRent, grade, walkMin, createdAt }]` | F2 · B5 |
| POST | `/me/favorites` | 찜하기 | 필수 | body `{ type, targetId }` | 201 찜 항목 · 409 이미 있음 | F1 |
| DELETE | `/me/favorites/{type}/{targetId}` | 찜 해제 | 필수 | — | 204 | F1 |

## 청년안심주택

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/housing` | 단지 목록 | 선택 | query `maxRent`, `maxDeposit`, `maxWalkMin`, `buildingId`, `bbox` | 200 `[{ id, name, address, lat, lng, recruiting, nextEvent{ type, date }, subscribed, minConvertedRent, walkMin }]` | I1 · B5 · B6 · C2 |
| GET | `/housing/{id}` | 단지 상세 · 주택형 | 선택 | query `buildingId`? | 200 목록 항목 + `unitTypes[{ id, name, exclusiveAreaM2, deposit, rent, mgmtFee, convertedRent, floorplanId }], floorLayoutImageUrl, contact` · 404 | I2 · B8 |
| GET | `/housing/announcements` | 공고 · 일정 (캘린더) | 없음 | query `status`? (UPCOMING · OPEN · CLOSED · ANNOUNCED · ADDITIONAL), `housingId`? | 200 `[{ id, housingId, title, status, events[{ type, date }] }]` | I4 |
| POST | `/housing/{id}/subscribe` | 공고 알림 구독 | 필수 | — | 204 | I3 |
| DELETE | `/housing/{id}/subscribe` | 구독 해제 | 필수 | — | 204 | I3 |

## 기숙사

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/dorms` | 기숙사 · 호실 비용 | 없음 | — | 200 `[{ id, name, lat, lng, walkMin, roomTypes[{ id, name, capacity, semesterFee, semesterMonths, mealIncluded, monthlyCost, floorplanId }] }]` | P1 · B5 · B8 · C2 |

## 양도

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/transfers` | 양도 글 목록 | 선택 | query `bbox`, `status`=OPEN (OPEN · DONE), `page`=0, `size`=20 | 200 페이지 `{ id, title, address, dong, lat, lng, deposit, rent, mgmtFee, areaM2, floor, roomType, convertedRent, grade, walkMin, remainingMonths, availableFrom, status, authorNickname, favorited }` | K1 · B5 · C2 |
| GET | `/transfers/{id}` | 양도 글 상세 (판결 포함) | 선택 | — | 200 목록 항목 + `description, photos[], priceCheck{…}, mine` · 404 | K1 · D3 |
| POST | `/transfers` | 양도 글 쓰기 | 필수 | body `{ title, address, dong, lat, lng, deposit, rent, mgmtFee, areaM2, roomType, floor, remainingMonths, availableFrom, description, photoUrls[] }` | 201 상세 | K2 |
| PUT | `/transfers/{id}` | 양도 글 수정 (작성자만) | 필수 | body 쓰기와 같음 | 200 상세 · 403 | K3 |
| PATCH | `/transfers/{id}/status` | 양도 완료 처리 (작성자만) | 필수 | body `{ status }` | 200 상세 · 403 | K3 |
| POST | `/uploads` | 사진 업로드 (jpg · png, 5MB) | 필수 | multipart `file` | 200 `{ url }` | K2 |

## 내 집 기록

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/me/home` | 내 집 조회 | 필수 | — | 200 `{ address, dong, lat, lng, deposit, rent, mgmtFee, areaM2, contractStart, contractEnd }` · 404 미등록 | H1 · I2 |
| PUT | `/me/home` | 내 집 등록 · 수정 | 필수 | body 위와 같음 | 200 내 집 | H1 |
| GET | `/me/payments` | 월세 납부 기록 | 필수 | — | 200 `[{ month, amount, paidAt }]` | H2 |
| POST | `/me/payments` | 월세 납부 추가 | 필수 | body `{ month "YYYY-MM", amount, paidAt }` | 201 | H2 |
| GET | `/me/utilities` | 공과금 기록 | 필수 | — | 200 `[{ month, electricity, gas, water, internet }]` | H3 |
| POST | `/me/utilities` | 공과금 추가 | 필수 | body `{ month, electricity, gas, water, internet }` | 201 | H3 |
| GET | `/me/report` | 월간 리포트 | 필수 | query `month` (YYYY-MM) | 200 `{ month, total, breakdown{ rent, mgmtFee, electricity, gas, water, internet }, prevTotal, diff, topIncrease{ item, diff }, excess{ monthly, cumulative, grade } }` | H4 |
| GET | `/me/home/alerts` | 계약 만료 알림 목록 | 필수 | — | 200 `[{ id, daysBefore, enabled }]` | H5 |
| POST | `/me/home/alerts` | 만료 알림 추가 | 필수 | body `{ daysBefore 1~365, enabled }` | 201 | H5 |
| PATCH | `/me/home/alerts/{id}` | 만료 알림 켜기 · 끄기 | 필수 | body `{ enabled }` | 200 | H5 |
| DELETE | `/me/home/alerts/{id}` | 만료 알림 삭제 | 필수 | — | 204 | H5 |

## 알림

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/me/notifications` | 알림함 (매일 09시 생성) | 필수 | — | 200 `[{ id, type (HOUSING_DDAY · CONTRACT_EXPIRY), title, body, targetType, targetId, createdAt, read }]` | Q1 · X4 |
| PATCH | `/me/notifications/{id}/read` | 읽음 처리 | 필수 | — | 204 | Q1 |

## 멀티플레이

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| POST | `/invites` | 초대 링크 만들기 (게스트 가능, 24시간 유효) | 없음 | body `{ playerId }` | 200 `{ url, token, expiresAt }` | M3 |
| WS | `/ws/world` | 공유 월드 (최대 30명, 100ms 틱). 접속 query `nickname`, `invite`? | 없음 | 보냄 `move{ p, r, a, room? }` · `look` · `emote` · `chat` · `ping` | 받음 `welcome` · `join` · `leave` · `state` · `look` · `emote` · `chat` · `error(WORLD_FULL)` | M1 · M2 · M3 · M4 |

## 운영

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| GET | `/health` | 서버 상태 확인 | 없음 | — | 200 `{ status }` | — |

## AI 서버 (내부 API, 백엔드만 호출)

| 메서드 | 경로 | 설명 | 인증 | 요청 · 파라미터 | 응답 | 기능 ID |
|---|---|---|---|---|---|---|
| POST | `/v1/floorplan/estimate` | 루트 A: 평면도 이미지 → FloorPlan (CubiCasa5K + PaddleOCR) | 내부 | multipart `image`, `id`, `name`, `areaM2`? | 200 `{ floorplan, issues[], route }` · 422 | X2 |
| POST | `/v1/floorplan/estimate-from-meta` | 루트 B: 면적 · 방 수 → 템플릿 FloorPlan | 내부 | body `{ id, name, areaM2, rooms? }` | 200 `{ floorplan, issues[], route }` | X2 |
| POST | `/v1/floorplan/validate` | FloorPlan 검수 | 내부 | body FloorPlan | 200 `{ ok, issues[] }` | X2 |
| POST | `/v1/rent/estimate` | 적정 월세 (분위 회귀 25 · 50 · 75%) | 내부 | body `{ dong, areaM2, contractYm, floor?, builtYear?, buildingType?, contractType? }` | 200 `{ fairRent, low, high, model }` | X1 |
| GET | `/health` | AI 서버 상태 · 모델 적재 여부 | 내부 | — | 200 `{ status, inference, weights, rentModel }` | — |
