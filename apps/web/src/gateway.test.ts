/**
 * The Pages gateway's PROXY branch, which no other test exercises: e2e runs against the
 * fixture stub (no BACKEND_ORIGIN), so a defect that lives only in the proxy path ships
 * straight to production. That happened on 2026-08-28: the security-header stamp rewrote
 * every upstream Content-Type to application/json, EventSource refused the SSE stream, and
 * live invalidation was dead on the deployed site while everything local stayed green.
 * These tests run the real onRequest with a stubbed global fetch standing in for Railway.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
// eslint-disable-next-line import/no-relative-packages -- the gateway deploys from repo root, outside the app tree
import { onRequest } from '../../../functions/[[path]].js';

const ENV = { BACKEND_ORIGIN: 'https://origin.example' };

function upstream(contentType: string, body: string): Response {
  return new Response(body, { status: 200, headers: { 'Content-Type': contentType } });
}

async function proxied(path: string, response: Response): Promise<{ res: Response; sent: URL }> {
  let sent: URL | null = null;
  vi.stubGlobal('fetch', vi.fn(async (input: URL | RequestInfo) => {
    sent = new URL(String(input));
    return response;
  }));
  const res = (await onRequest({ request: new Request(`https://gateway.example${path}`), env: ENV })) as Response;
  if (sent === null) throw new Error('the proxy branch never called fetch');
  return { res, sent };
}

afterEach(() => vi.unstubAllGlobals());

describe('gateway proxy headers', () => {
  it('the SSE stream keeps text/event-stream — EventSource aborts on anything else', async () => {
    const { res } = await proxied('/system/events', upstream('text/event-stream', 'retry: 5000\n\n'));
    expect(res.headers.get('Content-Type')).toBe('text/event-stream');
    // the security stamp still applies; it just may not overwrite what the backend said
    expect(res.headers.get('X-Content-Type-Options')).toBe('nosniff');
    expect(res.headers.get('Cache-Control')).toBe('no-store');
  });

  it('JSON responses stay JSON, with path and query preserved upstream', async () => {
    const { res, sent } = await proxied(
      '/viz/rivers?basin=basin:skagit',
      upstream('application/json', '{"items":[]}'),
    );
    expect(res.headers.get('Content-Type')).toBe('application/json');
    expect(sent.origin).toBe('https://origin.example');
    expect(sent.pathname).toBe('/viz/rivers');
    expect(sent.search).toBe('?basin=basin:skagit');
  });

  it('writes are refused before any fetch happens', async () => {
    const fetchSpy = vi.fn();
    vi.stubGlobal('fetch', fetchSpy);
    const res = (await onRequest({
      request: new Request('https://gateway.example/basins', { method: 'POST' }),
      env: ENV,
    })) as Response;
    expect(res.status).toBe(405);
    expect(fetchSpy).not.toHaveBeenCalled();
  });
});
