import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fingerprint,differences,offlineDependencies } from './parity-lib.mjs';
import { inlineAssets } from './inline-assets.mjs';
import { separateApprovedIsland,deepLinkMarkup } from '../src/lib/islands.mjs';

const page='<!doctype html><html><head><style>body{color:black}</style></head><body><main id="top"><p>条件 x&gt;0。</p><math><mi>x</mi><mo>+</mo><mn>1</mn></math><svg viewBox="0 0 10 10"><path d="M0 0 L10 10"/></svg><details class="exercise" id="ex-1-1"><summary>习题</summary><div class="exercise-question">x?</div><div class="answer">x+1</div></details><pre><code>return 1;</code></pre><a href="source.pdf#page=13">来源</a></main><script>console.log(1)</script></body></html>';
test('separately verifies the navigation addition while preserving every original fingerprint',()=>{
  const output=page.replace('</body>',deepLinkMarkup+'</body>');
  assert.deepEqual(fingerprint(separateApprovedIsland(output,'csapp')),fingerprint(page));
  assert.throws(()=>separateApprovedIsland(page,'csapp'),/Missing/);
  assert.throws(()=>separateApprovedIsland(output.replace('scrollIntoView','remove'),'csapp'),/changed/);
  assert.throws(()=>separateApprovedIsland(output,'weiss'),/approved/);
  assert.ok(differences(fingerprint(page),fingerprint(separateApprovedIsland(output.replace('console.log(1)','console.log(0)'),'csapp'))).includes('scripts'));
});
test('detects content, math, figure, anchor, PDF and executable-copy mutations',()=>{
  const baseline=fingerprint(page);
  for(const [before,after,key] of [['<style>body{color:black}</style>','','styles'],['<head>','<head><meta name="viewport" content="width=900">','head_metadata'],['x&gt;0','x&lt;0','body_text'],['<mn>1</mn>','<mn>2</mn>','mathml'],['L10 10','L0 10','svg'],['id="ex-1-1"','id="ex-1-2"','anchors'],['#page=13','#page=14','pdf_links'],['return 1;','return 0;','code'],['console.log(1)','console.log(0)','scripts']]){
    assert.ok(differences(baseline,fingerprint(page.replace(before,after))).includes(key),key);
  }
  assert.deepEqual(differences(baseline,fingerprint(page)),[]);
});
test('full DOM detects disclosure, visibility, accessibility, namespace and class mutations',()=>{
  for(const [before,after] of [['<details','<div'],['class="exercise"','class="exercise" hidden'],['class="exercise"','class="exercise" role="presentation"'],['class="exercise"','class="exercise" aria-hidden="true"'],['class="exercise"','class="question"'],['<mi>x</mi>','<mtext>x</mtext>']]){
    assert.ok(differences(fingerprint(page),fingerprint(page.replace(before,after))).includes('dom'),after);
  }
  assert.notDeepEqual(fingerprint(page).exercise_ids,fingerprint(page.replace('id="ex-1-1"','id="ex-9-9"')).exercise_ids);
});
test('offline gate rejects local, remote and script-loaded files; keeps fragment paint servers',()=>{
  assert.deepEqual(offlineDependencies(page),[]);
  for(const extra of ['<link rel="stylesheet" href="reader.css">','<script src="/app.js"></script>','<img src="https://example.invalid/pixel">','<style>@import "x.css";</style>','<style>p{background:url(x.png)}</style>'])assert.ok(offlineDependencies(page.replace('</head>',extra+'</head>')).length);
  assert.deepEqual(offlineDependencies(page.replace('</head>','<style>path{marker-end:url(#arrow)}</style></head>')),[]);
});
test('inliner preserves CSS and self-contained script bytes, refuses path escape and module imports',()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'rn-inline-'));
  try{
    fs.writeFileSync(path.join(dir,'reader.css'),'p { color: green; }');
    fs.writeFileSync(path.join(dir,'app.js'),'console.log("local");');
    const file=path.join(dir,'index.html');
    fs.writeFileSync(file,'<html><head><link rel="stylesheet" href="reader.css"></head><body><script src="app.js"></script></body></html>');
    inlineAssets(dir);const actual=fs.readFileSync(file,'utf8');
    assert.match(actual,/<style>p \{ color: green; \}<\/style>/);
    assert.match(actual,/<script>console.log\("local"\);<\/script>/);
    assert.deepEqual(offlineDependencies(actual),[]);
    fs.writeFileSync(file,'<script src="../escape.js"></script>');assert.throws(()=>inlineAssets(dir),/outside output/);
    fs.writeFileSync(file,'<script src="app.js"></script>');fs.writeFileSync(path.join(dir,'app.js'),'import("./x.js")');assert.throws(()=>inlineAssets(dir),/bundled/);
  }finally{fs.rmSync(dir,{recursive:true,force:true});}
});
