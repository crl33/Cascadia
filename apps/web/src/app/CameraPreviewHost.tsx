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
import { useEffect, useMemo, useRef, useState } from 'react';
import { API_BASE } from '../api/client';
import { useCameras, useVizBasins } from '../api/hooks';
import type { CameraRecord } from '../contracts/schemas';
import type { SceneController } from '../scene/SceneController';
import { useSceneStore } from '../state/store';
import { cameraAttentionByBasin } from '../layers/cameras/attention';
import { frameSrc, previewCameraIds } from './camera-preview-math';

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

  useEffect(() => {
    const node = cardRef.current;
    if (!node) return;
    return controller.trackScreenPosition(cam.lon, cam.lat, (pos) => {
      if (!pos) {
        node.style.display = 'none';
        return;
      }
      node.style.display = '';
      node.style.transform = `translate(${Math.round(pos.x)}px, ${Math.round(pos.y)}px)`;
    });
  }, [controller, cam.lon, cam.lat]);

  return (
    <div ref={cardRef} className={`camera-card${expanded ? ' expanded' : ''}`} data-testid={`camera-card-${cam.id}`}>
      <div className="camera-card-anchor" aria-hidden="true" />
      <div className="camera-card-body">
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
            <summary>tier {cam.tier} — why</summary>
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
