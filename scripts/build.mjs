import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { inlineAssets } from './inline-assets.mjs';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
process.chdir(root);
if (process.versions.node !== '24.21.0') throw new Error('Build requires pinned Node 24.21.0');
const shell = process.argv.includes('--shell');
const stage = path.join(root, 'tmp/reading-notes-migration');
fs.mkdirSync(stage, { recursive: true });
fs.writeFileSync(path.join(stage, 'build-state.json'), JSON.stringify({ shell }));
if (!shell) throw new Error('No book has passed the migration gate; use --shell for the scaffold');
const start = performance.now();
const astroPackage = JSON.parse(fs.readFileSync(path.join(root, 'node_modules/astro/package.json'), 'utf8'));
const result = spawnSync(process.execPath, [path.join(root, 'node_modules/astro', astroPackage.bin.astro), 'build'], {
  stdio: 'inherit', env: { ...process.env, ASTRO_TELEMETRY_DISABLED: '1' },
});
if (result.status !== 0) process.exit(result.status ?? 1);
const output = path.join(stage, 'astro-output');
inlineAssets(output);
const target = path.join(stage, 'shell-dist');
fs.rmSync(target, { recursive: true, force: true });
fs.cpSync(output, target, { recursive: true });
const report = { status: 'passed', mode: 'empty_scaffold', seconds: (performance.now()-start)/1000, output: path.relative(root,target) };
fs.writeFileSync(path.join(stage, 'scaffold-build.json'), JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report));
