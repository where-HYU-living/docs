# Harness ledger

원장 위치: `docs` 레포 `harness/progress.md` (작업 루트 기준 `docs/harness/progress.md`). 기능명세서는 `docs` 레포 `docs/spec-v0.5.md`.
레포: frontend · backend · campus-data · docs (각자 git, 원격 where-HYU-living/*). 작업 루트는 git 아님.

## Phases
- Phase 0: 원장 생성 (2026-11-08)
- Phase 1: complete — docs `spec-v0.5.md` 4-S 구현 상태 표(전 기능 ID·프론트/백엔드 상태·개선점). 테스트: 문서 단계라 없음(코드 대조로 확인)
- Phase 2-1: 프론트↔백엔드 싱크 — 진행 중

## Findings
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
