#!/usr/bin/env node
/**
 * Generates src/contracts/generated.ts from packages/contracts/schema/*.json.
 * SceneSummary.json is the superset schema (its $defs carry ContractEnvelope, Basin/River
 * visualization states, ProvenanceRef, Freshness…); the script asserts that every other
 * schema's definitions are contained in it so nothing is silently missed, then compiles once
 * to avoid duplicate type names. `--check` regenerates to memory and fails on drift.
 */
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { compile } from 'json-schema-to-typescript';

const here = dirname(fileURLToPath(import.meta.url));
const schemaDir = resolve(here, '../../../packages/contracts/schema');
const outFile = resolve(here, '../src/contracts/generated.ts');
const check = process.argv.includes('--check');

const files = readdirSync(schemaDir).filter((f) => f.endsWith('.json')).sort();
const schemas = Object.fromEntries(files.map((f) => [f, JSON.parse(readFileSync(resolve(schemaDir, f), 'utf8'))]));
const root = schemas['SceneSummary.json'];
if (!root) throw new Error('SceneSummary.json missing from schema dir');

for (const [file, schema] of Object.entries(schemas)) {
  if (file === 'SceneSummary.json') continue;
  const missing = Object.keys(schema.$defs ?? {}).filter((d) => !(d in root.$defs));
  if (!(schema.title in root.$defs) && schema.title !== 'SceneSummary') missing.push(schema.title);
  if (missing.length) throw new Error(`${file} has definitions not covered by SceneSummary.json: ${missing.join(', ')}`);
}

const banner = `/* eslint-disable */
/**
 * GENERATED — do not edit. Source: packages/contracts/schema/*.json (${files.join(', ')}).
 * Regenerate with \`npm run contracts:gen\`; \`npm run contracts:check\` fails on drift.
 */`;

const ts = await compile(structuredClone(root), 'SceneSummary', {
  bannerComment: banner,
  additionalProperties: false,
  strictIndexSignatures: true,
  style: { singleQuote: true, semi: true, printWidth: 110 },
  cwd: schemaDir,
});

if (check) {
  const current = existsSync(outFile) ? readFileSync(outFile, 'utf8') : '';
  if (current !== ts) {
    console.error('contracts:check FAILED — src/contracts/generated.ts is out of date. Run npm run contracts:gen.');
    process.exit(1);
  }
  console.log('contracts:check OK');
} else {
  writeFileSync(outFile, ts);
  console.log(`wrote ${outFile} (${ts.length} bytes)`);
}
