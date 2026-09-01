/**
 * WhiteTileDiscardPolicy — the GENERAL fix for USGS ImageryOnly's baked-white voids.
 *
 * The stock DiscardMissingTileImagePolicy compares against ONE reference tile and its
 * byte-length fast path only catches whites of that exact encoding (872 B at z13). The
 * research doc named the residual risk — "a different-sized white tile (other campaign,
 * other zoom) escapes" — and the owner's screenshot delivered it: z11–z12 San Juans
 * whites (≈2.4 KB) rendered as voids at basin framing.
 *
 * This policy inspects the DECODED tile: the whole image is downsampled into a 3×3
 * canvas (each sample averages a ninth of the tile), and only a tile whose EVERY region
 * averages ≥ WHITE_FLOOR discards. Real snowfields carry shadow/texture that pulls at
 * least one region below the floor; a service void is uniform 255. A discarded tile
 * renders the parent's real imagery (ImageryState.INVALID → ancestor upsample) — the
 * owner-desired result. Cost: one 3×3 drawImage + 36-byte read per loaded tile, off the
 * render loop's hot path.
 */

/** Region floor: a service void averages ≥252 across a whole ninth; textured snow/cloud
 * regions carry shadow and dip below. */
const WHITE_FLOOR = 252;
const GRID = 3;
/** This many void ninths and the WHOLE tile falls back to its parent (owner screenshots
 * 2026-09-01: per-pixel removal fringed every void; partial voids must fall back whole —
 * a slightly softer coastal tile beats any white block, black block, or outline). One
 * lone bright ninth stays: a single blown cloud/snow region must not soften real land. */
const VOID_REGIONS_TO_DISCARD = 2;

/** Pure decision over the GRID² region samples. */
export function samplesAreWhite(rgba: Uint8ClampedArray, floor = WHITE_FLOOR): boolean {
  if (rgba.length === 0) return false;
  let voidRegions = 0;
  for (let i = 0; i < rgba.length; i += 4) {
    if (rgba[i]! >= floor && rgba[i + 1]! >= floor && rgba[i + 2]! >= floor) voidRegions += 1;
  }
  return voidRegions >= VOID_REGIONS_TO_DISCARD;
}

type DiscardableImage = HTMLImageElement | HTMLCanvasElement | ImageBitmap;

export class WhiteTileDiscardPolicy {
  private readonly canvas: HTMLCanvasElement;
  private readonly ctx: CanvasRenderingContext2D | null;

  constructor() {
    this.canvas = document.createElement('canvas');
    this.canvas.width = GRID;
    this.canvas.height = GRID;
    this.ctx = this.canvas.getContext('2d', { willReadFrequently: true });
  }

  /** Duck-typed Cesium TileDiscardPolicy: no reference image to load — always ready. */
  isReady(): boolean {
    return true;
  }

  shouldDiscardImage(image: DiscardableImage): boolean {
    const ctx = this.ctx;
    if (!ctx) return false; // no 2D context: never discard on a guess
    try {
      ctx.clearRect(0, 0, GRID, GRID);
      ctx.drawImage(image, 0, 0, GRID, GRID);
      return samplesAreWhite(ctx.getImageData(0, 0, GRID, GRID).data);
    } catch {
      return false; // an undecodable/tainted image is a provider problem, not a void
    }
  }
}
