/**
 * CameraPreviewHost: the DOM half of the flood-observation network. Cesium owns the markers
 * (CameraLayer); this component owns the HTML preview windows, anchored to their geographic
 * position through SceneController.trackScreenPosition — the projection callback writes the
 * card's transform DIRECTLY on the DOM node, so no React state changes per frame.
 *
 * WHICH cameras preview is a coarse, semantic decision (previewCameraIds: pinned + capped
 * Tier-A autos at local band). Frames respect each camera's own refresh cadence via time
 * buckets (frameSrc) — the upstream is never polled faster than it updates, and only VISIBLE
 * cameras load frames at all (WSDOT low-volume terms; cost discipline).
 *
 * Honesty on the card: provider attribution always; the frame's age is shown as OUR load
 * bucket ("frame requested <time>"), because an <img> cannot read Last-Modified — the card
 * never claims a capture time the provider did not state. Tier reasons are visible on
 * demand. No face/person/plate processing exists anywhere in this system.
 */
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { API_BASE } from '../api/client';
import { useCameras, useVizBasins } from '../api/hooks';
import type { CameraRecord } from '../contracts/schemas';
import { useDismiss } from '../design-system/dismiss';
import type { SceneController } from '../scene/SceneController';
import { useSceneStore } from '../state/store';
import { cameraAttentionByBasin } from '../layers/cameras/attention';
import { placeCard, type Rect } from './card-layout';
import { collectOcclusions } from './overlay-layout';
import { frameSrc, previewCameraIds } from './camera-preview-math';

/** Below this width the card detaches into a bottom sheet (§17) — geographic anchoring
 * gives way to legibility; the ringed marker keeps the correspondence. */
const SHEET_BREAKPOINT_PX = 640;
const OCCLUSION_CACHE_MS = 600;

interface Props {
  controller: SceneController;
}

function PreviewCard({ controller, cam, pinned, expanded, attention }: {
  controller: SceneController;
  cam: CameraRecord;
  pinned: boolean;
  expanded: boolean;
  attention: { kind: string; detail: string } | null;
}) {
  const cardRef = useRef<HTMLDivElement>(null);
  const connectorRef = useRef<HTMLDivElement>(null);
  const pinCamera = useSceneStore((s) => s.pinCamera);
  // failure tracks the URL it happened on, so a new bucket un-fails without any effect
  const [failedSrc, setFailedSrc] = useState<string | null>(null);
  // The refresh bucket advances on the camera's own cadence; a 30 s ticker checks cheaply.
  const [nowMs, setNowMs] = useState(() => Date.now());
  useEffect(() => {
    const t = setInterval(() => setNowMs(Date.now()), 30_000);
    return () => clearInterval(t);
  }, []);
  const src = useMemo(() => frameSrc(cam, nowMs, API_BASE), [cam, nowMs]);
  const failed = failedSrc === src;

  // Dismissal (owner 2026-09-01): MAP clicks minimize the preview — and only map clicks.
  // Canvas interactions route through the pick pipeline (empty map or another entity →
  // unpin; marker → toggle/replace); clicks on panels and menus never touch the card and
  // never fall through. Escape and the ✕ remain.
  const unpin = useCallback(() => pinCamera(null), [pinCamera]);
  useDismiss(cardRef, unpin, { enabled: pinned, pointer: false });

  useEffect(() => {
    const node = cardRef.current;
    const connector = connectorRef.current;
    if (!node) return;
    // Spatial HUD placement (§11–§14): the solver scores candidate placements against the
    // viewport and the live [data-occlusion] chrome — never `origin = projected point`,
    // never a transform (an ancestor transform makes the glass body a Backdrop Root and
    // silently kills its blur: the flat-dark-card defect). Imperative DOM per frame by
    // design — no React state here (renderer-boundary rule).
    let occlusions: Rect[] = [];
    let occlusionsAt = 0;
    let lastPlacement: string | null = null;
    return controller.trackScreenPosition(cam.lon, cam.lat, (pos) => {
      if (!pos) {
        node.style.display = 'none';
        if (connector) connector.style.display = 'none';
        return;
      }
      node.style.display = '';
      const sheet = window.innerWidth < SHEET_BREAKPOINT_PX;
      node.classList.toggle('camera-card-sheet', sheet);
      if (sheet) {
        node.style.left = '';
        node.style.top = '';
        if (connector) connector.style.display = 'none';
        return;
      }
      const now = performance.now();
      if (now - occlusionsAt > OCCLUSION_CACHE_MS) {
        occlusions = collectOcclusions();
        occlusionsAt = now;
      }
      const card = { width: node.offsetWidth || 232, height: node.offsetHeight || 200 };
      const viewport = { width: window.innerWidth, height: window.innerHeight };
      const placed = placeCard({ x: pos.x, y: pos.y }, card, viewport, occlusions, lastPlacement);
      lastPlacement = placed.clamped ? null : placed.name;
      node.style.left = `${Math.round(placed.left)}px`;
      node.style.top = `${Math.round(placed.top)}px`;
      node.dataset.placement = placed.name;
      if (connector) {
        // leader line from the card's nearest edge midpoint to the anchor (§18)
        const cx = Math.min(Math.max(pos.x, placed.left), placed.left + card.width);
        const cy = Math.min(Math.max(pos.y, placed.top), placed.top + card.height);
        const dx = pos.x - cx;
        const dy = pos.y - cy;
        const len = Math.hypot(dx, dy);
        if (len < 6) {
          connector.style.display = 'none';
        } else {
          connector.style.display = '';
          connector.style.left = `${Math.round(cx)}px`;
          connector.style.top = `${Math.round(cy)}px`;
          connector.style.width = `${Math.round(len)}px`;
          connector.style.transform = `rotate(${Math.atan2(dy, dx)}rad)`;
        }
      }
    });
  }, [controller, cam.lon, cam.lat]);

  return (
    <div ref={cardRef} className={`camera-card${expanded ? ' expanded' : ''}`} data-testid={`camera-card-${cam.id}`}>
      <div ref={connectorRef} className="camera-card-connector" aria-hidden="true" />
      <div className="camera-card-body glass-surface glass-panel shape-sheet">
        <header className="camera-card-header">
          <span className="camera-card-name">{cam.name}</span>
          <button
            type="button"
            className="camera-card-pin"
            data-testid={`camera-card-${pinned ? 'unpin' : 'pin'}`}
            title={pinned ? 'Unpin this camera' : 'Pin this camera open'}
            onClick={() => pinCamera(pinned ? null : cam.id)}
          >
            {pinned ? '✕' : '⌖'}
          </button>
        </header>
        {failed ? (
          <div className="camera-card-fallback" role="status">
            frame unavailable right now — the marker stays; the instrument may be offline
          </div>
        ) : (
          <img
            className="camera-card-frame"
            src={src}
            alt={`Current frame: ${cam.name}`}
            onError={() => setFailedSrc(src)}
          />
        )}
        <footer className="camera-card-meta">
          {attention ? (
            <span className="camera-card-attention" data-testid="camera-card-attention">
              Highlighted: {attention.detail} — camera {cam.reasons[0]?.replaceAll('_', ' ') ?? 'in this basin'}
            </span>
          ) : null}
          <span className="camera-card-attribution">{cam.attribution}</span>
          <span className="camera-card-freshness">
            refresh ≤ {Math.round(cam.refresh_seconds / 60)} min
            {cam.orientation ? ` · facing ${cam.orientation.cardinal}` : ' · orientation unknown'}
          </span>
          <details className="camera-card-reasons">
            <summary>Why this camera?</summary>
            <ul>
              {cam.reasons.map((reason) => (
                <li key={reason}>{reason.replaceAll('_', ' ')}</li>
              ))}
            </ul>
          </details>
        </footer>
      </div>
    </div>
  );
}

export function CameraPreviewHost({ controller }: Props) {
  const cameraSet = useCameras();
  const vizBasins = useVizBasins();
  const attention = useMemo(() => cameraAttentionByBasin(vizBasins.data), [vizBasins.data]);
  const band = useSceneStore((s) => s.altitudeBand);
  const selectedBasinId = useSceneStore((s) => s.selectedBasinId);
  const pinnedCameraId = useSceneStore((s) => s.pinnedCameraId);

  const shown = useMemo(() => {
    if (!cameraSet.data) return [] as CameraRecord[];
    const ids = previewCameraIds(cameraSet.data.cameras, band, selectedBasinId, pinnedCameraId);
    return ids
      .map((id) => cameraSet.data!.cameras.find((c) => c.id === id))
      .filter((c): c is CameraRecord => c !== undefined);
  }, [cameraSet.data, band, selectedBasinId, pinnedCameraId]);

  if (shown.length === 0) return null;
  return (
    <div className="camera-preview-host" data-testid="camera-preview-host">
      {shown.map((cam) => (
        <PreviewCard
          key={cam.id}
          controller={controller}
          cam={cam}
          pinned={cam.id === pinnedCameraId}
          expanded={cam.id === pinnedCameraId}
          attention={cam.basin_id !== null ? attention[cam.basin_id] ?? null : null}
        />
      ))}
    </div>
  );
}
