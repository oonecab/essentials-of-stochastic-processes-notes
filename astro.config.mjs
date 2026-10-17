import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  outDir: './tmp/reading-notes-migration/astro-output',
  publicDir: './public',
  compressHTML: false,
  build: { format: 'file', inlineStylesheets: 'always' },
  vite: { build: { assetsInlineLimit: Number.MAX_SAFE_INTEGER } },
});
