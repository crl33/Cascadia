#!/usr/bin/env node
/**
 * Dev stub API: a dependency-free Node http server implementing the SPIKE API SPEC from the
 * committed fixtures (see stub-data.mjs). Read-only (GET/OPTIONS only), CORS allowlisted to the
 * Vite dev/preview origins plus CASCADE_CORS_ORIGINS, security headers on every response.
 * It never calls a provider. PORT defaults to 8000.
 */
import { createServer } from 'node:http';
import { loadFixtures } from './stub-load.mjs';
import { isErrorResult, route } from './stub-router.mjs';

const PORT = Number(process.env.PORT ?? 8000);
const ORIGINS = new Set(['http://localhost:5173', 'http://localhost:4173', ...(process.env.CASCADE_CORS_ORIGINS ?? '').split(',').map((s) => s.trim()).filter(Boolean)]);
const fx = loadFixtures();

const server = createServer((req, res) => {
  const origin = req.headers.origin;
  const headers = {
    'Content-Type': 'application/json; charset=utf-8',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Cache-Control': 'no-store',
  };
  if (origin && ORIGINS.has(origin)) {
    headers['Access-Control-Allow-Origin'] = origin;
    headers['Vary'] = 'Origin';
    headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS';
    headers['Access-Control-Allow-Headers'] = 'Accept, Content-Type';
  }
  if (req.method === 'OPTIONS') { res.writeHead(204, headers); return res.end(); }
  if (req.method !== 'GET') { res.writeHead(405, headers); return res.end(JSON.stringify({ detail: 'read-only API' })); }
  const url = new URL(req.url ?? '/', `http://localhost:${PORT}`);
  let pathname;
  try { pathname = decodeURIComponent(url.pathname); } catch { res.writeHead(400, headers); return res.end(JSON.stringify({ detail: 'bad path' })); }
  if (pathname.length > 256) { res.writeHead(414, headers); return res.end(JSON.stringify({ detail: 'path too long' })); }
  let result;
  try { result = route(fx, pathname, url.searchParams); } catch (err) { console.error(err); result = { status: 500, body: { detail: 'stub error' } }; }
  const isError = isErrorResult(result);
  res.writeHead(isError ? result.status : 200, headers);
  res.end(JSON.stringify(isError ? result.body : result));
});

server.listen(PORT, '127.0.0.1', () => console.log(`cascadia-papsukkal stub API listening on http://localhost:${PORT} (fixtures only; no provider calls)`));
