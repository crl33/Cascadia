/**
 * GlassSurface — the one way to make a floating surface (mission §13). Composes the
 * material (variant → density), the silhouette (shape → continuous corners), the
 * specular rim (CSS), and the Chromium edge-refraction enhancement (refraction.ts).
 *
 * No component may invent its own background/border/blur/radius/shadow: if a surface
 * floats over the world, it is a GlassSurface (or, for chrome that predates portals,
 * carries the same `glass-surface glass-* shape-*` classes).
 */
import { useEffect, useRef, type CSSProperties, type ReactNode } from 'react';
import { attachRefraction } from './refraction';

export type GlassVariant = 'chrome' | 'panel' | 'sheet' | 'popover' | 'compact';
export type GlassShape = 'capsule' | 'control' | 'card' | 'sheet' | 'panel';

interface GlassSurfaceProps {
  variant: GlassVariant;
  shape?: GlassShape;
  className?: string;
  style?: CSSProperties;
  children?: ReactNode;
  role?: string;
  'aria-label'?: string;
  'data-testid'?: string;
}

export function GlassSurface({ variant, shape = 'card', className, style, children, ...rest }: GlassSurfaceProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    return attachRefraction(el);
  }, []);

  const classes = ['glass-surface', `glass-${variant}`, `shape-${shape}`, className].filter(Boolean).join(' ');
  return (
    <div ref={ref} className={classes} style={style} {...rest}>
      {children}
    </div>
  );
}
