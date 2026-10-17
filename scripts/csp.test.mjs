import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {cspManifest,verifyCspManifest,cspHeader} from './csp-lib.mjs';
import {fingerprint,differences} from './parity-lib.mjs';
test('a post-validation inline script change invalidates release packaging',()=>{
  const root=fs.mkdtempSync(path.join(os.tmpdir(),'rn-csp-'));
  try{
    const page=path.join(root,'index.html');fs.writeFileSync(page,'<script>window.ready=true;</script>');
    const manifest=cspManifest(root);verifyCspManifest(root,manifest);
    assert.match(cspHeader('add_header Content-Security-Policy "script-src @@SCRIPT_SOURCES@@" always;',manifest.sources),/sha256-/);
    fs.writeFileSync(page,'<script>window.ready=false;</script>');assert.throws(()=>verifyCspManifest(root,manifest),/hash changed/);
  }finally{fs.rmSync(root,{recursive:true,force:true});}
});
test('escaped set:html output and dropped HTML attributes cannot pass parity',()=>{
  const original='<main role="main" aria-label="正文"><math><mi>x</mi></math></main>';
  for(const bad of [original.replaceAll('<','&lt;'),original.replace(' aria-label="正文"','')])assert.ok(differences(fingerprint(original),fingerprint(bad)).includes('dom'));
});
