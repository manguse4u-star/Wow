// Plays the scene.json timeline frame by frame (the same shapes and effects that
// make_pptx.py writes into the PPTX) and exports:
//   - MP4 (1920x1080, 30 fps) via ffmpeg
//   - per-slide final-state PNGs at 3840x2160 and SVG vector files
//   - a storyboard of key frames
// Usage: node render.js <outdir> [--frames-only|--stills-only]
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');
const { chromium } = require('playwright');

const scene = JSON.parse(fs.readFileSync(process.env.SCENE_JSON || path.join(__dirname, 'scene.json'), 'utf8'));
const OUT = path.resolve(process.argv[2] || path.join(__dirname, '..', 'deliverables'));
const MODE = process.argv[3] || 'all';

// ------------------------------------------------------------------ in-page renderer
function pageCode() {
  const clamp = (x) => Math.max(0, Math.min(1, x));
  // PowerPoint accelerate/decelerate: trapezoidal velocity profile
  function ease(p, a, d) {
    if (!a && !d) return p;
    const v = 1 / (1 - a / 2 - d / 2);
    if (p < a) return (v * p * p) / (2 * a);
    if (p <= 1 - d) return v * (a / 2 + (p - a));
    return 1 - (v * (1 - p) * (1 - p)) / (2 * d);
  }
  let uid = 0;
  const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
  const rgba = (hex, a) => `#${hex}` + (a < 0.999 ? Math.round(a * 255).toString(16).padStart(2, '0') : '');

  function state(sh, t) {
    const st = { vis: true, op: 1, dx: 0, dy: 0, clip: null };
    const fx = sh.fx || [];
    const firstEntr = fx.filter((e) => ['fade_in', 'wipe_in', 'split_out'].includes(e.type))
      .sort((a, b) => a.s - b.s)[0];
    if (firstEntr && t < firstEntr.s) st.vis = false;
    const [bx, by, bw, bh] = sh.bbox;
    for (const e of fx) {
      if (t < e.s) continue;
      const p = clamp((t - e.s) / e.d);
      if (e.type === 'fade_in') st.op *= p;
      else if (e.type === 'fade_out') { if (p >= 1) st.vis = false; st.op *= 1 - p; }
      else if (e.type === 'move') { const q = ease(p, e.accel || 0, e.decel || 0); st.dx += e.dx * q; st.dy += e.dy * q; }
      else if (e.type === 'split_out') st.clip = [bx + bw / 2 - (bw / 2) * p - 1, by - 50, bw * p + 2, bh + 100];
      else if (e.type === 'wipe_in') {
        const m = 60; // generous margin so glows are not cut off once fully revealed
        if (p >= 1) st.clip = null;
        else if (e.dir === 'up') st.clip = [bx - m, by + bh * (1 - p), bw + 2 * m, bh * p + m];
        else if (e.dir === 'down') st.clip = [bx - m, by - m, bw + 2 * m, bh * p + m];
        else if (e.dir === 'left') st.clip = [bx + bw * (1 - p), by - m, bw * p + m, bh + 2 * m];
        else st.clip = [bx - m, by - m, bw * p + m, bh + 2 * m];
      }
    }
    return st;
  }

  function paint(f, defs, sh) {
    if (!f) return 'none';
    if (f.type === 'solid') return rgba(f.color, f.a);
    const id = 'g' + uid++;
    const r = (f.angle * Math.PI) / 180, c = Math.cos(r), s = Math.sin(r);
    defs.push(`<linearGradient id="${id}" x1="${0.5 - c / 2}" y1="${0.5 - s / 2}" x2="${0.5 + c / 2}" y2="${0.5 + s / 2}">` +
      f.stops.map(([p, col, a]) => `<stop offset="${p}" stop-color="#${col}" stop-opacity="${a}"/>`).join('') + '</linearGradient>');
    return `url(#${id})`;
  }

  function geom(sh, attrs) {
    if (sh.kind === 'poly') {
      const d = 'M' + sh.pts.map((p) => p.join(' ')).join(' L') + (sh.closed ? ' Z' : '');
      return `<path d="${d}" ${attrs}/>`;
    }
    if (sh.kind === 'rect') return `<rect x="${sh.x}" y="${sh.y}" width="${sh.w}" height="${sh.h}" rx="${sh.r || 0}" ${attrs}/>`;
    if (sh.kind === 'ellipse') return `<ellipse cx="${sh.x + sh.w / 2}" cy="${sh.y + sh.h / 2}" rx="${sh.w / 2}" ry="${sh.h / 2}" ${attrs}/>`;
    return '';
  }

  function drawShape(sh, defs) {
    if (sh.kind === 'group') {
      const inner = sh.children.map((c) => drawShape(c, defs)).join('');
      if (!sh.clip) return inner;
      const id = 'k' + uid++;
      defs.push(`<clipPath id="${id}"><path d="M${sh.clip.map((p) => p.join(' ')).join(' L')} Z"/></clipPath>`);
      return `<g clip-path="url(#${id})">${inner}</g>`;
    }
    if (sh.kind === 'text') {
      const x = sh.align === 'ctr' ? sh.x + sh.w / 2 : sh.align === 'l' ? sh.x : sh.x + sh.w;
      const anchor = sh.align === 'ctr' ? 'middle' : sh.align === 'l' ? 'start' : 'end';
      const ff = window.SCENE.font_css || "Arial, 'Liberation Sans', sans-serif";
      const ls = sh.ls ? ` letter-spacing="${sh.ls}"` : '';
      const op = sh.a !== undefined && sh.a < 1 ? ` fill-opacity="${sh.a}"` : '';
      return `<text x="${x}" y="${sh.y + sh.h / 2}" font-family="${ff}" font-size="${sh.size * 2}"${ls}${op} ` +
        `font-weight="${sh.weight || (sh.bold ? 700 : 400)}" fill="#${sh.color}" text-anchor="${anchor}" dominant-baseline="central">${esc(sh.text)}</text>`;
    }
    if (sh.kind === 'rich') {
      const px = sh.size * 2, lh = px * sh.line;
      let o = '';
      for (const para of sh.paras) {
        para.lines.forEach((ln, i) => {
          const y = sh.y + para.y + lh * (i + 0.5);
          const ff = window.SCENE.font_css || "Arial, 'Liberation Sans', sans-serif";
          o += `<text x="${sh.x}" y="${y}" font-family="${ff}" font-size="${px}" fill="#${sh.color}" dominant-baseline="central" xml:space="preserve">` +
            ln.map(([t, it, col]) => `<tspan${it ? ' font-style="italic"' : ''}${col ? ` fill="#${col}"` : ''}>${esc(t)}</tspan>`).join('') + '</text>';
        });
      }
      return o;
    }
    let out = '';
    if (sh.glow) {
      const id = 'f' + uid++;
      defs.push(`<filter id="${id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${sh.glow.r / 1.6}"/></filter>`);
      out += geom(sh, `fill="${sh.fill && sh.closed !== false ? '#' + sh.glow.color : 'none'}" stroke="#${sh.glow.color}" stroke-width="${sh.glow.r}" stroke-linejoin="round" opacity="${sh.glow.a}" filter="url(#${id})"`);
    }
    const fill = sh.closed === false ? 'none' : paint(sh.fill, defs, sh);
    let stroke = 'stroke="none"';
    if (sh.line) {
      const ln = sh.line;
      const dash = ln.dash ? `stroke-dasharray="${ln.w * 4} ${ln.w * 3}"` : '';
      stroke = `stroke="#${ln.color}" stroke-opacity="${ln.a}" stroke-width="${ln.w}" stroke-linecap="round" stroke-linejoin="round" ${dash}`;
    }
    let filt = '';
    if (sh.soft) {
      const id = 'f' + uid++;
      defs.push(`<filter id="${id}" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="${sh.soft / 2}"/></filter>`);
      filt = `filter="url(#${id})"`;
    }
    out += geom(sh, `fill="${fill}" ${stroke} ${filt}`);
    return out;
  }

  function drawSlide(slide, t, defs) {
    let out = '';
    for (const sh of slide.shapes) {
      const st = state(sh, t);
      if (!st.vis || st.op <= 0.001) continue;
      let inner = drawShape(sh, defs);
      if (st.clip) {
        const id = 'c' + uid++;
        const [x, y, w, h] = st.clip;
        defs.push(`<clipPath id="${id}"><rect x="${x}" y="${y}" width="${Math.max(0, w)}" height="${Math.max(0, h)}"/></clipPath>`);
        inner = `<g clip-path="url(#${id})">${inner}</g>`;
      }
      out += `<g transform="translate(${st.dx.toFixed(3)} ${st.dy.toFixed(3)})" opacity="${st.op.toFixed(4)}">${inner}</g>`;
    }
    return out;
  }

  // T = global time (s).  Returns the SVG for that instant.
  window.svgAt = function (T, onlySlide, localT) {
    // ids keep increasing so two frames can be composited without clashes
    const defs = [];
    let body = '';
    const S = window.SCENE.slides;
    if (onlySlide !== undefined) {
      body = drawSlide(onlySlide === 'E' ? window.SCENE.endcard : S[onlySlide], localT, defs);
    } else {
      let i = S.length - 1;
      for (let k = 0; k < S.length; k++) if (T < S[k].t0 + S[k].transition + S[k].adv) { i = k; break; }
      const sl = S[i];
      const local = T - sl.t0;
      if (local < sl.transition && i > 0) {
        const p = local / sl.transition; // smooth cross-fade (PowerPoint "Fade", not through black)
        body = drawSlide(S[i - 1], S[i - 1].adv, defs) +
          `<g opacity="${p.toFixed(4)}">${drawSlide(sl, 0, defs)}</g>`;
      } else body = drawSlide(sl, Math.max(0, local - sl.transition), defs);
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080"><defs>${defs.join('')}</defs>${body}</svg>`;
  };
  window.show = function (svg) { document.getElementById('stage').innerHTML = svg; };
}

async function main() {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch();
  const mk = async (scale) => {
    const page = await browser.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: scale });
    await page.setContent(`<html><body style="margin:0;background:#000;overflow:hidden"><div id="stage"></div></body></html>`);
    await page.evaluate((s) => { window.SCENE = s; }, scene);
    await page.addScriptTag({ content: '(' + pageCode.toString() + ')()' });
    return page;
  };
  const S = scene.slides;

  if (MODE === 'all' || MODE === '--stills-only') {
    const page = await mk(2);
    const dirP = path.join(OUT, 'slides_png'), dirS = path.join(OUT, 'assets_svg'), dirK = path.join(OUT, 'storyboard');
    for (const d of [dirP, dirS, dirK]) fs.mkdirSync(d, { recursive: true });
    for (let i = 0; i < S.length; i++) {
      const svg = await page.evaluate(([i, t]) => window.svgAt(0, i, t), [i, S[i].adv]);
      fs.writeFileSync(path.join(dirS, `slide${i + 1}_final_state.svg`), svg);
      await page.evaluate((s) => window.show(s), svg);
      await page.screenshot({ path: path.join(dirP, `slide${i + 1}_final_state.png`) });
    }
    {
      const svg = await page.evaluate(() => window.svgAt(0, 3, 4.3));
      await page.evaluate((s) => window.show(s), svg);
      await page.screenshot({ path: path.join(dirP, 'slide4_magnetic_stripes_state.png') });
    }
    // storyboard key frames every 1 s (1080p)
    const page1 = await mk(1);
    for (let T = 0.5; T < scene.total; T += 1.0) {
      const svg = await page1.evaluate((T) => window.svgAt(T), T);
      await page1.evaluate((s) => window.show(s), svg);
      await page1.screenshot({ path: path.join(dirK, `t${T.toFixed(1).padStart(4, '0')}s.png`) });
    }
  }

  if (MODE === 'all' || MODE === '--endcard') {
    const ec = scene.endcard;
    const page2 = await mk(2);
    fs.mkdirSync(path.join(OUT, 'slides_png'), { recursive: true });
    fs.mkdirSync(path.join(OUT, 'assets_svg'), { recursive: true });
    const svgE = await page2.evaluate((t) => window.svgAt(0, 'E', t), ec.adv);
    fs.writeFileSync(path.join(OUT, 'assets_svg', 'slide5_references_end_card.svg'), svgE);
    await page2.evaluate((s) => window.show(s), svgE);
    await page2.screenshot({ path: path.join(OUT, 'slides_png', 'slide5_references_end_card.png') });
    const page = await mk(1);
    const n = Math.round(ec.adv * scene.fps);
    fs.mkdirSync(path.join(OUT, 'video'), { recursive: true });
    const mp4 = path.join(OUT, 'video', 'Spreading_Rates_References_EndCard.mp4');
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(scene.fps), '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-r', String(scene.fps),
      '-movflags', '+faststart', mp4], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < n; f++) {
      const svg = await page.evaluate((t) => window.svgAt(0, 'E', t), f / scene.fps);
      await page.evaluate((s) => window.show(s), svg);
      const buf = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    console.log('wrote', mp4);
  }

  async function encode(page, n, svgFor, mp4) {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(scene.fps), '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-r', String(scene.fps),
      '-movflags', '+faststart', mp4], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < n; f++) {
      const svg = await page.evaluate(svgFor, f / scene.fps);
      await page.evaluate((s) => window.show(s), svg);
      const buf = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    console.log('wrote', mp4);
  }

  // Closing animation for the presentation (played AFTER the on-camera demo):
  // seafloor spreading -> magnetic stripes -> paper-strip model, then a short hold.
  // The references follow as an editable PowerPoint slide.
  if (MODE === 'all' || MODE === '--clip') {
    const page = await mk(1);
    const LEAD = 0.3, XF = 0.5, TAIL = 0.7;
    const A = S[1], B = S[3];
    const total = LEAD + A.adv + XF + B.adv + TAIL;
    scene.clip = { lead: LEAD, a: A.adv, xf: XF, b: B.adv, tail: TAIL, total };
    const n = Math.round(total * scene.fps);
    fs.mkdirSync(path.join(OUT, 'video'), { recursive: true });
    const clipFn = new Function('c', `
      const S = window.SCENE.slides, A = S[1], B = S[3];
      const L = ${LEAD}, X = ${XF};
      const mix = (svgA, svgB, p) => svgA.replace('</svg>', '').concat('<g opacity="' + p.toFixed(4) + '">' +
        svgB.replace(/^<svg[^>]*>/, '').replace('</svg>', '') + '</g></svg>');
      let t = c;
      if (t < L) return window.svgAt(0, 1, 0);
      t -= L;
      if (t < A.adv) return window.svgAt(0, 1, t);
      t -= A.adv;
      if (t < X) return mix(window.svgAt(0, 1, A.adv), window.svgAt(0, 3, 0), t / X);
      t -= X;
      return window.svgAt(0, 3, Math.min(t, B.adv));`);
    await encode(page, n, clipFn, path.join(OUT, 'video', 'Spreading_Rates_Closing_Animation.mp4'));
    const page2 = await mk(1);
    const svg0 = await page2.evaluate(() => window.svgAt(0, 1, 0));
    await page2.evaluate((s) => window.show(s), svg0);
    await page2.screenshot({ path: path.join(OUT, 'video', 'clip_poster.png') });
    fs.writeFileSync(path.join(__dirname, 'clip.json'), JSON.stringify(scene.clip));
  }

  // Generic sequence: scene.sequences[name] = {xf, segments:[{slide, dur}]}
  if (MODE === '--seq') {
    const name = process.argv[4];
    const sq = scene.sequences[name];
    const page = await mk(1);
    const total = sq.segments.reduce((a, s) => a + s.dur, 0) - sq.xf * (sq.segments.length - 1);
    const n = Math.round(total * scene.fps);
    fs.mkdirSync(path.join(OUT, 'video'), { recursive: true });
    const fn = new Function('c', `
      const SQ = ${JSON.stringify(sq)}, S = window.SCENE.slides;
      const mix = (a, b, p) => a.replace('</svg>', '').concat('<g opacity="' + p.toFixed(4) + '">' +
        b.replace(/^<svg[^>]*>/, '').replace('</svg>', '') + '</g></svg>');
      let start = 0;
      for (let i = 0; i < SQ.segments.length; i++) {
        const sg = SQ.segments[i], end = start + sg.dur;
        const nx = SQ.segments[i + 1];
        if (c < end - (nx ? SQ.xf : 0) || !nx) return window.svgAt(0, sg.slide, Math.min(c - start, sg.dur));
        if (c < end) {
          const p = (c - (end - SQ.xf)) / SQ.xf;
          return mix(window.svgAt(0, sg.slide, c - start), window.svgAt(0, nx.slide, c - (end - SQ.xf)), p);
        }
        start = end - SQ.xf;
      }`);
    await encode(page, n, fn, path.join(OUT, 'video', name + '.mp4'));
    const page2 = await mk(2);
    fs.mkdirSync(path.join(OUT, 'stills_v2'), { recursive: true });
    for (const [i, sg] of sq.segments.entries()) {
      const svg = await page2.evaluate(([k, t]) => window.svgAt(0, k, t), [sg.slide, sg.dur]);
      await page2.evaluate((s) => window.show(s), svg);
      await page2.screenshot({ path: path.join(OUT, 'stills_v2', `${name}_${i + 1}_${S[sg.slide].name.replace(/[^A-Za-z0-9]+/g, '_')}.png`) });
    }
  }

  if (MODE === 'all' || MODE === '--frames-only') {
    const page = await mk(1);
    const n = Math.round(scene.total * scene.fps);
    const mp4 = path.join(OUT, 'Spreading_Rates_PPT_25sec.mp4');
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(scene.fps), '-i', '-',
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '15', '-pix_fmt', 'yuv420p', '-r', String(scene.fps),
      '-movflags', '+faststart', mp4], { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = 0; f < n; f++) {
      const svg = await page.evaluate((T) => window.svgAt(T), f / scene.fps);
      await page.evaluate((s) => window.show(s), svg);
      const buf = await page.screenshot({ type: 'png' });
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
      if (f % 60 === 0) process.stdout.write(`frame ${f}/${n}\n`);
    }
    ff.stdin.end();
    await new Promise((r) => ff.on('close', r));
    console.log('wrote', mp4);
  }
  await browser.close();
}
main().catch((e) => { console.error(e); process.exit(1); });
