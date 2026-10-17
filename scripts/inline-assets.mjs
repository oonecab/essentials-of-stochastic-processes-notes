import fs from 'node:fs';
import path from 'node:path';
import { parse } from 'parse5';
import { walk, attr } from '../src/lib/controlled-html.mjs';

export function htmlFiles(directory) {
  return fs.readdirSync(directory,{withFileTypes:true}).flatMap(e => e.isDirectory() ? htmlFiles(path.join(directory,e.name)) : e.name.endsWith('.html') ? [path.join(directory,e.name)] : []);
}
export function inlineAssets(directory) {
  for (const file of htmlFiles(directory)) {
    let html = fs.readFileSync(file, 'utf8');
    const edits = [];
    for (const node of walk(parse(html,{sourceCodeLocationInfo:true}))) {
      const style = node.tagName === 'link' && attr(node,'rel') === 'stylesheet';
      const script = node.tagName === 'script' && attr(node,'src');
      if (!style && !script) continue;
      const url = attr(node, style ? 'href':'src');
      if (/^(?:[a-z]+:|\/\/)/i.test(url) || /[?#]/.test(url)) throw new Error(`Uncontrolled asset: ${url}`);
      const source = path.resolve(url.startsWith('/') ? directory : path.dirname(file), url.replace(/^\//,''));
      if (!source.startsWith(path.resolve(directory)+path.sep) || fs.lstatSync(source).isSymbolicLink()) throw new Error(`Asset outside output: ${url}`);
      const data = fs.readFileSync(source,'utf8');
      if (!style && /\bimport\s*(?:\(|[{'"*])|\bexport\s/.test(data)) throw new Error('Script must be bundled before inlining');
      const loc = node.sourceCodeLocation;
      edits.push({start:loc.startOffset,end:loc.endOffset,value:style ? `<style>${data}</style>` : `<script${attr(node,'type')==='module'?' type="module"':''}>${data}</script>`});
    }
    for (const edit of edits.sort((a,b)=>b.start-a.start)) html=html.slice(0,edit.start)+edit.value+html.slice(edit.end);
    fs.writeFileSync(file,html);
  }
}
