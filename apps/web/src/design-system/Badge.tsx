/** Badge component: word + glyph + tone; the tone is decoration, the text is the meaning. */
import type { BadgeDescriptor } from './badges';

interface BadgeProps {
  badge: BadgeDescriptor;
  title?: string;
  testId?: string;
  onClick?: () => void;
}

export function Badge({ badge, title, testId, onClick }: BadgeProps) {
  const className = `badge tone-${badge.tone} pattern-${badge.pattern}`;
  const content = (
    <>
      <span className="badge-glyph" aria-hidden="true">{badge.glyph}</span>
      <span className="badge-label">{badge.label}</span>
    </>
  );
  if (onClick) {
    return (
      <button type="button" className={`${className} badge-button`} title={title} data-testid={testId} onClick={onClick}>
        {content}
      </button>
    );
  }
  return <span className={className} title={title} data-testid={testId}>{content}</span>;
}
