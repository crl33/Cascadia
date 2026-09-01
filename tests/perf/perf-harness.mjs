#!/usr/bin/env node
/**
 * Real-GPU performance harness for the web app (docs/research/cesium-cinematic-performance-2026-09-01.md
 * §7/§9.1; plan row 11 / step 1.1; exit test E1.1).
 *
 * Not a Playwright Test spec. One browser per run, explicit GPU selection, a JSON artifact and a
 * short table. It REFUSES to measure on SwiftShader: a number from the software renderer is not a
 * performance number and is never cited (tests/perf/README.md).
 *
 *   node tests/perf/perf-harness.mjs <url> [--gpu=low-power|high-performance] [--viewport=WxH] [--dpr=N]
 *        [--mode=newheadless|headed] [--runs=5] [--warmup=1] [--label=before] [--msaa=off]
 *        [--terrain=<origin>/terrain/v1] [--out=<dir>] [--scenarios=a,b,c] [--probe] [--browser=chromium|shell]
 *
 * Mechanism (doc §2, verified on the owner's machine): `channel: 'chromium'` selects the full
 * Chromium binary, which initialises ANGLE-Metal on the hardware GPU even with `--headless`; the
 * separate `chromium-headless-shell` binary defaults itself to SwiftShader. The WebGL
 * `powerPreference` attribute is injected by wrapping `HTMLCanvasElement.prototype.getContext`
 * (Cesium asks for 'high-performance' unless told otherwise) — `--gpu=low-power` is the switch that
 * turns a dual-GPU workstation into the "ordinary laptop" of the brief.
 *
 * Only public app hooks are used: `[data-testid=scene][data-scene-state]`, `[data-tiles-pending]`
 * (stamped on `.scene-canvas` by the SceneController), `data-testid=loading-veil`, `search-input`,
 * `search-result`, `flight-state[data-flight-state]`, `timeline-scrubber`, `snap-to-now`.
 * `window.__cascadiaScene` exists only in dev builds and is deliberately NOT used.
 *
 * `playwright` is resolved from apps/web/node_modules (the only install in this repo); the
 * script runs from any cwd.
 */
import { createRequire } from 'node:module';
import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, '../..');
const webDir = resolve(repoRoot, 'apps/web');

// ---------------------------------------------------------------------------------------------
// Arguments
// ---------------------------------------------------------------------------------------------
const argv = process.argv.slice(2);
const flags = {};
let positionalUrl = null;
for (const a of argv) {
  if (a.startsWith('--')) {
    const eq = a.indexOf('=');
    if (eq === -1) flags[a.slice(2)] = true;
    else flags[a.slice(2, eq)] = a.slice(eq + 1);
  } else if (positionalUrl === null) positionalUrl = a;
}
if (flags.help || flags.h) {
  console.log(`usage: node tests/perf/perf-harness.mjs <url> [options]
  --gpu=low-power|high-performance   WebGL powerPreference injected into every context (default low-power)
  --viewport=WxH                     CSS viewport (default 1280x800)
  --dpr=N                            deviceScaleFactor (default 1)
  --mode=newheadless|headed          new-headless Chromium is the reference mode (default newheadless)
  --runs=N                           measured runs; medians are taken across them (default 5)
  --warmup=N                         discarded runs before the measured ones (default 1)
  --label=NAME                       before|after|… stamped into the artifact name (default run)
  --msaa=off                         A/B lever: antialias:false + single-sample every MS renderbuffer
  --terrain=<origin>/terrain/v1      proxy **/terrain/v1/** same-origin to this origin (R2 sends no CORS)
  --out=DIR                          artifact directory (default tests/e2e/.results/perf, gitignored)
  --scenarios=a,b,c                  subset of: ${''}idle-home,zoom-in,pan,zoom-out,idle-final,basin-flight,scrub,idle-end
  --probe                            only launch, read UNMASKED_RENDERER on a blank WebGL page, print, exit
  --browser=chromium|shell           shell = the headless shell (SwiftShader) — allowed ONLY with --probe,
                                     to demonstrate the refusal; never for measurement`);
  process.exit(0);
}

const url = String(flags.url ?? positionalUrl ?? '');
const gpu = String(flags.gpu ?? 'low-power');
if (!['low-power', 'high-performance'].includes(gpu)) die(`--gpu must be low-power or high-performance, got ${gpu}`);
const [vw, vh] = String(flags.viewport ?? '1280x800').split('x').map((n) => Number(n));
if (!(vw > 0 && vh > 0)) die(`--viewport must be WxH, got ${flags.viewport}`);
const dpr = Number(flags.dpr ?? 1);
const mode = String(flags.mode ?? 'newheadless');
if (!['newheadless', 'headed'].includes(mode)) die(`--mode must be newheadless or headed, got ${mode}`);
const runs = Number(flags.runs ?? 5);
const warmup = Number(flags.warmup ?? 1);
const label = String(flags.label ?? 'run');
const msaaOff = String(flags.msaa ?? 'on') === 'off';
const terrain = flags.terrain ? String(flags.terrain).replace(/\/$/, '') : null;
const outDir = resolve(process.cwd(), String(flags.out ?? resolve(repoRoot, 'tests/e2e/.results/perf')));
const probeOnly = Boolean(flags.probe);
const browserKind = String(flags.browser ?? 'chromium');
if (!['chromium', 'shell'].includes(browserKind)) die(`--browser must be chromium or shell, got ${browserKind}`);
if (browserKind === 'shell' && !probeOnly) die('--browser=shell is a demonstration of the refusal and is only allowed with --probe');

const ALL_SCENARIOS = ['idle-home', 'zoom-in', 'pan', 'zoom-out', 'idle-final', 'basin-flight', 'scrub', 'idle-end'];
const scenarios = flags.scenarios ? String(flags.scenarios).split(',').map((s) => s.trim()).filter(Boolean) : ALL_SCENARIOS;
for (const s of scenarios) if (!ALL_SCENARIOS.includes(s)) die(`unknown scenario ${s}; known: ${ALL_SCENARIOS.join(',')}`);
if (!probeOnly && !url) die('an app URL is required (positional or --url=), e.g. http://localhost:5177');

// ---------------------------------------------------------------------------------------------
// Playwright, resolved from apps/web (the harness lives in tests/perf; Node resolves from the file)
// ---------------------------------------------------------------------------------------------
let chromium;
try {
  const require = createRequire(resolve(webDir, 'package.json'));
  const mod = await import(pathToFileURL(require.resolve('playwright')).href);
  chromium = mod.chromium ?? mod.default?.chromium; // playwright is CJS: the namespace carries it on `default`
  if (!chromium) throw new Error('playwright loaded but exposes no `chromium`');
} catch (error) {
  die(`could not load playwright from ${webDir}/node_modules — run \`npm ci\` in apps/web (${error?.message ?? error})`);
}

// ---------------------------------------------------------------------------------------------
// The in-page instrumentation: installed before the app boots; nothing in apps/web/src changes.
// ---------------------------------------------------------------------------------------------
function initScript({ forcedPower, msaaOff }) {
  const P = (window.__perf = {
    frames: [], marks: [], loaf: [], longtasks: [], gl: null, ext: null, renderer: null, vendor: null,
    drawCalls: 0, globeDefines: new Set(), contexts: 0, timerQuery: false,
  });
  const getContext = HTMLCanvasElement.prototype.getContext;
  HTMLCanvasElement.prototype.getContext = function (type, attrs) {
    if (type !== 'webgl2' && type !== 'webgl') return getContext.call(this, type, attrs);
    attrs = { ...(attrs ?? {}), powerPreference: forcedPower }; // integrated vs discrete GPU
    if (msaaOff) attrs.antialias = false;
    const gl = getContext.call(this, type, attrs);
    if (!gl) return gl;
    P.contexts += 1;
    if (msaaOff) { // A/B lever: single-sample every multisampled renderbuffer
      const og = gl.getParameter.bind(gl);
      gl.getParameter = (p) => (p === gl.MAX_SAMPLES ? 0 : og(p));
      gl.renderbufferStorageMultisample = (target, _s, fmt, w, h) => gl.renderbufferStorage(target, fmt, w, h);
    }
    if (!P.gl) {
      P.gl = gl;
      P.ext = type === 'webgl2' ? gl.getExtension('EXT_disjoint_timer_query_webgl2') : null;
      P.timerQuery = Boolean(P.ext);
      const dbg = gl.getExtension('WEBGL_debug_renderer_info');
      P.renderer = dbg ? gl.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
      P.vendor = dbg ? gl.getParameter(dbg.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR);
      const ss = gl.shaderSource.bind(gl);
      gl.shaderSource = (sh, src) => {
        if (src.includes('u_dayTextures')) for (const m of src.matchAll(/^#define\s+(\w+)/gm)) P.globeDefines.add(m[1]);
        return ss(sh, src);
      };
      for (const m of ['drawElements', 'drawArrays', 'drawElementsInstanced', 'drawArraysInstanced']) {
        const o = gl[m];
        if (typeof o !== 'function') continue;
        gl[m] = function (...a) { P.drawCalls += 1; return o.apply(this, a); };
      }
    }
    return gl;
  };
  // Per rAF callback: {t, cpuMs, draws, gpuMs}. One TIME_ELAPSED query at a time per context
  // (the extension forbids nesting); resolved asynchronously; discarded on GPU_DISJOINT.
  const pending = [];
  let active = false;
  const raf = window.requestAnimationFrame;
  window.requestAnimationFrame = (cb) => raf.call(window, (t) => {
    const gl = P.gl, ext = P.ext;
    const rec = { t, cpuMs: 0, gpuMs: null, draws: 0 };
    const d0 = P.drawCalls;
    let q = null;
    if (gl && ext && !active) { q = gl.createQuery(); gl.beginQuery(ext.TIME_ELAPSED_EXT, q); active = true; }
    const c0 = performance.now();
    try { cb(t); } finally {
      rec.cpuMs = performance.now() - c0;
      rec.draws = P.drawCalls - d0;
      if (q) { gl.endQuery(ext.TIME_ELAPSED_EXT); active = false; pending.push({ q, rec }); }
      P.frames.push(rec);
    }
  });
  setInterval(() => {
    const gl = P.gl, ext = P.ext;
    if (!gl || !ext) return;
    const disjoint = gl.getParameter(ext.GPU_DISJOINT_EXT);
    while (pending.length && gl.getQueryParameter(pending[0].q, gl.QUERY_RESULT_AVAILABLE)) {
      const { q, rec } = pending.shift();
      rec.gpuMs = disjoint ? null : gl.getQueryParameter(q, gl.QUERY_RESULT) / 1e6;
      gl.deleteQuery(q);
    }
  }, 50);
  try {
    new PerformanceObserver((l) => l.getEntries().forEach((e) => P.loaf.push({ t: e.startTime, d: e.duration, blocking: e.blockingDuration ?? 0 })))
      .observe({ type: 'long-animation-frame', buffered: true });
  } catch { /* observer type unsupported: loaf stays empty and is reported as n/a */ }
  try {
    new PerformanceObserver((l) => l.getEntries().forEach((e) => P.longtasks.push({ t: e.startTime, d: e.duration })))
      .observe({ type: 'longtask', buffered: true });
  } catch { /* same */ }
  P.mark = (name) => { P.marks.push({ name, t: performance.now() }); };
}

// ---------------------------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------------------------
function die(message, code = 1) { console.error(`perf-harness: ${message}`); process.exit(code); }
const fmt = (v, d = 1) => (v === null || v === undefined || Number.isNaN(v) ? 'n/a' : Number(v).toFixed(d));
function percentile(sorted, p) {
  if (!sorted.length) return null;
  const idx = Math.min(sorted.length - 1, Math.max(0, Math.ceil((p / 100) * sorted.length) - 1));
  return sorted[idx];
}
function stats(values) {
  const v = values.filter((x) => typeof x === 'number' && Number.isFinite(x)).sort((a, b) => a - b);
  return v.length ? { n: v.length, p50: percentile(v, 50), p95: percentile(v, 95), max: v[v.length - 1] } : { n: 0, p50: null, p95: null, max: null };
}
function median(values) {
  const v = values.filter((x) => typeof x === 'number' && Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return null;
  const mid = Math.floor(v.length / 2);
  return v.length % 2 ? v[mid] : (v[mid - 1] + v[mid]) / 2;
}
const IMAGERY_RE = /basemap\.nationalmap\.gov|tile\.openstreetmap\.org|\/terrain\/v1\/|\/tile\/\d+\/\d+\/\d+|\/tiles\/|\/MapServer\/|\.(png|jpe?g|webp|terrain)(\?|$)/i;
function isSwiftShader(...strings) { return strings.some((s) => typeof s === 'string' && /swiftshader/i.test(s)); }

async function launch() {
  if (browserKind === 'shell') return chromium.launch({ headless: true }); // the headless shell: SwiftShader by construction
  return chromium.launch(mode === 'headed' ? { headless: false, channel: 'chromium' } : { headless: true, channel: 'chromium' });
}

async function systemInfo(browser) {
  try {
    const session = await browser.newBrowserCDPSession();
    const info = await session.send('SystemInfo.getInfo');
    await session.detach().catch(() => {});
    return { commandLine: info.commandLine, devices: info.gpu?.devices ?? [], auxAttributes: info.gpu?.auxAttributes ?? null };
  } catch (error) {
    return { commandLine: null, devices: [], error: String(error?.message ?? error) };
  }
}

/** The refusal. Every measurement path goes through here before a single number is recorded. */
function refuseIfSoftware(renderer, sys) {
  const cmd = sys?.commandLine ?? '';
  const bad = isSwiftShader(renderer) || /use-angle=swiftshader/i.test(cmd);
  if (bad) {
    console.error('');
    console.error('perf-harness: REFUSING TO MEASURE — the WebGL renderer is software (SwiftShader).');
    console.error(`  UNMASKED_RENDERER: ${renderer}`);
    if (cmd) console.error(`  browser command line: ${cmd}`);
    console.error('  SwiftShader timings are never cited. Use `channel: \'chromium\'` (the full Chromium download,');
    console.error('  `npx playwright install chromium`, not --only-shell) so ANGLE-Metal reaches the hardware GPU.');
    process.exit(2);
  }
}

// ---------------------------------------------------------------------------------------------
// --probe: launch, create a WebGL2 context on a blank page, print the renderer, apply the refusal
// ---------------------------------------------------------------------------------------------
if (probeOnly) {
  const browser = await launch();
  const context = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: dpr });
  const page = await context.newPage();
  await page.addInitScript(initScript, { forcedPower: gpu, msaaOff });
  // Init scripts run on navigation (setContent does not navigate): a data: URL is the blank page.
  await page.goto('data:text/html,<canvas id="c" width="64" height="64"></canvas>');
  const probe = await page.evaluate(() => {
    const gl = document.getElementById('c').getContext('webgl2', { powerPreference: 'high-performance' });
    const P = window.__perf;
    return {
      renderer: P.renderer, vendor: P.vendor, timerQuery: P.timerQuery,
      maxSamples: gl ? gl.getParameter(gl.MAX_SAMPLES) : null,
      attrs: gl ? gl.getContextAttributes() : null,
    };
  });
  const sys = await systemInfo(browser);
  await browser.close();
  console.log(`browser        : ${browserKind === 'shell' ? 'chromium-headless-shell' : `chromium (channel: 'chromium', ${mode})`}`);
  console.log(`command line   : ${sys.commandLine ?? 'n/a'}`);
  console.log(`powerPreference: ${probe.attrs?.powerPreference ?? 'n/a'} (requested ${gpu})`);
  console.log(`UNMASKED_VENDOR: ${probe.vendor}`);
  console.log(`UNMASKED_RENDERER: ${probe.renderer}`);
  console.log(`MAX_SAMPLES    : ${probe.maxSamples}`);
  console.log(`EXT_disjoint_timer_query_webgl2: ${probe.timerQuery ? 'present' : 'absent (GPU time will be n/a)'}`);
  const devices = sys.devices
    .map((d) => `${d.vendorString || d.vendorId || ''} ${d.deviceString || d.deviceId || ''}`.trim() + (d.active ? ' [active]' : ''))
    .filter((s) => s.trim() && s.trim() !== '[active]');
  console.log(`GPU devices    : ${devices.length ? devices.join(' | ') : 'n/a (SystemInfo.getInfo reported no device strings)'}`);
  refuseIfSoftware(probe.renderer, sys);
  console.log('probe OK: hardware renderer; measurement would proceed.');
  process.exit(0);
}

// ---------------------------------------------------------------------------------------------
// One measured run: boot → scenarios → collect
// ---------------------------------------------------------------------------------------------
async function runOnce(runIndex) {
  const browser = await launch();
  const sys = await systemInfo(browser);
  const context = await browser.newContext({ viewport: { width: vw, height: vh }, deviceScaleFactor: dpr });
  const page = await context.newPage();
  await page.addInitScript(initScript, { forcedPower: gpu, msaaOff });

  if (terrain) {
    await page.route('**/terrain/v1/**', async (route) => { // same-origin proxy of the terrain origin
      const u = new URL(route.request().url());
      const target = terrain + u.pathname.replace(/^.*\/terrain\/v1/, '') + u.search;
      try { await route.fulfill({ response: await route.fetch({ url: target }) }); } catch { await route.abort(); }
    });
  }

  // Requests are timestamped in Node time; phases carry Node timestamps too, so per-phase
  // request counts need no clock mapping into the page.
  const requestLog = [];
  const failed = {};
  const nonOk = {};
  let viteDev = false;
  page.on('request', (r) => {
    const u = r.url();
    let host = 'other';
    try { host = new URL(u).host; } catch { /* data:/blob: */ }
    if (/\/@vite\/client/.test(u)) viteDev = true;
    requestLog.push({ host, imagery: IMAGERY_RE.test(u), t: Date.now() });
  });
  page.on('requestfailed', (r) => {
    let host = 'other';
    try { host = new URL(r.url()).host; } catch { /* ignore */ }
    failed[host] = (failed[host] ?? 0) + 1;
  });
  page.on('response', (r) => {
    if (r.status() >= 400) {
      let host = 'other';
      try { host = new URL(r.url()).host; } catch { /* ignore */ }
      nonOk[host] = (nonOk[host] ?? 0) + 1;
    }
  });

  const cdp = await context.newCDPSession(page);
  await cdp.send('Performance.enable');
  const heap = async () => {
    const { metrics } = await cdp.send('Performance.getMetrics');
    const g = (n) => metrics.find((m) => m.name === n)?.value;
    return { usedMB: g('JSHeapUsedSize') / 1048576, totalMB: g('JSHeapTotalSize') / 1048576 };
  };

  const phases = []; // {name, nodeT}
  const mark = async (name) => {
    phases.push({ name, nodeT: Date.now() });
    await page.evaluate((n) => window.__perf.mark(n), name);
  };
  const tilesPending = () => page.evaluate(() => Number(document.querySelector('[data-tiles-pending]')?.getAttribute('data-tiles-pending') ?? '0'));
  const settled = async (name, maxMs = 20000) => {
    await mark(`${name}:settle-start`);
    const t0 = Date.now();
    let zero = null;
    while (Date.now() - t0 < maxMs) {
      const p = await tilesPending();
      if (p === 0) { zero ??= Date.now(); if (Date.now() - zero > 800) break; } else zero = null;
      await page.waitForTimeout(100);
    }
    await mark(`${name}:settled`);
  };

  // Boot. The init script installs on navigation, so marks come AFTER goto.
  const tBoot0 = Date.now();
  await page.goto(url, { waitUntil: 'load' });
  await mark('boot');
  const scene = page.getByTestId('scene');
  await scene.waitFor({ timeout: 30000 });
  await page.waitForFunction(() => {
    const s = document.querySelector('[data-testid="scene"]')?.getAttribute('data-scene-state');
    return s === 'ready' || s === 'degraded' || s === 'unavailable';
  }, undefined, { timeout: 60000 });
  const sceneState = await scene.getAttribute('data-scene-state');
  if (sceneState === 'unavailable') { await browser.close(); die('the renderer reported data-scene-state=unavailable (no WebGL); nothing to measure'); }

  // The refusal, before any number is kept.
  const renderer = await page.evaluate(() => window.__perf.renderer);
  if (!renderer) { await browser.close(); die('no WebGL context was created by the app; cannot identify the renderer'); }
  refuseIfSoftware(renderer, sys);

  await page.getByTestId('loading-veil').waitFor({ state: 'detached', timeout: 90000 });
  await settled('boot');
  const bootMs = Date.now() - tBoot0;
  const heapAfterBoot = await heap();

  const cx = vw / 2, cy = vh / 2;
  const has = (s) => scenarios.includes(s);

  if (has('idle-home')) { await mark('idle-home'); await page.waitForTimeout(3000); }
  await page.mouse.move(cx, cy);
  if (has('zoom-in')) {
    await mark('zoom-in');
    for (let i = 0; i < 14; i++) { await page.mouse.wheel(0, -240); await page.waitForTimeout(60); }
    await settled('zoom-in');
  }
  if (has('pan')) {
    await mark('pan');
    await page.mouse.down();
    for (let i = 1; i <= 24; i++) { await page.mouse.move(cx + i * 12, cy + i * 6); await page.waitForTimeout(16); }
    await page.mouse.up();
    await settled('pan');
  }
  if (has('zoom-out')) {
    await mark('zoom-out');
    for (let i = 0; i < 14; i++) { await page.mouse.wheel(0, 240); await page.waitForTimeout(60); }
    await settled('zoom-out');
  }
  if (has('idle-final')) { await mark('idle-final'); await page.waitForTimeout(3000); }

  let flightOk = null;
  if (has('basin-flight')) {
    // orbital → basin:skagit, driven the way skagit-flight.spec.ts drives it: search, click the
    // first result, wait for the camera to report settled, then for the ground to settle.
    await mark('basin-flight');
    try {
      await page.getByTestId('search-input').fill('Skagit');
      const first = page.getByTestId('search-result').first();
      await first.waitFor({ timeout: 10000 });
      await first.click();
      await page.waitForFunction(
        () => document.querySelector('[data-testid="flight-state"]')?.getAttribute('data-flight-state') === 'settled',
        undefined, { timeout: 20000 },
      );
      flightOk = true;
    } catch (error) {
      flightOk = false;
      console.warn(`perf-harness: basin-flight did not reach settled (${error?.message?.split('\n')[0] ?? error})`);
    }
    await settled('basin-flight');
  }

  let scrubOk = null;
  if (has('scrub')) {
    // Five ArrowLeft steps into the past (as timeline-scrub.spec.ts), a beat between steps so
    // each knowledge-time commit lands, then snap-to-now.
    await mark('scrub');
    try {
      const scrubber = page.getByTestId('timeline-scrubber');
      await scrubber.waitFor({ timeout: 10000 });
      await scrubber.focus();
      for (let step = 0; step < 5; step += 1) { await scrubber.press('ArrowLeft'); await page.waitForTimeout(250); }
      await page.waitForTimeout(1500);
      await page.getByTestId('snap-to-now').click({ timeout: 5000 });
      scrubOk = true;
    } catch (error) {
      scrubOk = false;
      console.warn(`perf-harness: scrub could not be driven (${error?.message?.split('\n')[0] ?? error})`);
    }
    await settled('scrub');
  }
  if (has('idle-end')) { await mark('idle-end'); await page.waitForTimeout(3000); }
  await mark('end');
  await page.waitForTimeout(300); // let the last timer queries resolve

  const raw = await page.evaluate(() => {
    const P = window.__perf;
    const canvas = document.querySelector('.scene-canvas canvas') ?? document.querySelector('canvas');
    return {
      frames: P.frames, marks: P.marks, loaf: P.loaf, longtasks: P.longtasks,
      renderer: P.renderer, vendor: P.vendor, timerQuery: P.timerQuery, contexts: P.contexts,
      defines: [...P.globeDefines].sort(),
      canvas: canvas ? { width: canvas.width, height: canvas.height, cssWidth: canvas.clientWidth, cssHeight: canvas.clientHeight } : null,
      drawingBuffer: P.gl ? { width: P.gl.drawingBufferWidth, height: P.gl.drawingBufferHeight } : null,
      devicePixelRatio: window.devicePixelRatio,
      crossOriginIsolated: self.crossOriginIsolated,
    };
  });
  const heapEnd = await heap();
  const uaMem = await page.evaluate(async () => {
    try { return self.crossOriginIsolated ? (await performance.measureUserAgentSpecificMemory()).bytes : null; } catch { return null; }
  });
  await browser.close();

  // Reduce: one record per rAF frame (callbacks sharing a timestamp are one frame), then slice
  // by the page-time marks; requests are sliced by Node-time phases.
  const byT = new Map();
  for (const f of raw.frames) {
    const r = byT.get(f.t) ?? { t: f.t, cpuMs: 0, draws: 0, gpuMs: null };
    r.cpuMs += f.cpuMs; r.draws += f.draws;
    if (f.gpuMs !== null) r.gpuMs = (r.gpuMs ?? 0) + f.gpuMs;
    byT.set(f.t, r);
  }
  const frames = [...byT.values()].sort((a, b) => a.t - b.t);
  const markAt = (name) => raw.marks.find((m) => m.name === name)?.t ?? null;
  const nodeAt = (name) => phases.find((p) => p.name === name)?.nodeT ?? null;
  // Phase windows: from a scenario mark to the next mark that is not its own settle-start.
  const orderedMarks = raw.marks.map((m) => m.name);
  const phaseWindow = (name) => {
    const start = markAt(name);
    if (start === null) return null;
    const i = orderedMarks.indexOf(name);
    const next = orderedMarks.slice(i + 1).find((n) => n !== `${name}:settle-start`);
    const end = next ? markAt(next) : raw.marks[raw.marks.length - 1].t;
    const nStart = nodeAt(name);
    const nNext = next ? nodeAt(next) : phases[phases.length - 1].nodeT;
    return { start, end, nStart, nEnd: nNext };
  };
  const phaseReport = {};
  for (const name of ['boot', ...scenarios]) {
    const w = phaseWindow(name);
    if (!w) continue;
    const inWin = frames.filter((f) => f.t >= w.start && f.t < w.end);
    const deltas = inWin.slice(1).map((f, i) => f.t - inWin[i].t);
    const rendered = inWin.filter((f) => f.draws > 0);
    const gpu = inWin.map((f) => f.gpuMs).filter((g) => g !== null);
    const loaf = raw.loaf.filter((l) => l.t >= w.start && l.t < w.end);
    const reqs = requestLog.filter((r) => r.t >= w.nStart && r.t < w.nEnd);
    const perHost = {};
    for (const r of reqs) perHost[r.host] = (perHost[r.host] ?? 0) + 1;
    phaseReport[name] = {
      durationMs: w.end - w.start,
      frames: inWin.length,
      rendered: rendered.length,
      rafDeltaMs: stats(deltas),
      cpuCbMs: stats(inWin.map((f) => f.cpuMs)),
      gpuMs: raw.timerQuery ? stats(gpu) : null,
      drawCalls: { total: inWin.reduce((s, f) => s + f.draws, 0), perFrameP50: stats(rendered.map((f) => f.draws)).p50 },
      loaf: { n: loaf.length, maxMs: loaf.length ? Math.max(...loaf.map((l) => l.d)) : 0, blockingMs: loaf.reduce((s, l) => s + l.blocking, 0) },
      requests: { total: reqs.length, imagery: reqs.filter((r) => r.imagery).length, perHost },
    };
  }
  const requestsByHost = {};
  for (const r of requestLog) requestsByHost[r.host] = (requestsByHost[r.host] ?? 0) + 1;

  return {
    run: runIndex,
    info: {
      renderer: raw.renderer, vendor: raw.vendor, timerQuery: raw.timerQuery, contexts: raw.contexts, defines: raw.defines,
      canvas: raw.canvas, drawingBuffer: raw.drawingBuffer, devicePixelRatio: raw.devicePixelRatio,
      crossOriginIsolated: raw.crossOriginIsolated, sceneState, server: viteDev ? 'vite-dev' : 'static/preview',
      commandLine: sys.commandLine, gpuDevices: sys.devices,
    },
    bootMs, flightOk, scrubOk,
    heapAfterBoot, heapEnd, uaMemBytes: uaMem,
    requestsByHost, failedByHost: failed, nonOkByHost: nonOk,
    imageryRequests: requestLog.filter((r) => r.imagery).length,
    phases: phaseReport,
  };
}

// ---------------------------------------------------------------------------------------------
// Protocol: warm-up runs discarded, medians across the measured runs
// ---------------------------------------------------------------------------------------------
mkdirSync(outDir, { recursive: true });
const stamp = `${label}.${gpu}.${mode}.${vw}x${vh}@${dpr}${msaaOff ? '.msaa-off' : ''}`;
console.log(`perf-harness: ${url}  gpu=${gpu}  ${vw}x${vh}@${dpr}  mode=${mode}  runs=${runs} (+${warmup} warm-up)  msaa=${msaaOff ? 'off' : 'on'}  scenarios=${scenarios.join(',')}`);

const measured = [];
for (let i = 0; i < warmup + runs; i++) {
  const isWarm = i < warmup;
  const t0 = Date.now();
  const result = await runOnce(i);
  const secs = ((Date.now() - t0) / 1000).toFixed(0);
  if (i === 0) {
    console.log(`UNMASKED_RENDERER: ${result.info.renderer}`);
    console.log(`GPU timer query  : ${result.info.timerQuery ? 'EXT_disjoint_timer_query_webgl2 present' : 'n/a (extension absent)'}`);
    console.log(`drawing buffer   : ${result.info.drawingBuffer ? `${result.info.drawingBuffer.width}x${result.info.drawingBuffer.height}` : 'n/a'} (canvas ${result.info.canvas ? `${result.info.canvas.width}x${result.info.canvas.height}, CSS ${result.info.canvas.cssWidth}x${result.info.canvas.cssHeight}` : 'n/a'}, DPR ${result.info.devicePixelRatio})`);
    console.log(`server           : ${result.info.server}${result.info.server === 'vite-dev' ? ' (unminified modules — CPU numbers are not the production build’s)' : ''}`);
    console.log(`globe defines    : ${result.info.defines.join(' ') || 'none captured'}`);
    const failedTotal = Object.values(result.failedByHost).reduce((s, n) => s + n, 0);
    if (failedTotal) console.warn(`WARNING: ${failedTotal} request(s) failed (${JSON.stringify(result.failedByHost)}) — a CORS refusal from the API silently removes every vector layer and makes the scene look cheaper (doc §7).`);
  }
  console.log(`  run ${i + 1}/${warmup + runs}${isWarm ? ' (warm-up, discarded)' : ''}: ${secs}s, boot ${result.bootMs} ms, heap ${fmt(result.heapEnd.usedMB, 0)} MB, imagery requests ${result.imageryRequests}`);
  if (!isWarm) {
    measured.push(result);
    writeFileSync(resolve(outDir, `${stamp}.run${measured.length}.json`), JSON.stringify(result, null, 2));
  }
}

// Medians per phase per metric.
const phaseNames = ['boot', ...scenarios].filter((n) => measured.some((r) => r.phases[n]));
const med = (pick) => median(measured.map((r) => { try { return pick(r); } catch { return null; } }));
const summary = {
  label, url, gpu, mode, viewport: { width: vw, height: vh, dpr }, msaa: msaaOff ? 'off' : 'on', terrainProxy: terrain,
  runs: measured.length, warmupDiscarded: warmup, measuredAt: new Date().toISOString(),
  info: measured[0].info,
  medians: {
    bootMs: med((r) => r.bootMs),
    heapAfterBootMB: med((r) => r.heapAfterBoot.usedMB),
    heapEndMB: med((r) => r.heapEnd.usedMB),
    uaMemMB: med((r) => (r.uaMemBytes === null ? null : r.uaMemBytes / 1048576)),
    imageryRequests: med((r) => r.imageryRequests),
    phases: Object.fromEntries(phaseNames.map((n) => [n, {
      frames: med((r) => r.phases[n].frames),
      rendered: med((r) => r.phases[n].rendered),
      rafDeltaP50: med((r) => r.phases[n].rafDeltaMs.p50),
      rafDeltaP95: med((r) => r.phases[n].rafDeltaMs.p95),
      rafDeltaMax: med((r) => r.phases[n].rafDeltaMs.max),
      cpuCbP50: med((r) => r.phases[n].cpuCbMs.p50),
      cpuCbP95: med((r) => r.phases[n].cpuCbMs.p95),
      gpuP50: med((r) => r.phases[n].gpuMs?.p50),
      gpuP95: med((r) => r.phases[n].gpuMs?.p95),
      gpuN: med((r) => r.phases[n].gpuMs?.n),
      drawCallsP50: med((r) => r.phases[n].drawCalls.perFrameP50),
      loafN: med((r) => r.phases[n].loaf.n),
      loafMaxMs: med((r) => r.phases[n].loaf.maxMs),
      imageryRequests: med((r) => r.phases[n].requests.imagery),
      requests: med((r) => r.phases[n].requests.total),
    }])),
  },
  runsDetail: measured.map((r) => ({ run: r.run, bootMs: r.bootMs, flightOk: r.flightOk, scrubOk: r.scrubOk, requestsByHost: r.requestsByHost, failedByHost: r.failedByHost, nonOkByHost: r.nonOkByHost })),
};
const summaryPath = resolve(outDir, `${stamp}.json`);
writeFileSync(summaryPath, JSON.stringify(summary, null, 2));

// The table for the eye.
const timer = summary.info.timerQuery;
const cols = [
  ['phase', 13], ['frames', 7], ['drawn', 6], ['rAF p50', 8], ['rAF p95', 8], ['rAF max', 8],
  ['cpu p50', 8], ['cpu p95', 8], ['gpu p50', 8], ['gpu p95', 8], ['draws', 6], ['loaf', 5], ['img req', 8],
];
const line = (cells) => cells.map((c, i) => String(c).padStart(cols[i][1])).join('  ');
console.log('');
console.log(`medians of ${measured.length} run(s)  [ms; gpu = EXT_disjoint_timer_query_webgl2 ${timer ? 'per frame' : 'n/a'}; draws = per rendered frame p50; img req = imagery requests in phase]`);
console.log(line(cols.map((c) => c[0])));
console.log(line(cols.map((c) => '-'.repeat(c[1]))));
for (const n of phaseNames) {
  const p = summary.medians.phases[n];
  console.log(line([
    n, fmt(p.frames, 0), fmt(p.rendered, 0), fmt(p.rafDeltaP50, 2), fmt(p.rafDeltaP95, 2), fmt(p.rafDeltaMax, 1),
    fmt(p.cpuCbP50, 2), fmt(p.cpuCbP95, 1), timer ? fmt(p.gpuP50, 2) : 'n/a', timer ? fmt(p.gpuP95, 2) : 'n/a',
    fmt(p.drawCallsP50, 0), fmt(p.loafN, 0), fmt(p.imageryRequests, 0),
  ]));
}
console.log('');
console.log(`boot ${fmt(summary.medians.bootMs, 0)} ms · JS heap ${fmt(summary.medians.heapAfterBootMB, 0)} MB after boot → ${fmt(summary.medians.heapEndMB, 0)} MB at end · measureUserAgentSpecificMemory ${summary.medians.uaMemMB === null ? 'n/a (page not crossOriginIsolated)' : `${fmt(summary.medians.uaMemMB, 0)} MB`} · imagery requests/run ${fmt(summary.medians.imageryRequests, 0)}`);
console.log(`artifact: ${summaryPath}`);
