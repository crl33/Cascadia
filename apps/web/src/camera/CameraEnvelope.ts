/**
 * CameraEnvelope: the soft cinematic constraint (mission §2). The user's hand is never
 * fought mid-gesture; on idle (camera.moveEnd) a pose outside the operating envelope —
 * target beyond the PNW, height past the zoom band, pitch past the band's tilt cap,
 * heading off north — is corrected with ONE short flight back into frame. Pointerdown
 * cancels the correction instantly (the spring always loses to the hand) and it re-arms
 * on the next idle. Reduced motion corrects with a cut.
 *
 * The decision is the pure `clampToEnvelope` (envelope.ts); this class is only wiring.
 * React never touches it; SceneController owns its lifecycle.
 */
import { Cartesian3, Math as CesiumMath, type Viewer } from 'cesium';
import { minimumJerk, type MotionPreference } from '../design-system/motion';
import type { Band } from '../scene/bands';
import { clampToEnvelope } from './envelope';
import type { CameraController } from './CameraController';

const CORRECTION_DURATION_S = 0.7;

export class CameraEnvelope {
  private correcting = false;
  private motion: MotionPreference;
  private readonly removeListeners: () => void;

  constructor(
    private readonly viewer: Viewer,
    private readonly camera: CameraController,
    private readonly currentBand: () => Band,
    motion: MotionPreference,
  ) {
    this.motion = motion;
    const onMoveEnd = () => this.onIdle();
    viewer.camera.moveEnd.addEventListener(onMoveEnd);
    const canvas = viewer.scene.canvas;
    const onPointerDown = () => {
      if (!this.correcting) return;
      this.correcting = false;
      viewer.camera.cancelFlight();
    };
    canvas.addEventListener('pointerdown', onPointerDown);
    this.removeListeners = () => {
      viewer.camera.moveEnd.removeEventListener(onMoveEnd);
      canvas.removeEventListener('pointerdown', onPointerDown);
    };
  }

  setMotionPreference(motion: MotionPreference): void {
    this.motion = motion;
  }

  dispose(): void {
    this.removeListeners();
  }

  private onIdle(): void {
    if (this.correcting || this.camera.flightActive) return;
    const cam = this.viewer.camera;
    const carto = cam.positionCartographic;
    const correction = clampToEnvelope({
      lonDeg: CesiumMath.toDegrees(carto.longitude),
      latDeg: CesiumMath.toDegrees(carto.latitude),
      heightM: carto.height,
      headingDeg: CesiumMath.toDegrees(cam.heading),
      pitchDeg: CesiumMath.toDegrees(cam.pitch),
      band: this.currentBand(),
    });
    if (!correction) return;
    const destination = Cartesian3.fromDegrees(correction.lonDeg, correction.latDeg, correction.heightM);
    const orientation = {
      heading: CesiumMath.toRadians(correction.headingDeg),
      pitch: CesiumMath.toRadians(correction.pitchDeg),
      roll: 0,
    };
    if (this.motion === 'reduced') {
      cam.setView({ destination, orientation });
      this.viewer.scene.requestRender();
      return;
    }
    this.correcting = true;
    cam.flyTo({
      destination,
      orientation,
      duration: CORRECTION_DURATION_S,
      easingFunction: minimumJerk,
      complete: () => {
        this.correcting = false;
      },
      cancel: () => {
        this.correcting = false;
      },
    });
  }
}
