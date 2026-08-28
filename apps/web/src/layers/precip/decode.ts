/**
 * Decoding one FieldRasterState's packed cells: base64 -> gzip -> uint16 LE -> mm, with the
 * sentinel becoming NaN (absence, never zero). Pure but async (DecompressionStream); no
 * Cesium, no React — tested directly in decode.test.ts.
 */
import type { FieldRasterState } from '../../contracts/schemas';

export async function decodeFieldCells(state: FieldRasterState): Promise<Float32Array> {
  const packed = Uint8Array.from(atob(state.cells_b64), (c) => c.charCodeAt(0));
  const stream = new Blob([packed]).stream().pipeThrough(new DecompressionStream('gzip'));
  const raw = new Uint8Array(await new Response(stream).arrayBuffer());
  const expected = state.spec.nx * state.spec.ny * 2;
  if (raw.byteLength !== expected) {
    throw new Error(`field ${state.field}: decoded ${raw.byteLength} bytes, spec says ${expected}`);
  }
  const cells = new Uint16Array(raw.buffer, raw.byteOffset, raw.byteLength / 2);
  const out = new Float32Array(cells.length);
  for (let i = 0; i < cells.length; i += 1) {
    out[i] = cells[i] === state.sentinel ? Number.NaN : cells[i] * state.scale;
  }
  return out;
}
