// Run from the repository root with Playwright installed.
// Usage: node visual-tests/codecaps.mjs [output-directory]
import { chromium } from 'playwright';
import { createServer } from 'node:http';
import { readFile, mkdir } from 'node:fs/promises';
import { extname, resolve } from 'node:path';
import assert from 'node:assert/strict';
const root=process.cwd(); const out=resolve(process.argv[2]||'/tmp/codecaps-visual');await mkdir(out,{recursive:true});
const server=createServer(async(req,res)=>{try{let u=new URL(req.url,'http://localhost');let p=resolve(root,'.'+decodeURIComponent(u.pathname));assert(p.startsWith(root+'/'));if(u.pathname.endsWith('/'))p+='/index.html';res.setHeader('Content-Type',({'.html':'text/html','.css':'text/css','.webp':'image/webp','.png':'image/png','.svg':'image/svg+xml'})[extname(p)]||'application/octet-stream');res.end(await readFile(p));}catch{res.statusCode=404;res.end('not found')}});
await new Promise(r=>server.listen(0,'127.0.0.1',r));const browser=await chromium.launch({headless:true});
try{for(const width of [1280,390,320]){const page=await browser.newPage({viewport:{width,height:900}});const errors=[];page.on('response',r=>{if(r.status()>=400)errors.push(r.url())});await page.goto(`http://127.0.0.1:${server.address().port}/codecaps/`,{waitUntil:'networkidle'});const images=page.locator('.screenshot-card img');assert.equal(await images.count(),5);await images.evaluateAll(es=>es.forEach(e=>e.loading='eager'));await images.evaluateAll(es=>Promise.all(es.map(e=>e.decode())));assert(await images.evaluateAll(es=>es.every(e=>e.complete&&e.naturalWidth>0)));assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);assert.deepEqual(errors,[]);await page.screenshot({path:resolve(out,`codecaps-${width}.png`),fullPage:true});await page.close();console.log(`PASS ${width}px: five rendered screenshots, no overflow/load errors`);}}finally{await browser.close();server.close()}
