// Compatibility mirrors let the original Python checkers remain independent.
import fs from 'node:fs';
import { entries } from '../src/lib/controlled-html.mjs';
const write=process.argv.includes('--write');
for(const {metadata,html} of entries()){
  const current=fs.readFileSync(metadata.legacy_path,'utf8');
  if(current!==html){
    if(!write)throw new Error('Compatibility mirror differs: '+metadata.legacy_path);
    fs.writeFileSync(metadata.legacy_path,html);
  }
}
console.log(JSON.stringify({status:'passed',mode:write?'write':'check'}));
