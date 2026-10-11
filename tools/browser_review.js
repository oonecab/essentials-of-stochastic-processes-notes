// Run through ego-browser nodejs with an existing owned session in tmp/audit-fix-http.
const fs = await import('node:fs/promises');
const crypto = await import('node:crypto');
const root = globalThis.bookReviewRoot;
if(!root)throw Error('Set globalThis.bookReviewRoot to the checkout in the browser script');
const directory = root+'/tmp/audit-fix-http';
const session = JSON.parse(await fs.readFile(directory+'/session.json','utf8'));
const task = await taskSpace(session.space_id), page = task.page('p1');
const files = (await fs.readdir(root+'/notes')).filter(x=>x.endsWith('.html')).sort();
let results=[];try{results=JSON.parse(await fs.readFile(directory+'/browser-layouts.json','utf8'));}catch{}
await page.cdp('Page.addScriptToEvaluateOnNewDocument',{source:`globalThis.__review={errors:[],csp:[]};addEventListener('error',e=>__review.errors.push(e.message));addEventListener('unhandledrejection',e=>__review.errors.push(String(e.reason)));addEventListener('securitypolicyviolation',e=>__review.csp.push(e.violatedDirective));`});
const ready = ()=>page.evaluate(async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));});
for (const width of [1800,1440,1024,390]) {
 await page.cdp('Emulation.setDeviceMetricsOverride',{width,height:width===390?844:1000,deviceScaleFactor:1,mobile:width===390});
 for (const file of files) {
  const sha256=crypto.createHash('sha256').update(await fs.readFile(root+'/notes/'+file)).digest('hex');
  if(results.some(r=>r.file===file&&r.width===width&&r.sha256===sha256))continue;
  const started_at_utc=new Date().toISOString();
  await page.goto(session.origin+'/notes/'+file);await ready();
  await page.evaluate(()=>document.querySelectorAll('main details').forEach(e=>e.open=true));await ready();
  const row = await page.evaluate(()=>{
   const rail=document.getElementById('annotation-rail'),r=rail.getBoundingClientRect(),main=document.querySelector('main').getBoundingClientRect();
   return {width:innerWidth,root:document.documentElement.scrollWidth,railVisible:!rail.hidden&&r.width>0,railWidth:r.width,railX:r.x,mainRight:main.right,
   errors:__review.errors,csp:__review.csp,
   exercises:document.querySelectorAll('.exercise').length,statements:document.querySelectorAll('.source-statement').length,
   inlineVisible:[...document.querySelectorAll('main .reading-notes')].every(n=>n.getBoundingClientRect().height>0),
   renderedMath:[...document.querySelectorAll('main math')].filter(m=>!m.closest('.reading-notes')||!document.documentElement.classList.contains('notes-enhanced')).length,
   badMath:[...document.querySelectorAll('main math')].filter(m=>(!m.closest('.reading-notes')||!document.documentElement.classList.contains('notes-enhanced'))&&(m.querySelector('merror')||m.getBoundingClientRect().height<1)).length};
  });
  if(row.width!==width||row.root>width||row.badMath||row.errors.length||row.csp.length)throw Error(JSON.stringify({file,row}));
  if(width>=1440){if(!row.railVisible||row.railWidth!==280||row.railX<row.mainRight||row.inlineVisible)throw Error('Three-column layout '+file);}
  else if(row.railVisible||!row.inlineVisible)throw Error('Inline annotation layout '+file);
  let contexts=0,deepLinks=0;
  if(width===1800){
   const targets=await page.evaluate(()=>({sections:[...document.querySelectorAll('main > section')].map(x=>x.id),details:[...document.querySelectorAll('details.exercise,details.source-statement')].map(x=>x.id)}));
   for(let index=0;index<targets.sections.length;index+=4){
    contexts+=await page.evaluate(async ids=>{
     const ready=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
     for(const id of ids){
      const sec=document.getElementById(id);sec.scrollIntoView();if(scrollY+innerHeight<document.documentElement.scrollHeight-2)scrollBy(0,-55);await ready();
      if(document.getElementById('annotation-rail').dataset.activeSection!==id||document.querySelectorAll('#annotation-content .annotation-card').length!==2)throw Error('Wrong annotation context '+id);
      if([...document.querySelectorAll('#annotation-content math')].some(m=>m.querySelector('merror')||m.getBoundingClientRect().height<1))throw Error('Annotation math');
     }return ids.length;
    },targets.sections.slice(index,index+4));
   }
   for(let index=0;index<targets.details.length;index+=4){
    deepLinks+=await page.evaluate(async ids=>{
     const ready=()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
     for(const id of ids){
      const target=document.getElementById(id);target.open=false;location.hash=id;await ready();
      if(!target.open||target.getBoundingClientRect().height<50)throw Error('Deep link did not expand '+id);
     }return ids.length;
    },targets.details.slice(index,index+4));
   }
  }

  results.push({file,started_at_utc,finished_at_utc:new Date().toISOString(),sha256,...row,contexts,deepLinks});
  await fs.writeFile(directory+'/browser-layouts.json',JSON.stringify(results,null,2)+'\n');
  console.log({file,width,contexts,deepLinks,math:row.renderedMath});
 }
}
const shots=[
 [1800,'chapter01_markov_chains.html','ex-1-11','detailed-balance'],
 [1800,'chapter04_continuous_time_markov_chains.html','derive-c4-jackson-balance','traffic'],
 [1800,'chapter06_mathematical_finance.html','ex-6-20','literal-payoff'],
 [390,'chapter04_continuous_time_markov_chains.html','ex-4-24','birth-death'],
 [390,'chapter02_poisson_processes.html','theorem-2-1','poisson'],
 [390,'chapter06_mathematical_finance.html','sources-finance','code']
];
for(const [width,file,anchor,name] of shots){
 await page.cdp('Emulation.setDeviceMetricsOverride',{width,height:width===390?844:1100,deviceScaleFactor:1,mobile:width===390});
 await page.goto(session.origin+'/notes/'+file+'#'+anchor);await ready();
 await page.screenshot({path:directory+'/'+name+'.png'});
}
console.log({layouts:results.length,contexts:results.reduce((n,r)=>n+r.contexts,0),deepLinks:results.reduce((n,r)=>n+r.deepLinks,0)});
console.log(await page.snapshot());
