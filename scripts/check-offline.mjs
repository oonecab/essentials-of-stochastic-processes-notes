import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { entries, root, stage } from '../src/lib/controlled-html.mjs';
import { offlineDependencies, fingerprint, sha } from './parity-lib.mjs';

const i=process.argv.indexOf('--book'),book=i<0?undefined:process.argv[i+1];
const selected=entries().filter(p=>!book||p.metadata.book===book);
if(!selected.length)throw new Error('No migrated reading pages');
const pages=selected.map(({metadata})=>{
  const file=path.join(root,'dist',metadata.route),html=fs.readFileSync(file,'utf8');
  const issues=offlineDependencies(html);
  if(issues.length)throw new Error(metadata.route+': '+issues.join(', '));
  return {route:metadata.route,file,sha256:sha(html),counts:fingerprint(html).counts};
});
const sessionFile=path.join(stage,'browser-session.json');
const session=fs.existsSync(sessionFile)?JSON.parse(fs.readFileSync(sessionFile)):null;
const output=path.join(stage,'browser',book??'all');fs.mkdirSync(output,{recursive:true});
const config={pages,output,root,sessionFile,spaceId:session?.spaceId,page:session?.page??'p1',widths:[1800,1440,1024,390]};
const script='const config = '+JSON.stringify(config)+';\n'+fs.readFileSync('scripts/browser-acceptance.mjs','utf8');
const result=spawnSync('ego-browser',['nodejs'],{input:script,encoding:'utf8',maxBuffer:8*1024*1024});
fs.writeFileSync(path.join(output,'driver.log'),result.stdout+result.stderr);
if(result.status!==0){console.error((result.stdout+result.stderr).slice(-6000));process.exit(result.status??1);}
const report=JSON.parse(fs.readFileSync(path.join(output,'report.json')));
if(report.status!=='passed')throw new Error('Browser acceptance failed; see '+output);
console.log(JSON.stringify({status:report.status,pages:pages.length,js_views:report.views.length,no_js_views:report.no_js.length,external_requests:report.external_requests,evidence:path.relative(root,output)}));
