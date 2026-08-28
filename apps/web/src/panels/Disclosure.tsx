/**
 * Progressive disclosure for the panels (design direction 2026-08-28): the default view is a
 * compact summary; the forensic material — sample counts, reference windows, cadences, full
 * provenance prose — lives one level deeper, intact. Native <details>/<summary>: keyboard
 * operable and screen-reader announced for free, no state to manage, printable when open.
 *
 * Nothing is ever DELETED into a disclosure that doctrine requires at the surface: official
 * hazard categories and active alerts stay in the always-visible summary (calm-by-omission is
 * the failure mode this component must not enable).
 */
import type { ReactNode } from 'react';

interface DisclosureProps {
  id: string;
  label: string;
  /** A one-line hint rendered beside the label while closed (e.g. "3 drivers · 1 refusal"). */
  hint?: string | null;
  defaultOpen?: boolean;
  children: ReactNode;
}

export function Disclosure({ id, label, hint, defaultOpen = false, children }: DisclosureProps) {
  return (
    <details className="disclosure" data-testid={`disclosure-${id}`} open={defaultOpen}>
      <summary className="disclosure-summary">
        <span className="disclosure-label">{label}</span>
        {hint ? <span className="disclosure-hint muted">{hint}</span> : null}
      </summary>
      <div className="disclosure-body">{children}</div>
    </details>
  );
}
