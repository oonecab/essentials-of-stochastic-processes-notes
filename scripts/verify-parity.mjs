import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { entries, root, stage } from '../src/lib/controlled-html.mjs';
import { fingerprint, differences, sha } from './parity-lib.mjs';

export function verifyParity(directory=path.join(root,'dist'),book) {
  const state=JSON.parse(fs.readFileSync('scripts/migration-state.json'));
  const pages=entries().filter(e=>!book||e.metadata.book===book);
  if(!pages.length)throw new Error('No migrated pages selected');
  const baselineTransformer=execFileSync('git',['show',`${state.baseline_ref}:deploy/reader_views.py`]);
  if(!baselineTransformer.equals(fs.readFileSync('deploy/reader_views.py')))throw new Error('Golden publication transformer changed');
  const readerCss=execFileSync('git',['show',`${state.baseline_ref}:portal/reader.css`]);
  if(!readerCss.equals(fs.readFileSync(path.join(stage,'legacy/reader.css'))))throw new Error('Golden reader CSS changed');
  const records=[];
  for(const {metadata,html} of pages) {
    const frozen=execFileSync('git',['show',`${state.baseline_ref}:${metadata.legacy_path}`],{maxBuffer:32*1024*1024});
    if(sha(frozen)!==metadata.original_sha256 || !frozen.equals(Buffer.from(html)))throw new Error(`Reviewed source bytes changed: ${metadata.route}`);
    if(!frozen.equals(fs.readFileSync(metadata.legacy_path)))throw new Error(`Legacy compatibility HTML changed: ${metadata.route}`);
    const expected=fs.readFileSync(path.join(stage,'legacy',metadata.route),'utf8').replace('<link rel="stylesheet" href="../../reader.css">',()=>'<style>'+readerCss.toString()+'</style>');
    const actual=fs.readFileSync(path.join(directory,metadata.route),'utf8');
    const before=fingerprint(expected),after=fingerprint(actual);
    records.push({page:metadata.route,source_sha256:sha(frozen),output_sha256:sha(actual),source_counts:fingerprint(html).counts,
      publication_counts:after.counts,differences:differences(before,after),source_bytes:Buffer.byteLength(html),output_bytes:Buffer.byteLength(actual),js_bytes:after.js_bytes,
      js_ratio:after.js_bytes/before.js_bytes});
  }
  const report={status:records.every(r=>r.differences.length===0)?'passed':'failed',baseline_ref:state.baseline_ref,book:book??'all',pages:records.length,records};
  fs.mkdirSync(path.join(stage,'parity'),{recursive:true});
  fs.writeFileSync(path.join(stage,'parity',`${book??'all'}.json`),JSON.stringify(report,null,2)+'\n');
  if(report.status!=='passed')throw new Error('Parity differences: '+JSON.stringify(records.filter(r=>r.differences.length)));
  return report;
}
if(import.meta.url===pathToFileURL(process.argv[1]).href){
  const i=process.argv.indexOf('--book');const report=verifyParity(undefined,i<0?undefined:process.argv[i+1]);
  console.log(JSON.stringify({status:report.status,book:report.book,pages:report.pages,differences:0}));
}
