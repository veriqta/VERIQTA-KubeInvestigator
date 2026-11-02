// Disposable-cluster browser acceptance. Invoke through scripts/smoke.sh only.
const fs=require('node:fs');
const crypto=require('node:crypto');
const {execFileSync,spawn}=require('node:child_process');
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const context='kind-veriqta-investigator-demo';
const kc=(...args)=>execFileSync('kubectl',['--context',context,...args],{encoding:'utf8',timeout:200000});
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
let pf,browser,recording;
async function forward(){
 pf=spawn('kubectl',['--context',context,'-n','veriqta-system','port-forward','--address','127.0.0.1','svc/investigator','18080:8080'],{stdio:'ignore'});
 for(let i=0;i<100;i++){try{if((await fetch('http://127.0.0.1:18080/health/ready')).ok)return;}catch{} await delay(200);}
 throw Error('Disposable application did not become ready');
}
async function stopForward(){if(pf&&pf.exitCode===null){pf.kill();await new Promise(resolve=>pf.once('exit',resolve));}}
(async()=>{
 assert.equal(kc('config','current-context').trim(),context);
 assert(fs.existsSync('.data/smoke-owned'),'Use disposable smoke wrapper');
 const token=fs.readFileSync('.data/demo-access.env','utf8').trim().replace(/^KI_TOKEN=/,'');
 const out='docs/assets/cluster';fs.mkdirSync(out,{recursive:true});
 await forward();browser=await chromium.launch({headless:true});
 const session=await browser.newContext({viewport:{width:1440,height:1100},acceptDownloads:true,recordVideo:{dir:'.capture/cluster-video',size:{width:1440,height:1100}}});
 let page=await session.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('http://127.0.0.1:18080');
 assert.equal((await page.evaluate(async()=>await fetch('/api/investigations').then(r=>r.status))),401);
 async function login(){await page.getByLabel('Team access token').fill(token);await page.getByRole('button',{name:'Open workspace'}).click();await page.locator('#app').waitFor({state:'visible'});}
 await login();
 const configuration=await page.evaluate(async()=>await(await fetch('/api/config')).json());
 assert(configuration.mock&&configuration.source==='kubernetes','Requires real cluster evidence and MOCK interpretations');
 assert.match(await page.locator('#mock-banner').textContent(),/Evidence comes from your cluster/);
 // The token input is type=password and cleared on login; no browser state is written.
 recording=session;
 await page.screenshot({path:out+'/overview.png'});
 const reports=[];const verifications={};
 const readReport=()=>page.evaluate(async()=>{const id=document.querySelector('#report .report-meta').textContent.split(' · ').at(-1);return await(await fetch('/api/investigations/'+id)).json();});
 async function complete(id){await page.waitForFunction(id=>document.querySelector('#report .report-meta')?.textContent.includes(id)&&!['queued','running'].includes(document.querySelector('#report .status')?.textContent),id,{timeout:120000});return readReport();}
 async function download(format){const event=page.waitForEvent('download');await page.getByRole('link',{name:'Export '+format.toUpperCase()}).click();return fs.readFileSync(await(await event).path(),'utf8');}
 for(const [scenario,workload,problem] of [['service','frontend','The frontend Service has no endpoints although its pod is ready.'],['crash','checkout-crash','The checkout container keeps restarting.'],['image','catalog-image','The catalog image cannot be pulled.']]){
  await page.locator('#scenario').selectOption(scenario);await page.locator('#workload').fill(workload);await page.locator('#problem').fill(problem);
  const response=page.waitForResponse(r=>r.url().endsWith('/api/investigations')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Investigate →',exact:true}).click();const created=await(await response).json();const report=await complete(created.id);
  assert.equal(report.status,'completed');assert(report.mock&&report.source==='kubernetes'&&report.observations.length);
  assert.equal(JSON.parse(await download('json')).id,report.id);assert.match(await download('md'),/mock/i);
  if(scenario==='service'){await page.locator('#report').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/report.png'});}
  const details=page.locator('#report details').first();await details.locator('summary').click();assert(await details.evaluate(e=>e.open));
  if(scenario==='service'){await page.locator('#report').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/evidence.png'});}
  reports.push(report);
 }
 // Persisted reports must survive a real deployment restart; sessions must not.
 await stopForward();kc('-n','veriqta-system','rollout','restart','deployment/investigator');kc('-n','veriqta-system','rollout','status','deployment/investigator','--timeout=180s');await forward();
 await page.reload();await page.locator('#login').waitFor({state:'visible'});
 // Continue the same genuine recording through reauthentication and verification.
 // Credential inputs remain masked and are cleared immediately on login.
 await login();
 for(const original of reports){
  await page.locator('.history-item').filter({hasText:original.workload}).click();const retained=await complete(original.id);assert.deepEqual(retained,original);
  // Installer-only correction, outside the read-only application.
  execFileSync('bash',['scripts/demo.sh','correct-'+original.scenario],{stdio:'pipe',timeout:240000});
  const response=page.waitForResponse(r=>r.url().endsWith('/followup')&&r.request().method()==='POST');await page.getByRole('button',{name:'Run fresh follow-up'}).click();const child=await(await response).json();const report=await complete(child.id);
  assert.equal(report.parent_id,original.id);assert.match(report.verification,/absent in fresh evidence/);assert(report.evidence.every(e=>e.collected_at>original.completed_at));assert(report.mock&&report.source==='kubernetes');
  verifications[original.scenario]=report.verification;
  if(original.scenario==='service'){await page.locator('#report').scrollIntoViewIfNeeded();await page.screenshot({path:out+'/followup.png',fullPage:true});}
 }
 await page.getByRole('button',{name:'Sign out'}).click();await page.locator('#login').waitFor({state:'visible'});assert.equal(await page.evaluate(async()=>await fetch('/api/investigations').then(r=>r.status)),401);
 const video=page.video();await recording.close();await video.saveAs(out+'/investigation.webm');await browser.close();assert.deepEqual(errors,[]);
 const assets=['overview.png','report.png','evidence.png','followup.png','investigation.webm'];
 fs.writeFileSync(out+'/manifest.json',JSON.stringify({captured_at:new Date().toISOString(),software:configuration.version,revision:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),working_tree_changes:execFileSync('git',['diff','--name-only'],{encoding:'utf8'}).trim().split('\n').filter(Boolean),source:'kubernetes',provider:'mock',synthetic_workloads:true,playwright:require('playwright/package.json').version,assets:assets.map(file=>({file,sha256:crypto.createHash('sha256').update(fs.readFileSync(out+'/'+file)).digest('hex')}))},null,2)+'\n');
 fs.writeFileSync('.data/browser-result.json',JSON.stringify({status:'checks_passed_cleanup_pending',cluster_cleanup_verified:null,completed_at:new Date().toISOString(),revision:execFileSync('git',['rev-parse','HEAD'],{encoding:'utf8'}).trim(),source:'kubernetes',provider:'mock',checks:['unauthenticated denial','browser session login','three browser submissions','expandable real evidence','JSON and Markdown browser downloads','real deployment restart and session invalidation','exact persisted report equality','three external manual corrections','three browser follow-ups with newer evidence timestamps','logout invalidation'],verifications,versions:JSON.parse(kc('version','-o','json')),image_id:execFileSync('docker',['image','inspect','kubeinvestigator:0.1.0','--format','{{.Id}}'],{encoding:'utf8'}).trim()},null,2)+'\n');
 console.log('Real-cluster browser acceptance passed; interpretations remain MOCK.');
})().catch(e=>{console.error(e.message);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();await stopForward();});
