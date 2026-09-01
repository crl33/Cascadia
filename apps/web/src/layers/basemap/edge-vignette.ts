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

/** Fraction of the domain's span that fades at each edge. */
const FEATHER = 0.16;
const SIZE = 512;
/** Matches --canvas / globe.baseColor: hsl(222 52% 6%). */
const CANVAS_DARK = 'rgb(7, 12, 23)';

export function createDomainVignetteLayer(): ImageryLayer | null {
  const canvas = document.createElement('canvas');
  canvas.width = SIZE;
  canvas.height = SIZE;
  const ctx = canvas.getContext('2d');
  if (!ctx) return null;
  ctx.fillStyle = CANVAS_DARK;
  ctx.fillRect(0, 0, SIZE, SIZE);
  // punch a soft transparent interior: a blurred inset rectangle removed from the frame
  const inset = Math.round(SIZE * FEATHER);
  ctx.globalCompositeOperation = 'destination-out';
  ctx.filter = `blur(${Math.round(inset * 0.55)}px)`;
  ctx.fillStyle = 'rgb(0,0,0)';
  ctx.beginPath();
  ctx.roundRect(inset, inset, SIZE - inset * 2, SIZE - inset * 2, inset * 0.8);
  ctx.fill();
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
