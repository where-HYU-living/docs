// 발표 자료용 화면 캡처 (배포본 where-hyu-living.xyz, 사용자가 직접 로그인한 세션 사용)
//   node docs/ppt/capture/capture.mjs                # 전부
//   node docs/ppt/capture/capture.mjs listings rooms # 일부만 (home listings rooms tour extras mobile clips)
// 세션이 없거나 만료됐으면: node docs/ppt/capture/login.mjs 로 다시 로그인한다.
// 결과: docs/ppt/assets/shots/*.png, docs/ppt/assets/clips/*.webm
import { existsSync, mkdirSync, rmSync, writeFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '/Users/inter4259/maindesktop/chatatda-hanyang/frontend/node_modules/playwright-core/index.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const STATE = join(here, '.auth', 'state.json');
const SHOTS = join(here, '..', 'assets', 'shots');
const CLIPS = join(here, '..', 'assets', 'clips');
const BASE = 'https://where-hyu-living.xyz/';
mkdirSync(SHOTS, { recursive: true }); mkdirSync(CLIPS, { recursive: true });
if (!existsSync(STATE)) { console.log('로그인 세션이 없습니다. node docs/ppt/capture/login.mjs 를 먼저 실행해 주세요.'); process.exit(1); }

const only = process.argv.slice(2);
const want = (n) => !only.length || only.includes(n);
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// 화면에 실명·이메일이 보이지 않게: 계정 버튼 이름, '혼자 둘러보는 중' 안내를 숨긴다
const CLEAN_CSS = `
  .ui-tb-account .ui-tb-name { visibility: hidden !important; }
  .ui-chat-status .ui-chat-sub:empty { display:none }
`;

async function open({ w = 1600, h = 1000, dpr = 2, q = '?solo', video } = {}) {
  const browser = await chromium.launch({ channel: 'chrome', headless: true, args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'] });
  const ctx = await browser.newContext({
    storageState: STATE, viewport: { width: w, height: h }, deviceScaleFactor: dpr,
    ...(video ? { recordVideo: { dir: video, size: { width: w, height: h } } } : {}),
  });
  await ctx.addInitScript(() => { try { localStorage.setItem('ui-tour-coach-v1', '1'); } catch { /* */ } });
  const page = await ctx.newPage();
  const errs = [];
  page.on('pageerror', (e) => errs.push(e.message));
  await page.goto(BASE + q, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__ready, null, { timeout: 120000 });
  // 로그인 확인: 토큰이 없으면 멈춘다
  const authed = await page.evaluate(() => !!localStorage.getItem('chatatda.token'));
  if (!authed) { console.log('로그인이 풀렸습니다. node docs/ppt/capture/login.mjs 로 다시 로그인해 주세요.'); await browser.close(); process.exit(2); }
  await page.addStyleTag({ content: CLEAN_CSS });
  await wait(2500);
  return { browser, ctx, page, errs };
}

const tab = (page, name) => page.getByRole('tab', { name, exact: true }).click();
const hideSoloPill = (page) => page.evaluate(() => {
  for (const el of document.querySelectorAll('body *')) {
    if (el.children.length === 0 && /혼자 둘러보는 중/.test(el.textContent || '')) {
      let p = el; for (let i = 0; i < 4 && p.parentElement && p.parentElement !== document.body; i++) p = p.parentElement;
      (el.closest('section,aside,div') || el).style.visibility = 'hidden';
    }
  }
});
async function shot(page, name, opts = {}) {
  await hideSoloPill(page);
  await page.screenshot({ path: join(SHOTS, name + '.png'), ...opts });
  console.log('  ✓', name);
}
async function el(page, name, selectorOrFn) {
  const h = typeof selectorOrFn === 'string' ? await page.$(selectorOrFn) : await page.evaluateHandle(selectorOrFn);
  const e = h && h.asElement ? h.asElement() : null;
  if (!e) { console.log('  ✗ 없음', name); return; }
  await e.scrollIntoViewIfNeeded(); await wait(500);
  await e.screenshot({ path: join(SHOTS, name + '.png') });
  console.log('  ✓', name);
}
// 패널 안의 한 구역을 패널 맨 위로 올린 뒤 패널째 찍는다 (구역이 패널보다 넓어 잘리는 것 방지)
async function panelAt(page, name, sel) {
  const ok = await page.evaluate((s) => { const e = document.querySelector(s); if (!e) return false; const b = e.closest('.ui-panel-body'); if (b) b.scrollTop += e.getBoundingClientRect().top - b.getBoundingClientRect().top - 8; return true; }, sel);
  if (!ok) { console.log('  ✗ 없음', name); return; }
  await wait(500); await el(page, name, () => document.querySelector('[class*=ui-panel]'));
}
const zoomOut = async (page, n = 4) => { await page.mouse.move(1000, 500); for (let i = 0; i < n; i++) { await page.mouse.wheel(0, 400); await wait(150); } await wait(800); };
const drag = async (page, dx, dy = 0) => { await page.mouse.move(1000, 500); await page.mouse.down(); await page.mouse.move(1000 + dx, 500 + dy, { steps: 12 }); await page.mouse.up(); await wait(600); };
const closePanel = (page) => page.evaluate(() => document.querySelector('[class*=ui-panel] button[aria-label*="접기"], [class*=ui-panel-head] button')?.click());
const enterChip = async (page, re) => { const b = page.locator('.ui-tour-rail button', { hasText: re }).first(); if (await b.count()) { await b.click(); await wait(2500); } };
const setTime = async (page, v) => {
  await page.locator('button[aria-label="더 보기"]').click(); await wait(400);
  await page.locator('input[aria-label^="시간대"]').first().fill(String(v)); await wait(600);
  await page.keyboard.press('Escape'); await page.mouse.click(1200, 900); await wait(800);
};

// ───────── 표지·전경 ─────────
async function home() {
  console.log('[home]');
  {
    // 표지: 사자상·역사관·애지문이 한눈에 보이는 높은 시점
    const a = await open({ q: '?solo&cam=-13,1.5,0,1.5,90,0.55' });
    await shot(a.page, 'cover-aerial');
    await setTime(a.page, 700); await shot(a.page, 'cover-aerial-dusk');
    await a.browser.close();
  }
  const { browser, page } = await open();
  await shot(page, 'campus-hero');
  await tab(page, '캠퍼스 투어'); await wait(1500);
  await page.locator('.ui-tour-item', { hasText: '제2학생생활관' }).first().click(); await wait(6000);
  await tab(page, '캠퍼스 투어'); await wait(800); // 패널 접기
  await zoomOut(page, 6); await drag(page, -160, 40);
  await shot(page, 'cover-campus');
  await setTime(page, 720);
  await shot(page, 'cover-dusk');
  await browser.close();
}

// ───────── 매물·판결·후기 ─────────
async function listings() {
  console.log('[listings]');
  const { browser, page } = await open();
  await tab(page, '매물 찾기'); await wait(2000);
  await shot(page, 'listings-panel');
  await el(page, 'listings-cards', () => document.querySelector('[class*=ui-panel]'));
  await page.locator('.ui-cards > *').first().click(); await wait(2500);
  await shot(page, 'detail-verdict');
  await el(page, 'verdict-card', () => { let e = document.querySelector('.ui-vd-basis'); while (e && !e.querySelector('.ui-vd-big')) e = e.parentElement; return e; });
  await el(page, 'wanted', '.ui-wanted');
  await panelAt(page, 'compare', '.ui-compare');
  await panelAt(page, 'reviews', '.ui-reviews');
  const write = page.getByRole('button', { name: '후기 쓰기' });
  if (await write.count()) { await write.first().click(); await wait(1200); await el(page, 'review-form', '.ui-review-form'); await page.keyboard.press('Escape'); }
  // 3D에서 보기 (말풍선)
  await page.locator('.ui-ld-go').click(); await wait(8000);
  await shot(page, 'detail-3d');
  // 과 건물까지 도보 길
  const walk = page.locator('button', { hasText: '과 건물까지' }).first();
  if (await walk.count()) {
    await walk.click(); await wait(7000); await shot(page, 'walk-route');
    const onMap = page.getByRole('button', { name: /지도에서 보기/ }).last();
    if (await onMap.count()) { await onMap.click(); await wait(6000); await shot(page, 'walk-route-map'); }
  }
  await browser.close();
}

// ───────── 룸투어 4종 ─────────
async function rooms() {
  console.log('[rooms]');
  const { browser, page } = await open();
  // 자취방: 사근동 풀옵션 원룸 → 주변 걸어보기 → 실내 보기
  await tab(page, '매물 찾기'); await wait(1500);
  await page.locator('.ui-cards > *', { hasText: '사근동 풀옵션 원룸' }).click(); await wait(1500);
  await page.locator('.ui-v-walk').first().click(); await wait(12000);
  await tab(page, '매물 찾기'); await wait(800);
  await zoomOut(page, 6); await drag(page, 220, 30);
  await shot(page, 'nb-listing');
  await page.locator('.ui-v-hud-in').click(); await wait(9000);
  await shot(page, 'room-listing-entry');
  await enterChip(page, /침실/);
  await shot(page, 'room-listing');
  await page.locator('.ui-tour-back').click(); await wait(3500);
  // 기숙사: 2인실
  await tab(page, '기숙사'); await wait(2000);
  await page.getByRole('button', { name: '실내 보기' }).nth(1).click(); await wait(9000);
  await enterChip(page, /침실|방/);
  await shot(page, 'room-dorm');
  await page.locator('.ui-tour-back').click(); await wait(3500);
  // 청년안심주택: 청량리역 퀸즈W 35B
  await tab(page, '청년안심주택'); await wait(2000);
  await page.locator('.ui-v-place', { hasText: '퀸즈W' }).first().click(); await wait(3000);
  await shot(page, 'housing-detail');
  await page.getByRole('button', { name: '실내 보기' }).first().click(); await wait(9000);
  await enterChip(page, /거실/);
  await shot(page, 'room-housing');
  // 실내 핀 후기: 벽을 길게 눌러 작성 창만 띄운다 (저장하지 않는다)
  await page.mouse.move(560, 520); await page.mouse.down(); await wait(900); await page.mouse.up(); await wait(1800);
  await shot(page, 'room-pin-form');
  await setTime(page, 820).catch(() => {});
  await shot(page, 'room-housing-night');
  await page.locator('.ui-tour-back').click(); await wait(3500);
  // 양도
  await tab(page, '양도'); await wait(2000);
  await page.locator('.ui-cards > *').first().click(); await wait(3000);
  await shot(page, 'transfer-detail');
  const go3d = page.getByRole('button', { name: '3D로 보기' });
  if (await go3d.count()) { await go3d.first().click(); await wait(9000); await zoomOut(page, 4); await shot(page, 'transfer-3d'); }
  await browser.close();
}

// ───────── 캠퍼스 투어 ─────────
async function tour() {
  console.log('[tour]');
  const { browser, page } = await open();
  await tab(page, '캠퍼스 투어'); await wait(2000);
  await shot(page, 'tour-panel');
  await page.locator('.ui-tour-item', { hasText: '백남학술정보관' }).first().click(); await wait(7000);
  await shot(page, 'tour-go');
  await tab(page, '캠퍼스 투어'); await wait(800);
  await zoomOut(page, 5); await drag(page, 200, 60);
  await shot(page, 'tour-wide');
  await browser.close();
}

// ───────── 그 밖의 기능 ─────────
async function extras() {
  console.log('[extras]');
  const { browser, page } = await open();
  await tab(page, '청년안심주택'); await wait(1500);
  await page.getByRole('tab', { name: '공고 캘린더' }).click(); await wait(2500);
  await shot(page, 'housing-calendar');
  await el(page, 'housing-calendar-panel', () => document.querySelector('[class*=ui-panel]'));
  await tab(page, '내 집 기록'); await wait(2500);
  await shot(page, 'myhome');
  await tab(page, '내 집 기록'); await wait(600);
  await page.locator('button[aria-label="더 보기"]').click(); await wait(500);
  await page.getByRole('button', { name: '캐릭터 꾸미기' }).click(); await wait(2500);
  await shot(page, 'avatar');
  await browser.close();
}

// ───────── 모바일 ─────────
async function mobile() {
  console.log('[mobile]');
  const { browser, page } = await open({ w: 390, h: 844, dpr: 3 });
  await shot(page, 'm-home');
  await page.locator('button[data-pop="menu"]').click(); await wait(500);
  await page.locator('.ui-tb-item', { hasText: '매물 찾기' }).click(); await wait(2000);
  await shot(page, 'm-listings');
  await page.locator('.ui-cards > *').first().click(); await wait(2500);
  await shot(page, 'm-verdict');
  await browser.close();
}

// ───────── 영상 (webm, 6~8초로 자르고 압축) ─────────
// 크롬 화면 송출(screencast) 프레임을 모아 시스템 ffmpeg 로 webm 을 만든다 (playwright 영상 기능은 별도 ffmpeg 가 필요해서 쓰지 않음)
async function record(name, fn, maxSec = 8) {
  const tmp = join(CLIPS, '_tmp_' + name); rmSync(tmp, { recursive: true, force: true }); mkdirSync(tmp, { recursive: true });
  const { browser, ctx, page } = await open({ dpr: 1 });
  await fn.prep?.(page);
  const cdp = await ctx.newCDPSession(page);
  const frames = [];
  cdp.on('Page.screencastFrame', async (f) => {
    const i = frames.length; frames.push(f.metadata.timestamp);
    writeFileSync(join(tmp, `f${String(i).padStart(5, '0')}.jpg`), Buffer.from(f.data, 'base64'));
    cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }).catch(() => {});
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 85, maxWidth: 1600, maxHeight: 1000, everyNthFrame: 1 });
  await fn(page);
  await cdp.send('Page.stopScreencast'); await wait(300);
  await browser.close();
  // 프레임별 표시 시간으로 concat 목록을 만든다
  const lines = []; let total = 0;
  for (let i = 0; i < frames.length; i++) {
    const d = Math.min(0.5, Math.max(1 / 60, (frames[i + 1] ?? frames[i] + 1 / 30) - frames[i]));
    if (total + d > maxSec) break; total += d;
    lines.push(`file 'f${String(i).padStart(5, '0')}.jpg'`, `duration ${d.toFixed(4)}`);
  }
  writeFileSync(join(tmp, 'list.txt'), lines.join('\n') + '\n');
  const out = join(CLIPS, name + '.webm');
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', join(tmp, 'list.txt'), '-vf', 'fps=30,scale=1280:-2', '-c:v', 'libvpx-vp9', '-b:v', '0', '-crf', '36', '-deadline', 'good', '-row-mt', '1', '-an', out]);
  rmSync(tmp, { recursive: true, force: true });
  console.log(`  ✓ ${name}.webm (${frames.length}프레임, ${total.toFixed(1)}초)`);
}
async function clips() {
  console.log('[clips]');
  // 1) 캠퍼스 걷기: 사자상에서 앞으로 걷다가 시점을 돌린다
  const walk = async (page) => {
    await page.keyboard.down('KeyW'); await wait(2800);
    await page.mouse.move(800, 500); await page.mouse.down(); await page.mouse.move(560, 500, { steps: 50 }); await page.mouse.up();
    await wait(2600); await page.keyboard.up('KeyW'); await wait(1200);
  };
  walk.prep = async (page) => { await page.mouse.click(800, 760); await wait(500); };
  await record('walk-campus', walk, 7);
  // 2) 캠퍼스 투어: 목록에서 건물을 누르면 그 입구 앞으로 간다
  const jump = async (page) => {
    await wait(600);
    await page.locator('.ui-tour-item', { hasText: '제1공학관' }).first().click(); await wait(3200);
    await page.locator('.ui-tour-item', { hasText: '백남학술정보관' }).first().click(); await wait(3500);
  };
  jump.prep = async (page) => { await tab(page, '캠퍼스 투어'); await wait(1500); };
  await record('tour-jump', jump, 7.5);
  // 3) 실내 투어: 청년안심주택 퀸즈W 실내에서 걷고 방을 옮긴다
  const room = async (page) => {
    await page.keyboard.down('KeyW'); await wait(1600); await page.keyboard.up('KeyW');
    await enterChip(page, /욕실/); await enterChip(page, /거실/); await wait(800);
  };
  room.prep = async (page) => {
    await tab(page, '청년안심주택'); await wait(1500);
    await page.locator('.ui-v-place', { hasText: '퀸즈W' }).first().click(); await wait(2500);
    await page.getByRole('button', { name: '실내 보기' }).first().click(); await wait(9000);
    await page.mouse.click(800, 500); await wait(300);
  };
  await record('room-walk', room, 8);
}

const t0 = Date.now();
if (want('home')) await home();
if (want('listings')) await listings();
if (want('rooms')) await rooms();
if (want('tour')) await tour();
if (want('extras')) await extras();
if (want('mobile')) await mobile();
if (want('clips')) await clips();
console.log(`끝 (${Math.round((Date.now() - t0) / 1000)}초)`);
