/**
 * card-layout: the deterministic placement solver for world-anchored HUD cards
 * (mission §13–14, §21). Never `origin = projected coordinate`: given an anchor, the card
 * size, the viewport and the UI occlusion rectangles, candidate placements are scored and
 * the best one wins — entirely inside the safe viewport, avoiding persistent chrome,
 * keeping the connector short, preferring the side away from the nearest edge.
 *
 * Pure and total: no DOM here. The caller collects occlusions from [data-occlusion]
 * elements (overlay-layout service) and applies {left, top} — never a transform: an
 * ancestor transform makes the card a Backdrop Root and silently kills its glass.
 *
 * Determinism and stability: candidates are evaluated in a fixed order and scoring is
 * integer-ish; the caller may pass `previous` — the previous winner is kept unless it is
 * now invalid or beaten by a clear margin (placement must not flip-flop per frame).
 */

export interface Rect {
  left: number;
  top: number;
  right: number;
  bottom: number;
}
export interface Size {
  width: number;
  height: number;
}
export interface Point {
  x: number;
  y: number;
}

export interface CardPlacement {
  name: string;
  left: number;
  top: number;
  /** True when no candidate fit and the result is a clamped best-effort. */
  clamped: boolean;
}

const SAFE_MARGIN_PX = 8;
/** Gap between the anchor point and the card's near edge. */
const ANCHOR_GAP_PX = 18;
/** A previous placement survives unless a challenger beats it by this much. */
const STICKINESS = 48;

interface Candidate {
  name: string;
  left: number;
  top: number;
}

function candidates(anchor: Point, card: Size): Candidate[] {
  const { width, height } = card;
  const cx = anchor.x - width / 2;
  const cy = anchor.y - height / 2;
  return [
    { name: 'above', left: cx, top: anchor.y - height - ANCHOR_GAP_PX },
    { name: 'below', left: cx, top: anchor.y + ANCHOR_GAP_PX },
    { name: 'right', left: anchor.x + ANCHOR_GAP_PX, top: cy },
    { name: 'left', left: anchor.x - width - ANCHOR_GAP_PX, top: cy },
    { name: 'above-right', left: anchor.x + ANCHOR_GAP_PX * 0.6, top: anchor.y - height - ANCHOR_GAP_PX * 0.6 },
    { name: 'above-left', left: anchor.x - width - ANCHOR_GAP_PX * 0.6, top: anchor.y - height - ANCHOR_GAP_PX * 0.6 },
    { name: 'below-right', left: anchor.x + ANCHOR_GAP_PX * 0.6, top: anchor.y + ANCHOR_GAP_PX * 0.6 },
    { name: 'below-left', left: anchor.x - width - ANCHOR_GAP_PX * 0.6, top: anchor.y + ANCHOR_GAP_PX * 0.6 },
  ];
}

const overlapArea = (a: Rect, b: Rect): number => {
  const w = Math.min(a.right, b.right) - Math.max(a.left, b.left);
  const h = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
  return w > 0 && h > 0 ? w * h : 0;
};

function score(c: Candidate, anchor: Point, card: Size, viewport: Size, occlusions: readonly Rect[]): number | null {
  const rect: Rect = { left: c.left, top: c.top, right: c.left + card.width, bottom: c.top + card.height };
  if (
    rect.left < SAFE_MARGIN_PX ||
    rect.top < SAFE_MARGIN_PX ||
    rect.right > viewport.width - SAFE_MARGIN_PX ||
    rect.bottom > viewport.height - SAFE_MARGIN_PX
  ) {
    return null; // hard requirement: entirely inside the safe viewport
  }
  let occluded = 0;
  for (const o of occlusions) occluded += overlapArea(rect, o);
  const centerX = c.left + card.width / 2;
  const centerY = c.top + card.height / 2;
  const connector = Math.hypot(centerX - anchor.x, centerY - anchor.y);
  // directional preference: away from the nearest viewport edge (§13 — near north prefer
  // below, near east prefer left, …), expressed as a mild penalty toward the edge side
  const towardTop = c.top < anchor.y - card.height ? 1 : 0;
  const towardBottom = c.top > anchor.y ? 1 : 0;
  const towardLeft = c.left < anchor.x - card.width ? 1 : 0;
  const towardRight = c.left > anchor.x ? 1 : 0;
  const nearTop = anchor.y < viewport.height * 0.33 ? 1 : 0;
  const nearBottom = anchor.y > viewport.height * 0.67 ? 1 : 0;
  const nearLeft = anchor.x < viewport.width * 0.33 ? 1 : 0;
  const nearRight = anchor.x > viewport.width * 0.67 ? 1 : 0;
  const edgePenalty =
    (nearTop * towardTop + nearBottom * towardBottom + nearLeft * towardLeft + nearRight * towardRight) * 120;
  return occluded * 4 + connector + edgePenalty;
}

export function placeCard(
  anchor: Point,
  card: Size,
  viewport: Size,
  occlusions: readonly Rect[],
  previous: string | null = null,
): CardPlacement {
  let best: { c: Candidate; s: number } | null = null;
  let prev: { c: Candidate; s: number } | null = null;
  for (const c of candidates(anchor, card)) {
    const s = score(c, anchor, card, viewport, occlusions);
    if (s === null) continue;
    if (c.name === previous) prev = { c, s };
    if (best === null || s < best.s) best = { c, s };
  }
  if (best === null) {
    // no candidate fits (tiny viewport / anchor off-edge): clamp the least-bad candidate
    const c = candidates(anchor, card)[0]!;
    const left = Math.min(Math.max(c.left, SAFE_MARGIN_PX), Math.max(SAFE_MARGIN_PX, viewport.width - card.width - SAFE_MARGIN_PX));
    const top = Math.min(Math.max(c.top, SAFE_MARGIN_PX), Math.max(SAFE_MARGIN_PX, viewport.height - card.height - SAFE_MARGIN_PX));
    return { name: 'clamped', left, top, clamped: true };
  }
  // stability: keep the previous placement while it is valid and not clearly beaten
  const winner = prev !== null && prev.s <= best.s + STICKINESS ? prev : best;
  return { name: winner.c.name, left: winner.c.left, top: winner.c.top, clamped: false };
}
