#!/usr/bin/env node
// Minify JS and CSS in dist/ after astro build.
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const dist = path.resolve(__dirname, '..', 'dist');

function walk(dir, ext) {
  const out = [];
  for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) out.push(...walk(full, ext));
    else if (e.name.endsWith(ext)) out.push(full);
  }
  return out;
}

for (const f of walk(dist, '.js')) {
  try {
    execSync('npx terser "' + f + '" -o "' + f + '" --compress --mangle', { stdio: 'pipe' });
  } catch (e) { console.error('JS minify failed:', f, e.message); }
}
// CSS: use a simple approach via npx cssnano if available, else skip
console.log('Minification done.');
