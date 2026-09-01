/**
 * overlay-layout: the shared UI occlusion service (mission §14). Persistent chrome marks
 * itself with `data-occlusion` and the placement solver reads the live rectangles — no
 * component hardcodes another component's pixels. Measured on demand (placement runs on
 * camera settle and card churn, not per animation frame), so no observers are needed.
 */
import type { Rect } from './card-layout';

export function collectOcclusions(root: Document = document): Rect[] {
  const rects: Rect[] = [];
  root.querySelectorAll<HTMLElement>('[data-occlusion]').forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return;
    rects.push({ left: r.left, top: r.top, right: r.right, bottom: r.bottom });
  });
  return rects;
}
