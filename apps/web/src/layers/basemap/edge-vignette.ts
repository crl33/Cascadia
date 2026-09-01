/**
 * The intentional world edge (mission §8, option D — vignetted regional earth). The globe
 * outside HARD_DOMAIN is shader-discarded into the design's canvas; without treatment the
 * domain ends in a razor cut and the region reads as a floating map sheet (harness frame
 * D-000). This layer drapes a feathered dark frame over the OUTER band of the domain so
 * the world dissolves into the canvas — the useful Pacific Northwest stays illuminated,
 * the edge looks composed, and no extra tiles are ever requested (one static 512² canvas).
 */
import { ImageryLayer, Rectangle, SingleTileImageryProvider } from 'cesium';
import { HARD_DOMAIN } from '../../camera/envelope';

/** Fraction of the domain's span that fades at each edge. Owner 2026-09-01: the previous
 * wide rounded feather made max-out read as an iOS APP ICON — the fade is now narrow,
 * square-edged and partial, so the world reads as a map sheet dimming at its margin. */
const FEATHER = 0.06;
const EDGE_ALPHA = 0.82;
const SIZE = 512;
/** Matches --canvas / globe.baseColor: hsl(222 52% 6%). */
const CANVAS_DARK = 'rgba(7, 12, 23,';

export function createDomainVignetteLayer(): ImageryLayer | null {
  const canvas = document.createElement('canvas');
  canvas.width = SIZE;
  canvas.height = SIZE;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  // four straight-edged linear fades — no rounded geometry anywhere
  const inset = Math.round(SIZE * FEATHER);
  const edges: [number, number, number, number, number, number, number, number][] = [
    [0, 0, 0, inset, 0, 0, SIZE, inset], // top: gradient from y0..inset over full width
    [0, SIZE, 0, SIZE - inset, 0, SIZE - inset, SIZE, inset], // bottom
    [0, 0, inset, 0, 0, 0, inset, SIZE], // left
    [SIZE, 0, SIZE - inset, 0, SIZE - inset, 0, inset, SIZE], // right
  ];
  for (const [gx0, gy0, gx1, gy1, rx, ry, rw, rh] of edges) {
    const g = ctx.createLinearGradient(gx0, gy0, gx1, gy1);
    g.addColorStop(0, `${CANVAS_DARK} ${EDGE_ALPHA})`);
    g.addColorStop(1, `${CANVAS_DARK} 0)`);
    ctx.fillStyle = g;
    ctx.fillRect(rx, ry, rw, rh);
  }
  const layer = new ImageryLayer(
    new SingleTileImageryProvider({
      url: canvas.toDataURL('image/png'),
      rectangle: Rectangle.fromDegrees(HARD_DOMAIN.west, HARD_DOMAIN.south, HARD_DOMAIN.east, HARD_DOMAIN.north),
      tileWidth: SIZE,
      tileHeight: SIZE,
    }),
  );
  return layer;
}
