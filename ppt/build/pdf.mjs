// ?print-pdf 로 PDF 를 뽑는다: node docs/ppt/build/pdf.mjs <출력.pdf>
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { chromium } from '/Users/inter4259/maindesktop/chatatda-hanyang/frontend/node_modules/playwright-core/index.mjs';
const here = dirname(fileURLToPath(import.meta.url));
const out = process.argv[2] || join(here, '..', '어디서사냥-발표.pdf');
const b = await chromium.launch({ channel: 'chrome', headless: true });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
await p.goto('file://' + join(here, '..', 'index.html') + '?print-pdf');
await p.waitForFunction(() => window.Reveal && Reveal.isReady());
await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(2500);
await p.pdf({ path: out, width: '1920px', height: '1080px', printBackground: true, preferCSSPageSize: true });
console.log('saved', out);
await b.close();
