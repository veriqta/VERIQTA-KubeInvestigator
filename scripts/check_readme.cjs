// Optional local README rendering check. Requires marked and playwright.
const fs=require('node:fs'),path=require('node:path');
const {chromium}=require('playwright');
(async()=>{
 const {marked}=await import(require.resolve('marked'));
 const root=path.resolve(__dirname,'..');
 const html=await marked.parse(fs.readFileSync(path.join(root,'README.md'),'utf8'));
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage();
 await page.route('**/*',async route=>{
  const url=new URL(route.request().url());
  if(url.hostname!=='readme.local'){
   if(url.hostname==='img.shields.io')return route.fulfill({response:await route.fetch({timeout:15000})});
   return route.abort();
  }
  if(url.pathname==='/')return route.fulfill({contentType:'text/html',body:`<!doctype html><html><head><meta charset="utf-8"><style>body{margin:0;font:16px/1.6 system-ui;background:var(--bg);color:var(--fg)}main{max-width:1000px;margin:auto;padding:24px}img{max-width:100%;height:auto}pre{overflow:auto;padding:16px;background:#77889922}a{color:#3282cb}h1,h2{line-height:1.3}table{display:block;overflow:auto}</style></head><body><main>${html}</main></body></html>`});
  const file=path.resolve(root,'.'+decodeURIComponent(url.pathname));
  if(!file.startsWith(root+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:'Missing repository asset'});
  const mime={'.png':'image/png','.svg':'image/svg+xml','.gif':'image/gif','.webm':'video/webm'}[path.extname(file)]||'text/plain';
  return route.fulfill({contentType:mime,body:fs.readFileSync(file)});
 });
 for(const [theme,width] of [['light',1440],['dark',1440],['light',390]]){
  await page.setViewportSize({width,height:1000});
  await page.goto('http://readme.local/');
  await page.evaluate(theme=>{
   document.documentElement.style.setProperty('--bg',theme==='dark'?'#0d1117':'#ffffff');
   document.documentElement.style.setProperty('--fg',theme==='dark'?'#e6edf3':'#1f2328');
   document.querySelectorAll('h1,h2,h3').forEach(h=>h.id=h.textContent.toLowerCase().replace(/[^\p{L}\p{N}\s-]/gu,'').replace(/\s/g,'-'));
  },theme);
  await page.waitForFunction(()=>[...document.images].every(i=>i.complete));
  const broken=await page.evaluate(()=>[...document.images].filter(i=>i.naturalWidth===0).map(i=>i.src));
  if(broken.length)throw Error('Broken local README images: '+broken.join(', '));
  const anchors=await page.evaluate(()=>[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.getElementById(a.hash.slice(1))).map(a=>a.hash));
  if(anchors.length)throw Error('Broken README anchors: '+anchors.join(', '));
  if(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw Error('README horizontal overflow');
  fs.mkdirSync(path.join(root,'.capture/readme'),{recursive:true});
  await page.screenshot({path:path.join(root,`.capture/readme/${theme}-${width}.png`),fullPage:true});
 }
 await browser.close();
 console.log('README local images, navigation anchors, light/dark and narrow rendering passed. Remote badges loaded; exact hosted GitHub rendering unverified.');
})().catch(e=>{console.error(e);process.exit(1);});
