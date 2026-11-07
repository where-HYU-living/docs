# 백엔드 서버 Implementation Plan (담당: 장시현)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 공통 계약 문서 v1.1의 REST API와 멀티플레이 WebSocket을 그대로 제공하는 Spring Boot 서버를 만든다.

**Architecture:** 기능별 패키지(인증, 판정, 매물, 청년안심주택, 기숙사, 찜, 양도, 후기, 내 집, 알림, 월드)로 나눈 단일 Spring Boot 애플리케이션. 초과액 판정은 스프링에 의존하지 않는 순수 도메인 클래스로 두고 서비스가 감싼다. 외부 API(국토부·TMAP·카카오)는 인터페이스 뒤에 두어 테스트에서 가짜로 바꾼다.

**Tech Stack:** Java 21, Spring Boot 3 (Web, Validation, Data JPA, Security, Mail, WebSocket, Scheduling), PostgreSQL 16, Flyway, springdoc-openapi, jjwt, JUnit 5 + AssertJ + MockMvc, Testcontainers(PostgreSQL), Gradle(Kotlin DSL)

**Spec:** `docs/spec-v0.5.md` · **계약:** `docs/api-contract.md` (요청·응답 형식은 전부 계약 문서가 정답. 이 계획은 형식을 반복하지 않는다)

## Global Constraints
- Java 21, Spring Boot 3.x, 패키지 루트 `com.chatatda.api`
- 모든 경로 접두사 `/api/v1`, JSON camelCase, 금액 원 단위 `long`, 비율 소수 셋째 자리 반올림, 값 없음은 `null`
- 게스트 허용: `/me/*`와 쓰기 요청(`/auth/*`, `/invites` 제외)만 인증 필요
- 학교 메일 도메인 `@hanyang.ac.kr`만 허용, 코드 6자리·10분 유효·재발송 60초·5회 오류 시 폐기, JWT 7일
- 등급 경계: `PENDING`(표본 부족) / `≤0.10 FAIR` / `≤0.25 SLIGHTLY_HIGH` / `≤0.50 HIGH` / `>0.50 CULPRIT` (처음 초안 0.05/0.15/0.30 에서 실거래 분포로 재조정, 계약 v1.2 2-1장), 기준값은 설정 `pricing.grade-fair` · `pricing.grade-slight` · `pricing.grade-high`. 등급은 **셋째 자리로 반올림한 `excessRate`** 로 매긴다 (응답 값과 등급이 항상 일치)
- 적정가 표본: 같은 동·면적 ±30%·최근 12개월(**판정하는 날의 직전 달까지**), 10건 미만이면 인접 동 포함, 그래도 10건 미만이면 `PENDING`. 표본 거래는 **신규 월세 계약만** (갱신·계약 구분 빈 값·전세 제외, 스펙 3-4 "갱신 계약 구분"을 앞당김)
- 계약 기간 기본 24개월, 양도 글은 `remainingMonths`
- 외부 API 실패 시 상위 응답은 200 + 해당 필드 `null`/`[]`, 단독 엔드포인트(`/walk`, `/geo/address`)만 502 `UPSTREAM_FAILED`
- CORS 허용: `http://localhost:5173` + 배포 프론트 주소(설정값)
- 알림 계산: 매일 09:00 KST (`Asia/Seoul`)
- WebSocket: 공유 월드 1개, 10Hz 상태 방송, 30초 무응답 시 퇴장, `world.maxPlayers` 기본 50, 초대 스폰 = 초대자 위치 x+1.5
- AI(LLM) 사용 없음, PostGIS 사용 안 함(위경도 컬럼 + BETWEEN으로 충분, **계획 작성자 판단**)

## Review Focus
- **표본 부족 매물·양도 글:** `PENDING` + 숫자 필드 `null`로 200 응답해야 한다 (0이나 500이 나오면 안 됨) → Task 4, 6, 10 테스트
- **학교 메일이 없는 신입생(게스트):** 목록·상세·판정·검색·멀티플레이가 토큰 없이 200이어야 하고 `/me/*`만 401 → Task 2 테스트
- **관리비 0·보증금 0·관리비 미입력:** 환산 월세 계산이 정상이어야 한다 → Task 4 테스트
- **초대 토큰 만료·초대자 오프라인:** 에러 없이 기본 스폰 → Task 15 테스트
- **TMAP·카카오 실패·한도 초과:** 매물 목록이 깨지지 않고 `walkMin: null`, 주변 `[]` → Task 7 테스트

## 진행 현황
| Task | 상태 | 테스트 | 비고 |
|---|---|---|---|
| 1 골격·에러·CORS·Swagger | 구현 완료 | `CommonApiTest` 10 | |
| 2 메일 인증·JWT·보안 | 구현 완료 | `AuthApiTest` 16, `SecurityRulesTest` 10, `JwtProviderTest` 7 | 실제 서버로 로그인 흐름 확인 |
| 3 프로필·학과·건물·시더 | 구현 완료 + **실제 학과·건물 시드 있음** | `ProfileApiTest` 7, `CatalogApiTest` 4, `FixtureSeederTest` 5 | 학과 61개·건물 66곳(프론트 담당이 campus-data 에서 생성). 남은 문제: **입구(`GATE`) 1곳뿐**(계약 최소 2), 학과 건물이 **행정팀 기준**(공대 19개 학과가 모두 206 공업센터본관), 807 게스트하우스가 `DORM` |
| 4 판정 엔진 | 구현 완료 | `PriceCalculatorTest` 11, `GradePolicyTest` 7 | |
| 5 실거래 수집·표본 | 구현 완료 + **실제 수집 완료** | `RealDealNormalizerTest` 8, `MolitHttpClientTest` 3, `RealDealIngestJobTest` 5, `DongAdjacencyTest` 3, `FairRentEstimatorTest` 6 | 개발 DB에 27,718건 (2025-11 ~ 2026-10) |
| 6 매물 API | 구현 완료 + **데모 매물 20건** | `ListingApiTest` 16 | `fixtures/listings.json`: 사근동 9·행당동 8·마장동 3 (실제 지번 좌표), 서버 판정 결과 적정 10·조금 비쌈 4·비쌈 3·범인 2·보류 1. 1번 = "한양대 도보 1분 11㎡" 범인, 9번 = 사근동 8㎡ 표본 부족 보류 |
| 7 도보·주변·주소 | 구현 완료 + **실서버 확인** | `TmapWalkAdapterTest` 4, `KakaoAdaptersTest` 6, `BusStopIndexTest` 3, `WalkServiceTest` 6, `GeoApiTest` 12 | 실제 TMAP 도보 시간 확인 (행당동 지점 → 공업센터본관 11분, IT/BT관 14분) |
| (프론트 담당 추가) 구글 로그인·Docker | 구현 완료 | `GoogleAuthApiTest`, `GoogleJwtVerifierTest` | `POST /auth/google`(계약 v1.4), `Dockerfile`·`docker compose up --build`로 DB+서버 실행 |
| 8 청년안심주택·공고·구독·기숙사·대안 | 구현 완료 + **실제 수집 확인** | `ScheduleParserTest` 5, `SocoParserTest` 6, `AnnouncementStatusPolicyTest` 4, `HousingIngestJobTest` 11, `HousingApiTest` 12, `DormApiTest` 3, `AlternativeApiTest` 4 | soco 실수집: 단지 5곳(퀸즈W·한영스테이·라봄성동·청아진·힐데스하임), 최근 12개월 공고 16건, 실패 0. 2026-11-07 기준 접수 중인 공고 없음. 평면도 연결표 27장 모두 작성(연결표 없는 이미지 0). 한영스테이는 이미지에 면적이 없어 이름 숫자(18·22)를 전용면적으로 사용 |
| 9 찜 | 구현 완료 | `FavoriteApiTest` 12 | 매물·청년안심주택·기숙사·양도 글 목록·상세 `favorited` 실제 값 (청년안심주택·기숙사는 계약 v1.6 에서 추가) |
| 10 양도 게시판·업로드 | 구현 완료 + **실서버 확인** | `TransferApiTest` 15 | 제목 필수(계약 v1.6), 남은 개월 기준 판정, 업로드는 전체 주소 응답·첫 바이트로 jpg/png 확인, 데모 양도 글 3건 |
| 15 멀티플레이 | **구현 완료 (프론트 담당이 진행)** | `WorldServiceTest`·`SessionOutboxTest`·`WorldSocketIT`·`WorldLoadIT` | `/ws/world` 공유 월드(최대 30명, 10Hz), `POST /invites`. 계획과 다른 점은 아래 Task 15 참고 |
| 11~14, 16 | 대기 | | |

전체 테스트 262개 통과 (2026-11-08 기준, 프론트 담당의 멀티플레이 테스트 포함).

**판정 기준값 (현재)** — 모두 `application.yml` 의 `pricing.*` 설정값, 테스트는 별도 고정값(전환율 0.06, 기준 관리비 71,000) 사용
| 값 | 현재 | 출처·근거 |
|---|---|---|
| 전환율 `conversion-rate` | **0.046** | 한국부동산원 지역별 전월세전환율, 서울 · 단독주택+연립다세대, 2026년 8월 (KOSIS 확인). 아파트가 섞인 종합값은 원룸 표본과 성격이 달라 쓰지 않음 |
| 기준 관리비 `baseline-mgmt-fee` | **71,000원** | 한양대 인근 평균 관리비 (2024, `research/okrs-주제재해석.md` 7장 인용 기사) |
| 등급 기준 `grade-*` | **0.10 / 0.25 / 0.50** | 대상 동 18㎡ 원룸 신규 월세 실거래 2,303건을 동 중앙값과 비교 → 적정 69% · 조금 비쌈 16% · 비쌈 10% · 범인 5% ("범인 = 실제 거래 상위 약 5%"를 목표로 고름. 초안 0.05/0.15/0.30 은 범인 11%) |
| 최소 표본 `min-sample` | 10 | 계획 그대로 |

**검증 메모 (OKR 안 2):** 같은 데이터에서 각 거래가 자기 동 중앙값에서 벗어난 정도의 중앙값은 약 14% → KR1 "적정 환산 월세 오차 중앙값 15% 이하"에 해당하는 근거. 정식 검증(실거래 일부를 떼어 두고 비교)은 아직 안 함

**공통 테스트 기반:** `support/IntegrationTest`(PostgreSQL 컨테이너 공유, 매 테스트 전 `users`·`email_codes` 비움, 시드는 `classpath:test-fixtures/`), `MutableClock`(시간 이동), `FakeMailPort`, `TestSupportConfig`, 테스트 전용 `common/ErrorProbeController`

**로컬 실행:** `docker compose up -d`(개발 DB) → `config/application-local.yml`(gitignore, 양식은 `application-local.example.yml`)에 `jwt.secret`(32자 이상)과 외부 키 → `./gradlew bootRun`

---

## 파일 구조
```
backend/
├── build.gradle.kts, settings.gradle.kts, docker-compose.yml(개발 DB)
├── config/application-local.example.yml  # 로컬 비밀값 양식 (실제 파일 application-local.yml 은 gitignore)
├── contract/fixtures/*.json            # 공유 픽스처 정본 (계약 7장)
├── src/main/resources/
│   ├── application.yml                 # pricing.*, world.*, cors.*, external.*, app.* 설정
│   ├── db/migration/V1__init.sql …     # Flyway
│   └── fixtures/ ← contract/fixtures   # 빌드 시 processResources 가 복사
└── src/main/java/com/chatatda/api/
    ├── common/      ApiError, ErrorCode, ApiException, GlobalExceptionHandler, PageResponse, HealthController, ClockConfig, WebConfig, SecurityConfig, JwtProvider, JwtFilter, CurrentUser(+CurrentUserArgumentResolver)
    ├── auth/        AuthController, EmailCodeService, MailPort(+SmtpMailAdapter, LoggingMailAdapter), EmailCode(+Repository)
    ├── user/        User, UserRepository, Budget, ProfileController, ProfileService
    ├── catalog/     Department, Building, BuildingType, (Department|Building)Repository, CatalogController, FixtureSeeder
    ├── pricing/     PricingProperties, PriceInput, PriceResult, Sample, Grade, PriceCalculator, GradePolicy, FairRentEstimator, PriceCheckService
    ├── realdeal/    RealDeal, RealDealType, YearMonthIntegerConverter, RealDealRepository, MolitClient(+MolitHttpClient), MolitApiException, RealDealNormalizer, RealDealIngestJob, DongAdjacency
    ├── listing/     Listing, RoomType, ListingRepository, ListingQuery, ListingDtos, ListingController, ListingService, ListingGradeJob
    ├── geo/         WalkPort(TmapWalkAdapter), PlacePort(KakaoPlaceAdapter), AddressPort(KakaoAddressAdapter), KakaoLocalClient, BusStopIndex, WalkService(+WalkKey·WalkCacheStore), NearbyService, GeoController, GeoMath, ExternalApiException
    ├── housing/     Housing, HousingUnitType, Announcement, AnnouncementEvent, HousingSubscription, FloorplanImage, AnnouncementStatusPolicy, HousingController, HousingService, HousingIngestJob
    │   └── soco/    SocoClient(+SocoHttpClient), SocoParser, ScheduleParser, SocoHome·SocoUnit·SocoNotice
    ├── dorm/        Dorm, DormRoomType, DormController, DormService
    ├── compare/     AlternativeService (alternatives)
    ├── favorite/    Favorite, FavoriteType, FavoriteRepository, FavoriteController, FavoriteService
    ├── transfer/    Transfer, TransferStatus, TransferDtos, TransferRepository, TransferController, TransferService, UploadController, StoragePort(+LocalDiskStorage), UploadConfig
    ├── review/      Review, ReviewController
    ├── home/        Home, Payment, Utility, ExpiryAlert, HomeController, ReportService
    ├── notification/ Notification, NotificationController, NotificationJob
    ├── search/      SearchController, SearchService
    ├── floorplan/   FloorPlan(jsonb 컬럼), FloorPlanController
    └── world/       WorldService, WorldSocketHandler, WorldPlayer, SessionOutbox(+Outbox), InviteService, InviteController, WorldProperties, WorldConfig (프론트 담당 구현)
```

---

### Task 1: 프로젝트 골격 · 공통 에러 · CORS · Swagger

**Files:**
- Create: `build.gradle.kts`, `application.yml`, `common/ApiError.java`, `common/ErrorCode.java`, `common/ApiException.java`, `common/GlobalExceptionHandler.java`, `common/PageResponse.java`, `common/HealthController.java`
- Test: `src/test/java/com/chatatda/api/common/CommonApiTest.java`, `src/test/java/com/chatatda/api/support/IntegrationTest.java` (Testcontainers PostgreSQL 베이스 클래스)

**Interfaces:**
- Produces: `record ApiError(String code, String message, Object details)`, `enum ErrorCode { VALIDATION_FAILED(400), INVALID_EMAIL_DOMAIN(400), CODE_MISMATCH(400), CODE_EXPIRED(400), UNAUTHORIZED(401), FORBIDDEN(403), NOT_FOUND(404), ALREADY_EXISTS(409), TOO_MANY_REQUESTS(429), UPSTREAM_FAILED(502), WORLD_FULL(503), METHOD_NOT_ALLOWED(405), INTERNAL_ERROR(500) }` (뒤의 두 개는 구현 중 추가, 계약 v1.1 반영), `class ApiException extends RuntimeException { ApiException(ErrorCode, String message) }`, `record PageResponse<T>(List<T> items, int page, int size, long total)`, 추상 클래스 `IntegrationTest`

- [x] **Step 1: 실패하는 테스트 작성**
```java
@Test void health_ok() { mvc.perform(get("/api/v1/health")).andExpect(status().isOk()); }
@Test void notFound_usesErrorFormat() {
  mvc.perform(get("/api/v1/__none"))
     .andExpect(status().isNotFound()).andExpect(jsonPath("$.code").value("NOT_FOUND"));
}
@Test void cors_allowsLocalFront() {
  mvc.perform(options("/api/v1/health").header("Origin","http://localhost:5173").header("Access-Control-Request-Method","GET"))
     .andExpect(header().string("Access-Control-Allow-Origin","http://localhost:5173"));
}
```
- [x] **Step 2: 실행해서 실패 확인** — `./gradlew test --tests '*CommonApiTest'` → FAIL (프로젝트·핸들러 없음)
- [x] **Step 3: 구현** — Spring Initializr 의존성: web, validation, data-jpa, security, mail, websocket, postgresql, flyway, springdoc-openapi-starter-webmvc-ui, jjwt, testcontainers-postgresql. `GlobalExceptionHandler`는 `ApiException`·`MethodArgumentNotValidException`(→ `VALIDATION_FAILED`, `details`=필드별 메시지)·`NoResourceFoundException`(→ `NOT_FOUND`)를 `ApiError`로 변환. CORS 오리진은 `cors.allowed-origins` 설정값
  - **구현 반영:**
    - security·mail·jjwt는 Task 2, websocket은 Task 15에서 추가 (Security가 있으면 설정 전까지 모든 경로가 401이라 Task 1 테스트가 통과할 수 없음)
    - Flyway 10 이후 PostgreSQL 지원이 분리되어 `flyway-database-postgresql` 추가
    - Docker Engine 29가 구버전 클라이언트를 거부해서 Testcontainers를 `1.21.4`로 고정 (Spring Boot 3.5.0 기본값 1.21.0은 연결 불가)
    - 계약 형식을 지키려고 핸들러 추가: 깨진 JSON·잘못된 enum/타입·필수 파라미터 누락 → `400 VALIDATION_FAILED`, 잘못된 메서드 → `405 METHOD_NOT_ALLOWED`, 처리 못 한 예외 → `500 INTERNAL_ERROR`(상세 내용은 로그에만)
    - `ClockConfig`(`Asia/Seoul` 시계 빈) 추가, `spring.jpa.open-in-view: false`
    - 테스트는 계획 3개 + 위 핸들러 확인 6개 + 시계 1개
- [x] **Step 4: 통과 확인** — 같은 명령 → PASS. `./gradlew bootRun` 후 `http://localhost:8080/swagger-ui.html` 열림
- [ ] **Step 5: 커밋** — `git commit -m "chore: bootstrap spring server with error format, cors, swagger"`

### Task 2: 학교 메일 인증 · JWT · 게스트 허용 보안

**Files:**
- Create: `auth/AuthController.java`, `auth/EmailCodeService.java`, `auth/EmailCode.java`, `auth/MailPort.java`, `auth/SmtpMailAdapter.java`, `common/JwtProvider.java`, `common/JwtFilter.java`, `common/SecurityConfig.java`, `common/CurrentUser.java`, `user/User.java`, `user/UserRepository.java`, `db/migration/V1__users_auth.sql`
- Test: `auth/AuthApiTest.java`, `common/SecurityRulesTest.java`

**Interfaces:**
- Consumes: Task 1 `ApiException`, `ErrorCode`
- Produces: `interface MailPort { void send(String to, String subject, String body); }`, `JwtProvider.issue(long userId): String`, `JwtProvider.parse(String token): Optional<Long>`, 컨트롤러 파라미터 `@CurrentUser Long userId`(필수), `@CurrentUser(required=false) Long userIdOrNull`, `EmailCodeService` 내부 시계 `Clock` 주입(테스트 시간 이동용)

- [x] **Step 1: 실패하는 테스트 작성** (`MailPort`는 테스트에서 받은 코드를 저장하는 가짜 빈)
```java
@Test void send_rejectsOtherDomain()  // POST /auth/email/send {email:"a@gmail.com"} → 400, code INVALID_EMAIL_DOMAIN
@Test void send_then_verify_issuesToken() // send → 204, fakeMail.lastCode() 6자리 숫자, verify → 200, $.accessToken 존재, $.user.nickname 이 "한양"으로 시작
@Test void verify_wrongCode_400()      // code CODE_MISMATCH
@Test void verify_after10min_expired() // clock +601초 → CODE_EXPIRED
@Test void resend_within60s_429()      // TOO_MANY_REQUESTS
@Test void fiveWrongAttempts_discardsCode() // 1~4회 오류 → 400 CODE_MISMATCH, 5번째 오류 → 429 TOO_MANY_REQUESTS, 그 뒤 맞는 코드도 429 (계약 5-1)
// SecurityRulesTest
@Test void guest_canBrowse()   // 토큰 없이 GET /api/v1/listings, /api/v1/housing, /api/v1/search?q=행당 → 200
@Test void guest_meIs401()     // 토큰 없이 GET /api/v1/me/profile → 401, code UNAUTHORIZED
@Test void guest_writeIs401()  // 토큰 없이 POST /api/v1/me/favorites → 401
@Test void guest_canCreateInvite() // 토큰 없이 POST /api/v1/invites → 401 아님
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*AuthApiTest' --tests '*SecurityRulesTest'` → FAIL
- [x] **Step 3: 구현** — 코드 생성 `SecureRandom` 6자리(앞자리 0 허용), 저장은 DB `email_codes`(email, code_hash, expires_at, attempts, sent_at). 첫 인증 시 `User` 생성(닉네임 `한양` + 4자리 난수, 중복 시 재생성). `SecurityConfig`: `/api/v1/me/**` 인증, `HttpMethod.GET` 전부 허용, `/api/v1/auth/**`·`/api/v1/invites` 허용, 그 외 쓰기는 인증. 인증 실패 응답도 `ApiError` 형식. `SmtpMailAdapter`는 `spring.mail.*` 설정 사용 (로컬은 로그 출력 어댑터로 대체 가능)
  - **구현 반영:**
    - `guest_canBrowse`는 대상 엔드포인트(Task 6·8·14)가 아직 없어서 "401·403이 아님"으로 검사. **각 Task에서 200 검사로 바꿀 것**
    - 메일 어댑터 선택: `app.mail.mode: log | smtp` (기본 `log`, 로컬은 인증 코드를 로그에 출력)
    - `jwt.secret`(환경 변수 `JWT_SECRET`)이 비었거나 32자 미만이면 시작 시 실패
    - 틀린 코드의 `attempts + 1`이 예외와 함께 롤백되지 않도록 `verify`는 `noRollbackFor = ApiException`
    - 코드 미요청 메일로 verify → `CODE_MISMATCH`, 메일 발송 실패 → `502 UPSTREAM_FAILED`(재발송 제한 안 걸림), 코드 형식 오류는 횟수에 미포함 (계약 v1.1 반영)
    - JWT 필터는 빈으로 등록하지 않음(두 번 실행 방지). 만료·위조 토큰은 에러 대신 게스트로 처리 → 공개 GET은 200, `/me`는 401
    - CORS를 `SecurityConfig`로 이동(인증 경로 preflight가 401이 되는 문제 방지). `WebConfig`는 `@CurrentUser` 리졸버 등록용으로 남김
    - 스프링 기본 계정 자동 생성(`UserDetailsServiceAutoConfiguration`) 제외
    - 403 처리기는 아직 없음 (보안 계층에서 403이 나는 규칙이 생기면 추가)
- [x] **Step 4: 통과 확인** — 같은 명령 → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(auth): hanyang email code login, jwt, guest-friendly security"`

### Task 3: 프로필 · 학과 · 건물 · 공유 픽스처 시더

**Files:**
- Create: `user/ProfileController.java`, `user/ProfileService.java`, `catalog/Department.java`, `catalog/Building.java`, `catalog/CatalogController.java`, `catalog/FixtureSeeder.java`, `db/migration/V2__catalog_profile.sql`
- Test: `user/ProfileApiTest.java`, `catalog/CatalogApiTest.java`, `catalog/FixtureSeederTest.java`

**Interfaces:**
- Produces: `FixtureSeeder.seedIfEmpty()` — `fixtures/*.json`(계약 7장)을 읽어 비어 있는 테이블에만 넣음, `app.seed.enabled=true`일 때 시작 시 실행. 다른 Task들의 엔티티 시드는 각 Task가 이 클래스에 메서드를 추가(`seedListings()`, `seedDorms()` …)
  - **픽스처 `id`를 그대로 저장**하고, 테이블마다 넣은 뒤 `select setval('<seq>', (select max(id) from <table>))`로 시퀀스를 맞춤 (이후 새로 만드는 행과 ID 충돌 방지)
  - `FixtureSeeder.demoUser(String nickname): long` — 후기·양도 글 픽스처의 `authorNickname`마다 데모 사용자를 만들어 ID 반환(이미 있으면 재사용). Task 10·11 시드에서 사용
- Produces: `ProfileService.firstBuildingId(long userId): Optional<Long>` (Task 6, 8에서 도보 기준 건물로 사용), `ProfileService.budget(long userId): Optional<Budget>`, `record Budget(Long rentCap, Long depositCap)`

- [x] **Step 1: 실패하는 테스트 작성**
```java
@Test void departments_listed()        // GET /departments → 길이 ≥ 5, $[0].defaultBuildingIds 배열
@Test void buildings_filterByType()    // GET /buildings?type=GATE → 전부 type=="GATE", 길이 ≥ 2
@Test void profile_updatePartial()     // PUT /me/profile {budget:{rentCap:600000,depositCap:10000000}} → 200, departmentId 그대로, budget.rentCap==600000
@Test void profile_settingDepartment_fillsDefaultBuildings() // PUT {departmentId: X} (buildingIds 생략) → buildingIds == 학과 defaultBuildingIds
@Test void seeder_isIdempotent()       // seedIfEmpty() 두 번 → 학과 수 변화 없음
@Test void seeder_keepsFixtureIds()    // 픽스처 학과 id 그대로 조회됨 / 시드 후 새로 저장한 행의 id > 픽스처 max id
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*ProfileApiTest' --tests '*CatalogApiTest' --tests '*FixtureSeederTest'` → FAIL
- [x] **Step 3: 구현** — PUT은 null 필드를 "변경 안 함"으로 처리. Jackson으로 픽스처 파싱
  - **구현 반영:**
    - 시더가 읽는 위치를 설정 `app.seed.location`(기본 `classpath:fixtures/`)으로 둠. 테스트는 가짜 데이터 `src/test/resources/test-fixtures/` 사용 (실제 학과·건물 데이터는 Task 6 전까지 작성)
    - 시드는 JPA 대신 SQL로 id를 지정해 넣고 `pg_get_serial_sequence`로 시퀀스를 맞춤. 건물 → 학과 순서, 한 트랜잭션
    - 픽스처 검증: 필수 필드(건물 `lat`·`lng` 포함) 누락, 없는 건물 id 참조 → 시작 시 어느 항목인지 알려 주며 실패
    - `demoUser` 이메일은 로그인할 수 없는 `demo-<임의값>@demo.invalid`
    - `PUT /me/profile`: "null이면 변경 안 함"은 최상위 필드에만 적용, `budget`은 통째로 교체(두 값 모두 null이면 삭제 → `budget: null`), 없는 학과·건물 id → `400 VALIDATION_FAILED`, 닉네임 수정 불가, 토큰은 유효한데 계정이 없으면 401 (계약 v1.1 반영)
    - `buildingIds`·학과 기본 건물은 순서 저장 (`@OrderColumn`), 위경도 컬럼은 `double precision`
    - 시드 실행 여부 `app.seed.enabled`(환경 변수 `SEED_ENABLED`, 기본 true)
    - 시더는 **비어 있는 테이블에만** 넣으므로, 개발 DB에 들어간 뒤 픽스처를 고치면 `docker compose down -v`로 비우고 다시 실행
- [x] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(catalog): departments, buildings, profile, fixture seeder"`

### Task 4: 초과액 판정 엔진 (순수 도메인)

**Files:**
- Create: `pricing/PricingProperties.java`, `pricing/PriceInput.java`, `pricing/Sample.java`, `pricing/PriceResult.java`, `pricing/Grade.java`, `pricing/PriceCalculator.java`, `pricing/GradePolicy.java`
- Test: `pricing/PriceCalculatorTest.java`, `pricing/GradePolicyTest.java`

**Interfaces:**
- Produces:
  - `@ConfigurationProperties("pricing") record PricingProperties(double conversionRate /*기본 0.06*/, double gradeFair /*0.05*/, double gradeSlight /*0.15*/, double gradeHigh /*0.30*/, int minSample /*10*/, double areaTolerance /*0.30*/, int periodMonths /*12*/, int defaultContractMonths /*24*/, long baselineMgmtFee /*0, 구현 중 추가*/)`
  - `record PriceInput(long deposit, long rent, Long mgmtFee /*null 허용*/, double areaM2, String dong, int contractMonths)`
  - `record Sample(int count, String scope /*DONG|ADJACENT|NONE*/, List<String> dongs, Double areaMinM2, Double areaMaxM2, YearMonth from, YearMonth to, Double medianPerM2 /*㎡당 환산월세*/)`
  - `enum Grade { FAIR, SLIGHTLY_HIGH, HIGH, CULPRIT, PENDING }`
  - `PriceCalculator.convertedRent(long deposit, long rent, Long mgmtFee, double rate): long`
  - `PriceCalculator.evaluate(PriceInput in, Sample sample): PriceResult`
  - `record PriceResult(long convertedRent, Long fairRent, Long monthlyExcess, int contractMonths, Long totalExcess, Double excessRate, Grade grade, double conversionRate, Sample sample)`
  - `GradePolicy.of(Double excessRate, boolean pending): Grade`

- [x] **Step 1: 실패하는 테스트 작성**
```java
@Test void convertedRent_includesDepositAndMgmt() {
  assertThat(calc.convertedRent(10_000_000, 550_000, 80_000L, 0.06)).isEqualTo(680_000); // 550000+80000+50000
}
@Test void convertedRent_nullMgmt_treatedAsZero() { assertThat(calc.convertedRent(0, 400_000, null, 0.06)).isEqualTo(400_000); }
@Test void evaluate_computesExcess() {
  var s = new Sample(23,"DONG",List.of("행당동"),12.6,23.4,YearMonth.of(2025,11),YearMonth.of(2026,10), 30_000.0);
  var r = calc.evaluate(new PriceInput(10_000_000,550_000,80_000L,18.0,"행당동",24), s);
  assertThat(r.fairRent()).isEqualTo(540_000);        // 30000 × 18
  assertThat(r.monthlyExcess()).isEqualTo(140_000);   // 680000 − 540000
  assertThat(r.totalExcess()).isEqualTo(3_360_000);
  assertThat(r.excessRate()).isEqualTo(0.259);        // 셋째 자리 반올림
  assertThat(r.grade()).isEqualTo(Grade.HIGH);
}
@Test void evaluate_pendingWhenNoSample() {
  var r = calc.evaluate(input, new Sample(4,"NONE",List.of(),null,null,null,null,null));
  assertThat(r.grade()).isEqualTo(Grade.PENDING);
  assertThat(r.fairRent()).isNull(); assertThat(r.totalExcess()).isNull(); assertThat(r.excessRate()).isNull();
}
@ParameterizedTest @CsvSource({"-0.2,FAIR","0.05,FAIR","0.0501,SLIGHTLY_HIGH","0.15,SLIGHTLY_HIGH","0.3,HIGH","0.3001,CULPRIT"})
void grade_boundaries(double rate, Grade expected) { assertThat(policy.of(rate,false)).isEqualTo(expected); }
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*PriceCalculatorTest' --tests '*GradePolicyTest'` → FAIL
- [x] **Step 3: 구현** — 금액은 `Math.round`(원 단위), `excessRate`는 `BigDecimal` HALF_UP 셋째 자리. 스프링 의존 없음
  - **구현 반영:**
    - **기준 관리비 `pricing.baseline-mgmt-fee`**: 적정 월세 = ㎡당 중앙값 × 면적 + 기준 관리비. 매물은 관리비를 포함하는데 실거래에는 관리비가 없어서 모든 매물이 관리비만큼 비싸게 판정되는 편향을 보정 (스펙 3-1 식과 다름, 3-4 "관리비 보정"을 앞당김). 현재 **71,000원** (진행 현황의 판정 기준값 표 참고)
    - 등급은 반올림한 `excessRate`로 판정 (Global Constraints 참고)
    - 보류 조건: 표본 없음, 중앙값 없음, 건수 < `minSample`, 적정 월세 ≤ 0
    - 시세보다 싼 집의 음수 초과액은 0으로 자르지 않음
    - 금액은 실수 오차를 피하려고 `BigDecimal` HALF_UP으로 계산 (`Math.round`와 결과 같음)
    - `PricingProperties`는 생성 시 값 검증(전환율 0~1, 등급 기준 오름차순 등) → 설정 키 오타로 0이 들어가면 시작 시 실패. 메인 클래스에 `@ConfigurationPropertiesScan`
    - 테스트: 계획 5개 + 관리비 0·보증금 0(Review Focus), 최소 표본 미달, 음수 초과액, 반올림 등급, 계약 개월 수, 기준 관리비, 설정값 검증, 보류 처리
- [x] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(pricing): converted rent, fair rent, excess and grade domain"`

### Task 5: 실거래 수집 · 정제 · 적정가 표본 조회

**Files:**
- Create: `realdeal/RealDeal.java`, `realdeal/RealDealRepository.java`, `realdeal/MolitClient.java`, `realdeal/RealDealNormalizer.java`, `realdeal/RealDealIngestJob.java`, `realdeal/DongAdjacency.java`, `pricing/FairRentEstimator.java`, `db/migration/V3__real_deals.sql`
- Test: `realdeal/RealDealNormalizerTest.java`, `pricing/FairRentEstimatorTest.java`, 픽스처 `src/test/resources/molit/officetel-rent-sample.xml`

**Interfaces:**
- Consumes: Task 4 `PricingProperties`, `PriceCalculator.convertedRent`, `Sample`
- Produces:
  - `RealDeal` 컬럼: `dong, buildingType(OFFICETEL|ROWHOUSE|DETACHED), areaM2, deposit, rent, contractYm(YearMonth), floor, builtYear, canceled`
  - `RealDealNormalizer.parse(String xml, String buildingType): List<RealDeal>` — 취소 건(해제 사유 있음) 제외, 보증금·월세 "만원" 문자열(쉼표 포함) → 원 단위
  - `DongAdjacency.neighbors(String dong): List<String>` — 대상 동 인접 관계 하드코딩 (행당·사근·마장·홍익·도선·하왕십리·상왕십리·답십리 등)
  - `FairRentEstimator.sampleFor(String dong, double areaM2, YearMonth asOf): Sample`
  - `MolitClient.fetch(String lawdCd, YearMonth ym, String buildingType): String` (XML 원문), 서비스키는 설정 `external.molit.key`
  - `RealDealIngestJob.ingest(YearMonth from, YearMonth to)` — 성동구(11200)·동대문구(11230) 법정동코드 앞 5자리, 수동 실행용 관리자 엔드포인트 없이 `CommandLineRunner`(`app.ingest.enabled=true`)로 실행

- [x] **Step 1: 실패하는 테스트 작성**
```java
@Test void normalizer_dropsCanceled_andConvertsManwon() {
  var deals = normalizer.parse(readXml("officetel-rent-sample.xml"), "OFFICETEL");
  assertThat(deals).noneMatch(RealDeal::isCanceled);
  assertThat(deals.get(0).getDeposit()).isEqualTo(10_000_000L); // "1,000"만원
}
@Test void estimator_usesSameDong_whenEnough()   // 행당동 18㎡±30% 최근12개월 12건 저장 → scope "DONG", count 12, medianPerM2 = 중앙값
@Test void estimator_expandsToAdjacent()         // 행당동 4건 + 사근동 8건 → scope "ADJACENT", dongs 에 두 동
@Test void estimator_noneWhenStillShort()        // 합쳐도 9건 → scope "NONE", medianPerM2 null
@Test void estimator_ignoresOldDeals()           // 13개월 전 거래는 제외
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*RealDealNormalizerTest' --tests '*FairRentEstimatorTest'` → FAIL
- [x] **Step 3: 구현** — 표본의 ㎡당 환산 월세 = `convertedRent(deposit, rent, null, rate) / areaM2` (실거래에는 관리비 없음), 중앙값은 정렬 후 가운데(짝수면 두 값 평균). 국토부 API 데이터셋 이름·파라미터는 공공데이터포털 상세 페이지 기준으로 확인 후 `MolitClient`에 상수로 기록
  - **실제 응답으로 확인한 사실 (성동구 2026-10, 3개 데이터셋 모두 정상 조회):**
    - 엔드포인트: `apis.data.go.kr/1613000/` + `RTMSDataSvcOffiRent/getRTMSDataSvcOffiRent`(오피스텔) · `RTMSDataSvcRHRent/getRTMSDataSvcRHRent`(연립다세대) · `RTMSDataSvcSHRent/getRTMSDataSvcSHRent`(단독다가구), 파라미터 `serviceKey`·`LAWD_CD`·`DEAL_YMD`(yyyyMM)·`pageNo`·`numOfRows`, 응답 UTF-8 XML, 정상 `resultCode` 는 `000`
    - **취소(해제) 필드는 세 데이터셋 모두 없음** → 계획의 "취소 건 제외"는 하지 않음
    - `contractType`(신규/갱신) 있음. 빈 값은 약 3% (첫 확인 때 10건짜리 한 페이지만 보고 "60%"라고 잘못 판단했던 것을 정정)
    - 동 `umdNm` 은 법정동, 금액 `deposit`·`monthlyRent` 는 쉼표 포함 만원 문자열, 면적은 오피스텔·연립다세대 `excluUseAr` / 단독다가구 `totalFloorAr`, 단독다가구에는 `floor`·`jibun` 없음, 빈 값은 공백 한 칸
  - **구현 반영:**
    - 정제(`RealDealNormalizer`)는 형식이 틀린 행만 제외하고 **갱신·전세도 모두 저장**, 표본 조건은 `FairRentEstimator` 조회에서 적용 → 규칙을 바꿔도 재수집 불필요
    - 시그니처: `parse(String xml, RealDealType type, Instant ingestedAt): MolitPage`(전체 건수·제외 건수 포함), `MolitClient.fetch(lawdCd, ym, type, pageNo, numOfRows)` — 페이지 처리 때문에 계획보다 인자가 늘어남. 건물 유형은 문자열 대신 enum `RealDealType`
    - `MolitClient` 는 인터페이스, 실제 구현은 `MolitHttpClient`(서비스키는 한 번만 URL 인코딩, 응답은 바이트로 받아 UTF-8 해석, 연결 5초·읽기 15초)
    - XML 외부 엔티티(XXE) 차단, 오류 응답(`OpenAPI_ServiceResponse`, `resultCode` ≠ `000`)은 `MolitApiException`
    - 수집은 (구, 월, 유형) 묶음마다 **지우고 다시 넣기** → 여러 번 돌려도 중복 없음. 한 묶음이 실패해도 나머지는 계속, 실패 목록은 로그로
    - 기본 수집 범위 `app.ingest.months: 12` → 직전 달까지 12개월
    - 인접 동은 쌍으로 적어 자동으로 양방향 (`DongAdjacency`). 초안 목록이라 **사용자 확인 필요**, 다만 실제로 인접 확대가 일어나는 건 상왕십리동·응봉동뿐
    - 표본 `dongs` 에는 실제 거래가 들어간 동만, 기준 동이 맨 앞. `NONE` 이면 `dongs: []`, 면적·기간 null
- [x] **Step 4: 통과 확인** → PASS. 실제 키로 `./gradlew bootRun --args='--app.ingest.enabled=true'` 1회 실행 후 `select dong, count(*) from real_deals group by dong` 결과를 PR 설명에 기록 (OKR 안 2의 표본 수 근거)
  - **실제 수집 결과 (2026-11-07):** 성동구·동대문구, 2025-11 ~ 2026-10, **27,718건 저장 · 형식 오류 0 · 실패 0**
  - **동별 표본 (18㎡ ±30%, 신규 월세, 전환율 0.06 기준):**

    | 동 | 표본 | ㎡당 중앙값 | 판정 범위 |
    |---|---|---|---|
    | 마장동 | 505 | 35,294원 | 같은 동 |
    | 행당동 | 480 | 36,111원 | 같은 동 |
    | 용답동 | 349 | 37,110원 | 같은 동 |
    | 답십리동 | 346 | 36,372원 | 같은 동 |
    | 사근동 | 267 | 31,668원 | 같은 동 |
    | 도선동 | 222 | 46,739원 | 같은 동 |
    | 하왕십리동 | 91 | 33,333원 | 같은 동 |
    | 홍익동 | 43 | 32,895원 | 같은 동 |
    | 응봉동 | 1 | — | 인접 확대 (행당동 포함 481건) |
    | 상왕십리동 | 0 | — | 인접 확대 (홍익·하왕십리 포함 134건) |

    18·26·33·45·60㎡ 모두에서 대상 동은 상왕십리동·응봉동을 빼고 같은 동 표본 10건 이상 → **표본 부족 위험은 해소**. 유형별로는 단독다가구 58% · 오피스텔 33% · 연립다세대 10%
- [ ] **Step 5: 커밋** — `git commit -m "feat(realdeal): molit ingest, normalization, fair-rent sample"`

### Task 6: 자취방 매물 API (목록 필터 · 상세 · price-check)

**Files:**
- Create: `listing/Listing.java`, `listing/ListingRepository.java`, `listing/ListingQuery.java`, `listing/ListingService.java`, `listing/ListingController.java`, `pricing/PriceCheckService.java`, `db/migration/V4__listings.sql`
- Modify: `catalog/FixtureSeeder.java` (`seedListings()`)
- Test: `listing/ListingApiTest.java`

**Interfaces:**
- Consumes: Task 3 `ProfileService.firstBuildingId/budget`, Task 4·5 `PriceCalculator`, `FairRentEstimator`, Task 7 `WalkService.minutesOrNull`(Task 7 전에는 `WalkService` 인터페이스만 만들고 null 반환 구현)
- Produces:
  - `PriceCheckService.check(PriceInput in, Long userIdOrNull): PriceCheckDto` (계약 PriceCheck 형식, `budget` 포함)
  - `ListingService.summaryOf(Listing l, Long buildingId, Long userIdOrNull): ListingSummaryDto` — 찜·양도·검색에서 재사용
  - 매물 등급·환산 월세는 저장 시 계산해 컬럼(`converted_rent`, `grade`)에 캐시 → 목록 필터 `grade`가 DB 조건으로 동작. 실거래 재수집 후 `ListingService.recomputeAll()`

- [x] **Step 1: 실패하는 테스트 작성** (픽스처 시드 사용)
```java
@Test void list_bboxFilter()        // bbox 행당동 범위 → 전부 lat/lng 범위 안
@Test void list_gradeFilter()       // grade=HIGH,CULPRIT → 전부 두 등급 중 하나
@Test void list_maxRentFilter()     // maxRent=500000 → 전부 rent ≤ 500000
@Test void list_walkFilterIgnoredWithoutBuilding() // 게스트 + maxWalkMin=5 → 필터 무시, total == 전체 수, items[*].walkMin == null
@Test void list_pagination()        // size=5,page=1 → items 5개, page 1, total == 시드 수
@Test void detail_404()             // GET /listings/999999 → NOT_FOUND
@Test void priceCheck_shape()       // $.grade, $.convertedRent, $.sample.scope 존재, 게스트면 $.budget == null
@Test void priceCheck_pendingListing_returns200WithNulls() // 시드의 PENDING 매물 → 200, $.fairRent null, $.sample.scope "NONE"
@Test void priceCheck_budgetForLoggedIn() // rentCap 600000 설정 사용자 → $.budget.overRent == max(0, convertedRent-600000)
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*ListingApiTest'` → FAIL
- [x] **Step 3: 구현** — 목록은 JPA Specification으로 조건 조합. `favorited`는 Task 9 전까지 false
  - **구현 반영:**
    - 매물 저장 구조 `V4__listings.sql` (`listings` + 순서 있는 `listing_options`·`listing_photos`), 시드는 SQL로 id 지정, 픽스처의 계산 필드(`convertedRent`·`grade`·`walkMin`·`favorited`)는 무시하고 서버가 다시 계산
    - 등급·환산 월세 캐시는 `ListingService.recomputeAll()`. 서버 시작 시 **실거래 수집(CommandLineRunner) → 시드(`@Order(1)`) → 재계산(`ListingGradeJob`, `@Order(2)`)** 순서로 자동 실행
    - `/price-check` 는 캐시가 아니라 요청마다 다시 계산 (표본·예산이 매번 다를 수 있음). 같은 데이터면 캐시 등급과 같음을 테스트로 확인
    - 판정 기준월은 계산하는 날의 직전 달 (`PriceCheckService.evaluate`)
    - 응답 `sample` 은 계약 형식(`from`·`to` 는 `"2025-11"`, 내부 값 `medianPerM2` 없음)
    - 예산: 상한이 하나만 있으면 없는 쪽 `over*` 는 null
    - 페이지 크기 100 초과는 100으로 줄임, `page < 0`·`size < 1`·잘못된 `bbox`(4개가 아님, 숫자 아님, 최솟값 > 최댓값)는 `400 VALIDATION_FAILED`
    - 관리비 상한 필터는 관리비가 없는(null) 매물을 제외
    - **도보 시간 필터:** 기준 건물이 있으면 조건에 맞는 매물을 모두 가져와 메모리에서 거르고 페이지를 나눔(데모 매물 수십 건 규모라 충분). 도보 시간을 모르는 매물은 제외 → 지금은 `WalkService` 가 null 만 돌려줘서 기준 건물 + 도보 필터 조합의 결과가 0건 (Task 7에서 해결)
    - `guest_canBrowse` 의 `/listings` 를 200 검사로 변경
    - 테스트는 어떤 판정 기준값에서도 결과가 같은 매물(매우 비싼 집 → 범인, 표본 없는 동·면적 → 보류)로 구성, 판정 기준값은 테스트에서 별도로 고정
  - ~~남은 일: 데모 매물 20건~~ → 완료 (2026-11-08). `src/main/resources/fixtures/listings.json`
    - 동: 학생 수요가 많은 사근동·행당동 위주 + 마장동 (도선동·홍익동은 학교 생활권에서 멀어 제외, 사용자 결정)
    - 좌표: 카카오 주소 검색으로 찾은 실제 지번 (도로명 주소가 있는 곳만). 3D 월드가 캠퍼스 주변뿐이라 대부분 3D 범위 밖이지만, 매물은 말풍선·2D 지도로 표시되므로 문제없음
    - 금액: 동·면적별 적정가(서버와 같은 규칙)에 맞춰 등급 경계에서 충분히 떨어지게 정함. 보류는 사근동 8㎡ (인접 동 포함 표본 6건)
    - 실거래를 다시 수집하면 적정가가 바뀌어 등급이 달라질 수 있음
- [x] **Step 4: 통과 확인** → PASS (실서버에서도 `/listings` 200, 잘못된 `bbox` 400, 없는 매물 404 확인)
- [ ] **Step 5: 커밋** — `git commit -m "feat(listing): search filters, detail, price-check"`

### Task 7: 지리 외부 API (도보 · 주변 · 주소) + 장애 규칙

**Files:**
- Create: `geo/WalkPort.java`, `geo/TmapWalkAdapter.java`, `geo/PlacePort.java`, `geo/KakaoPlaceAdapter.java`, `geo/AddressPort.java`, `geo/KakaoAddressAdapter.java`, `geo/WalkService.java`, `geo/NearbyService.java`, `geo/GeoController.java`
- Modify: `listing/ListingController.java` (`/listings/{id}/nearby`)
- Test: `geo/GeoApiTest.java`, `geo/WalkServiceTest.java`

**Interfaces:**
- Produces:
  - `interface WalkPort { WalkResult route(double fromLat, double fromLng, double toLat, double toLng); }`, `record WalkResult(int minutes, int distanceM, List<double[]> path)`
  - `WalkService.minutesOrNull(double lat, double lng, Long buildingId): Integer` — 실패·buildingId null이면 null, 결과는 `(위경도 소수4자리, buildingId)` 키로 메모리 캐시(Caffeine, 24시간)
  - `WalkService.route(double lat, double lng, long buildingId): WalkDto` — 실패 시 `ApiException(UPSTREAM_FAILED)`
  - `interface PlacePort { List<Place> near(double lat, double lng, int radius, NearbyCategory c); }`, `NearbyService.near(...)`: 실패하면 `[]`
  - `interface AddressPort { List<AddressDto> search(String q); }`
  - 카카오 카테고리 코드: 편의점 `CS2`, 지하철역 `SW8`. 세탁방·버스정류장은 키워드 검색(`코인세탁`, `버스정류장`)

- [x] **Step 1: 실패하는 테스트 작성** (포트는 `@MockBean` → 실제로는 `FakeWalkPort`·`FakePlacePort`·`FakeAddressPort` 를 `TestSupportConfig` 에 등록. 테스트마다 새 스프링 컨텍스트가 생기지 않게)
```java
@Test void walk_ok()                    // GET /walk?... → $.minutes == 가짜 값
@Test void walk_upstreamFails_502()     // WalkPort 예외 → 502, code UPSTREAM_FAILED
@Test void listing_walkMinNull_whenTmapDown() // WalkPort 예외 + buildingId 지정 GET /listings → 200, items[*].walkMin == null
@Test void nearby_emptyWhenKakaoDown()  // PlacePort 예외 → 200, []
@Test void nearby_radiusCappedAt500()   // radius=2000 → PlacePort가 500으로 호출됨
@Test void walkService_caches()         // 같은 좌표 2회 → WalkPort 1회 호출
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*GeoApiTest' --tests '*WalkServiceTest'` → FAIL
- [x] **Step 3: 구현** — `RestClient`, 타임아웃 3초. 키는 `external.tmap.key`, `external.kakao.rest-key`
  - **실제 응답으로 확인한 사실 (2026-11-07):**
    - TMAP: `POST /tmap/routes/pedestrian?version=1`, 헤더 `appKey`, `startName`·`endName` 필수. 응답 GeoJSON, 첫 지점의 `totalTime`(초)·`totalDistance`(m), 경로는 `LineString` 들을 이은 것이고 좌표가 `[경도, 위도]`
    - 카카오: 앱 설정에서 지도·로컬(OPEN_MAP_AND_LOCAL)을 켜야 함(꺼져 있으면 403). 편의점 `CS2`·지하철역 `SW8` 정상, **키워드 "버스정류장"은 0건**, "코인세탁"만으로는 "빨래방" 이름 가게를 놓침
    - 주소 검색: `행당동 16-53` → 법정동 `행당동`, 행정동 `사근동`. 한양대(`왕십리로 222`)의 법정동은 `사근동` → **반드시 법정동(`region_3depth_name`)**
  - **구현 반영:**
    - 도보 분은 **올림**(506초 → 9분), 경로는 `[위도, 경도]` 로 바꾸고 연속 중복 점 제거, `gateId` 는 항상 null
    - **캐시:** 도보 분은 메모리(Caffeine 24시간) + **DB `walk_cache` 30일**(`V5__walk_cache.sql`, 키 = 위경도 소수 4자리 + 건물 id). `/walk` 경로는 메모리 24시간만(DB에 경로 저장 안 함). 실패는 캐시하지 않음. 외부 API 약관상 결과 저장 조건은 확인하지 못함
    - **차단 장치:** TMAP 연속 3번 실패 → 1분 동안 호출하지 않고 바로 null (목록 20건마다 3초씩 기다리는 것 방지)
    - 캐시 저장은 **별도 트랜잭션**(`REQUIRES_NEW`)이고 실패해도 응답에 영향 없음 — 읽기 전용 트랜잭션(매물 목록) 안에서 저장하다 목록 전체가 500 이 나던 버그를 테스트가 잡아서 고침
    - **버스정류장은 카카오 대신 서울시 공식 데이터:** 서울 열린데이터광장 「서울시 버스정류소 위치정보」(2026-09-02) 중 3D 범위(위도 37.548~37.574, 경도 127.022~127.063) 315곳을 `src/main/resources/geo/bus-stops.json` 으로 저장, `BusStopIndex` 가 거리로 찾음 (정류장은 거의 안 바뀌어서 실시간 API 대신 파일)
    - 세탁방은 "코인세탁"·"빨래방" 두 키워드로 검색해 중복 제거
    - 주변 시설은 카테고리마다 따로 실패 처리 → 카카오가 죽어도 버스정류장은 보여 줌. 결과는 편의점 → 세탁방 → 버스정류장 → 지하철역 순, 카테고리마다 가까운 순 최대 15곳, 1시간 메모리 캐시(일부라도 실패하면 캐시 안 함)
    - 반경 기본 300m, 500 초과는 500으로, 1 미만은 400. 없는 건물로 `/walk` → 404
    - Task 6 의 도보 필터 동작("도보 시간을 모르면 제외")은 유지
    - Docker: `docker-compose.yml` 에 `MOLIT_KEY`·`TMAP_KEY`·`KAKAO_REST_KEY` 를 `.env` 에서 읽도록 추가(`.env.example` 양식). 없으면 도보 null·주소 502
    - 통합 검색 보충(Task 14)은 주소 검색이 아니라 **키워드 검색**이어야 건물명이 잡힘 (그대로 Task 14로)
- [x] **Step 4: 통과 확인** → PASS (실서버: 실제 TMAP 도보 시간·DB 캐시 저장, 실제 카카오 주소 검색 확인)
- [ ] **Step 5: 커밋** — `git commit -m "feat(geo): walk time, nearby places, address search with graceful fallback"`

### Task 8: 청년안심주택(soco 수집) · 공고 · 구독 · 기숙사 · 대안 비교

**정한 것 (2026-11-07, 사용자 결정):**
| 항목 | 결정 | 비고 |
|---|---|---|
| 단지·주택형·공고 데이터 | **서버가 soco 를 매일 수집** (스펙 7장 수정) | 원래 계획은 사람이 JSON 작성. 공고가 수시로 올라와서 바꿈 |
| 수집 대상 단지 | **대상 동(`DongAdjacency.dongs()`)에 있는 단지 자동** | 동은 카카오 주소 검색의 법정동 (매물·실거래와 같은 기준). 2026-11 기준 5곳: 청아진(홍익동)·라봄성동·한영스테이(마장동)·힐데스하임(용답동)·퀸즈W 청량리역(전농동, 인접 동이지만 사용자 결정으로 포함) |
| 주택형 | **일반공급 + 청년 자격만** | 특별공급(소득 조건)·신혼부부 타입 제외 |
| 공고 상태 | **일정 날짜로 계산** (저장값 아님) | 시간이 지나도 맞음. 계약 v1.5 |
| 다음 일정 | **오늘 포함** | 마감 당일 D-day, Task 13 당일 알림과 맞음 |
| 평면도 이미지 | **주소·지문(sha256)만 저장**, 파일 보관·앱 표시 안 함 | 이미지 → 타입·전용면적 연결표는 이미지를 보고 한 번 작성. 평면도 JSON·API는 Task 14 |
| 기숙사 | **학기마다 모집요강 PDF 를 읽어 `dorms.json` 직접 입력** | PDF 가 이미지라 자동 수집 안 함. 2026-2학기 값 확보(모집요강 4·16쪽) |
| 기숙사 id | **= 건물 id** (801 제1, 804 제2+한양테크노숙사, 805 개나리, 806 한누리, 810 제7) | 804 는 호실 유형 2개로 나눔 |
| 대안 비교 | **보고 있는 매물보다 싼 것만**, 낮은 순 최대 3개씩 | 스펙 I19 "절약액". 없으면 빈 배열 (프론트는 빈 배열이면 비교 칸 숨김) |
| 청년안심주택 필터 (스펙 C3) | `GET /housing` 에 `maxRent`·`maxDeposit`·`maxWalkMin`·`buildingId`·`bbox` + 응답 `minConvertedRent`·`walkMin` | Task 6 때 합의. 계약 v1.5 반영 |
| soco 이용 조건 | 이용약관 페이지 없음(개인정보처리방침·저작권 표기만), `robots.txt` 없음 | 공개 정보, 1초 간격, 하루 1회 수준으로만 요청 |

**soco 에서 받는 것 (2026-11-07 확인):**
| 대상 | 방법 | 내용 |
|---|---|---|
| 단지 목록 | `POST /youth/pgm/home/yohome/yoHomeListJson.json` (`pageNum`, `rowCount`) → JSON | 101단지, `homeCode`·`homeName`·`adres`·`adresGu` |
| 단지 상세 | `GET /youth/pgm/home/yohome/view.do?menuNo=400002&homeCode=` → HTML | 좌표(`xpos`·`ypos`), 대표전화, 홈페이지, **일반공급 표**(구분·자격·보증금·월임대료·관리비), 평면도 `<img>` |
| 모집공고 | `POST /youth/pgm/home/yohome/bbsListJson.json` (`bbsId=BMSR00015`, `pageIndex`) → JSON | 542건(10건/쪽), `boardId`·`nttSj`(제목)·`optn1`(게시일)·`content`(본문 HTML, `[공급일정]` 포함) |

**Files:**
- Create:
  - `housing/` — `EventType`, `AnnouncementStatus`, `AnnouncementStatusPolicy`, `HousingDtos`, `HousingService`, `HousingController`, `HousingIngestJob`
  - `housing/soco/` — `SocoClient`(interface) + `SocoHttpClient`, `SocoParser`(목록 JSON·상세 HTML·공고 JSON, jsoup), `ScheduleParser`(본문 일정 → `EventType`·날짜), `SocoHome`·`SocoHomeDetail`·`SocoUnit`·`SocoNotice` record, `SocoApiException`
  - `dorm/` — `DormService`(+`DormDto`·`RoomTypeDto`), `DormController`
  - `compare/AlternativeService`, `common/SchedulingConfig`(`@EnableScheduling`)
  - `db/migration/V6__housing_dorm.sql` (아래 "저장하는 데이터")
  - `src/main/resources/fixtures/dorms.json`, `fixtures/floorplan-labels.json`
  - 청년안심주택·기숙사는 **JPA 엔티티 없이 `JdbcTemplate`** 으로 읽고 쓴다. 수집이 soco 번호 기준 `insert … on conflict do update` 로 id 를 유지해야 해서 (계획의 엔티티 파일들은 만들지 않음)
- Modify: `catalog/FixtureSeeder.java`(`seedDorms()`만, 테이블이 비었을 때만. 청년안심주택은 수집으로 들어오므로 `housing.json`·`announcements.json` 픽스처 없음), `listing/ListingController.java`(`/listings/{id}/alternatives`), `listing/ListingQuery.java`(`Bbox.parse`·`contains` 를 매물·청년안심주택이 같이 씀), `application.yml`(`app.housing-ingest.*`, `external.soco.base-url`), `build.gradle.kts`(jsoup 1.18.3)
- Test: `housing/soco/SocoParserTest`, `housing/soco/ScheduleParserTest`, `housing/AnnouncementStatusPolicyTest`, `housing/HousingIngestJobTest`, `housing/HousingApiTest`(+`HousingFixtures`), `dorm/DormApiTest`, `compare/AlternativeApiTest`, `support/FakeSocoClient`
- Test resources: `soco/home-list.json`, `soco/view-cheongajin.html`, `soco/view-labom.html`, `soco/notices.json` (실제 응답을 줄여서 저장), `soco/floorplan-labels.json`, `test-fixtures/dorms.json`

**저장하는 데이터 (V6):**
| 테이블 | 칸 | 채우는 곳 |
|---|---|---|
| `housing` | `id`, `soco_home_code`(unique), `name`, `address`, `dong`(법정동), `lat`·`lng`, `contact`(대표전화), `homepage_url`, `floor_layout_image_url`(지금은 비어 있음), `updated_at` | 수집 |
| `housing_unit_types` | `id`, `housing_id`, `name`(예 `18타입(18.22)`, `19A`), `room_kind`(원룸·1.5룸), `exclusive_area_m2`(**전용면적만**), `deposit`, `rent`, `mgmt_fee`, `floorplan_id`(Task 14, 수집이 덮어쓰지 않음). unique `(housing_id, name)` | 수집 (일반공급·청년만) |
| `announcements` | `id`, `soco_board_id`(unique), `housing_id`, `title`, `additional`(제목에 추가모집), `posted_on` | 수집 (최근 12개월, 지나면 삭제) |
| `announcement_events` | `id`, `announcement_id`, `type`(`NOTICE`~`MOVE_IN`), `event_date`. unique `(announcement_id, type)` → 다시 수집해도 id 유지 (Task 13 알림이 참조) | 수집 |
| `housing_subscriptions` | `user_id`, `housing_id`, `created_at`. PK `(user_id, housing_id)` | API |
| `housing_floorplan_images` | `housing_id`, `position`, `url`(unique, soco 경로), `sha256`, `unit_type_name`(연결표로 채움) | 수집 (이미지 파일은 저장 안 함) |
| `dorms` | `id`(= 건물 번호), `name`, `lat`·`lng`(buildings 에서 복사) | `dorms.json` 시드 |
| `dorm_room_types` | `id`, `dorm_id`, `name`(성별 포함), `capacity`, `semester_fee`, `semester_months`, `meal_included`, `floorplan_id` | `dorms.json` 시드 |

- **저장하지 않고 응답할 때 계산:** 공고 `status`·단지 `recruiting`·`nextEvent`(일정 날짜와 오늘), 주택형 `convertedRent`·단지 `minConvertedRent`(전환율 설정값), 기숙사 `monthlyCost`, `walkMin`(도보 캐시), 구독 여부
- 외래키 없음: `floorplan_id`(평면도 테이블이 Task 14), `dorms.id`→`buildings.id`(시드에서 존재 확인)

**Interfaces:**
- Consumes: Task 4 `PriceCalculator.convertedRent`, Task 5 `DongAdjacency.dongs()`, Task 7 `WalkService.minutesOrNull`, `AddressPort`(법정동), `ProfileService.firstBuildingId`
- Produces:
  - `HousingService.subscriberIds(long housingId): List<Long>`, `HousingService.eventsOn(LocalDate date): List<EventOn>` — `EventOn(eventId, announcementId, housingId, housingName, type, date)` (Task 13)
  - `HousingService.unitOptions(): List<UnitOption>` (대안 비교용)
  - `AnnouncementStatusPolicy.statusOf(Map<EventType, LocalDate> events, boolean additional, LocalDate today): AnnouncementStatus`
  - `DormService.RoomTypeDto.monthlyCost` = `Math.round((double) semesterFee / semesterMonths)`
  - `AlternativeService.forListing(long listingId, Long buildingId, Long userIdOrNull): AlternativesDto` — 매물 환산 월세보다 **낮은** 주택형·호실만, 낮은 순 최대 3개씩. `monthlyDiff = listing − alt`(항상 양수), `twoYearDiff = monthlyDiff × 24`, `id` = 단지·기숙사 id. 기준 건물이 없으면 로그인 사용자의 첫 번째 건물
  - `HousingIngestJob.run(LocalDate today): Report(homes, announcements, unlabeledImages, failures)` — `@Scheduled(cron = "0 0 6 * * *", zone = "Asia/Seoul")` + 켜져 있고 단지가 비어 있으면 기동 시 1회. 설정 `app.housing-ingest.enabled`(환경 변수 `HOUSING_INGEST_ENABLED`, 기본 false), `districts: 성동구,동대문구`, `notice-months: 12`, `request-interval-ms: 1000`, `labels-location`
  - 테스트용 오늘 날짜는 `Clock` 빈 주입

**수집 규칙:**
- 단지: 목록 전체 → 상세 HTML → 주소로 법정동 확인 → 대상 동이면 저장. `homeCode` 기준 덮어쓰기(단지 id 유지 → 구독 유지). 목록에서 사라진 단지는 지우지 않음
- 주택형: 상세의 **일반공급** 표에서 신청자격 `청년` 행만. 이름 = 구분 칸(예 `18타입(18.22)`, `19A`). 전용면적 = 괄호 안 값, 없으면 연결표 값, 둘 다 없으면 이름의 숫자. `(housing_id, name)` 기준 덮어쓰기 → **`floorplan_id` 는 덮어쓰지 않음**(Task 14 연결 보존)
- 공고: 최신 쪽부터 읽고, 한 쪽이 전부 이미 저장된 `boardId` 이거나 게시일이 12개월(`app.housing-ingest.notice-months: 12`)보다 오래되면 멈춤. 12개월보다 오래된 공고는 DB 에서도 지움. 제목을 정규화(공백·괄호·`청년주택` 제거)해 단지 이름이 들어 있으면 그 단지 공고. 제목에 `추가모집` → 추가모집
- 일정(`[공급일정]` 본문): `모집공고`→`NOTICE`, `청약신청 A ~ B`→`APPLY_START`=A·`APPLY_END`=B, `서류…제출 … ~ B`→`DOCS_DUE`=B, `…발표`→`RESULT`, `계약체결`→`CONTRACT`(시작일), `입주지정기간`→`MOVE_IN`(시작일). `‘26. 07. 17.` 두 자리 연도, 범위 끝은 시작의 연도를 이어 씀. `개별 안내`·`추후` → 건너뜀
- 평면도 이미지: 상세의 평면도 `<img>` 주소와 sha256 저장. `floorplan-labels.json` 에 없는 지문이면 경고 로그(새 평면도·바뀐 평면도 → 연결표 갱신 필요)
- 실패: 한 단지·한 공고 파싱 실패는 건너뛰고 로그, soco 접속 실패는 이번 실행 중단. 기존 DB 데이터는 그대로

**공고 상태 (오늘 기준):** 접수 시작 전 `UPCOMING` → 접수 기간(마감 당일 포함) `OPEN`/`ADDITIONAL` → 마감 후 발표 전 `CLOSED` → 발표일부터 `ANNOUNCED`. 접수 일정이 없으면 `CLOSED`

- [ ] **Step 1: 실패하는 테스트 작성**
```java
// SocoParserTest (저장한 실제 응답)
@Test void homeList_parsesCodesAndAddresses()
@Test void view_generalSupplyYouthOnly()   // 라봄: 19A·19B·20·25A·25B 5개, 39A·39B(신혼부부) 제외, 특별공급 제외
@Test void view_areaFromParentheses()      // 청아진 18타입(18.22) → 18.22
@Test void view_coordinatesPhoneImages()   // xpos·ypos, 02-6273-0266, 평면도 img 2개
// ScheduleParserTest (실제 본문 문구)
@Test void cheongajin_fullSchedule()       // 공고 26-07-07, 접수 07-17~07-20, 발표 07-21, 서류 ~07-29, 계약 08-06, 입주 08-17
@Test void labom_individualNoticeSkipped() // 서류·계약 "개별 안내" → 없음
@Test void hanyoung_resultAndContract()
// AnnouncementStatusPolicyTest
@Test void upcoming_open_closed_announced() // 접수 전·중·마감 당일·마감 후·발표일
@Test void additionalWithinApply()          // 추가모집 + 접수 중 → ADDITIONAL
// HousingIngestJobTest (FakeSocoClient·FakeAddressPort)
@Test void onlyTargetDongs()               // 용답동 O, 중랑구 X
@Test void runTwice_noDuplicates()
@Test void rerun_keepsSubscriptionsAndFloorplanId()
@Test void socoDown_keepsExistingData()
@Test void unlabeledFloorplan_logged()
// HousingApiTest
@Test void housing_recruitingFlag()
@Test void housing_nextEvent_includesToday() // clock=2026-11-07, 일정 11-05·11-07·11-20 → 11-07
@Test void housing_filters_and_minConvertedRent() // maxRent, maxWalkMin+buildingId, 관리비 포함 환산 월세
@Test void housing_subscribedFlag()        // 로그인 구독 → true, 비로그인 → false
@Test void announcements_filterByStatusAndHousing()
@Test void subscribe_idempotent()          // POST 두 번 → 204, 1건 / DELETE 없어도 204
@Test void subscribe_guest401()
@Test void housing_unknown404()
// DormApiTest
@Test void dorm_monthlyCost()              // 1_137_000 / 4 → 284250
@Test void dorm_detailWalkMin()
@Test void dorm_unknown404()
// AlternativeServiceTest
@Test void alternatives_onlyCheaper_sortedAndDiff() // 싼 것만, 오름차순, ≤3, twoYearDiff == monthlyDiff*24
@Test void alternatives_noneCheaper_empty()
@Test void alternatives_unknownListing404()
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*Soco*' --tests '*Schedule*' --tests '*AnnouncementStatus*' --tests '*HousingIngest*' --tests '*HousingApiTest' --tests '*DormApiTest' --tests '*AlternativeServiceTest'` → FAIL
- [ ] **Step 3: 구현** — 주택형 `convertedRent`는 `mgmtFee` 포함·전환율 4.6%, 기숙사는 `monthlyCost`를 환산 월세로 사용
- [ ] **Step 4: 통과 확인** → PASS. 실서버에서 수집 1회 실행해 4단지·공고·일정 확인
- [ ] **Step 5: 커밋** — `git commit -m "feat(housing,dorm): soco ingest, announcements, subscriptions, dorms, alternatives"`
- **실수집에서 발견해 고친 것:** 카카오 주소 검색이 라봄성동 지번(마장동 339-2)을 못 찾아 조용히 빠졌음 → 카카오 결과가 없거나 장애면 **주소 글자에서 동 이름**을 찾고(`dongFromText`), 그래도 없으면 실패로 기록
- **남은 일:**
  - ~~`floorplan-labels.json` 작성~~ → 완료(27장). 새 평면도가 올라오면 수집 로그의 "연결표에 없는 이미지" 경고를 보고 추가
  - 참고: 퀸즈W 35A·35B 는 전용 20.00㎡ + 확장 15.22㎡ (이름 숫자가 전용면적이 아님). 우리는 전용면적만 저장
  - 데모 날 접수 중인 공고가 없을 수 있음 → Task 16 에서 결정
  - 807 게스트하우스 `DORM` 분류, 학과 건물·입구는 campus-data 원본 수정(Task 3 남은 일)

### Task 9: 찜

**Files:**
- Create: `favorite/Favorite.java`, `favorite/FavoriteService.java`, `favorite/FavoriteController.java`, `db/migration/V7__favorites.sql` (unique `(user_id, type, target_id)`)
- Modify: `listing/ListingService.java` (`favorited` 채우기)
- Test: `favorite/FavoriteApiTest.java`

**Interfaces:**
- Consumes: Task 6 `ListingService.summaryOf`, Task 8 단지·기숙사 조회
- Produces: `FavoriteRepository.existsByUserIdAndTypeAndTargetId(long userId, FavoriteType type, long targetId): boolean`, `FavoriteRepository.findTargetIds(long userId, FavoriteType type): Set<Long>` (목록 N+1 방지). 서비스가 아니라 저장소에 둔 이유: `FavoriteService` 가 매물·양도 서비스를 쓰므로 반대로 쓰면 순환 의존

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void add_list_remove()      // POST {LISTING,12} → 201 / GET → 1개, convertedRent·grade 채워짐 / DELETE → 204 / GET → 0개
@Test void duplicate_409()        // 같은 POST 두 번 → 두 번째 409 ALREADY_EXISTS
@Test void delete_missing_204()
@Test void unknownTarget_404()    // POST {LISTING,999999} → 404
@Test void listingShowsFavorited()// 찜 후 GET /listings (토큰) → 해당 항목 favorited true
@Test void dormFavorite_gradeNull() // POST {DORM,107} 후 GET → grade null, convertedRent == 가장 싼 호실 monthlyCost (기숙사 id = 건물 번호, 테스트 기숙사 107)
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*FavoriteApiTest'` → FAIL
- [x] **Step 3: 구현** — 타입별 대상 조회를 `switch`로 분기
- [x] **Step 4: 통과 확인** → PASS (12개)
- [ ] **Step 5: 커밋** — `git commit -m "feat(favorite): add, list, remove favorites across types"`
- **구현하며 정한 것:**
  - 추가 테스트: 비로그인 401, 잘못된 요청 400, `type` 필터·최신순, 청년안심주택 찜(가장 싼 주택형), 대상이 사라진 찜은 목록에서 빠짐, 도보 시간은 프로필 첫 번째 건물 기준
  - `favorites` 테이블은 `(user_id, type, target_id)` unique, 사용자 삭제 시 함께 삭제. 대상 종류가 여러 개라 대상 외래키는 없음 → 대상이 없으면 목록에서 빼고 보여 줌
  - `TRANSFER` 는 양도 글 테이블이 없어서 지금은 404. **Task 10 에서 `FavoriteService.target()` 의 `TRANSFER` 분기를 채울 것**
  - 순환 의존 방지: `ListingService` 는 `FavoriteRepository` 를 직접 읽고, `FavoriteService` 가 `ListingService` 를 쓴다
  - 목록 조회는 트랜잭션으로 묶지 않음 (대상 하나가 404 면 묶인 트랜잭션 전체가 실패로 표시되어 500 이 났음)
  - 청년안심주택·기숙사 목록·상세에도 `favorited` 추가 (2026-11-08, 계약 v1.6). 스펙 C6 "모든 대상 찜"인데 계약 응답에 찜 여부 칸이 매물에만 있어서 프론트 하트가 `false` 로 고정돼 있었음. `HousingService`·`DormService` 가 `FavoriteRepository.findTargetIds` 로 채움 (순환 의존 없음)

### Task 10: 양도 게시판 · 업로드

**Files:**
- Create: `transfer/Transfer.java`, `transfer/TransferService.java`, `transfer/TransferController.java`, `transfer/UploadController.java`, `transfer/StoragePort.java`, `transfer/LocalDiskStorage.java`, `db/migration/V8__transfers.sql`
- Modify: `catalog/FixtureSeeder.java` (`seedTransfers()`)
- Test: `transfer/TransferApiTest.java`

**Interfaces:**
- Consumes: Task 6 `PriceCheckService.check`, Task 9 `FavoriteRepository.existsByUserIdAndTypeAndTargetId`·`findTargetIds`
- Produces: `interface StoragePort { String save(byte[] bytes, String ext); boolean owns(String url); }` (로컬은 디스크 + 정적 경로 `/files/**`, 배포 시 S3 호환 구현으로 교체), `TransferService.summaryOf(long id, Long userIdOrNull)` (찜 목록용)

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void create_computesPriceCheck()  // POST → 201, $.priceCheck.contractMonths == remainingMonths, $.mine true
@Test void create_validation()          // rent 음수, remainingMonths 0 → 400 VALIDATION_FAILED, details.rent 존재
@Test void update_byOther_403()
@Test void markDone_hiddenFromDefaultList() // PATCH status DONE → GET /transfers 에 없음, ?status=DONE 에 있음
@Test void pendingWhenFewDeals()        // 실거래 없는 동 → 201, priceCheck.grade PENDING
@Test void upload_rejectsNonImage()     // text/plain → 400
@Test void upload_rejectsOver5MB()      // 6MB → 400
```
- [x] **Step 2: 실패 확인** — `./gradlew test --tests '*TransferApiTest'` → FAIL (15개 중 12개)
- [x] **Step 3: 구현** — 판정은 저장 시 계산해 캐시(Task 6과 같은 방식), 수정 시 재계산
- [x] **Step 4: 통과 확인** → PASS (15개)
- [ ] **Step 5: 커밋** — `git commit -m "feat(transfer): transfer board with auto price-check and uploads"`
- **구현하며 정한 것 (2026-11-08, 계약 v1.6):**
  - **제목 필수** (1~50자, 사용자 결정): 원래 계약은 응답에만 `title`(ListingSummary 필드)이 있고 글쓰기 요청에는 없어서 앞뒤가 안 맞았음. 프론트 글쓰기 폼에 제목 칸 추가 필요
  - 검증: 금액 0 이상, 면적 0 초과, `remainingMonths` 1~60, 설명 2000자, 사진 10장. `photoUrls` 는 **우리 `/uploads` 가 돌려준 주소만** (`StoragePort.owns`)
  - 업로드: `StoragePort.save(byte[], ext)` 가 **전체 주소**를 돌려준다. 로컬은 `LocalDiskStorage`(디스크 `app.upload.dir` + `/files/**` 정적 제공), 앞부분은 `UPLOAD_PUBLIC_BASE_URL`(비우면 요청 주소). 배포에서 디스크가 지워지면 외부 저장소 구현만 추가 (Task 16). 파일 **첫 바이트**로 jpg·png 확인, 5MB 초과는 컨트롤러와 `spring.servlet.multipart` 둘 다 막음
  - 상태 `OPEN`↔`DONE` 양방향, 삭제 없음. 수정·상태 변경은 작성자만(403)
  - 목록 최신순, `thumbnailUrl` = 첫 사진, `favorited`·`walkMin`(프로필 첫 건물)·작성자 닉네임
  - 판정 캐시는 서버 시작 시 매물과 함께 다시 계산 (`ListingGradeJob`)
  - 찜: `FavoriteService` 의 `TRANSFER` 분기 연결 (이름 = 글 제목)
  - 시드 `fixtures/transfers.json` 3건 (데모 작성자, 적정·비쌈·조금 비쌈)
  - 추가 테스트: 비로그인 401, 제목 누락·51자, 목록 필드·bbox·찜·mine, 없는 글 404, 양도 글 찜, 업로드 후 실제로 받아 보기, 외부 사진 주소 거부, 최신순

### Task 11: 후기

**Files:**
- Create: `review/Review.java`, `review/ReviewController.java`, `db/migration/V9__reviews.sql`
- Test: `review/ReviewApiTest.java`

**Interfaces:**
- Produces: `GET /reviews` 응답의 `average`는 소수 첫째 자리 반올림, 후기 없으면 `average: null, count: 0, items: []`

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void create_and_list()     // POST → 201 / GET ?targetType=LISTING&targetId=12 → count 1, items[0].authorNickname 존재
@Test void ratingOutOfRange_400()// rating 6, scores.noise 0 → 400
@Test void textTooLong_400()     // 501자 → 400
@Test void empty_averageNull()   // 후기 없는 대상 → average null, count 0
@Test void pinOptional()         // pin 없이 POST → 201, pin null
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*ReviewApiTest'` → FAIL
- [ ] **Step 3: 구현** — `scores`는 개별 컬럼 5개, `pin`은 `double[]` → jsonb
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(review): reviews with category scores and optional pin"`

### Task 12: 내 집 기록 · 월간 리포트 · 만료 알림 설정

**Files:**
- Create: `home/Home.java`, `home/Payment.java`, `home/Utility.java`, `home/ExpiryAlert.java`, `home/HomeController.java`, `home/ReportService.java`, `db/migration/V10__home.sql`
- Test: `home/HomeApiTest.java`, `home/ReportServiceTest.java`

**Interfaces:**
- Consumes: Task 6 `PriceCheckService.check` (내 집을 `PriceInput`으로 판정)
- Produces: `ReportService.report(long userId, YearMonth month): ReportDto`, `ExpiryAlert` 조회 `alertsDueOn(LocalDate date): List<(userId, daysBefore)>` (Task 13)

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void home_404BeforeRegister()
@Test void payment_sameMonthOverwrites()      // 2026-10 두 번 POST → GET 길이 1, 두 번째 금액
@Test void utilities_nullItemsAllowed()       // {month, electricity: 42000, gas: null…} → 201
@Test void alerts_crud()                      // POST {daysBefore:60} → 201 / PATCH enabled false / DELETE 204
@Test void alerts_daysBeforeRange()           // 0, 366 → 400
// ReportServiceTest (계약 5-9 예시 값 그대로)
@Test void report_totalsAndTopIncrease()      // 10월 total 742000, prevTotal 701000, diff 41000, topIncrease.item "gas", diff 21000
@Test void report_rentFallsBackToContract()   // 그 달 납부 기록 없음 → breakdown.rent == 계약 월세
@Test void report_noPrevMonth_nulls()         // prevTotal, diff, topIncrease == null
@Test void report_cumulativeExcess()          // contractStart 2026-03, month 2026-10, monthly 164000 → cumulative 1312000 (8개월)
@Test void report_pendingExcessNull()
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*HomeApiTest' --tests '*ReportServiceTest'` → FAIL
- [ ] **Step 3: 구현** — 개월 수는 `contractStart`의 월부터 `month`까지 포함 계산(3월~10월 = 8). 공과금 `null`은 합계에서 0으로
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(home): home records, monthly report, expiry alert settings"`

### Task 13: 알림 생성 스케줄러 · 알림함

**Files:**
- Create: `notification/Notification.java`, `notification/NotificationController.java`, `notification/NotificationJob.java`, `db/migration/V11__notifications.sql` (unique `(user_id, type, source_id, ref_date, days_before)` 로 중복 생성 방지)
  - `source_id` = 공고 일정(`announcement_events.id`) 또는 만료 알림 설정(`expiry_alerts.id`), `ref_date` = 그 일정 날짜 또는 `contractEnd`, `days_before` = 7·1·0 또는 설정값
  - 기존 키 `(user_id, type, target_id, ref_date)`는 같은 일정의 D-7·D-1·당일이 같은 키가 되어 하나만 저장되므로 쓰지 않음
- Test: `notification/NotificationJobTest.java`, `notification/NotificationApiTest.java`

**Interfaces:**
- Consumes: Task 8 `HousingService.subscriberIds`, `eventsOn`, Task 12 `alertsDueOn`
- Produces: `NotificationJob.run(LocalDate today)` — `@Scheduled(cron = "0 0 9 * * *", zone = "Asia/Seoul")`가 `LocalDate.now(clock)`로 호출

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void housingDday_7_1_0()    // 구독 단지 APPLY_END 2026-11-14 → run(11-07), run(11-13), run(11-14) 각각 HOUSING_DDAY 1건, run(11-10)은 0건
@Test void contractExpiry()       // contractEnd 2027-01-06, daysBefore 60 → run(2026-11-07) 1건 CONTRACT_EXPIRY
@Test void disabledAlertSkipped() // enabled false → 0건
@Test void runTwice_noDuplicate() // 같은 날 두 번 → 1건
@Test void twoEventsSameDay_bothCreated() // 같은 단지 DOCS_DUE 11-08(D-1) + RESULT 11-14(D-7) → run(11-07) 2건
@Test void list_and_read()        // GET → 최신순, PATCH read → read true
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*NotificationJobTest' --tests '*NotificationApiTest'` → FAIL
- [ ] **Step 3: 구현** — 제목 예: `"[D-7] 왕십리역 청아진 접수 마감"`, `"계약 만료 60일 전이에요"`
  - **구현 전 확인할 것 (Task 6 진행 중 정리):** 매물 등급 캐시는 서버 시작 시에만 다시 계산됨 → 서버를 띄운 채 달이 바뀌면 목록 등급이 판정 API(요청마다 계산)와 어긋날 수 있음. 같은 09:00 스케줄러에서 `ListingService.recomputeAll()` 도 매일 실행할지 정할 것
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(notification): daily dday and expiry notifications, inbox"`

### Task 14: 통합 검색 · 평면도

**Files:**
- Create: `search/SearchService.java`, `search/SearchController.java`, `floorplan/FloorPlan.java`, `floorplan/FloorPlanController.java`, `db/migration/V12__floorplans.sql`
- Modify: `catalog/FixtureSeeder.java` (`seedFloorPlans()`)
- Test: `search/SearchApiTest.java`, `floorplan/FloorPlanApiTest.java`

**Interfaces:**
- Consumes: Task 7 `AddressPort`
- Produces: 검색 순서 = 매물·청년안심주택·기숙사·양도(OPEN)·캠퍼스 건물 이름/주소 `ILIKE '%q%'` → 부족분을 `ADDRESS`로 채움, 총 `limit`개

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void search_minLength()        // q=행 → 400
@Test void search_dbFirstThenAddress() // q=청아진 → $[0].type HOUSING / AddressPort 결과는 뒤에
@Test void search_addressFailure_stillReturnsDb() // AddressPort 예외 → 200, DB 결과만
@Test void search_limit()            // limit=3 → 길이 ≤ 3
@Test void floorplan_roundTrip()     // 시드 청아진 18 → walls 길이 > 0, entrance 존재, 계약 FloorPlan 필드 그대로
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*SearchApiTest' --tests '*FloorPlanApiTest'` → FAIL
- [ ] **Step 3: 구현** — FloorPlan은 `jsonb` 컬럼에 원문 저장, 그대로 응답
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(search,floorplan): unified search and floor plan data"`

### Task 15: 멀티플레이 WebSocket · 초대

**Files:**
- Create: `world/WebSocketConfig.java`, `world/WorldSocketHandler.java`, `world/WorldState.java`, `world/Player.java`, `world/InviteService.java`, `world/InviteController.java`, `world/WorldProperties.java`
- Test: `world/WorldStateTest.java`, `world/InviteApiTest.java`, `world/WorldSocketIT.java`

**Interfaces:**
- Produces:
  - `@ConfigurationProperties("world") record WorldProperties(int maxPlayers /*50*/, int tickHz /*10*/, int idleTimeoutSec /*30*/, int chatMaxLen /*40*/)`
  - `WorldState.join(String nickname, String inviteToken): JoinResult` (`selfId`, `spawn`, 현재 `players`), `move(String id, double[] p, double r, String a)`, `leave(String id)`, `drainDirty(): List<PlayerState>` (마지막 방송 이후 움직인 사람만)
  - `InviteService.create(String playerId): InviteDto` (토큰 `inv_` + 8자리, 24시간), `InviteService.resolveSpawn(String token): Optional<double[]>` — 토큰 유효 + 초대자 접속 중이면 초대자 `p` + `[1.5, 0, 0]`
  - 플레이어 ID 형식 `p_` + 4자리 16진수
  - 메시지 형식은 계약 6장 그대로

- [ ] **Step 1: 실패하는 테스트 작성**
```java
// WorldStateTest
@Test void join_defaultSpawnAtOrigin()        // invite null → spawn.p == [0,0,0]
@Test void join_withInvite_spawnsNextToInviter() // A가 [10,0,-5]에 있음, A의 토큰으로 B join → B spawn [11.5,0,-5]
@Test void join_expiredInvite_defaultSpawn()  // 25시간 지난 토큰 → [0,0,0], 예외 없음
@Test void join_inviterOffline_defaultSpawn() // A leave 후 B join → [0,0,0]
@Test void drainDirty_onlyMoved()             // A,B join, A만 move → drainDirty 길이 1, 두 번째 호출 길이 0
@Test void maxPlayers_rejects()               // maxPlayers 2, 세 번째 join → WORLD_FULL
// InviteApiTest
@Test void createInvite_guestAllowed()        // 토큰 없이 POST /invites {playerId} → 200, $.url 에 "?invite=" 포함
@Test void createInvite_unknownPlayer_404()
// WorldSocketIT (StandardWebSocketClient로 실제 연결 2개)
@Test void twoClients_seeEachOther()          // A 접속 → welcome / B 접속 → A가 join 수신 / A move → B가 1초 안에 state 수신 / A 끊김 → B가 leave 수신
@Test void chat_truncatedTo40()
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*WorldStateTest' --tests '*InviteApiTest' --tests '*WorldSocketIT'` → FAIL
- [ ] **Step 3: 구현** — `TextWebSocketHandler` + Jackson. 방송은 `ScheduledExecutorService` 100ms 주기로 `drainDirty()` 결과 전송. `ping` 수신 시각을 기록하고 30초 넘으면 `leave`. 세션 전송은 `ConcurrentWebSocketSessionDecorator`로 감싸 동시 전송 충돌 방지. WS 경로 `/ws/world`, CORS 오리진은 REST와 같은 설정
  - **구현 전 확인할 것:** 현재 `SecurityConfig`의 CORS는 `/api/**`만 등록되어 있으므로 `/ws/**`를 추가. websocket 의존성 추가(Task 1에서 미룸)
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(world): shared world websocket, invites with spawn next to inviter"`
- **완료 (2026-11-08, 프론트 담당이 구현 `e72869b`):** `world/` 패키지 (`WorldService`, `WorldSocketHandler`, `SessionOutbox`, `InviteService`·`InviteController`, `WorldProperties`, `WorldConfig`), 테스트 4종(단위·전송 큐·소켓 통합·30명 부하)
  - 계획과 다른 값: 최대 인원 **30**(계획 50), 무응답 정리 **60초**(계획 30초), 틱 100ms(같음), 초대 24시간(같음). `application.yml` 의 `world.*`
  - 추가된 것: `look`(잠바·머리·피부) 공유, 접속자별 전송 큐(가상 스레드)로 느린 접속자가 틱을 막지 않게, 좌표 양자화·속도 제한
  - 백엔드 담당 확인: 머지 후 전체 테스트 245개 통과 (2026-11-08)

### Task 16: 배포 · 프론트 연동 확인

**Files:**
- Create: `Dockerfile`, `application-prod.yml`, `README.md` (실행 방법, 환경 변수 목록)
- Test: `src/test/java/com/chatatda/api/ContractSmokeTest.java`

**Interfaces:**
- Produces: 환경 변수 `DB_URL`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET`, `MAIL_*`, `MOLIT_KEY`, `TMAP_KEY`, `KAKAO_REST_KEY`, `HOUSING_INGEST_ENABLED`, `UPLOAD_DIR`, `UPLOAD_PUBLIC_BASE_URL`, `CORS_ALLOWED_ORIGINS`, `FRONT_BASE_URL`

- [ ] **Step 1: 실패하는 테스트 작성** — 계약 5장의 모든 GET 엔드포인트를 픽스처 시드 상태에서 한 번씩 호출해 2xx(또는 `/me/*`는 토큰으로 2xx)인지 확인하는 표 기반 테스트 `allContractGetsRespond()`
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*ContractSmokeTest'` → 누락 엔드포인트가 있으면 FAIL
- [ ] **Step 3: 구현** — 누락분 보완, Dockerfile(멀티 스테이지, `eclipse-temurin:21-jre`), Railway·Render 중 하나에 PostgreSQL과 함께 배포
  - **배포 전 체크리스트 (Task 1~4 진행 중 정리):**
    - `MAIL_MODE=smtp`와 `spring.mail.*` 설정 (기본값 `log`라 빠뜨리면 인증 코드가 메일 대신 로그로만 감), **SMTP 실제 발송 처음 확인**
    - 실제 메일 발송 전에 **IP 단위 발송 제한** 추가 (지금은 메일 주소별 60초만 있어서 여러 주소로 대량 발송 가능)
    - 배포용 `JWT_SECRET`은 로컬과 다른 값
    - 무료 플랜의 잠들기(09:00 알림·WebSocket 중단), 업로드 파일이 재배포 때 사라지는지 확인 → 사라지면 디스크 유지 볼륨을 붙이거나 `StoragePort` 외부 저장소(S3·R2 등) 구현 추가
    - `UPLOAD_PUBLIC_BASE_URL` = 배포 서버 공개 주소 (프록시 뒤라 요청 주소로 만들면 http/도메인이 틀릴 수 있음)
    - `CORS_ALLOWED_ORIGINS`에 배포 프론트 주소 추가, `SEED_ENABLED` 결정
    - **청년안심주택 수집 켜기**: `HOUSING_INGEST_ENABLED=true` (단지가 비어 있으면 기동 시 1회 + 매일 06:00, 1~2분). 서버가 잠드는 무료 플랜이면 06:00 수집이 빠질 수 있음. 데모 날 접수 중인 공고가 없을 때 대책도 여기서 결정
    - **배포 DB에서 실거래 첫 수집** (`INGEST_ENABLED=true`로 1회 기동, 1~2분), `MOLIT_KEY` 환경 변수. 달이 바뀌면 최근 12개월이 유지되도록 **매달 재수집**할지 정할 것 (지금은 수동 실행만)
    - 배포 DB 후보: 서버와 DB를 한 곳에(Railway 등) 또는 DB만 따로(Supabase·Neon 등, 스프링 서버는 별도). 무료 플랜의 잠들기·일시 정지 조건을 확인하고 결정. 프론트는 DB에 직접 붙지 않으므로 API 주소만 바뀜
- [ ] **Step 4: 통과 확인** — 전체 `./gradlew test` → PASS, 배포 주소의 `/api/v1/health` 200, `/swagger-ui.html` 열림, 프론트 담당에게 배포 주소 공유
- [ ] **Step 5: 커밋** — `git commit -m "chore: dockerize and deploy, contract smoke test"`

---

## 이 계획에서 뺀 것 (스펙의 P2·△, 시간 남으면)
- F3 언덕·계단 보정: TMAP 응답에 고도 정보가 없으면 하지 않음
- H8 거주자 평면도 등록: `POST /floorplans` 미구현 (조회만)
- M2 밤길 안전 레이어 데이터, N2 수배 전단: 서버 작업 없음

## 진행 순서 (프론트와 맞추는 지점)
| 순서 | 백엔드 Task | 이때 프론트가 실서버로 바꿀 수 있는 것 |
|---|---|---|
| 1 | 1~3 | 학과·건물, 로그인, 프로필 |
| 2 | 4~7 | 매물 목록·상세·판정·도보·주변 (데모 핵심) |
| 3 | 15 | 멀티플레이 (데모 핵심, 일찍 붙여서 오래 시험) |
| 4 | 8~10 | 청년안심주택·기숙사·비교·찜·양도 |
| 5 | 11~14 | 후기·내 집·알림·검색·평면도 |
| 6 | 16 | 배포 |
