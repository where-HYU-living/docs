# 어디서사냥 발표 자료

reveal.js 5.1.0으로 만든 웹 발표 자료입니다.

## 고치는 법

- **슬라이드는 `index.html`을 직접 고칩니다.** 빌드 단계는 없습니다.
- 스타일은 `assets/deck.css`, 차트 숫자는 `assets/charts.js`에 있습니다.
- 캡처는 `assets/shots/`, 영상은 `assets/clips/`, 도식·로고·QR은 `assets/img/`에 둡니다.
- 배경 테마는 `assets/theme/`의 SVG 세 장입니다. 본문 장은 `page.svg`, 표지와 마무리는 `cover.svg`, 구분 장은 `blueprint.svg`를 씁니다. `index.html` 아래쪽 스크립트가 장마다 자동으로 붙입니다. 모눈을 바꾸려면 `python3 build/theme.py`로 다시 만듭니다. PDF 뷰어에서 흐려지지 않도록 반투명·mask 없이 단색 선으로만 그립니다.
- 제목·큰 숫자 글씨체는 Paperlogy(SIL OFL)이고 `assets/fonts/`에 있습니다. 본문은 Pretendard입니다.
- 슬라이드 안에 `<section>` 태그를 또 넣지 마세요. reveal이 새 장으로 인식합니다.
- 슬라이드에 넣는 수치는 `research.md`에 출처와 함께 적어 둡니다.

## 보기

```
cd docs/ppt && python3 -m http.server 8000
```

크롬에서 http://localhost:8000 을 엽니다. `S` 발표자 노트, `F` 전체 화면, `Esc` 전체 장 보기, 주소 끝 `#/5`로 5쪽 이동.

## 점검과 PDF

```
node docs/ppt/build/verify.mjs   # 모든 장 렌더링, 넘침·글꼴·영상 확인 (build/renders/)
node docs/ppt/build/pdf.mjs      # docs/ppt/어디서사냥-발표.pdf
```

## 배포 (Vercel)

```
cd docs/ppt && vercel deploy --prod
```

프로젝트 `where-hyu-living-ppt`, 주소 https://where-hyu-living-ppt.vercel.app

## 그 밖의 파일

- `capture/`: 화면 캡처 스크립트. `capture/.auth`, `capture/.profile`은 로그인 세션이라 git·배포에서 빠집니다.
- `build/gen_tables.py`: 기능 명세서·API 명세서가 바뀌었을 때 부록 표를 다시 만드는 도구.
- `research.md`: 시장 조사 출처, `outline.md`: 처음 짠 목차 초안.
