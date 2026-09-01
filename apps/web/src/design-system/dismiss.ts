/**
 * useDismiss — THE dismissal primitive (mission §12). Every dismissible floating surface
 * (camera previews, popovers, transient inspectors, menus) gets the same contract:
 *
 *   - pointerdown OUTSIDE the surface dismisses;
 *   - Escape dismisses;
 *   - interaction INSIDE never dismisses;
 *   - the close affordance stays (this hook adds behavior, it removes nothing).
 *
 * pointerdown, not click: dismissal should feel immediate, and a drag that starts on the
 * map (camera pan) should close the surface at its first touch, not on release. Capture
 * phase so a stopPropagation inside other handlers cannot strand an open surface.
 */
import { useEffect, type RefObject } from 'react';

export interface DismissOptions {
  enabled?: boolean;
  /** Targets for which the OUTSIDE-pointer rule must defer to another owner — e.g. the
   * Cesium canvas, whose clicks are routed by the pick pipeline (a marker click must
   * toggle/replace, an empty-map click closes via SceneController.onEmptyClick). Escape
   * still dismisses regardless. */
  ignore?: (target: EventTarget | null) => boolean;
}

export function useDismiss(
  ref: RefObject<HTMLElement | null>,
  onDismiss: () => void,
  options: DismissOptions = {},
): void {
  const { enabled = true, ignore } = options;
  useEffect(() => {
    if (!enabled) return;
    const onPointerDown = (event: PointerEvent) => {
      const el = ref.current;
      if (!el) return;
      if (event.target instanceof Node && el.contains(event.target)) return;
      if (ignore?.(event.target)) return;
      onDismiss();
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onDismiss();
    };
    document.addEventListener('pointerdown', onPointerDown, true);
    document.addEventListener('keydown', onKeyDown, true);
    return () => {
      document.removeEventListener('pointerdown', onPointerDown, true);
      document.removeEventListener('keydown', onKeyDown, true);
    };
  }, [ref, onDismiss, enabled, ignore]);
}

/** The standard ignore predicate for world-anchored surfaces: canvas interaction belongs
 * to the pick pipeline, never to blind outside-click dismissal. */
export const ignoreCanvas = (target: EventTarget | null): boolean => target instanceof HTMLCanvasElement;
