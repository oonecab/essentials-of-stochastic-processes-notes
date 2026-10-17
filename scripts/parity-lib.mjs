import { parse } from 'parse5';
import { createHash } from 'node:crypto';
import { walk, attr } from '../src/lib/controlled-html.mjs';

export const sha = data => createHash('sha256').update(data).digest('hex');
const normalize = text => text.replace(/\s+/g,' ').trim();
function textOf(node) {
  if (['script','style'].includes(node.tagName)) return '';
  return node.nodeName==='#text' ? node.value : (node.childNodes??[]).map(textOf).join('');
}
export function canonical(node) {
  if (node.nodeName==='#text') return normalize(node.value) || null;
  if (node.nodeName==='#comment') return null;
  return [node.tagName ?? node.nodeName,node.namespaceURI??'',(node.attrs??[]).map(a=>[a.namespace??'',a.prefix??'',a.name,a.value]).sort(),(node.content?.childNodes??node.childNodes??[]).map(canonical).filter(n=>n!==null)];
}
export function fingerprint(html) {
  const tree = parse(html,{sourceCodeLocationInfo:true});
  const nodes = walk(tree);
  const classes=n=>(attr(n,'class')??'').split(/\s+/);
  const originals=nodes.filter(n=>classes(n).includes('exercise')&&(attr(n,'id')??'').startsWith('ex'));
  const maths=nodes.filter(n=>n.tagName==='math'); const svgs=nodes.filter(n=>n.tagName==='svg');
  const raw=n=>{const l=n.sourceCodeLocation;return html.slice(l.startOffset,l.endOffset);};
  const body=nodes.find(n=>n.tagName==='body');
  return {
    dom:sha(JSON.stringify(canonical(tree))),
    exercise_ids:originals.map(n=>attr(n,'id')),
    head_metadata:sha(JSON.stringify(nodes.filter(n=>['meta','title','base'].includes(n.tagName)).map(canonical))),
    styles:sha(JSON.stringify(nodes.filter(n=>n.tagName==='style').map(n=>(n.childNodes??[]).map(c=>c.value??'').join('')))),
    body_text: sha(normalize(textOf(body))),
    mathml: sha(JSON.stringify(maths.map(canonical))),
    mathml_bytes: sha(maths.map(raw).join('')),
    svg: sha(JSON.stringify(svgs.map(canonical))),
    svg_bytes: sha(svgs.map(raw).join('')),
    anchors:nodes.filter(n=>attr(n,'id')!==undefined).map(n=>attr(n,'id')),
    links:nodes.filter(n=>n.tagName==='a'&&attr(n,'href')!==undefined).map(n=>attr(n,'href')),
    pdf_links:nodes.filter(n=>n.tagName==='a'&&(attr(n,'href')??'').includes('#page=')).map(n=>attr(n,'href')),
    code:sha(JSON.stringify(nodes.filter(n=>n.tagName==='code').map(n=>(n.childNodes??[]).map(textOf).join('')))),
    scripts:sha(JSON.stringify(nodes.filter(n=>n.tagName==='script').map(n=>n.childNodes.map(c=>c.value??'').join('')))),
    counts:{exercises:originals.length,self_checks:nodes.filter(n=>classes(n).includes('exercise')).length-originals.length,
      statements:nodes.filter(n=>classes(n).includes('statement')||classes(n).includes('source-statement')).length,mathml:maths.length,svg:svgs.length},
    js_bytes:nodes.filter(n=>n.tagName==='script').reduce((sum,n)=>sum+Buffer.byteLength(n.childNodes.map(c=>c.value??'').join('')),0),
  };
}
export function validateInternalAnchors(pages) {
  const parsed=new Map([...pages].map(([route,html])=>[route,walk(parse(html))]));
  const ids=new Map([...parsed].map(([route,nodes])=>[route,new Set(nodes.map(n=>attr(n,'id')).filter(Boolean))]));
  for(const [route,nodes] of parsed)for(const n of nodes){
    if(n.tagName!=='a'||!attr(n,'href'))continue;
    const url=new URL(attr(n,'href'),'https://reading-notes.invalid/'+route);
    if(url.origin!=='https://reading-notes.invalid'||!url.hash)continue;
    let target=decodeURIComponent(url.pathname).slice(1);if(target.endsWith('/'))target+='index.html';
    if(target.endsWith('.html')&&(!ids.has(target)||!ids.get(target).has(decodeURIComponent(url.hash.slice(1)))))throw new Error(`Missing internal anchor: ${route} -> ${attr(n,'href')}`);
  }
}
export function differences(expected,actual) {
  return Object.keys(expected).filter(key=>JSON.stringify(expected[key])!==JSON.stringify(actual[key]));
}
export function offlineDependencies(html) {
  const issues=[];
  const nodes=walk(parse(html));
  for(const n of nodes) {
    const tag=n.tagName;
    if (tag==='base'||tag==='iframe'||tag==='object'||tag==='embed'||tag==='astro-island') issues.push(`uncontrolled element ${tag}`);
    if(n.attrs?.some(a=>a.name.startsWith('on')))issues.push('inline event handler');
    for(const key of ['src','srcset','poster','data','xlink:href','href']) {
      const value=attr(n,key);
      if(!value || tag==='a' || (key==='href'&&!['link','use','image','script'].includes(tag)))continue;
      if(!value.startsWith('data:')&&!value.startsWith('#'))issues.push(`${tag}[${key}]=${value}`);
    }
    if(tag==='style'||attr(n,'style')) {
      const css=tag==='style'?(n.childNodes??[]).map(c=>c.value??'').join(''):attr(n,'style');
      if(/@import\b|image-set\s*\(/i.test(css))issues.push('CSS import/image-set');
      for(const m of css.matchAll(/url\(\s*['"]?([^)'"\s]+)/gi))if(!m[1].startsWith('#')&&!m[1].startsWith('data:'))issues.push('CSS URL '+m[1]);
    }
  }
  return issues;
}
