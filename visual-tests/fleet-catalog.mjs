// Run from the repository root with Playwright installed.
// Usage: node visual-tests/fleet-catalog.mjs [output-directory]
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, resolve, sep } from 'node:path';
import assert from 'node:assert/strict';

const root = process.cwd();
const out = resolve(process.argv[2] || '/tmp/fleet-catalog-visual');
await mkdir(out, { recursive: true });
const server = createServer(async (req, res) => {
  try {
    const url = new URL(req.url, 'http://localhost');
    let file = resolve(root, '.' + decodeURIComponent(url.pathname));
    assert(file === root || file.startsWith(root + sep));
    if (url.pathname.endsWith('/')) file = resolve(file, 'index.html');
    res.setHeader('Content-Type', ({ '.html': 'text/html', '.css': 'text/css', '.mjs': 'text/javascript', '.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml' })[extname(file)] || 'application/octet-stream');
    res.end(await readFile(file));
  } catch {
    res.statusCode = 404;
    res.end('Not found');
  }
});
await new Promise(done => server.listen(0, '127.0.0.1', done));
const origin = `http://127.0.0.1:${server.address().port}`;
let browser;
try {
  browser = await chromium.launch({ headless: true });
  for (const colorScheme of ['light', 'dark']) {
    for (const width of [1280, 390, 320]) {
      for (const route of ['/', '/muster/', '/ai-fleet-coordinator/', '/muster/support.html', '/ai-fleet-coordinator/support.html']) {
        const page = await browser.newPage({ viewport: { width, height: 900 }, colorScheme });
        // Keep screenshots repeatable; this fixture is not live service-health evidence.
        await page.route('https://status.simplewithus.com/index.json', request => request.fulfill({
          contentType: 'application/json',
          body: JSON.stringify({ data: { attributes: { aggregate_state: 'operational' } } }),
        }));
        const localErrors = [];
        page.on('response', response => {
          if (response.url().startsWith(origin) && response.status() >= 400) localErrors.push(response.url());
        });
        await page.goto(origin + route, { waitUntil: 'networkidle' });
        await page.locator('img').evaluateAll(async images => {
          images.forEach(image => { image.loading = 'eager'; });
          await Promise.all(images.map(image => image.decode()));
        });
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false, `${route}: horizontal overflow at ${width}px`);
        assert.deepEqual(localErrors, [], `${route}: missing local assets`);
        const icon = await page.locator('link[rel="icon"]').evaluateAll(icons => {
          return icons.filter(icon => !icon.media || matchMedia(icon.media).matches).at(-1).getAttribute('href');
        });
        assert.equal(icon, `/assets/logos/swu-favicon-32-${colorScheme}.png`);
        assert.equal(await page.evaluate(async path => {
          const image = new Image();
          image.src = path;
          await image.decode();
          return image.naturalWidth;
        }, icon), 32);
        assert.equal(await page.locator('link[rel="mask-icon"]').count(), 0);
        if (route === '/') {
          for (const path of ['/muster/', '/ai-fleet-coordinator/']) {
            assert.equal(await page.locator(`.card h4 a[href="${path}"]`).count(), 1);
          }
        } else {
          assert.equal(await page.locator('h1').textContent(), route.startsWith('/muster/') ? 'Muster' : 'AI Fleet Coordinator');
          assert.equal(await page.locator('a[href*="testflight.apple.com"], a[href*="apps.apple.com"], a[href*="releases/latest/download"]').count(), 0);
        }
        const label = route === '/' ? 'catalog' : route.replace(/^\//, '').replace(/\/$/, '').replaceAll('/', '-').replace('.html', '');
        await page.screenshot({ path: resolve(out, `${label}-${colorScheme}-${width}.png`), fullPage: true });
        await page.close();
        console.log(`PASS ${route} ${colorScheme} ${width}px: rendered images, matching favicon, no overflow or missing assets`);
      }
    }
  }
} finally {
  await browser?.close();
  await new Promise(done => server.close(done));
}
