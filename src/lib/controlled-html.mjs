import fs from 'node:fs';
import path from 'node:path';
import { parse } from 'parse5';

export const root = process.cwd();
export const stage = path.join(root, 'tmp/reading-notes-migration');
export function walk(node) {
  return [node, ...(node.childNodes ?? []).flatMap(walk)];
}
export function attr(node, name) { return node.attrs?.find(a => a.name === name)?.value; }
export function readSource(filename) {
  const source = fs.readFileSync(filename, 'utf8');
  const match = source.match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) throw new Error(`Missing controlled JSON frontmatter: ${filename}`);
  const metadata = JSON.parse(match[1]);
  for (const key of ['book', 'chapter', 'title', 'printed_start', 'printed_end', 'pdf_start', 'pdf_end', 'exercise_range', 'statement_count', 'source_manifest']) {
    if (!(key in metadata)) throw new Error(`Missing ${key}: ${filename}`);
  }
  const html = source.slice(match[0].length).replace(/<!-- RN:include ([\w/.-]+) -->/g, (_, name) => {
    if (!/^(styles|scripts)\/[a-z0-9-]+\.(css|js)$/.test(name)) throw new Error('Invalid shared asset');
    return fs.readFileSync(path.join(root, 'src', name), 'utf8');
  });
  return { metadata, html, filename };
}
export function entries() {
  const state = JSON.parse(fs.readFileSync(path.join(root, 'scripts/migration-state.json'), 'utf8'));
  const mode = JSON.parse(fs.readFileSync(path.join(stage, 'build-state.json'), 'utf8'));
  if (mode.shell) return [];
  return state.migrated_books.flatMap(book => {
    const directory = path.join(root, 'src/content/books', book);
    return fs.readdirSync(directory).filter(f => f.endsWith('.html')).sort().map(file => readSource(path.join(directory, file)));
  });
}

// Locations preserve the reviewed bytes, including MathML and SVG namespaces.
// Components own semantic boundaries; the HTML parser is never used to rewrite them.
export function segments(html) {
  const tree = parse(html, { sourceCodeLocationInfo: true });
  const result = [];
  function inspect(node) {
    const classes = (attr(node, 'class') ?? '').split(/\s+/);
    const type = node.tagName === 'header' ? 'Header'
      : classes.includes('chapter-sidebar') ? 'Toc'
      : classes.includes('annotation-sidebar') ? 'AnnotationRail'
      : classes.includes('chapter-nav') ? 'ChapterNav'
      : classes.includes('exercise') ? 'Exercise'
      : classes.includes('code-pair') ? 'CodePair'
      : node.tagName === 'figure' ? 'Figure'
      : node.tagName === 'math' ? 'MathBlock' : null;
    const loc = node.sourceCodeLocation;
    if (type && loc && loc.endOffset > loc.startOffset) result.push({ type, start: loc.startOffset, end: loc.endOffset });
    else for (const child of node.childNodes ?? []) inspect(child);
  }
  inspect(tree);
  const parts = []; let offset = 0;
  for (const item of result.sort((a,b) => a.start-b.start)) {
    if (item.start < offset) throw new Error('Overlapping controlled fragments');
    if (item.start > offset) parts.push({type: 'Raw', html: html.slice(offset, item.start)});
    parts.push({type: item.type, html: html.slice(item.start, item.end)}); offset = item.end;
  }
  if (offset < html.length) parts.push({type: 'Raw', html: html.slice(offset)});
  return parts;
}
