import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {entries,syncMirrors} from '../src/lib/controlled-html.mjs';
import {validateInternalAnchors} from './parity-lib.mjs';

test('new book/page dry-run derives routes and generates absent checker mirrors',()=>{
  const base=fs.mkdtempSync(path.join(os.tmpdir(),'rn-catalog-'));
  try{
    fs.mkdirSync(path.join(base,'scripts'));fs.mkdirSync(path.join(base,'books'));
    const books=[{id:'existing',expected_pages:1},{id:'dummy',expected_pages:2}].map(b=>({...b,directory:'books/'+b.id,publish_prefix:b.id}));
    fs.writeFileSync(path.join(base,'books/catalog.json'),JSON.stringify({books}));
    fs.writeFileSync(path.join(base,'scripts/migration-state.json'),JSON.stringify({migrated_books:books.map(b=>b.id)}));
    for(const book of books)for(let i=0;i<book.expected_pages;i++){
      const directory=path.join(base,'src/content/books',book.id);fs.mkdirSync(directory,{recursive:true});
      const metadata={book:book.id,chapter:i,title:'fixture',printed_start:1,printed_end:1,pdf_start:1,pdf_end:1,exercise_range:[],statement_count:0,source_manifest:'fixture.json',route:book.id+'/notes/page'+i+'.html',legacy_path:book.directory+'/notes/page'+i+'.html'};
      fs.writeFileSync(path.join(directory,'page'+i+'.html'),'---\n'+JSON.stringify(metadata)+'\n---\n<!doctype html><html><head><title>fixture</title></head><body><main>fixture</main></body></html>');
    }
    const pages=entries(base);assert.equal(pages.length,3);assert.equal(pages.filter(p=>p.metadata.book==='dummy').length,2);
    assert.throws(()=>syncMirrors(pages,{base}),/differs/);
    syncMirrors(pages,{base,write:true});syncMirrors(pages,{base});
    assert.equal(fs.readFileSync(path.join(base,'books/dummy/notes/page1.html'),'utf8'),pages.at(-1).html);
  }finally{fs.rmSync(base,{recursive:true,force:true});}
});
test('same-page and cross-page anchors must resolve',()=>{
  const pages=new Map([['a.html','<a href="b.html#target">go</a>'],['b.html','<main id="target"></main>']]);
  validateInternalAnchors(pages);
  pages.set('b.html','<main id="other"></main>');assert.throws(()=>validateInternalAnchors(pages),/Missing internal anchor/);
  assert.throws(()=>validateInternalAnchors(new Map([['a.html','<a href="#missing">x</a>']])),/Missing internal anchor/);
});
