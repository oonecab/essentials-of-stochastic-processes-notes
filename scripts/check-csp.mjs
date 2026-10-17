import fs from 'node:fs';
import path from 'node:path';
import http from 'node:http';
import {selectSpace,acquireSession,createRun,finishRun,failedRun,runDriver,atomicJson} from './browser-runtime.mjs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {cspManifest,cspHeader,cspHash,scriptSources,verifyCspManifest} from './csp-lib.mjs';

export async function checkCsp(directory){
  const root=path.dirname(path.dirname(fileURLToPath(import.meta.url)));
  const output=path.join(root,'tmp/reading-notes-migration/csp');
  const manifest=cspManifest(directory), covered=new Set(), pages=[];
  for(const route of Object.keys(manifest.files)){
    const hashes=scriptSources(fs.readFileSync(path.join(directory,route),'utf8')).map(cspHash);
    if(hashes.some(h=>!covered.has(h))){pages.push(route);hashes.forEach(h=>covered.add(h));}
  }
  if(!pages.length)throw new Error('CSP smoke requires an inline script');
  const header=cspHeader(fs.readFileSync(path.join(root,'deploy/nginx/static.inc.template'),'utf8'),manifest.sources);
  const server=http.createServer((req,res)=>{
    const url=new URL(req.url,'http://localhost');
    const route=decodeURIComponent(url.pathname).slice(1);
    if(!Object.hasOwn(manifest.files,route)){res.writeHead(404);res.end();return;}
    let html=fs.readFileSync(path.join(directory,route),'utf8');
    if(url.searchParams.has('tamper'))html=html.replace(/(<script\b[^>]*>)([\s\S]*?)(<\/script>)/,(_,open,body,close)=>open+body+'\n/* injected hash mismatch */'+close);
    res.writeHead(200,{'Content-Type':'text/html; charset=utf-8','Content-Security-Policy':header,'Cache-Control':'no-store'});res.end(html);
  });
  const sessionFile=path.join(root,'tmp/final-assessment/browser-session.json');
  const release=acquireSession(sessionFile);
  let run;
  try{
    run=createRun(output);
    const session=fs.existsSync(sessionFile)?JSON.parse(fs.readFileSync(sessionFile)):{};
    const selection=selectSpace(process.env.READING_NOTES_CSP_SPACE,session);
    await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
    const config={base:`http://127.0.0.1:${server.address().port}/`,pages,output:run.output,sessionFile,selection,page:session.page??'p1',runtime:pathToFileURL(path.join(root,'scripts/browser-runtime.mjs')).href};
    const script=`const config=${JSON.stringify(config)};\n`+fs.readFileSync(path.join(root,'scripts/csp-browser.mjs'),'utf8');
    const report=await runDriver(script,run);
    verifyCspManifest(directory,manifest);
    atomicJson(path.join(run.output,'manifest.json'),manifest);
    atomicJson(path.join(output,'manifest.json'),manifest);
    finishRun(run,report);
    console.log(JSON.stringify({csp:'passed',pages:pages.length,script_hashes:covered.size,tampered_script:'blocked'}));
    return manifest;
  }catch(error){if(run)failedRun(run,error);throw error;}
  finally{server.closeAllConnections();await new Promise(resolve=>server.close(resolve));release();}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)await checkCsp(path.resolve(process.argv[2]??'dist'));
