// 모든 장을 1920×1080 으로 찍고 넘침을 검사한다
//   node docs/ppt/build/verify.mjs <출력 폴더>
import { mkdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '/Users/inter4259/maindesktop/chatatda-hanyang/frontend/node_modules/playwright-core/index.mjs';
const here = dirname(fileURLToPath(import.meta.url));
const out = process.argv[2] || join(here, 'renders'); mkdirSync(out, { recursive: true });
const b = await chromium.launch({ channel: 'chrome', headless: true });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
const errs = []; p.on('pageerror', (e) => errs.push(e.message)); p.on('console', (m) => { if (m.type() === 'error') errs.push(m.text()); });
await p.goto('file://' + join(here, '..', 'index.html'));
await p.waitForFunction(() => window.Reveal && Reveal.isReady());
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(1500);
const n = await p.evaluate(() => Reveal.getTotalSlides());
const fonts = await p.evaluate(() => ({ pre: document.fonts.check('700 40px "Pretendard Variable"'), arc: document.fonts.check('800 40px Archivo') }));
console.log('slides', n, 'fonts', JSON.stringify(fonts));
for (let i = 0; i < n; i++) {
  await p.evaluate((i) => { Reveal.slide(i, 0, 99); }, i);
  await p.waitForTimeout(700);
  const r = await p.evaluate(() => {
    const s = Reveal.getCurrentSlide();
    const bad = [];
    const sb = s.getBoundingClientRect(); const sc = sb.width / 1920;
    for (const e of s.querySelectorAll('*')) {
      if (e.closest('aside.notes') || e.closest('svg')) continue;
      const cs = getComputedStyle(e); if (cs.display === 'none' || cs.visibility === 'hidden') continue;
      const rc = e.getBoundingClientRect(); if (!rc.width || !rc.height) continue;
      const bottom = (rc.bottom - sb.top) / sc, right = (rc.right - sb.left) / sc;
      if (bottom > 1082 || right > 1922) bad.push(`${e.tagName.toLowerCase()}.${(e.className && e.className.baseVal == null ? e.className : '').toString().split(' ')[0]} b${Math.round(bottom)} r${Math.round(right)}`);
    }
    const fr = s.querySelector('.frame'); const body = s.querySelector('.body');
    const over = [];
    if (fr && fr.scrollHeight > fr.clientHeight + 1) over.push(`frame ${fr.scrollHeight}>${fr.clientHeight}`);
    if (body && body.scrollHeight > body.clientHeight + 1) over.push(`body ${body.scrollHeight}>${body.clientHeight}`);
    const vids = [...s.querySelectorAll('video')].map((v) => `${v.readyState}/${v.paused ? 'paused' : 'playing'}`);
    return { bad: bad.slice(0, 6), over, vids, title: (s.querySelector('h2,h1')?.textContent || '').slice(0, 40) };
  });
  await p.screenshot({ path: join(out, `s${String(i + 1).padStart(2, '0')}.png`) });
  console.log(i + 1, r.title, r.over.join(' '), r.bad.length ? 'OUT:' + r.bad.join(', ') : '', r.vids.length ? 'video:' + r.vids.join(',') : '');
}
console.log('errors', errs.slice(0, 8));
await b.close();
