import type { StubFixtures } from './stub-data.mjs';
export function route(fx: StubFixtures, pathname: string, params: URLSearchParams): unknown;
export function isErrorResult(result: unknown): result is { status: number; body: unknown };
