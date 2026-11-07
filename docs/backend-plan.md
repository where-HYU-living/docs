# 백엔드 서버 Implementation Plan (담당: 장시현)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 공통 계약 문서 v1.0의 REST API와 멀티플레이 WebSocket을 그대로 제공하는 Spring Boot 서버를 만든다.

**Architecture:** 기능별 패키지(인증, 판정, 매물, 청년안심주택, 기숙사, 찜, 양도, 후기, 내 집, 알림, 월드)로 나눈 단일 Spring Boot 애플리케이션. 초과액 판정은 스프링에 의존하지 않는 순수 도메인 클래스로 두고 서비스가 감싼다. 외부 API(국토부·TMAP·카카오)는 인터페이스 뒤에 두어 테스트에서 가짜로 바꾼다.

**Tech Stack:** Java 21, Spring Boot 3 (Web, Validation, Data JPA, Security, Mail, WebSocket, Scheduling), PostgreSQL 16, Flyway, springdoc-openapi, jjwt, JUnit 5 + AssertJ + MockMvc, Testcontainers(PostgreSQL), Gradle(Kotlin DSL)

**Spec:** `docs/spec-v0.5.md` · **계약:** `docs/api-contract.md` (요청·응답 형식은 전부 계약 문서가 정답. 이 계획은 형식을 반복하지 않는다)

## Global Constraints
- Java 21, Spring Boot 3.x, 패키지 루트 `com.chatatda.api`
- 모든 경로 접두사 `/api/v1`, JSON camelCase, 금액 원 단위 `long`, 비율 소수 셋째 자리 반올림, 값 없음은 `null`
- 게스트 허용: `/me/*`와 쓰기 요청(`/auth/*`, `/invites` 제외)만 인증 필요
- 학교 메일 도메인 `@hanyang.ac.kr`만 허용, 코드 6자리·10분 유효·재발송 60초·5회 오류 시 폐기, JWT 7일
- 등급 경계: `PENDING`(표본 부족) / `≤0.05 FAIR` / `≤0.15 SLIGHTLY_HIGH` / `≤0.30 HIGH` / `>0.30 CULPRIT`, 기준값은 설정 `pricing.grade.*`
- 적정가 표본: 같은 동·면적 ±30%·최근 12개월, 10건 미만이면 인접 동 포함, 그래도 10건 미만이면 `PENDING`
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

---

## 파일 구조
```
backend/
├── build.gradle.kts, settings.gradle.kts
├── src/main/resources/
│   ├── application.yml                 # pricing.*, world.*, cors.*, external.* 설정
│   ├── db/migration/V1__init.sql …     # Flyway
│   └── fixtures/ → contract/fixtures   # 공유 픽스처 (계약 7장)
└── src/main/java/com/chatatda/api/
    ├── common/      ApiError, ErrorCode, ApiException, GlobalExceptionHandler, PageResponse, SecurityConfig, JwtProvider, JwtFilter, CurrentUser
    ├── auth/        AuthController, EmailCodeService, MailPort(+SmtpMailAdapter), EmailCode
    ├── user/        User, UserRepository, ProfileController, ProfileService
    ├── catalog/     Department, Building, CatalogController, FixtureSeeder
    ├── pricing/     PricingProperties, PriceInput, PriceResult, Sample, Grade, PriceCalculator, GradePolicy, FairRentEstimator, PriceCheckService
    ├── realdeal/    RealDeal, RealDealRepository, MolitClient, RealDealNormalizer, RealDealIngestJob, DongAdjacency
    ├── listing/     Listing, ListingRepository, ListingQuery, ListingController, ListingService
    ├── geo/         WalkPort(TmapWalkAdapter), PlacePort(KakaoPlaceAdapter), AddressPort(KakaoAddressAdapter), GeoController, WalkService, NearbyService
    ├── housing/     Housing, UnitType, Announcement, AnnouncementEvent, Subscription, HousingController, HousingService
    ├── dorm/        Dorm, DormRoomType, DormController
    ├── compare/     AlternativeService (alternatives)
    ├── favorite/    Favorite, FavoriteController, FavoriteService
    ├── transfer/    Transfer, TransferController, TransferService, UploadController, StoragePort
    ├── review/      Review, ReviewController
    ├── home/        Home, Payment, Utility, ExpiryAlert, HomeController, ReportService
    ├── notification/ Notification, NotificationController, NotificationJob
    ├── search/      SearchController, SearchService
    ├── floorplan/   FloorPlan(jsonb 컬럼), FloorPlanController
    └── world/       WorldSocketHandler, WorldState, Player, InviteService, InviteController, WebSocketConfig
```

---

### Task 1: 프로젝트 골격 · 공통 에러 · CORS · Swagger

**Files:**
- Create: `build.gradle.kts`, `application.yml`, `common/ApiError.java`, `common/ErrorCode.java`, `common/ApiException.java`, `common/GlobalExceptionHandler.java`, `common/PageResponse.java`, `common/HealthController.java`
- Test: `src/test/java/com/chatatda/api/common/CommonApiTest.java`, `src/test/java/com/chatatda/api/support/IntegrationTest.java` (Testcontainers PostgreSQL 베이스 클래스)

**Interfaces:**
- Produces: `record ApiError(String code, String message, Object details)`, `enum ErrorCode { VALIDATION_FAILED(400), INVALID_EMAIL_DOMAIN(400), CODE_MISMATCH(400), CODE_EXPIRED(400), UNAUTHORIZED(401), FORBIDDEN(403), NOT_FOUND(404), ALREADY_EXISTS(409), TOO_MANY_REQUESTS(429), UPSTREAM_FAILED(502), WORLD_FULL(503) }`, `class ApiException extends RuntimeException { ApiException(ErrorCode, String message) }`, `record PageResponse<T>(List<T> items, int page, int size, long total)`, 추상 클래스 `IntegrationTest`

- [ ] **Step 1: 실패하는 테스트 작성**
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
- [ ] **Step 2: 실행해서 실패 확인** — `./gradlew test --tests '*CommonApiTest'` → FAIL (프로젝트·핸들러 없음)
- [ ] **Step 3: 구현** — Spring Initializr 의존성: web, validation, data-jpa, security, mail, websocket, postgresql, flyway, springdoc-openapi-starter-webmvc-ui, jjwt, testcontainers-postgresql. `GlobalExceptionHandler`는 `ApiException`·`MethodArgumentNotValidException`(→ `VALIDATION_FAILED`, `details`=필드별 메시지)·`NoResourceFoundException`(→ `NOT_FOUND`)를 `ApiError`로 변환. CORS 오리진은 `cors.allowed-origins` 설정값
- [ ] **Step 4: 통과 확인** — 같은 명령 → PASS. `./gradlew bootRun` 후 `http://localhost:8080/swagger-ui.html` 열림
- [ ] **Step 5: 커밋** — `git commit -m "chore: bootstrap spring server with error format, cors, swagger"`

### Task 2: 학교 메일 인증 · JWT · 게스트 허용 보안

**Files:**
- Create: `auth/AuthController.java`, `auth/EmailCodeService.java`, `auth/EmailCode.java`, `auth/MailPort.java`, `auth/SmtpMailAdapter.java`, `common/JwtProvider.java`, `common/JwtFilter.java`, `common/SecurityConfig.java`, `common/CurrentUser.java`, `user/User.java`, `user/UserRepository.java`, `db/migration/V1__users_auth.sql`
- Test: `auth/AuthApiTest.java`, `common/SecurityRulesTest.java`

**Interfaces:**
- Consumes: Task 1 `ApiException`, `ErrorCode`
- Produces: `interface MailPort { void send(String to, String subject, String body); }`, `JwtProvider.issue(long userId): String`, `JwtProvider.parse(String token): Optional<Long>`, 컨트롤러 파라미터 `@CurrentUser Long userId`(필수), `@CurrentUser(required=false) Long userIdOrNull`, `EmailCodeService` 내부 시계 `Clock` 주입(테스트 시간 이동용)

- [ ] **Step 1: 실패하는 테스트 작성** (`MailPort`는 테스트에서 받은 코드를 저장하는 가짜 빈)
```java
@Test void send_rejectsOtherDomain()  // POST /auth/email/send {email:"a@gmail.com"} → 400, code INVALID_EMAIL_DOMAIN
@Test void send_then_verify_issuesToken() // send → 204, fakeMail.lastCode() 6자리 숫자, verify → 200, $.accessToken 존재, $.user.nickname 이 "한양"으로 시작
@Test void verify_wrongCode_400()      // code CODE_MISMATCH
@Test void verify_after10min_expired() // clock +601초 → CODE_EXPIRED
@Test void resend_within60s_429()      // TOO_MANY_REQUESTS
@Test void fiveWrongAttempts_discardsCode() // 5회 틀린 뒤 맞는 코드 → CODE_MISMATCH
// SecurityRulesTest
@Test void guest_canBrowse()   // 토큰 없이 GET /api/v1/listings, /api/v1/housing, /api/v1/search?q=행당 → 200
@Test void guest_meIs401()     // 토큰 없이 GET /api/v1/me/profile → 401, code UNAUTHORIZED
@Test void guest_writeIs401()  // 토큰 없이 POST /api/v1/me/favorites → 401
@Test void guest_canCreateInvite() // 토큰 없이 POST /api/v1/invites → 401 아님
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*AuthApiTest' --tests '*SecurityRulesTest'` → FAIL
- [ ] **Step 3: 구현** — 코드 생성 `SecureRandom` 6자리(앞자리 0 허용), 저장은 DB `email_codes`(email, code_hash, expires_at, attempts, sent_at). 첫 인증 시 `User` 생성(닉네임 `한양` + 4자리 난수, 중복 시 재생성). `SecurityConfig`: `/api/v1/me/**` 인증, `HttpMethod.GET` 전부 허용, `/api/v1/auth/**`·`/api/v1/invites` 허용, 그 외 쓰기는 인증. 인증 실패 응답도 `ApiError` 형식. `SmtpMailAdapter`는 `spring.mail.*` 설정 사용 (로컬은 로그 출력 어댑터로 대체 가능)
- [ ] **Step 4: 통과 확인** — 같은 명령 → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(auth): hanyang email code login, jwt, guest-friendly security"`

### Task 3: 프로필 · 학과 · 건물 · 공유 픽스처 시더

**Files:**
- Create: `user/ProfileController.java`, `user/ProfileService.java`, `catalog/Department.java`, `catalog/Building.java`, `catalog/CatalogController.java`, `catalog/FixtureSeeder.java`, `db/migration/V2__catalog_profile.sql`
- Test: `user/ProfileApiTest.java`, `catalog/CatalogApiTest.java`, `catalog/FixtureSeederTest.java`

**Interfaces:**
- Produces: `FixtureSeeder.seedIfEmpty()` — `fixtures/*.json`(계약 7장)을 읽어 비어 있는 테이블에만 넣음, `app.seed.enabled=true`일 때 시작 시 실행. 다른 Task들의 엔티티 시드는 각 Task가 이 클래스에 메서드를 추가(`seedListings()`, `seedHousing()` …)
- Produces: `ProfileService.firstBuildingId(long userId): Optional<Long>` (Task 6, 8에서 도보 기준 건물로 사용), `ProfileService.budget(long userId): Optional<Budget>`, `record Budget(Long rentCap, Long depositCap)`

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void departments_listed()        // GET /departments → 길이 ≥ 5, $[0].defaultBuildingIds 배열
@Test void buildings_filterByType()    // GET /buildings?type=GATE → 전부 type=="GATE", 길이 ≥ 2
@Test void profile_updatePartial()     // PUT /me/profile {budget:{rentCap:600000,depositCap:10000000}} → 200, departmentId 그대로, budget.rentCap==600000
@Test void profile_settingDepartment_fillsDefaultBuildings() // PUT {departmentId: X} (buildingIds 생략) → buildingIds == 학과 defaultBuildingIds
@Test void seeder_isIdempotent()       // seedIfEmpty() 두 번 → 학과 수 변화 없음
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*ProfileApiTest' --tests '*CatalogApiTest' --tests '*FixtureSeederTest'` → FAIL
- [ ] **Step 3: 구현** — PUT은 null 필드를 "변경 안 함"으로 처리. Jackson으로 픽스처 파싱
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(catalog): departments, buildings, profile, fixture seeder"`

### Task 4: 초과액 판정 엔진 (순수 도메인)

**Files:**
- Create: `pricing/PricingProperties.java`, `pricing/PriceInput.java`, `pricing/Sample.java`, `pricing/PriceResult.java`, `pricing/Grade.java`, `pricing/PriceCalculator.java`, `pricing/GradePolicy.java`
- Test: `pricing/PriceCalculatorTest.java`, `pricing/GradePolicyTest.java`

**Interfaces:**
- Produces:
  - `@ConfigurationProperties("pricing") record PricingProperties(double conversionRate /*기본 0.06*/, double gradeFair /*0.05*/, double gradeSlight /*0.15*/, double gradeHigh /*0.30*/, int minSample /*10*/, double areaTolerance /*0.30*/, int periodMonths /*12*/, int defaultContractMonths /*24*/)`
  - `record PriceInput(long deposit, long rent, Long mgmtFee /*null 허용*/, double areaM2, String dong, int contractMonths)`
  - `record Sample(int count, String scope /*DONG|ADJACENT|NONE*/, List<String> dongs, Double areaMinM2, Double areaMaxM2, YearMonth from, YearMonth to, Double medianPerM2 /*㎡당 환산월세*/)`
  - `enum Grade { FAIR, SLIGHTLY_HIGH, HIGH, CULPRIT, PENDING }`
  - `PriceCalculator.convertedRent(long deposit, long rent, Long mgmtFee, double rate): long`
  - `PriceCalculator.evaluate(PriceInput in, Sample sample): PriceResult`
  - `record PriceResult(long convertedRent, Long fairRent, Long monthlyExcess, int contractMonths, Long totalExcess, Double excessRate, Grade grade, double conversionRate, Sample sample)`
  - `GradePolicy.of(Double excessRate, boolean pending): Grade`

- [ ] **Step 1: 실패하는 테스트 작성**
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
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*PriceCalculatorTest' --tests '*GradePolicyTest'` → FAIL
- [ ] **Step 3: 구현** — 금액은 `Math.round`(원 단위), `excessRate`는 `BigDecimal` HALF_UP 셋째 자리. 스프링 의존 없음
- [ ] **Step 4: 통과 확인** → PASS
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

- [ ] **Step 1: 실패하는 테스트 작성**
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
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*RealDealNormalizerTest' --tests '*FairRentEstimatorTest'` → FAIL
- [ ] **Step 3: 구현** — 표본의 ㎡당 환산 월세 = `convertedRent(deposit, rent, null, rate) / areaM2` (실거래에는 관리비 없음), 중앙값은 정렬 후 가운데(짝수면 두 값 평균). 국토부 API 데이터셋 이름·파라미터는 공공데이터포털 상세 페이지 기준으로 확인 후 `MolitClient`에 상수로 기록
- [ ] **Step 4: 통과 확인** → PASS. 실제 키로 `./gradlew bootRun --args='--app.ingest.enabled=true'` 1회 실행 후 `select dong, count(*) from real_deals group by dong` 결과를 PR 설명에 기록 (OKR 안 2의 표본 수 근거)
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

- [ ] **Step 1: 실패하는 테스트 작성** (픽스처 시드 사용)
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
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*ListingApiTest'` → FAIL
- [ ] **Step 3: 구현** — 목록은 JPA Specification으로 조건 조합. `favorited`는 Task 9 전까지 false
- [ ] **Step 4: 통과 확인** → PASS
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

- [ ] **Step 1: 실패하는 테스트 작성** (포트는 `@MockBean`)
```java
@Test void walk_ok()                    // GET /walk?... → $.minutes == 가짜 값
@Test void walk_upstreamFails_502()     // WalkPort 예외 → 502, code UPSTREAM_FAILED
@Test void listing_walkMinNull_whenTmapDown() // WalkPort 예외 + buildingId 지정 GET /listings → 200, items[*].walkMin == null
@Test void nearby_emptyWhenKakaoDown()  // PlacePort 예외 → 200, []
@Test void nearby_radiusCappedAt500()   // radius=2000 → PlacePort가 500으로 호출됨
@Test void walkService_caches()         // 같은 좌표 2회 → WalkPort 1회 호출
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*GeoApiTest' --tests '*WalkServiceTest'` → FAIL
- [ ] **Step 3: 구현** — `RestClient`, 타임아웃 3초. 키는 `external.tmap.key`, `external.kakao.rest-key`
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(geo): walk time, nearby places, address search with graceful fallback"`

### Task 8: 청년안심주택 · 공고 · 구독 · 기숙사 · 대안 비교

**Files:**
- Create: `housing/Housing.java`, `housing/UnitType.java`, `housing/Announcement.java`, `housing/AnnouncementEvent.java`, `housing/Subscription.java`, `housing/HousingService.java`, `housing/HousingController.java`, `dorm/Dorm.java`, `dorm/DormRoomType.java`, `dorm/DormController.java`, `compare/AlternativeService.java`, `db/migration/V5__housing_dorm.sql`
- Modify: `catalog/FixtureSeeder.java` (`seedHousing()`, `seedDorms()`), `listing/ListingController.java` (`/listings/{id}/alternatives`)
- Test: `housing/HousingApiTest.java`, `dorm/DormApiTest.java`, `compare/AlternativeServiceTest.java`

**Interfaces:**
- Consumes: Task 4 `PriceCalculator.convertedRent`, Task 7 `WalkService.minutesOrNull`
- Produces:
  - `HousingService.recruiting(long housingId, LocalDate today): boolean`, `HousingService.nextEvent(long housingId, LocalDate today): Optional<EventDto>`
  - `HousingService.subscriberIds(long housingId): List<Long>`, `HousingService.eventsOn(LocalDate date): List<AnnouncementEvent>` (Task 13)
  - `DormRoomType.monthlyCost(): long` = `Math.round((double) semesterFee / semesterMonths)`
  - `AlternativeService.forListing(long listingId, Long buildingId): AlternativesDto` — 청년안심주택 주택형·기숙사 호실을 환산 월세 낮은 순 최대 3개, `monthlyDiff = listing.convertedRent − alt.convertedRent`, `twoYearDiff = monthlyDiff × 24`
  - 테스트용 오늘 날짜는 `Clock` 빈 주입

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void housing_recruitingFlag()    // OPEN 공고가 있는 단지 → recruiting true, 없는 단지 → false
@Test void housing_nextEvent()         // clock=2026-11-07, 일정 11-05·11-10·11-20 → nextEvent.date "2026-11-10"
@Test void announcements_filterByStatus() // ?status=OPEN → 전부 OPEN
@Test void subscribe_idempotent()      // POST 두 번 → 둘 다 204, 구독 1건
@Test void subscribe_guest401()
@Test void dorm_monthlyCost()          // semesterFee 1_200_000, months 4 → monthlyCost 300000
@Test void alternatives_sortedAndDiff() // 결과 housing 리스트 convertedRent 오름차순, size ≤ 3, twoYearDiff == monthlyDiff*24
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*HousingApiTest' --tests '*DormApiTest' --tests '*AlternativeServiceTest'` → FAIL
- [ ] **Step 3: 구현** — 주택형 `convertedRent`는 `mgmtFee` 포함, 기숙사는 `monthlyCost`를 환산 월세로 사용
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(housing,dorm): complexes, announcements, subscriptions, alternatives"`

### Task 9: 찜

**Files:**
- Create: `favorite/Favorite.java`, `favorite/FavoriteService.java`, `favorite/FavoriteController.java`, `db/migration/V6__favorites.sql` (unique `(user_id, type, target_id)`)
- Modify: `listing/ListingService.java` (`favorited` 채우기)
- Test: `favorite/FavoriteApiTest.java`

**Interfaces:**
- Consumes: Task 6 `ListingService.summaryOf`, Task 8 단지·기숙사 조회
- Produces: `FavoriteService.isFavorited(Long userIdOrNull, FavoriteType type, long targetId): boolean`, `FavoriteService.favoritedIds(long userId, FavoriteType type): Set<Long>` (목록 N+1 방지)

- [ ] **Step 1: 실패하는 테스트 작성**
```java
@Test void add_list_remove()      // POST {LISTING,12} → 201 / GET → 1개, convertedRent·grade 채워짐 / DELETE → 204 / GET → 0개
@Test void duplicate_409()        // 같은 POST 두 번 → 두 번째 409 ALREADY_EXISTS
@Test void delete_missing_204()
@Test void unknownTarget_404()    // POST {LISTING,999999} → 404
@Test void listingShowsFavorited()// 찜 후 GET /listings (토큰) → 해당 항목 favorited true
@Test void dormFavorite_gradeNull() // POST {DORM,1} 후 GET → grade null, convertedRent == 가장 싼 호실 monthlyCost
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*FavoriteApiTest'` → FAIL
- [ ] **Step 3: 구현** — 타입별 대상 조회를 `switch`로 분기
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(favorite): add, list, remove favorites across types"`

### Task 10: 양도 게시판 · 업로드

**Files:**
- Create: `transfer/Transfer.java`, `transfer/TransferService.java`, `transfer/TransferController.java`, `transfer/UploadController.java`, `transfer/StoragePort.java`, `transfer/LocalDiskStorage.java`, `db/migration/V7__transfers.sql`
- Modify: `catalog/FixtureSeeder.java` (`seedTransfers()`)
- Test: `transfer/TransferApiTest.java`

**Interfaces:**
- Consumes: Task 6 `PriceCheckService.check`, Task 9 `FavoriteService.isFavorited`
- Produces: `interface StoragePort { String save(MultipartFile f); }` (로컬은 디스크 + 정적 경로 `/files/**`, 배포 시 S3 호환 구현으로 교체)

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
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*TransferApiTest'` → FAIL
- [ ] **Step 3: 구현** — 판정은 저장 시 계산해 캐시(Task 6과 같은 방식), 수정 시 재계산
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(transfer): transfer board with auto price-check and uploads"`

### Task 11: 후기

**Files:**
- Create: `review/Review.java`, `review/ReviewController.java`, `db/migration/V8__reviews.sql`
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
- Create: `home/Home.java`, `home/Payment.java`, `home/Utility.java`, `home/ExpiryAlert.java`, `home/HomeController.java`, `home/ReportService.java`, `db/migration/V9__home.sql`
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
- Create: `notification/Notification.java`, `notification/NotificationController.java`, `notification/NotificationJob.java`, `db/migration/V10__notifications.sql` (unique `(user_id, type, target_id, ref_date)` 로 중복 생성 방지)
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
@Test void list_and_read()        // GET → 최신순, PATCH read → read true
```
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*NotificationJobTest' --tests '*NotificationApiTest'` → FAIL
- [ ] **Step 3: 구현** — 제목 예: `"[D-7] 왕십리역 청아진 접수 마감"`, `"계약 만료 60일 전이에요"`
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(notification): daily dday and expiry notifications, inbox"`

### Task 14: 통합 검색 · 평면도

**Files:**
- Create: `search/SearchService.java`, `search/SearchController.java`, `floorplan/FloorPlan.java`, `floorplan/FloorPlanController.java`, `db/migration/V11__floorplans.sql`
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
- [ ] **Step 4: 통과 확인** → PASS
- [ ] **Step 5: 커밋** — `git commit -m "feat(world): shared world websocket, invites with spawn next to inviter"`

### Task 16: 배포 · 프론트 연동 확인

**Files:**
- Create: `Dockerfile`, `application-prod.yml`, `README.md` (실행 방법, 환경 변수 목록)
- Test: `src/test/java/com/chatatda/api/ContractSmokeTest.java`

**Interfaces:**
- Produces: 환경 변수 `DB_URL`, `DB_USER`, `DB_PASSWORD`, `JWT_SECRET`, `MAIL_*`, `MOLIT_KEY`, `TMAP_KEY`, `KAKAO_REST_KEY`, `CORS_ALLOWED_ORIGINS`, `FRONT_BASE_URL`

- [ ] **Step 1: 실패하는 테스트 작성** — 계약 5장의 모든 GET 엔드포인트를 픽스처 시드 상태에서 한 번씩 호출해 2xx(또는 `/me/*`는 토큰으로 2xx)인지 확인하는 표 기반 테스트 `allContractGetsRespond()`
- [ ] **Step 2: 실패 확인** — `./gradlew test --tests '*ContractSmokeTest'` → 누락 엔드포인트가 있으면 FAIL
- [ ] **Step 3: 구현** — 누락분 보완, Dockerfile(멀티 스테이지, `eclipse-temurin:21-jre`), Railway·Render 중 하나에 PostgreSQL과 함께 배포
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
