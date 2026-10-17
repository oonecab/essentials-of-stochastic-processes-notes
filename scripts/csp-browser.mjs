// Served with the exact generated production CSP over loopback HTTP.
const {atomicJson,openSpace,waitDocument}=await import(config.runtime);
const task=await openSpace(taskSpace,config.selection);
atomicJson(config.sessionFile,{spaceId:task.spaceId,page:config.page??'p1'});
const page=task.page(config.page??'p1');
const report={status:'running',space:task.spaceId,pages:[],negative:null,errors:[]};
await page.cdp('Network.enable');await page.cdp('Runtime.enable');
await page.cdp('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1});
await page.cdp('Emulation.setScriptExecutionDisabled',{value:false});
const observer=await page.cdp('Page.addScriptToEvaluateOnNewDocument',{source:'window.__rnCsp=[];document.addEventListener("securitypolicyviolation",e=>window.__rnCsp.push({directive:e.effectiveDirective,blocked:e.blockedURI}));'});
try{
  for(const route of config.pages){
    await page.events();await page.goto(config.base+route);
    await waitDocument(page,config.base+route);
    const violations=await page.evaluate(()=>window.__rnCsp);
    const events=await page.events();const errors=events.filter(e=>e.method==='Runtime.exceptionThrown');
    const responses=events.filter(e=>e.method==='Network.responseReceived'&&e.params.type==='Document');
    if(!responses.some(e=>Object.keys(e.params.response.headers).some(h=>h.toLowerCase()==='content-security-policy')))throw new Error('CSP response header missing');
    if(violations.length||errors.length)throw new Error('CSP/runtime error at '+route+': '+JSON.stringify({violations,errors}));
    report.pages.push({route,violations,errors});
  }
  await page.goto(config.base+config.pages[0]+'?tamper=1');
  await page.waitForFunction(()=>window.__rnCsp.some(v=>v.directive.startsWith('script-src')),undefined,{timeout:10000});
  report.negative={tampered_script:'blocked',violations:await page.evaluate(()=>window.__rnCsp)};
  report.status='passed';
}catch(error){report.status='failed';report.errors.push(String(error));throw error;}
finally{
  atomicJson(config.output+'/report.json',report);
  await page.cdp('Page.removeScriptToEvaluateOnNewDocument',{identifier:observer.identifier});
}
