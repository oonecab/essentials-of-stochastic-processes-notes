import fs from 'node:fs';
import path from 'node:path';
import { root } from './controlled-html.mjs';
export const deepLinkSource=fs.readFileSync(path.join(root,'src/scripts/deep-link-settle.js'),'utf8');
export const deepLinkMarkup='<script data-rn-island="deep-link-settle">'+deepLinkSource+'</script>';
export function islandsFor(book){return book==='csapp'?deepLinkMarkup:'';}
export function separateApprovedIsland(html,book){
  const expected=islandsFor(book),matches=html.match(/<script data-rn-island="deep-link-settle">[\s\S]*?<\/script>/g)??[];
  if(expected?(matches.length!==1||matches[0]!==expected):matches.length!==0)throw new Error('Missing or changed approved navigation island');
  return expected?html.replace(expected,''):html;
}
