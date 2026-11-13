// Run from the repository root with Playwright installed.
// Usage: node visual-tests/fleet-catalog.mjs [output-directory]
import { chromium } from 'playwright';
import { expect } from '@playwright/test';
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
        await page.locator('img').evaluateAll(images => {
          images.forEach(image => { image.loading = 'eager'; });
        });
        await expect.poll(() => page.locator('img').evaluateAll(images =>
          images.length > 0 && images.every(image => image.complete && image.naturalWidth > 0)
        ), { message: `${route}: images rendered` }).toBe(true);
        await page.evaluate(() => document.fonts.ready);
        await expect.poll(() => page.evaluate(() => document.documentElement.scrollWidth > innerWidth), {
          message: `${route}: horizontal overflow at ${width}px`,
        }).toBe(false);
        expect(localErrors, `${route}: missing local assets`).toEqual([]);
        const icon = `/assets/logos/swu-favicon-32-${colorScheme}.png`;
        await expect.poll(() => page.locator('link[rel="icon"]').evaluateAll(icons =>
          icons.filter(icon => !icon.media || matchMedia(icon.media).matches).at(-1)?.getAttribute('href')
        )).toBe(icon);
        await expect.poll(() => page.evaluate(async path => {
          const image = new Image();
          image.src = path;
          try {
            await image.decode();
          } catch {
            return 0;
          }
          return image.naturalWidth;
        }, icon)).toBe(32);
        await expect(page.locator('link[rel="mask-icon"]')).toHaveCount(0);
        if (route === '/') {
          for (const path of ['/muster/', '/ai-fleet-coordinator/']) {
            await expect(page.locator(`.card h4 a[href="${path}"]`)).toHaveCount(1);
          }
        } else {
          await expect(page.locator('h1')).toHaveText(route.startsWith('/muster/') ? 'Muster' : 'AI Fleet Coordinator');
          await expect(page.locator('a[href*="testflight.apple.com"], a[href*="apps.apple.com"], a[href*="releases/latest/download"]')).toHaveCount(0);
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
