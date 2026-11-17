// node svg2png.js in.svg out.png [scale]
const fs = require('fs');
const { chromium } = require('playwright');
(async () => {
  const [inp, out, scale] = process.argv.slice(2);
  const svg = fs.readFileSync(inp, 'utf8');
  const w = +svg.match(/width="(\d+)"/)[1], h = +svg.match(/height="(\d+)"/)[1];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: w, height: h }, deviceScaleFactor: +(scale || 2) });
  await p.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await p.screenshot({ path: out, clip: { x: 0, y: 0, width: w, height: h } });
  await b.close();
})();
