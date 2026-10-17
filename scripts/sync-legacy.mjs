// Compatibility mirrors let the original Python checkers remain independent.
import fs from 'node:fs';
import { entries, syncMirrors } from '../src/lib/controlled-html.mjs';
const write=process.argv.includes('--write');
syncMirrors(entries(),{write});
console.log(JSON.stringify({status:'passed',mode:write?'write':'check'}));
