import fs from 'node:fs';
import path from 'node:path';
import { pathToFileURL } from 'node:url';
import {selectSpace,acquireSession,createRun,finishRun,failedRun,runDriver} from './browser-runtime.mjs';
import { entries, root, stage } from '../src/lib/controlled-html.mjs';
import { offlineDependencies, fingerprint, sha } from './parity-lib.mjs';
import { htmlFiles } from './inline-assets.mjs';

const i=process.argv.indexOf('--book'),book=i<0?undefined:process.argv[i+1];
const selected=entries().filter(p=>!book||p.metadata.book===book);
if(!selected.length)throw new Error('No migrated reading pages');
const candidates=htmlFiles(path.join(root,'dist')).map(file=>({route:path.relative(path.join(root,'dist'),file)})).filter(p=>!book||p.route.startsWith(book+'/'));
const pages=candidates.map(metadata=>{
  const file=path.join(root,'dist',metadata.route),html=fs.readFileSync(file,'utf8');
  const issues=offlineDependencies(html);
  if(issues.length)throw new Error(metadata.route+': '+issues.join(', '));
  const redirect=html.match(/<meta http-equiv="refresh" content="0;url=([^"]+)"/);
  const target=redirect?path.resolve(path.dirname(file),redirect[1]):file;
  if(!target.startsWith(path.join(root,'dist')+path.sep)||!fs.existsSync(target))throw new Error('Invalid static redirect: '+metadata.route);
  return {route:metadata.route,file,sha256:sha(html),counts:fingerprint(fs.readFileSync(target,'utf8')).counts,redirect_file:redirect?target:null};
});
const sessionFile=path.join(root,'tmp/final-assessment/browser-session.json');
const release=acquireSession(sessionFile);
let run;
try{
  run=createRun(path.join(stage,'browser',book??'all'));
  const session=fs.existsSync(sessionFile)?JSON.parse(fs.readFileSync(sessionFile)):{};
  const selection=selectSpace(process.env.READING_NOTES_CSP_SPACE,session);
  const config={pages,output:run.output,root,sessionFile,selection,page:session.page??'p1',widths:[1800,1440,1024,390],runtime:pathToFileURL(path.join(root,'scripts/browser-runtime.mjs')).href};
  const script='const config = '+JSON.stringify(config)+';\n'+fs.readFileSync(path.join(root,'scripts/browser-acceptance.mjs'),'utf8');
  const report=finishRun(run,await runDriver(script,run));
  console.log(JSON.stringify({status:report.status,pages:pages.length,js_views:report.views.length,no_js_views:report.no_js.length,external_requests:report.external_requests,evidence:path.relative(root,run.output)}));
}catch(error){if(run)failedRun(run,error);throw error;}
finally{release();}
