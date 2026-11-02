// npm install --no-save playwright; npx playwright install chromium
// Run against the local fixture server. KI_CAPTURE_TOKEN_FILE points to a private token file.
const fs = require('node:fs');
const crypto=require('node:crypto');
const path=require('node:path');
const { chromium } = require('playwright');
(async()=>{
 const token=fs.readFileSync(process.env.KI_CAPTURE_TOKEN_FILE||'.data/capture-token','utf8').trim();
 const out='docs/assets/screenshots';fs.mkdirSync(out,{recursive:true});
 fs.mkdirSync('docs/assets/demos',{recursive:true});
 const browser=await chromium.launch({headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1100},recordVideo:{dir:'.capture/video',size:{width:1440,height:1100}}});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:8080');
 await page.waitForFunction(()=>{const logo=document.querySelector('.brand-logo');return logo?.complete&&logo.naturalWidth>0;});
 await page.getByLabel('Team access token').fill(token);
 await page.getByRole('button',{name:'Open workspace'}).click();
 await page.locator('#app').waitFor({state:'visible'});
 const configuration=await page.evaluate(async()=>await(await fetch('/api/config')).json());
 if(!configuration.mock||configuration.source!=='fixture')throw Error('Committed captures require mock provider and synthetic fixture source');
 await page.keyboard.press('Tab');
 if(!(await page.evaluate(()=>document.activeElement?.tagName==='BUTTON'||document.activeElement?.tagName==='SELECT'||document.activeElement?.tagName==='INPUT'||document.activeElement?.tagName==='A')))throw Error('Keyboard focus not on an interactive control');
 await page.screenshot({path:out+'/overview.png',fullPage:false});
 await page.getByLabel('What is happening?').fill('The frontend Service has no endpoints, but its pods appear ready.');
 const submit=async()=>{
  const response=page.waitForResponse(r=>r.url().endsWith('/api/investigations')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Investigate →',exact:true}).click();
  const created=await (await response).json();
  await page.waitForFunction(id=>document.querySelector('#report .report-meta')?.textContent.includes(id),created.id);
  await page.locator('#report .status').filter({hasText:'completed'}).waitFor();
  return created.id;
 };
 await submit();
 await page.locator('#report').scrollIntoViewIfNeeded();
 await page.screenshot({path:out+'/report.png',fullPage:false});
 await page.locator('#report summary').first().focus();
 await page.keyboard.press('Enter');
 if(!(await page.locator('#report details').first().evaluate(e=>e.open)))throw Error('Keyboard evidence expansion failed');
 await page.screenshot({path:out+'/evidence.png',fullPage:false});
 const childResponse=page.waitForResponse(r=>r.url().endsWith('/followup')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Run fresh follow-up'}).click();
 const child=await(await childResponse).json();
 await page.waitForFunction(id=>document.querySelector('#report .report-meta')?.textContent.includes(id),child.id);
 await page.locator('.verification').waitFor();
 if(!(await page.locator('.verification').textContent()).includes('cannot verify a real correction'))throw Error('Fixture follow-up misrepresented recovery');
 const downloadEvent=page.waitForEvent('download');
 await page.getByRole('link',{name:'Export JSON'}).click();
 const download=await downloadEvent;
 const exported=JSON.parse(fs.readFileSync(await download.path(),'utf8'));
 if(exported.id!==child.id||!exported.mock)throw Error('Browser export mismatch');
 await page.screenshot({path:out+'/followup.png',fullPage:false});
 // Exercise the other supported scenarios through the real browser UI.
 for(const scenario of ['crash','image']){
  await page.locator('#scenario').selectOption(scenario);
  await page.getByLabel('What is happening?').fill('The application is unavailable; investigate the observed container condition.');
  await submit();
 }
 await page.setViewportSize({width:390,height:844});
 if(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth))throw Error('Mobile layout overflows');
 await page.screenshot({path:out+'/mobile.png',fullPage:true});
 const video=page.video();await context.close();
 await video.saveAs('docs/assets/demos/investigation.webm');
 await browser.close();
 if(errors.length)throw Error(errors.join('\n'));
 const assets=['screenshots/overview.png','screenshots/report.png','screenshots/evidence.png','screenshots/followup.png','screenshots/mobile.png','demos/investigation.webm'];
 const sourceFiles=[];
 function walk(directory){for(const entry of fs.readdirSync(directory,{withFileTypes:true})){const file=path.join(directory,entry.name);if(entry.isDirectory()&&entry.name!=='__pycache__')walk(file);else if(entry.isFile()&&/\.(py|js|css|html)$/.test(file))sourceFiles.push(file);}}
 walk('src/kubeinvestigator');
 const fingerprint=crypto.createHash('sha256');sourceFiles.sort().forEach(file=>fingerprint.update(file+'\n'+fs.readFileSync(file)));
 fs.writeFileSync('docs/assets/capture-manifest.json',JSON.stringify({captured_at:new Date().toISOString(),application_version:configuration.version,mode:'mock',source:'fixture',commit:null,branding:{source:'brand/veriqta-supplied.png',source_sha256:crypto.createHash('sha256').update(fs.readFileSync('docs/assets/brand/veriqta-supplied.png')).digest('hex'),ui_asset_sha256:crypto.createHash('sha256').update(fs.readFileSync('src/kubeinvestigator/static/veriqta-logo.png')).digest('hex')},authoring_tools:{playwright:require('playwright/package.json').version},source_sha256:fingerprint.digest('hex'),assets:assets.map(file=>({file,sha256:crypto.createHash('sha256').update(fs.readFileSync('docs/assets/'+file)).digest('hex')}))},null,2)+'\n');
 console.log('Browser flow passed: login, three scenarios, evidence, follow-up and mobile capture.');
})().catch(e=>{console.error(e);process.exit(1);});
