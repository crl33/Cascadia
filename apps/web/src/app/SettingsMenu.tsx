/**
 * SettingsMenu: the home for preferences that are real but not primary (mission §19–20).
 * Motion lives here — it is an accessibility/cinematic preference, not an instrument
 * control — alongside the graphics quality tier. The main chrome shows a single ⚙ button;
 * the menu is a standard dismissable glass popover (useDismiss: outside click + Escape).
 *
 * Motion never changes what information exists — only how transitions move (the reduced
 * path cuts instead of flying). Scientific completeness is identical on every tier.
 */
import { useCallback, useRef, useState } from 'react';
import { useDismiss } from '../design-system/dismiss';
import type { MotionSetting } from '../design-system/motion';
import { useSceneStore, type QualityTier } from '../state/store';

const MOTION_CHOICES: { value: MotionSetting; label: string; hint: string }[] = [
  { value: 'system', label: 'System', hint: 'follow the device setting' },
  { value: 'reduced', label: 'Reduced', hint: 'cuts instead of camera flights' },
  { value: 'full', label: 'Full', hint: 'cinematic transitions' },
];
const QUALITY_CHOICES: { value: QualityTier; label: string; hint: string }[] = [
  { value: 'ultra', label: 'Ultra', hint: 'full glass optics, largest cache' },
  { value: 'high', label: 'High', hint: 'near-full effects' },
  { value: 'balanced', label: 'Balanced', hint: 'default' },
  { value: 'low', label: 'Low', hint: 'frosted glass, lightest' },
];

export function SettingsMenu() {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const motionSetting = useSceneStore((s) => s.motionSetting);
  const setMotionSetting = useSceneStore((s) => s.setMotionSetting);
  const qualityTier = useSceneStore((s) => s.qualityTier);
  const setQualityTier = useSceneStore((s) => s.setQualityTier);
  const close = useCallback(() => setOpen(false), []);
  useDismiss(anchorRef, close, { enabled: open });

  return (
    <div className="settings-anchor" ref={anchorRef}>
      <button
        type="button"
        className="link-button settings-button"
        data-testid="settings-button"
        aria-haspopup="menu"
        aria-expanded={open}
        title="Settings"
        onClick={() => setOpen((was) => !was)}
      >
        ⚙<span className="visually-hidden">Settings</span>
      </button>
      {open ? (
        <div className="settings-menu glass-surface glass-popover shape-card" role="menu" aria-label="Settings" data-testid="settings-menu">
          <fieldset className="settings-group">
            <legend>Motion</legend>
            {MOTION_CHOICES.map((choice) => (
              <label key={choice.value} className="settings-choice">
                <input
                  type="radio"
                  name="motion"
                  checked={motionSetting === choice.value}
                  onChange={() => setMotionSetting(choice.value)}
                />
                <span>{choice.label}</span>
                <span className="settings-hint">{choice.hint}</span>
              </label>
            ))}
          </fieldset>
          <fieldset className="settings-group">
            <legend>Graphics</legend>
            {QUALITY_CHOICES.map((choice) => (
              <label key={choice.value} className="settings-choice">
                <input
                  type="radio"
                  name="quality"
                  checked={qualityTier === choice.value}
                  onChange={() => setQualityTier(choice.value)}
                />
                <span>{choice.label}</span>
                <span className="settings-hint">{choice.hint}</span>
              </label>
            ))}
          </fieldset>
        </div>
      ) : null}
    </div>
  );
}
