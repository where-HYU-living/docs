// 캡처용 로그인: 사람이 직접 구글(한양대 계정)로 로그인하면 세션을 저장한다.
//   node docs/ppt/capture/login.mjs [https://where-hyu-living.xyz]
// 창이 뜨면 로그인만 하면 된다. 앱이 localStorage['chatatda.token'] 을 쓰는 순간 .auth/state.json 에 저장하고 창을 닫는다.
// 저장 파일엔 JWT 가 들어 있다 → .auth/ 는 git 에 올리지 않는다(.gitignore).
import { mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '/Users/inter4259/maindesktop/chatatda-hanyang/frontend/node_modules/playwright-core/index.mjs';

const here = dirname(fileURLToPath(import.meta.url));
const url = process.argv[2] || 'https://where-hyu-living.xyz';
const out = join(here, '.auth', 'state.json');
mkdirSync(join(here, '.auth'), { recursive: true });

// 구글이 '자동화 브라우저' 로그인을 막지 않도록 실제 크롬 + 별도 프로필 + 자동화 표시 끄기
const ctx = await chromium.launchPersistentContext(join(here, '.profile'), {
  channel: 'chrome',
  headless: false,
  viewport: null,
  ignoreDefaultArgs: ['--enable-automation'],
  args: ['--disable-blink-features=AutomationControlled', '--start-maximized'],
});
const page = ctx.pages()[0] ?? (await ctx.newPage());
await page.goto(url);
console.log(`[login] ${url} 창에서 한양대 구글 계정으로 로그인하세요 (최대 10분 대기)`);

const deadline = Date.now() + 10 * 60 * 1000;
let token = null;
while (Date.now() < deadline) {
  for (const p of ctx.pages()) {
    try {
      if (new URL(p.url()).origin !== new URL(url).origin) continue;
      token = await p.evaluate(() => localStorage.getItem('chatatda.token'));
      if (token) break;
    } catch { /* 이동 중 */ }
  }
  if (token) break;
  await new Promise((r) => setTimeout(r, 1500));
}

if (!token) {
  console.log('[login] 시간 초과 — 토큰을 못 찾았습니다.');
  await ctx.close();
  process.exit(1);
}
await ctx.storageState({ path: out });
console.log(`[login] 저장 완료 → ${out}`);
await ctx.close();
