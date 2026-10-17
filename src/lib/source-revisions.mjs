// Preserve the I028 source snapshot while allowing explicitly reviewed later edits.
import fs from 'node:fs';
import {execFileSync} from 'node:child_process';
import {sha,fingerprint} from '../../scripts/parity-lib.mjs';

export function reviewedIdentity(entry,frozen,registry,review){
  const original=sha(frozen),current=sha(entry.html);
  if(original!==entry.metadata.original_sha256)throw new Error('Historical source identity changed');
  if(current===original)return {source_sha256:current,original_sha256:original,revision:null};
  const row=registry.pages?.[entry.metadata.route];
  if(!row||row.original_sha256!==original||row.source_sha256!==current||!row.history?.length)throw new Error('Unreviewed source revision: '+entry.metadata.route);
  let previous=original;
  for(const change of row.history){
    if(change.from_sha256!==previous||!change.reason||!change.reviewed_anchors?.length)throw new Error('Broken source review chain');
    previous=change.to_sha256;
  }
  if(previous!==current||review.source_sha256?.[entry.metadata.route]!==current)throw new Error('Current content review does not bind source');
  const before=fingerprint(frozen.toString()),after=fingerprint(entry.html);
  if(JSON.stringify(before.exercise_ids)!==JSON.stringify(after.exercise_ids))throw new Error('Original exercise IDs changed');
  let i=0;for(const anchor of after.anchors)if(anchor===before.anchors[i])i++;
  if(i!==before.anchors.length)throw new Error('Original anchors removed or reordered');
  return {source_sha256:current,original_sha256:original,revision:row.history.at(-1).revision};
}

export function checkSource(entry){
  const state=JSON.parse(fs.readFileSync('scripts/migration-state.json'));
  const frozen=execFileSync('git',['show',`${state.baseline_ref}:${entry.metadata.legacy_path}`],{maxBuffer:32*1024*1024});
  const registry=fs.existsSync('src/content-revisions.json')?JSON.parse(fs.readFileSync('src/content-revisions.json')):{pages:{}};
  const row=registry.pages?.[entry.metadata.route];
  const review=row?JSON.parse(fs.readFileSync(row.review_record)):{};
  return {...reviewedIdentity(entry,frozen,registry,review),frozen};
}
