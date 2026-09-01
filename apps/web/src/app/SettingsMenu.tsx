/**
 * SettingsMenu: the home for preferences that are real but not primary (mission §19–20).
 * Motion lives here — it is an accessibility/cinematic preference, not an instrument
 * control — alongside the EXPERIENCE switch. The main chrome shows a single ⚙ button;
 * the menu is a standard dismissable glass popover (useDismiss: outside click + Escape).
 *
 * Experience (owner 2026-09-01: "the user chooses a stripped down version or full
 * version"): two ways, Essential or Cinematic. The renderer measures the machine and
 * picks a default; the switch overrides it and the choice persists per browser. Neither
 * setting changes what information exists — Essential draws the same truth with less
 * rendering; the reduced motion path cuts instead of flying.
 */
import { useCallback, useRef, useState } from 'react';
import { useDismiss } from '../design-system/dismiss';
import type { MotionSetting } from '../design-system/motion';
import { EXPERIENCE_LABEL, experienceOf, type Experience } from '../scene/quality';
import { useSceneStore } from '../state/store';

const MOTION_CHOICES: { value: MotionSetting; label: string; hint: string }[] = [
  { value: 'system', label: 'System', hint: 'follow the device setting' },
  { value: 'reduced', label: 'Reduced', hint: 'cuts instead of camera flights' },
  { value: 'full', label: 'Full', hint: 'cinematic transitions' },
];
const EXPERIENCE_CHOICES: { value: Experience; hint: string }[] = [
  { value: 'essential', hint: 'lighter renderer, same intelligence' },
  { value: 'cinematic', hint: 'native resolution, full effects' },
];

export function SettingsMenu() {
  const [open, setOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const motionSetting = useSceneStore((s) => s.motionSetting);
  const setMotionSetting = useSceneStore((s) => s.setMotionSetting);
  const experience = useSceneStore((s) => s.experience);
  const setExperience = useSceneStore((s) => s.setExperience);
  const qualityTier = useSceneStore((s) => s.qualityTier);
  const detectedTier = useSceneStore((s) => s.detectedTier);
  const close = useCallback(() => setOpen(false), []);
  useDismiss(anchorRef, close, { enabled: open });
  const running = experienceOf(qualityTier);

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
            <legend>Experience</legend>
            <div className="settings-segmented" role="group" aria-label="Experience">
              {EXPERIENCE_CHOICES.map((choice) => (
                <button
                  key={choice.value}
                  type="button"
                  className="settings-segment"
                  aria-pressed={running === choice.value}
                  data-testid={`experience-${choice.value}`}
                  onClick={() => setExperience(choice.value)}
                >
                  <span>{EXPERIENCE_LABEL[choice.value]}</span>
                  <small>{choice.hint}</small>
                </button>
              ))}
            </div>
            <p className="settings-auto" data-testid="experience-status">
              {experience === 'auto' ? (
                <span>Automatic · {detectedTier ? `this device measured ${EXPERIENCE_LABEL[experienceOf(detectedTier)]}` : 'measuring this device'}</span>
              ) : (
                <>
                  <span>Your choice</span>
                  <button type="button" className="link-button" data-testid="experience-auto" onClick={() => setExperience('auto')}>
                    Use automatic
                  </button>
                </>
              )}
            </p>
          </fieldset>
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
        </div>
      ) : null}
    </div>
  );
}
