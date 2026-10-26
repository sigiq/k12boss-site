// Render raster brand assets (podcast cover, social share image, PNG icons)
// from HTML/SVG using the bundled fonts. Run: node tools/render_art.js
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');
const A = (p) => path.join(ROOT, 'assets', p);
const F = (p) => 'file://' + path.join(__dirname, 'fonts', p);
const svgData = (p) => 'data:image/svg+xml;base64,' + fs.readFileSync(A(p)).toString('base64');

const fonts = `
@font-face { font-family: BS; font-weight: 900; src: url(${F('BigShoulders-900.ttf')}); }
@font-face { font-family: BS; font-weight: 800; src: url(${F('BigShoulders-800.ttf')}); }
@font-face { font-family: AH; font-weight: 400; src: url(${F('Atkinson-400.ttf')}); }
@font-face { font-family: AH; font-weight: 700; src: url(${F('Atkinson-700.ttf')}); }
@font-face { font-family: PM; font-weight: 500; src: url(${F('PlexMono-500.ttf')}); }
* { box-sizing: border-box; margin: 0; }
.grid { background-color: #FFC21A;
  background-image: linear-gradient(rgba(21,22,27,.075) 1px, transparent 1px), linear-gradient(90deg, rgba(21,22,27,.075) 1px, transparent 1px);
  background-position: -1px -1px; }
`;

// Podcast cover: 1000px CSS square rendered at 3x = 3000x3000.
const cover = `<style>${fonts}
body { width: 1000px; height: 1000px; color: #15161B; font-family: AH; }
.c { position: relative; width: 1000px; height: 1000px; background-size: 62.5px 62.5px; padding: 84px 92px; display: flex; flex-direction: column; }
.top { font-family: PM; font-weight: 500; font-size: 30px; letter-spacing: .1em; text-transform: uppercase; display: flex; justify-content: space-between; }
.mark { margin-top: auto; width: 82%; }
.mark img { width: 100%; display: block; }
.exp { margin-top: 32px; font-family: BS; font-weight: 800; font-size: 58px; text-transform: uppercase; line-height: 1; letter-spacing: .01em; }
.exp b { font-weight: 900; background: #15161B; color: #FFC21A; padding: 0 6px; }
.hosts { margin-top: 26px; font-size: 30px; font-weight: 700; }
</style>
<div class="c grid">
  <div class="top"><span>A podcast for K-12 educators</span><span>Season 1</span></div>
  <div class="mark"><img src="${svgData('logo-stacked.svg')}"></div>
  <p class="exp"><b>B</b>iggest <b>O</b>pportunity<br>for <b>S</b>tudent <b>S</b>uccess</p>
  <p class="hosts">with Dr. Kartik Mangalam &amp; Dr. Matt Callison</p>
</div>`;

// Social share card: 1200x630 at 2x.
const og = `<style>${fonts}
body { width: 1200px; height: 630px; color: #15161B; font-family: AH; }
.o { width: 1200px; height: 630px; background-size: 30px 30px; display: grid; grid-template-columns: 1.35fr 1fr; gap: 48px; padding: 56px 64px; align-items: stretch; }
.l { display: flex; flex-direction: column; }
.l img { height: 74px; width: auto; align-self: flex-start; }
h1 { margin-top: auto; font-family: BS; font-weight: 900; font-size: 138px; line-height: .86; text-transform: uppercase; }
.when { margin-top: 26px; font-family: PM; font-weight: 500; font-size: 22px; letter-spacing: .08em; text-transform: uppercase; }
.r { background: #15161B; color: #F3F4EF; padding: 36px 36px; display: flex; flex-direction: column; justify-content: center; gap: 4px; box-shadow: 10px 10px 0 rgba(21,22,27,.18); }
.r p { font-family: PM; font-size: 18px; letter-spacing: .1em; text-transform: uppercase; color: #FFC21A; margin-bottom: 14px; }
.r div { font-family: BS; font-weight: 800; font-size: 54px; line-height: .98; text-transform: uppercase; }
.r .L { color: #FFC21A; font-weight: 900; }
.r .for { font-family: PM; font-size: 18px; letter-spacing: .1em; opacity: .7; padding: 4px 0; }
</style>
<div class="o grid">
  <div class="l">
    <img src="${svgData('logo.svg')}">
    <h1>The ceiling<br>is gone.</h1>
    <p class="when">New podcast · Episode 1 · Nov 15, 2026</p>
  </div>
  <div class="r">
    <p>K12 BOSS stands for</p>
    <div><span class="L">B</span>iggest</div>
    <div><span class="L">O</span>pportunity</div>
    <div class="for">for</div>
    <div><span class="L">S</span>tudent</div>
    <div><span class="L">S</span>uccess</div>
  </div>
</div>`;

const icon = (file, size) => `<style>body{margin:0;width:${size}px;height:${size}px}img{width:${size}px;height:${size}px;display:block}</style><img src="${svgData(file)}">`;

async function shot(browser, html, out, w, h, scale) {
  const page = await browser.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: scale });
  const tmp = path.join(__dirname, '.render.html');
  fs.writeFileSync(tmp, '<!doctype html>' + html);
  await page.goto('file://' + tmp);
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(150);
  await page.screenshot({ path: out, omitBackground: out.includes('favicon') });
  await page.close();
  fs.unlinkSync(tmp);
  console.log('wrote', path.relative(ROOT, out));
}

(async () => {
  const b = await chromium.launch();
  await shot(b, cover, A('cover-3000.png'), 1000, 1000, 3);
  await shot(b, cover, A('cover-1400.png'), 1000, 1000, 1.4);
  await shot(b, og, A('og-image.png'), 1200, 630, 1);
  await shot(b, icon('favicon.svg', 32), A('favicon-32.png'), 32, 32, 1);
  await shot(b, icon('mark.svg', 180), A('apple-touch-icon.png'), 180, 180, 1);
  await shot(b, icon('mark.svg', 512), A('icon-512.png'), 512, 512, 1);
  await b.close();
})();
