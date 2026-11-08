# 공통 계약 문서 — API 명세 · 데이터 형식 · 멀티플레이 프로토콜

> 백엔드(장시현)와 프론트·3D(김준형)가 **함께 보는 단 하나의 기준 문서**.
> 프론트는 이 문서에 맞춰 개발하고, 백엔드는 이 문서대로 응답한다.
> 기준 스펙: `docs/spec-v0.5.md`
> 버전: contract v1.8 (2026-11-08)

---

## 0. 변경 규칙
1. 이 문서가 바뀌면 **둘 다 확인한 뒤** 머지한다. 한쪽만 바꾸지 않는다.
2. 필드 추가는 자유(프론트는 모르는 필드를 무시). **필드 삭제·이름 변경·타입 변경은 합의 필수.**
3. 변경 시 맨 아래 「변경 이력」에 한 줄 추가.
4. 백엔드는 Swagger(`/swagger-ui.html`)를 이 문서와 일치시킨다. 둘이 다르면 **이 문서가 정답**.

## 1. 공통 규약

| 항목 | 규칙 |
|---|---|
| Base URL | `{API_BASE}/api/v1` (로컬: `http://localhost:8080/api/v1`) |
| 형식 | JSON, UTF-8, 필드명 **camelCase** |
| 금액 | **원 단위 정수** (`Long`). 예: 월세 55만 원 → `550000`. 만원 변환은 프론트에서 |
| 면적 | ㎡, 소수 둘째 자리까지 (`18.22`) |
| 비율 | 0~1 소수, 셋째 자리까지 (`0.153` = 15.3%) |
| 날짜 | `YYYY-MM-DD`, 일시는 ISO 8601 + `+09:00` (`2026-11-07T09:00:00+09:00`) |
| 월 | `YYYY-MM` |
| ID | 정수 (`Long`) |
| 좌표 | 위경도 WGS84 `lat`, `lng` (소수 7자리) |
| 없음 | 값을 모르면 **`null`** (0이나 빈 문자열로 대신하지 않음). 목록은 빈 배열 `[]` |
| 페이지 | 요청 `page`(0부터), `size`(기본 20, 최대 100) / 응답 `{ "items": [], "page": 0, "size": 20, "total": 57 }` |

### 1-1. 인증
- 학교 메일 인증 후 **JWT access token** 발급, 헤더 `Authorization: Bearer <token>`
- 유효기간 7일, 갱신 없음(만료 시 재인증)
- **비로그인(게스트)도 둘러보기 가능.** 로그인이 필요한 것은 `/me/*`, `POST/PUT/PATCH/DELETE` 전부(단 `/auth/*`, `/invites` 제외)
- 신입생은 아직 학교 메일이 없을 수 있다 → 게스트로 3D·검색·판정·멀티플레이까지 모두 가능해야 한다

### 1-2. 에러 형식
```json
{ "code": "CODE_MISMATCH", "message": "인증 코드가 맞지 않아요.", "details": null }
```
| HTTP | code | 상황 |
|---|---|---|
| 400 | `VALIDATION_FAILED` | 필드 형식 오류 (`details`: `{ "field": "사유" }`) |
| 400 | `INVALID_EMAIL_DOMAIN` | `@hanyang.ac.kr`가 아닌 메일 |
| 400 | `CODE_MISMATCH` / `CODE_EXPIRED` | 인증 코드 불일치 / 10분 초과 |
| 401 | `UNAUTHORIZED` | 토큰 없음·만료 |
| 403 | `FORBIDDEN` | 남의 양도 글 수정 등 |
| 404 | `NOT_FOUND` | 대상 없음 |
| 405 | `METHOD_NOT_ALLOWED` | 지원하지 않는 HTTP 메서드 |
| 409 | `ALREADY_EXISTS` | 같은 찜 중복 등 |
| 429 | `TOO_MANY_REQUESTS` | 인증 메일 재발송 60초 이내, 코드 5회 오류 |
| 500 | `INTERNAL_ERROR` | 서버 내부 오류 (상세 내용은 응답에 싣지 않음) |
| 502 | `UPSTREAM_FAILED` | 외부 API 실패 (단, 아래 「외부 실패 시 응답」 규칙 우선) |

**외부 API 실패 시 응답:** 도보 시간·주변 시설·주소 검색이 외부 API 실패로 안 될 때, 그 값을 포함하는 상위 응답은 **200으로 주고 해당 필드만 `null`/`[]`**. 단독 엔드포인트(`/walk`, `/geo/address`)만 502.

## 2. 열거형 (enum)

| 이름 | 값 | 의미 |
|---|---|---|
| `Grade` | `FAIR` · `SLIGHTLY_HIGH` · `HIGH` · `CULPRIT` · `PENDING` | 적정 · 조금 비쌈 · 비쌈 · 범인 · 판정 보류 |
| `RoomType` | `OPEN` · `SEPARATED` · `ONE_HALF` · `TWO_ROOM` · `DUPLEX` | 오픈형 · 분리형 · 1.5룸 · 투룸 · 복층 |
| `FavoriteType` | `LISTING` · `HOUSING` · `DORM` · `TRANSFER` | 자취방 · 청년안심주택 · 기숙사 · 양도 글 |
| `BuildingType` | `CAMPUS` · `GATE` · `DORM` | 캠퍼스 건물 · 입구 · 기숙사 |
| `AnnouncementStatus` | `UPCOMING` · `OPEN` · `CLOSED` · `ANNOUNCED` · `ADDITIONAL` | 예정 · 접수 중 · 마감 · 발표 완료 · 추가모집 |
| `EventType` | `NOTICE` · `APPLY_START` · `APPLY_END` · `DOCS_DUE` · `RESULT` · `CONTRACT` · `MOVE_IN` | 공고 일정 단계 |
| `NearbyCategory` | `CONVENIENCE` · `LAUNDRY` · `BUS_STOP` · `SUBWAY` | 편의점 · 세탁방 · 버스정류장 · 지하철역 |
| `SearchType` | `LISTING` · `HOUSING` · `DORM` · `TRANSFER` · `BUILDING` · `ADDRESS` | 통합 검색 결과 종류 |
| `TransferStatus` | `OPEN` · `DONE` | 양도 중 · 양도 완료 |
| `NotificationType` | `HOUSING_DDAY` · `CONTRACT_EXPIRY` | 공고 D-day · 계약 만료 |
| `ReviewTargetType` | `LISTING` · `HOUSING` · `DORM` | 후기 대상 |

### 2-1. 등급 경계 (서버 계산, 프론트는 색·문구만)
| 조건 (`excessRate`) | Grade |
|---|---|
| 표본 부족 | `PENDING` |
| `≤ 0.10` (음수 포함) | `FAIR` |
| `0.10 < r ≤ 0.25` | `SLIGHTLY_HIGH` |
| `0.25 < r ≤ 0.50` | `HIGH` |
| `> 0.50` | `CULPRIT` |

기준값 0.10 / 0.25 / 0.50은 서버 설정값(`pricing.grade-fair` · `grade-slight` · `grade-high`)이며 바뀌어도 API는 그대로. 등급은 셋째 자리로 반올림한 `excessRate`로 판정한다.
- 근거 (스펙 3-4 "실거래 분포를 보고 재조정"): 한양대 주변 동의 18㎡ 원룸 신규 월세 실거래 2,303건(2025-11 ~ 2026-10)을 각자 동 중앙값과 비교하면 적정 69% · 조금 비쌈 16% · 비쌈 10% · 범인 5%. 이전 초안 0.05 / 0.15 / 0.30 은 실제 거래의 11%가 범인이 되어 너무 엄격했음

### 2-2. 등급 표시 (프론트 기준, 서버는 몰라도 됨)
| Grade | 색 | 라벨 | 판결 문구 |
|---|---|---|---|
| `FAIR` | `#3BA55C` | 적정 | 시세대로예요 |
| `SLIGHTLY_HIGH` | `#F2C94C` | 조금 비쌈 | 2년이면 {total}만 원 더 내요 |
| `HIGH` | `#F2994A` | 비쌈 | 이 집이 내 돈을 써버릴 놈일 수 있어요 |
| `CULPRIT` | `#EB5757` | 범인 | 찾았다. 2년간 {total}만 원을 써버릴 놈 |
| `PENDING` | `#9E9E9E` | 판정 보류 | 비교할 거래가 부족해요 |

## 3. 공통 객체

### PriceCheck — 초과액 판정 결과
```json
{
  "convertedRent": 712000,
  "fairRent": 548000,
  "monthlyExcess": 164000,
  "contractMonths": 24,
  "totalExcess": 3936000,
  "excessRate": 0.299,
  "grade": "HIGH",
  "conversionRate": 0.06,
  "sample": { "count": 23, "scope": "DONG", "dongs": ["행당동"], "areaMinM2": 12.6, "areaMaxM2": 23.4, "from": "2025-11", "to": "2026-10" },
  "budget": { "rentCap": 600000, "depositCap": 10000000, "overRent": 112000, "overDeposit": 0 }
}
```
- `PENDING`이면 `fairRent`, `monthlyExcess`, `totalExcess`, `excessRate` = `null`, `sample.scope` = `"NONE"`
- `sample.scope`: `DONG`(같은 동) · `ADJACENT`(인접 동 포함) · `NONE`
- `budget`: 비로그인이거나 예산 미설정이면 `null`. `overRent` = `max(0, convertedRent − rentCap)`
- 계산식은 스펙 3-1 (초안). 환산 월세 = 월세 + 관리비 + 보증금 × `conversionRate` ÷ 12
- **현재 `conversionRate` = 0.046** (한국부동산원 서울 단독+연립다세대, 2026-08). 위 예시의 0.06 은 예시 값이다. 화면에서 미리 계산할 때도 0.046 을 쓰고, 판정 응답이 있으면 응답의 `conversionRate` 를 쓴다
- 적정 환산 월세에는 기준 관리비 71,000원이 더해진다 (실거래에는 관리비가 없어서)

### Alternative — 비교 대상 (N3, I19)
```json
{ "type": "HOUSING", "id": 3, "name": "왕십리역 청아진 18타입", "convertedRent": 488000, "monthlyDiff": 224000, "twoYearDiff": 5376000, "walkMin": 11 }
```
- `id` = `type`에 해당하는 **단지·기숙사 ID** (`/housing/{id}`, `/dorms/{id}`, 찜 `targetId`에 그대로 사용). `name`에 든 주택형·호실 유형은 표시용
- `monthlyDiff` = 보고 있는 집 환산 월세 − 이 대상 환산 월세 (양수면 이 대상이 더 쌈)

### ListingSummary
```json
{
  "id": 12, "title": "행당동 분리형 원룸", "address": "서울 성동구 행당동 ○○-○", "dong": "행당동",
  "lat": 37.5580000, "lng": 127.0410000,
  "deposit": 10000000, "rent": 550000, "mgmtFee": 80000, "areaM2": 18.22, "floor": 3,
  "roomType": "SEPARATED", "convertedRent": 712000, "grade": "HIGH",
  "walkMin": 9, "thumbnailUrl": "https://…/12.jpg", "favorited": false
}
```
- `walkMin`: 요청의 `buildingId` → 없으면 로그인 사용자 첫 번째 과 건물 → 둘 다 없으면 `null`
- `favorited`: 게스트는 항상 `false`

### ListingDetail = ListingSummary + 
```json
{ "options": ["에어컨", "세탁기"], "photos": ["https://…"], "floorplanId": 5, "builtYear": 2019, "description": "…" }
```

### FloorPlan — 실내 3D용
```json
{
  "id": 5, "name": "청아진 18타입", "areaM2": 18.22, "ceilingHeight": 2.4,
  "walls": [ { "from": [0, 0], "to": [2.6, 0], "thickness": 0.15, "height": 2.4 } ],
  "openings": [ { "type": "door", "wall": 0, "offset": 0.3, "width": 0.9, "height": 2.1, "sill": 0,
                  "style": "swing", "swing": { "hinge": "start", "opensTo": -1 } },
                { "type": "window", "wall": 2, "offset": 0.5, "width": 1.6, "height": 1.2, "sill": 0.9, "style": "sliding" } ],
  "rooms": [ { "name": "거실", "polygon": [[0, 0], [2.6, 0], [2.6, 4.2], [0, 4.2]], "kind": "living",
               "floor": { "material": "wood", "height": 0 } } ],
  "entrance": [1.3, 0],
  "fixtures": [ { "kind": "bed", "position": [1.8, 3.2], "facing": "S", "size": [1.1, 2.0], "room": "거실" } ],
  "glbUrl": null
}
```
- 단위 m. 평면 좌표 `[x, y]`: **x = 오른쪽, y = 아래쪽**, 원점은 **벽 중심선 바운딩박스의 좌상단**. 벽은 중심선 기준
- 3D 변환: 평면 `[x, y]` → three.js `(x, 높이, y)`
- `walls[].height`: 없으면 `ceilingHeight` (낮은 칸막이·반벽)
- `openings[]`: `wall` = `walls` 인덱스, `offset` = 그 벽의 `from` 에서 열린 곳 시작까지 거리. `style`: `swing`(여닫이, 기본)·`sliding`·`open`(문 없는 개구부). `swing.hinge`: `start`(from 쪽)·`end`(to 쪽), `swing.opensTo`: 위에서 본 평면도에서 벽 진행방향(from→to)을 바라볼 때 왼쪽으로 열리면 `+1`, 오른쪽 `-1`. 없으면 3D 가 정한다
- `rooms[].kind`: `bedroom`·`living`·`kitchen`·`bathroom`·`entrance`·`balcony`·`utility`·`storage`·`hallway`·`other`. `rooms[].floor`: `material` = `wood`·`tile`·`vinyl`·`concrete`, `color`(선택), `height` = 기준 바닥 대비 단차(m, 욕실·현관 -0.05~-0.15)
- `fixtures[]` (선택, 없으면 3D 가 방 이름·면적으로 예시 배치): `kind` = `toilet`·`sink`·`shower`·`bathtub`·`washer`·`kitchenSink`·`cooktop`·`fridge`·`kitchenCounter`·`upperCabinet`·`bed`·`desk`·`chair`·`wardrobe`·`builtinWardrobe`·`shoeRack`·`shelf`·`sofa`·`tv`·`table`·`acOutdoor`·`waterHeater`. `position` = 바닥 접지 면 중심, `facing` = 앞면 방향 `N`·`E`·`S`·`W`, `elevation`(선택, 공중에 놓인 것), `size` = `[폭, 깊이, 높이?]`(선택), `room`(선택, 검수용)
- `glbUrl`이 있으면 프론트는 JSON 대신 GLB를 로드
- 데이터는 사람이(평면도 이미지를 보고, AI 보조 가능) 작성한 JSON을 **백엔드 `src/main/resources/fixtures/floorplans/{id}.json`** (파일 하나에 도면 하나, 파일명 = `id`)에 두고, 서버가 그대로 제공한다. 프론트 `interior/planFiles.test.ts` 가 이 폴더 전체를 검수한다(벽을 파고드는 문·가구, 걸어서 갈 수 없는 방). 정본 타입은 프론트 `src/api/types.ts` 의 `FloorPlan`
- id 구간: **1~99 청년안심주택 / 101~199 매물(데모) / 201~299 기숙사**. 주택형·매물·기숙사 호실의 `floorplanId` 가 이 id 를 가리킨다 (`null` 이면 실내 보기 없음)

## 4. 좌표 기준 (3D ↔ 위경도)
- 기준점(원점) `ORIGIN = { lat: 37.5561486, lng: 127.044341 }` — **확정**: 3D 월드의 사자상(한양대 정문 앞) 위치. 프론트 `src/app/map/geo.ts`의 값과 같다
- 3D 좌표계: three.js 기준 **+x = 동쪽, +y = 위, −z = 북쪽** (미터)
- 변환 (등장방형 근사, 반경 3km 안에서 오차 무시 가능):
  - `x = (lng − ORIGIN.lng) × cos(ORIGIN.lat × π/180) × 111320`
  - `z = −(lat − ORIGIN.lat) × 110540`
  - 역변환은 위 식을 거꾸로
- **서버는 위경도만 다룬다.** 예외: 멀티플레이 WS 메시지는 3D 미터 좌표(서버는 해석하지 않고 중계만)

## 5. REST API

> 🔒 = 로그인 필요. 표기 없는 것은 게스트 가능.

### 5-1. 인증·내 정보
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| POST | `/auth/email/send` | `{ "email": "a@hanyang.ac.kr" }` | `204` |
| POST | `/auth/email/verify` | `{ "email", "code": "123456" }` | `{ "accessToken", "expiresIn": 604800, "user": { "id", "email", "nickname" } }` |
| GET 🔒 | `/me/profile` | | `{ "id", "email", "nickname", "departmentId", "buildingIds": [], "budget": { "rentCap", "depositCap" } \| null }` |
| PUT 🔒 | `/me/profile` | 위 객체 중 바꿀 필드만 | 갱신된 프로필 |
| GET | `/departments` | | `[{ "id", "name", "college", "defaultBuildingIds": [] }]` |
| GET | `/buildings?type=` | `type` 생략 시 전체 | `[{ "id", "name", "type", "lat", "lng" }]` |

**구글 로그인**

| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| POST | `/auth/google` | `{ "idToken": "<구글 ID 토큰(JWT)>" }` | `/auth/email/verify` 와 같은 `{ accessToken, expiresIn, user }` |

- 프론트가 Google Identity Services 버튼으로 받은 ID 토큰을 그대로 보낸다. `hd=hanyang.ac.kr` 는 계정 선택창 힌트일 뿐이라 **서버가 반드시 검증**한다: 구글 공개키로 서명·`aud`(우리 클라이언트 ID)·만료 확인, `email_verified` = true, 이메일이 `@hanyang.ac.kr` 로 끝나는지 확인.
- 도메인이 다르면 `400 INVALID_EMAIL_DOMAIN`, 토큰이 잘못됐으면 `401 UNAUTHORIZED`(프론트는 "구글 로그인을 확인하지 못했어요"로 표시). 계정이 없으면 자동 생성(닉네임 규칙은 메일 인증과 동일).
- 구글 계정에 워크스페이스 도메인(`hd`)이 있으면 `hanyang.ac.kr` 이어야 한다.
- 서버에 클라이언트 ID(`google.client-id`)가 설정되지 않았거나 구글 공개키를 가져오지 못하면 `502 UPSTREAM_FAILED`.
- 프론트 `VITE_GOOGLE_CLIENT_ID` 와 서버 설정의 클라이언트 ID 는 같은 값. 시크릿은 필요 없다.

- 인증 코드: 숫자 6자리, 10분 유효, 재발송 60초 제한, 5회 틀리면 해당 코드 폐기
  - 1~4번째 오류 → `400 CODE_MISMATCH` / 5번째 오류 → `429 TOO_MANY_REQUESTS` + 코드 폐기 (이후 verify도 `429`, 재발송 필요)
  - 코드를 요청한 적 없는 메일로 verify → `400 CODE_MISMATCH`
  - 메일 발송 실패 → `502 UPSTREAM_FAILED` (재발송 60초 제한이 걸리지 않음, 바로 다시 요청 가능)
- 첫 인증 시 계정 자동 생성, 닉네임 기본값 `한양{4자리 숫자}`
- 토큰은 유효한데 계정이 없으면 → `401 UNAUTHORIZED`
- `PUT /me/profile` 규칙
  - 바꿀 수 있는 필드: `departmentId`, `buildingIds`, `budget` (`email`, `nickname` 등은 보내도 무시)
  - 보내지 않았거나 `null`인 필드는 **변경 안 함**
  - `departmentId`만 보내고 `buildingIds`를 생략하면 → `buildingIds`를 그 학과의 `defaultBuildingIds`로 채움
  - `buildingIds`는 보낸 순서대로 저장 (첫 번째가 도보 시간 기준 건물), `[]`이면 모두 해제
  - `budget`은 **두 값을 통째로 교체**. `{ "rentCap": null, "depositCap": null }`이면 예산 삭제 → 응답 `budget: null`
  - 없는 학과·건물 id → `400 VALIDATION_FAILED` (`details`에 `departmentId` 또는 `buildingIds`)

### 5-2. 자취방 매물 · 판정
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET | `/listings` | `bbox=minLng,minLat,maxLng,maxLat` `maxRent` `maxDeposit` `maxMgmtFee` `grade=HIGH,CULPRIT` `maxWalkMin` `roomType` `buildingId` `page` `size` | Page<ListingSummary> |
| GET | `/listings/{id}` | `buildingId`(선택) | ListingDetail |
| GET | `/listings/{id}/price-check` | | PriceCheck |
| GET | `/listings/{id}/alternatives` | `buildingId`(선택) | `{ "housing": [Alternative], "dorms": [Alternative] }` — 각각 환산 월세 낮은 순 최대 3개 |
| GET | `/listings/{id}/nearby` | `radius`(기본 300, 최대 500) | `[{ "category", "name", "lat", "lng", "distanceM" }]` |
| GET | `/walk` | `fromLat` `fromLng` `buildingId` | `{ "minutes", "distanceM", "path": [[lat, lng]], "gateId": null }` |

- `maxWalkMin` 필터는 `buildingId`(또는 로그인 사용자 과 건물)가 있을 때만 적용, 없으면 무시
- 정렬: 기본 `id` 오름차순 (정렬 기능은 스펙에서 제외)

### 5-3. 검색 · 주소
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET | `/search` | `q`(2자 이상) `limit`(기본 10) | `[{ "type": SearchType, "id": null, "name", "address", "lat", "lng" }]` — DB 결과 먼저, 부족하면 `ADDRESS` 결과로 채움 |
| GET | `/geo/address` | `q` | `[{ "address", "roadAddress", "dong", "lat", "lng" }]` (양도 글 주소 입력용) |

### 5-4. 청년안심주택
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET | `/housing` | `maxRent` `maxDeposit` `maxWalkMin` `buildingId` `bbox` (모두 선택) | `[{ "id", "name", "address", "lat", "lng", "recruiting": true, "nextEvent": { "type", "date" } \| null, "subscribed": false, "minConvertedRent", "walkMin" }]` |
| GET | `/housing/{id}` | `buildingId`(선택) | 위 + `{ "unitTypes": [{ "id", "name", "exclusiveAreaM2", "deposit", "rent", "mgmtFee", "convertedRent", "floorplanId" }], "floorLayoutImageUrl", "contact", "walkMin" }` |
| GET | `/housing/announcements` | `status` `housingId` | `[{ "id", "housingId", "title", "status", "events": [{ "type": EventType, "date" }] }]` |
| POST 🔒 | `/housing/{id}/subscribe` | | `204` (이미 구독이면 그대로 204) |
| DELETE 🔒 | `/housing/{id}/subscribe` | | `204` |

- `recruiting` = 해당 단지 공고 중 `OPEN` 또는 `ADDITIONAL`이 하나라도 있으면 `true`
- `nextEvent` = 오늘(KST)을 포함해 그 이후 가장 가까운 일정
- 필터는 `/listings`와 같은 의미이며 **주택형 중 하나라도 조건을 만족하면** 단지를 포함한다. `maxRent`·`maxDeposit`은 주택형의 월세·보증금, `maxWalkMin`은 `buildingId`(없으면 로그인 사용자의 첫 번째 건물) 기준 도보 분
- `minConvertedRent` = 가장 싼 주택형의 환산 월세, `walkMin` = 위 기준 건물까지 도보 분(기준 건물이 없으면 `null`)
- 단지·주택형·공고는 서버가 서울시 청년안심주택(soco.seoul.go.kr)에서 매일 수집한다. 대상 동(실거래 판정 대상 동)에 있는 단지만, 주택형은 **일반공급·청년 자격** 기준
- 공고 `status`는 일정 날짜로 계산한다: 접수 시작 전 `UPCOMING` · 접수 기간 중 `OPEN`(추가모집 공고면 `ADDITIONAL`) · 접수 마감 후 발표 전 `CLOSED` · 발표일부터 `ANNOUNCED`
- 공고는 최근 12개월 게시분만 있다. `events`는 날짜순이며 공고문에 없는 단계는 빠진다(예: "개별 안내"인 서류·계약)
- 화면 참고:
  - 주택형 `name`은 soco 표기 그대로다 (`18타입(18.22)`, `19A`, `25A(20.00)` …). 이름 숫자가 전용면적과 다를 수 있으니 면적은 `exclusiveAreaM2`를 쓴다
  - `exclusiveAreaM2`는 **전용면적**(㎡)이다. 계약면적·공용면적은 없다
  - `floorLayoutImageUrl`은 지금 항상 `null`, 주택형 `floorplanId`는 Task 14(평면도) 전까지 `null`
  - **하트(찜 여부)는 `GET /me/favorites` 한 곳에서 읽는다** (매물·청년안심주택·기숙사·양도 글 모두 같은 방식, 스펙 C6). 청년안심주택·기숙사 응답에는 `favorited` 가 없다. 매물·양도 글의 `favorited` 는 그대로 내려가지만 프론트는 쓰지 않아도 된다

### 5-5. 기숙사
| 메서드 | 경로 | 응답 |
|---|---|---|
| GET | `/dorms` | `[{ "id", "name", "lat", "lng", "roomTypes": [{ "id", "name", "capacity", "semesterFee", "semesterMonths", "mealIncluded", "monthlyCost", "floorplanId" }] }]` |
| GET | `/dorms/{id}` | 위 단건 + `walkMin`(`buildingId` 쿼리 선택) |

- `monthlyCost` = `round(semesterFee ÷ semesterMonths)`
- 기숙사 `id` = 그 기숙사 건물의 건물 id (`buildings`의 `DORM`, 예: 801). 한 건물에 생활관이 둘이면(804 제2학생생활관·한양테크노숙사) 호실 유형으로 나눈다
- 기숙사는 학부 재학생 모집 대상 5동(801·804·805·806·810)만 있다. 호실 `name`에 성별이 들어 있다(`2인실 (남)`). `mealIncluded`는 모두 `false`(식비 별도)
- `/listings/{id}/alternatives`는 **보고 있는 매물보다 환산 월세가 낮은 대상만** 낮은 순으로 각각 최대 3개 (없으면 빈 배열)

### 5-6. 찜
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET 🔒 | `/me/favorites` | `type`(선택) | `[{ "type", "targetId", "name", "lat", "lng", "convertedRent", "grade", "walkMin", "createdAt" }]` |
| POST 🔒 | `/me/favorites` | `{ "type": FavoriteType, "targetId" }` | `201` + 위 항목 1개 / 중복이면 `409 ALREADY_EXISTS` |
| DELETE 🔒 | `/me/favorites/{type}/{targetId}` | | `204` (없어도 204) |

- 기숙사·청년안심주택의 `convertedRent`는 가장 싼 호실·주택형 기준, `grade`는 `null`

### 5-7. 양도 게시판
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET | `/transfers` | `bbox` `status`(기본 `OPEN`) `page` `size` | Page<TransferSummary> = ListingSummary 필드 + `{ "remainingMonths", "availableFrom", "status", "authorNickname" }` |
| GET | `/transfers/{id}` | | TransferSummary + `{ "description", "photos", "priceCheck": PriceCheck, "mine": false }` |
| POST 🔒 | `/transfers` | `{ "title", "address", "dong", "lat", "lng", "deposit", "rent", "mgmtFee", "areaM2", "roomType", "floor", "remainingMonths", "availableFrom", "description", "photoUrls": [] }` | `201` + 상세 (판정 자동 계산 포함) |
| PUT 🔒 | `/transfers/{id}` | POST와 같은 본문 | 상세 / 작성자 아니면 `403` |
| PATCH 🔒 | `/transfers/{id}/status` | `{ "status": "DONE" }` (`OPEN` 으로 되돌리기도 가능) | 상세 / 작성자 아니면 `403` |
| POST 🔒 | `/uploads` | `multipart/form-data` `file` (jpg/png, 5MB 이하) | `{ "url" }` |

- 양도 글 판정의 `contractMonths` = `remainingMonths`
- 요청 검증 (어기면 `400 VALIDATION_FAILED`, `details`에 칸 이름): `title` **필수** 2~40자 (앞뒤 공백 제외) · `address`·`dong`·`lat`·`lng`·`deposit`·`rent`·`areaM2`·`roomType`·`remainingMonths` 필수 · 금액 0 이상 · `areaM2` 0 초과 · `remainingMonths` 1~60 · `description` 2000자 이하 · `photoUrls` 10장 이하, **`/uploads` 가 돌려준 주소만**
- 선택 항목: `mgmtFee`·`floor`·`availableFrom`(`YYYY-MM-DD`)·`description`·`photoUrls` (없으면 `null` 또는 생략). `address`·`dong`·`lat`·`lng` 는 **`GET /geo/address` 결과를 그대로** 넣는다 (`dong` 은 법정동, 판정 기준이라 손으로 고치지 않는다)
- `/uploads` 의 `url` 은 **전체 주소**(예 `https://api.…/files/3f2a….jpg`)다. 그대로 `<img src>`·`photoUrls`에 쓴다. 파일 내용(첫 바이트)으로 jpg·png 를 확인한다
- 목록 `thumbnailUrl` = 첫 번째 사진, 없으면 `null`. 양도 글은 삭제 없이 `DONE` 으로 마감한다

### 5-8. 후기
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET | `/reviews` | `targetType` `targetId` | `{ "average": 4.1, "count": 7, "items": [{ "id", "rating", "scores": { "noise", "light", "bugs", "landlord", "depositReturn" }, "text", "pin": [x, y, z] \| null, "floorplanId", "authorNickname", "createdAt" }] }` |
| POST 🔒 | `/reviews` | `{ "targetType", "targetId", "rating", "scores", "text", "pin", "floorplanId" }` | `201` + 항목 |

- `rating`, `scores.*`(5개 모두): 1~5 정수, 필수. `text` 필수(빈 문자열 `""` 은 허용) 500자 이하. `pin`은 실내 3D 좌표 `[x, y, z]`(FloorPlan 기준, 선택, 숫자 3개)
- **`floorplanId`** = 핀을 찍은 평면도(방) 번호 (선택, 없는 평면도면 400). 한 단지·기숙사에 평면도가 여러 개라 **실내에서는 지금 방과 `floorplanId` 가 같은 핀만 그린다**. 단지·기숙사·매물 상세의 후기 목록은 `floorplanId` 와 상관없이 전부 보여 준다(건물 후기)
- 목록은 최신순, `average` 는 소수 첫째 자리 반올림, 후기가 없으면 `average: null, count: 0`. 같은 사람이 같은 대상에 여러 번 쓸 수 있다(핀마다 따로). 수정·삭제는 없다. 대상이 없으면 `404`

### 5-9. 내 집 기록
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET 🔒 | `/me/home` | | `{ "address", "dong", "lat", "lng", "deposit", "rent", "mgmtFee", "areaM2", "contractStart", "contractEnd" }` / 없으면 `404` |
| PUT 🔒 | `/me/home` | 위 객체 | 위 객체 |
| GET 🔒 | `/me/payments` | | `[{ "month", "amount", "paidAt" }]` 최신순 |
| POST 🔒 | `/me/payments` | `{ "month", "amount", "paidAt" }` | `201` (같은 달이면 덮어씀) |
| GET 🔒 | `/me/utilities` | | `[{ "month", "electricity", "gas", "water", "internet" }]` |
| POST 🔒 | `/me/utilities` | 위 항목 1개 (모르는 항목은 `null`) | `201` (같은 달이면 덮어씀) |
| GET 🔒 | `/me/home/alerts` | | `[{ "id", "daysBefore", "enabled" }]` |
| POST 🔒 | `/me/home/alerts` | `{ "daysBefore": 60, "enabled": true }` (1~365) | `201` |
| PATCH 🔒 | `/me/home/alerts/{id}` | `{ "enabled": false }` | 항목 |
| DELETE 🔒 | `/me/home/alerts/{id}` | | `204` |
| GET 🔒 | `/me/report` | `month` | 아래 |

```json
{
  "month": "2026-10",
  "total": 742000,
  "breakdown": { "rent": 550000, "mgmtFee": 80000, "electricity": 42000, "gas": 38000, "water": 12000, "internet": 20000 },
  "prevTotal": 701000, "diff": 41000,
  "topIncrease": { "item": "gas", "diff": 21000 },
  "excess": { "monthly": 164000, "cumulative": 1312000, "grade": "HIGH" }
}
```
- `total`의 `rent`는 그 달 **납부 기록**, 없으면 계약 월세
- 지난달 기록이 없으면 `prevTotal`, `diff`, `topIncrease` = `null`
- 판정 보류면 `excess` = `null`. `cumulative` = 월 초과액 × (`contractStart`부터 `month`까지 개월 수)

### 5-10. 알림 · 평면도 · 초대
| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| GET 🔒 | `/me/notifications` | | `[{ "id", "type", "title", "body", "targetType", "targetId", "createdAt", "read" }]` 최신순 50개 |
| PATCH 🔒 | `/me/notifications/{id}/read` | | `204` |
| GET | `/floorplans/{id}` | | FloorPlan |
| POST | `/invites` | `{ "playerId": "p_8f2a" }` | `{ "token": "inv_x7k2", "url": "{FRONT_BASE}/?invite=inv_x7k2", "expiresAt" }` (24시간) |

- 알림 생성: 서버가 매일 09:00 KST에 계산 (구독 단지 일정 D-7·D-1·당일, 계약 만료 `daysBefore` 일치)

## 6. 멀티플레이 WebSocket

- 주소: `ws(s)://{API_HOST}/ws/world?nickname={닉네임}&invite={토큰}` (`invite` 선택)
- 서버 1대, **공유 월드 1개**. 서버는 인스턴스를 나누지 않고 `room` 을 그대로 중계한다
- 메시지는 JSON 텍스트, 모든 메시지에 `t`(타입) 필드
- 좌표 `p`: 3D 미터 `[x, y, z]` (4장 기준), `r`: y축 회전(라디안), `a`: 애니메이션 `"idle" | "walk" | "run"`
- `room`: 실내 방 투어 중이면 그 도면 id(양의 정수), 바깥이면 **보내지 않거나 null**. `room` 이 있으면 `p` 는 그 FloorPlan 좌표(m), 없으면 4장의 월드 좌표다
- 받는 쪽은 `room` 으로 나눠 그린다: 바깥 화면은 `room` 없는 사람만, 실내 화면은 같은 `room` 인 사람만. 방을 오가면 좌표계가 바뀌므로 위치 보간을 끊고 새로 시작한다 (2026-11-08 추가, 예전엔 실내에서 `move` 를 안 보냈음)

**클라이언트 → 서버**
| t | 필드 | 설명 |
|---|---|---|
| `move` | `p`, `r`, `a`, `room?` | 최대 10Hz로 전송. `room` 이 정수 1~10억이 아니면(0·음수·소수·문자열) 메시지째 버림 |
| `emote` | `e`: `"wave" \| "heart" \| "clap"` | |
| `chat` | `m` (40자 이하) | 넘으면 서버가 잘라서 중계 |
| `look` | `look: { jacket, hair, skin }` | 접속 직후 1회 + 꾸밀 때마다. `jacket` 은 `^[A-Za-z0-9-]{1,16}$`, `hair`·`skin` 은 `#rrggbb`. 잘못된 필드는 기본값(`school1`, `#2a1d16`, `#f2c9a5`), 객체가 아니면 버림 |
| `ping` | | 15초마다 |

**서버 → 클라이언트**
| t | 필드 | 설명 |
|---|---|---|
| `welcome` | `selfId`, `spawn: { p, r, room? }`, `invited`, `players: [{ id, nickname, look?, p, r, a, room? }]` | 접속 직후 1회. `invited` 는 초대 토큰이 유효해 초대한 사람 옆에 놓였을 때 true. `spawn.room` 이 있으면 초대한 사람이 그 방 안에 있다 → 그 방으로 들어간다 |
| `join` | `player: { id, nickname, look?, p, r, a, room? }` | 누가 들어옴 |
| `leave` | `id` | 누가 나감 (끊김 포함, 60초 무응답 시. 서버가 20초마다 WebSocket ping 을 보내 pong 으로도 생존을 확인) |
| `state` | `players: [{ id, p, r, a, room? }]` | 10Hz, **움직인 사람만, 본인 제외**. 좌표는 소수 2자리. 방에 들어가거나 나온 것도 '움직임'이다 |
| `look` | `id`, `look` | 외형이 바뀜. 본인 제외, 최대 10Hz 로 모아서 중계 (`state` 에는 안 넣음) |
| `emote` | `id`, `e` | |
| `chat` | `id`, `m` | |
| `pong` | | |
| `error` | `code`, `message` | 예: `WORLD_FULL` |

**스폰 규칙**
- `invite` 없음 → 기본 스폰 `p: [0, 0, 0]` (ORIGIN = 사자상, 정문 앞)
- `invite` 유효 + 초대한 사람이 접속 중 → 초대한 사람 위치에서 **반경 1.5m 안 임의 방향** (여러 명이 겹치지 않게). 초대한 사람이 실내면 같은 `room`, 반경 0.8m (실제 설 자리는 클라이언트가 벽·가구를 피해 고른다)
- `invite` 만료·무효·초대자 오프라인 → 기본 스폰 (에러 아님)
- 동시 접속 상한: 서버 설정 `world.max-players` (기본 **30**), 같은 IP 동시 접속 `world.max-per-client` (기본 30 = 사실상 제한 없음, 학교 와이파이 시연용). 넘으면 `error: WORLD_FULL` 후 연결 종료(클라이언트는 재접속하지 않음)

## 7. 공유 픽스처 (목 데이터)

- 위치: 서버 시드는 **백엔드 저장소 `src/main/resources/fixtures/*.json`**. 아직 없는 픽스처(`listings.json` 등)도 이 폴더에 둔다
- 학과·건물(`departments.json`·`buildings.json`)은 **손으로 고치지 않는다.** 원본은 campus-data `campus/departments.json`(출처·확신도 포함)이고, frontend `scripts/build-departments.mjs` 가 프론트 내장 목록과 백엔드 시드를 함께 만든다
- 건물 id = 학교 건물 번호(101, 212 …). 번호가 숫자가 아닌 건물(L01·N08 …)은 1001부터. 프론트 `campusPlaces.json` 의 id 와 같다
- 학과의 `defaultBuildingIds` 는 현재 **학과 행정팀(사무실) 건물** 기준이다 (수업 건물과 다를 수 있음, 첫 번째가 도보 시간 기준)
- 픽스처의 `id`는 서버 DB에도 **그대로** 들어간다 (픽스처끼리 `floorplanId`, `housingId`, `defaultBuildingIds` 등으로 서로 참조하므로)
- 프론트는 MSW 목 응답으로, 백엔드는 데모 시드 데이터로 **같은 파일**을 사용
- 청년안심주택 단지·주택형·공고는 픽스처 파일이 없다. 서버가 soco 에서 매일 수집해 DB 에 저장한다 (5-4장)

| 파일 | 내용 | 최소 수량 |
|---|---|---|
| `listings.json` | ListingDetail 배열 (데모용 샘플 매물) | 20건 (등급 5종 모두 포함, `PENDING` 1건 이상) |
| `price-checks.json` | `{ "<listingId>": PriceCheck }` | 매물 수만큼 |
| `dorms.json` | 기숙사 + 호실 유형 (id = 건물 id, 학기마다 모집요강 보고 갱신) | 1동 이상 |
| `floorplans/{id}.json` | FloorPlan 하나씩 (파일명 = id) | 청아진 18·18A + 기숙사 1종 |
| `departments.json`, `buildings.json` | 학과·캠퍼스 건물·입구·기숙사 | 데모 학과 5개 이상, 입구 2개 이상 |
| `transfers.json` | 양도 글 (`authorNickname` 으로 데모 작성자 생성, 판정은 서버 계산) | 3건 |
| `reviews.json` | 후기 | 매물 5곳에 각 2건 |

## 8. 첫날 함께 정할 체크리스트
- [x] ORIGIN 좌표 확정 (4장) — 사자상 `37.5561486, 127.044341`
- [x] 픽스처 파일 위치·첫 버전 커밋 (7장) — 백엔드 `src/main/resources/fixtures`
- [x] `listings.json` 샘플 20건 금액·좌표 채우기 — 사근동 9·행당동 8·마장동 3, 등급 5종
- [ ] 청아진 18·18A 평면도 JSON 작성 (`floorplans/{id}.json`)
- [ ] 백엔드 로컬 실행 주소·CORS 허용 오리진 (`http://localhost:5173`)
- [ ] Swagger 주소 공유

## 변경 이력
| 날짜 | 버전 | 내용 |
|---|---|---|
| 2026-11-07 | v1.0 | 최초 작성 (스펙 v0.5 기준) |
| 2026-11-07 | v1.1 | 인증 5회 오류 응답 명시(429) · `Alternative.id` 의미 명시 · WS 실내 중 `move` 미전송 명시 · 픽스처 위치 확정, id 보존 · 에러 코드 `METHOD_NOT_ALLOWED`·`INTERNAL_ERROR` 추가 · 인증 세부 응답(코드 미요청, 메일 발송 실패, 계정 없음) · `PUT /me/profile` 수정 규칙 |
| 2026-11-07 | v1.2 | 등급 기준 0.05/0.15/0.30 → **0.10/0.25/0.50** (실거래 분포로 재조정, 2-1장). API 형식 변경 없음 |
| 2026-11-07 | v1.3 | ORIGIN 확정: 임시값 → 사자상 `37.5561486, 127.044341` (프론트 3D 월드 기준). 서버 거리 계산·시드 좌표는 위경도라 영향 없음, 3D 미터 좌표 해석하는 곳만 확인 |
| 2026-11-07 | v1.4 | 구글 로그인 `POST /auth/google` 확정(백엔드 구현·테스트 완료) + `hd` 검사·502 경우 추가 · 픽스처 위치를 실제 방식으로 정정(`src/main/resources/fixtures`, 학과·건물은 campus-data → 프론트 스크립트로 생성), 건물 id 규칙 |
| 2026-11-07 | v1.5 | `GET /housing` 필터(`maxRent`·`maxDeposit`·`maxWalkMin`·`buildingId`·`bbox`)와 `minConvertedRent`·`walkMin` 추가(스펙 C3) · `nextEvent`에 오늘 포함 · 공고 `status`를 일정 날짜로 계산 · 청년안심주택은 soco 매일 수집(대상 동, 일반공급·청년) · 기숙사 id = 건물 id · 대안 비교는 더 싼 대상만 · 픽스처 `housing.json`·`announcements.json` 삭제(수집으로 대체) · 화면 참고(주택형 이름 표기, 전용면적, 비어 있는 필드, 기숙사 5동) |
| 2026-11-08 | v1.6 | 양도 글 요청에 **`title` 필수** 추가(프론트 글쓰기 폼에 제목 칸 필요) · 양도 글 검증 규칙 · `/uploads` 는 전체 주소 응답, `photoUrls` 는 업로드 주소만 · 상태 `OPEN` 되돌리기 허용 · 현재 전환율 0.046·기준 관리비 71,000원 명시 (예시의 0.06 과 구분) · 청년안심주택·기숙사 목록·상세에 `favorited` 추가 (하트 상태, v1.5 의 "/me/favorites 로 판단" 대체) |
| 2026-11-08 | v1.7 | 프론트 구현에 맞춤: 양도 글 `title` **2~40자** · 하트는 `GET /me/favorites` 로 판단하고 청년안심주택·기숙사 `favorited` 는 다시 뺌 · FloorPlan 확장 형식(방 종류·바닥·문 형태·열림 방향·벽 높이·가구 `fixtures`), 원점 = 벽 중심선 바운딩박스 좌상단, 서버 원본은 `fixtures/floorplans/{id}.json` |
| 2026-11-08 | v1.8 | 후기에 `floorplanId`(핀을 찍은 방, 선택) 추가 — 같은 단지 다른 타입 방에 핀이 섞여 보이던 문제. 후기 검증·정렬·평균 규칙 명시 |
