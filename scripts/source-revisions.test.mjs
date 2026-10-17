import test from 'node:test';
import assert from 'node:assert/strict';
import {sha} from './parity-lib.mjs';
import {reviewedIdentity} from '../src/lib/source-revisions.mjs';
test('later content requires a historical hash, unbroken review chain and bound review record',()=>{
  const original='<main id="topic"><details class="exercise" id="ex-1-1">question</details></main>';
  const html=original.replace('question','question and proof');
  const entry={html,metadata:{route:'book/notes/one.html',original_sha256:sha(original)}};
  const registry={pages:{[entry.metadata.route]:{original_sha256:sha(original),source_sha256:sha(html),history:[{from_sha256:sha(original),to_sha256:sha(html),reason:'reviewed proof',reviewed_anchors:['ex-1-1'],revision:'fixture'}]}}};
  const review={source_sha256:{[entry.metadata.route]:sha(html)}};
  assert.throws(()=>reviewedIdentity(entry,Buffer.from(original),{pages:{}},review),/Unreviewed/);
  reviewedIdentity(entry,Buffer.from(original),registry,review);
  assert.throws(()=>reviewedIdentity(entry,Buffer.from(original),registry,{}),/does not bind/);
  const bad={...entry,html:html.replace('id="ex-1-1"','id="ex-1-2"')};
  const row=registry.pages[entry.metadata.route];row.source_sha256=sha(bad.html);row.history[0].to_sha256=sha(bad.html);review.source_sha256[entry.metadata.route]=sha(bad.html);
  assert.throws(()=>reviewedIdentity(bad,Buffer.from(original),registry,review),/IDs changed/);
});
