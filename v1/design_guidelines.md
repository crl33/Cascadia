{
  "meta": {
    "product_name": "Cascade Oracle",
    "design_intent": "Cinematic hydrologic observatory: calm-first deep navy command center that progressively ‘wakes up’ into amber/red tension states. Futuristic presentation, traceable data logic, unmistakable source labeling.",
    "app_type": "dashboard",
    "tech_stack": {
      "frontend": ["React 19 (CRA)", "Tailwind CSS 3.4", "shadcn/ui (Radix)", "lucide-react"],
      "animation": ["framer-motion"],
      "charts": ["recharts@3.6"],
      "backend": ["FastAPI typed JSON"]
    },
    "hard_rules": {
      "no_purple_for_ai": true,
      "no_cartoon": true,
      "no_emergency_broadcast_aesthetic": true,
      "no_neon_overload": true,
      "body_background_must_be_cinematic_dark": true,
      "source_badges_non_negotiable": true,
      "data_testid_required": "All interactive + key informational elements must include data-testid in kebab-case."
    }
  },

  "brand_attributes": {
    "keywords": [
      "foresight",
      "forecasting",
      "outlook",
      "risk anticipation",
      "early signal detection",
      "basin intelligence",
      "hydrologic intelligence"
    ],
    "tone": {
      "calm": "quiet, deep, beautiful, credible",
      "watch": "measured tension, increased attention",
      "elevated": "persistent concern, clear emphasis",
      "flood": "high-contrast urgency without panic",
      "unknown": "neutral, non-alarming"
    }
  },

  "design_tokens": {
    "color_system": {
      "format": "HSL (Tailwind-friendly) + optional OKLCH references",
      "base": {
        "bg": {
          "canvas": {
            "hsl": "222 52% 6%",
            "usage": "App background (solid)."
          },
          "canvas_2": {
            "hsl": "223 46% 8%",
            "usage": "Secondary background layers behind glass cards."
          },
          "glass": {
            "hsl": "222 40% 10%",
            "alpha": 0.55,
            "usage": "Card surfaces (glassmorphism)."
          },
          "glass_strong": {
            "hsl": "222 42% 12%",
            "alpha": 0.72,
            "usage": "Hero status panel + modal surfaces for readability."
          }
        },
        "text": {
          "primary": { "hsl": "210 40% 98%" },
          "secondary": { "hsl": "215 18% 78%" },
          "muted": { "hsl": "215 14% 62%" },
          "disabled": { "hsl": "215 10% 48%" }
        },
        "stroke": {
          "hairline": { "hsl": "215 22% 22%", "alpha": 0.7 },
          "hairline_soft": { "hsl": "215 22% 22%", "alpha": 0.45 }
        },
        "focus_ring": {
          "hsl": "191 92% 55%",
          "alpha": 0.55,
          "usage": "Keyboard focus ring (calm cyan)."
        }
      },

      "risk_states": {
        "calm": {
          "accent": { "hsl": "191 92% 55%", "name": "cascade-cyan" },
          "accent_2": { "hsl": "205 88% 58%", "name": "glacier-blue" },
          "glow": { "hsl": "191 92% 55%", "alpha": 0.22 },
          "oklch_reference": "oklch(0.78 0.12 200)"
        },
        "watch": {
          "accent": { "hsl": "38 92% 58%", "name": "amber-watch" },
          "glow": { "hsl": "38 92% 58%", "alpha": 0.18 },
          "oklch_reference": "oklch(0.82 0.12 75)"
        },
        "elevated": {
          "accent": { "hsl": "32 96% 56%", "name": "amber-elevated" },
          "glow": { "hsl": "32 96% 56%", "alpha": 0.22 },
          "oklch_reference": "oklch(0.78 0.14 62)"
        },
        "flood": {
          "accent": { "hsl": "6 86% 56%", "name": "flood-red" },
          "glow": { "hsl": "6 86% 56%", "alpha": 0.20 },
          "oklch_reference": "oklch(0.66 0.18 25)"
        },
        "unknown": {
          "accent": { "hsl": "215 10% 58%", "name": "neutral-unknown" },
          "glow": { "hsl": "215 10% 58%", "alpha": 0.0 },
          "oklch_reference": "oklch(0.70 0.02 250)"
        }
      },

      "badges": {
        "source_official": {
          "bg": "191 92% 55%",
          "bg_alpha": 0.14,
          "border": "191 92% 55%",
          "border_alpha": 0.35,
          "text": "191 92% 70%",
          "label": "Official NWS / NWPS"
        },
        "source_configured": {
          "bg": "38 92% 58%",
          "bg_alpha": 0.10,
          "border": "38 92% 58%",
          "border_alpha": 0.28,
          "text": "38 92% 72%",
          "label": "Configured threshold"
        },
        "source_unavailable": {
          "bg": "215 18% 78%",
          "bg_alpha": 0.06,
          "border": "215 22% 22%",
          "border_alpha": 0.55,
          "text": "215 18% 78%",
          "label": "Thresholds not configured"
        }
      },

      "chart": {
        "line_observed": { "hsl": "191 92% 55%" },
        "line_forecast_official": { "hsl": "205 88% 58%" },
        "line_modeled": { "hsl": "38 92% 58%" },
        "threshold_watch": { "hsl": "38 92% 58%", "alpha": 0.22 },
        "threshold_flood": { "hsl": "6 86% 56%", "alpha": 0.22 },
        "grid": { "hsl": "215 22% 22%", "alpha": 0.55 },
        "tooltip_bg": { "hsl": "222 42% 12%", "alpha": 0.92 }
      }
    },

    "radius": {
      "xs": "0.5rem",
      "sm": "0.75rem",
      "md": "1rem",
      "lg": "1.25rem",
      "xl": "1.5rem",
      "pill": "9999px"
    },

    "spacing": {
      "layout_gutter": "px-4 sm:px-6 lg:px-8",
      "section_y": "py-6 sm:py-8 lg:py-10",
      "card_padding": "p-4 sm:p-5",
      "dense_row_gap": "gap-3",
      "grid_gap": "gap-4 sm:gap-5"
    },

    "shadows_and_glow": {
      "glass_shadow": "0 18px 50px rgba(0,0,0,0.55)",
      "glass_inset": "inset 0 1px 0 rgba(255,255,255,0.06)",
      "glow_calm": "0 0 0 1px rgba(64,224,255,0.10), 0 0 28px rgba(64,224,255,0.10)",
      "glow_watch": "0 0 0 1px rgba(255,196,92,0.10), 0 0 26px rgba(255,196,92,0.10)",
      "glow_flood": "0 0 0 1px rgba(255,92,92,0.12), 0 0 26px rgba(255,92,92,0.12)"
    },

    "motion": {
      "easing": {
        "standard": "[0.22, 1, 0.36, 1]",
        "snappy": "[0.2, 0.9, 0.2, 1]",
        "calm": "[0.16, 1, 0.3, 1]"
      },
      "duration_ms": {
        "micro": 140,
        "ui": 220,
        "panel": 320,
        "state": 520,
        "ambient": 2400
      },
      "ambient": {
        "calm": "slow shimmer + subtle noise drift",
        "watch": "slightly faster shimmer + gentle pulse",
        "elevated": "persistent pulse on risk accents",
        "flood": "subtle ‘waking up’ motion: stronger rim light + low-frequency pulse"
      },
      "reduced_motion": "Respect prefers-reduced-motion: disable shimmer/pulse; keep opacity/contrast changes only."
    },

    "typography": {
      "google_fonts": {
        "display": {
          "name": "Space Grotesk",
          "weights": [500, 600, 700],
          "usage": "Headings, hero status title"
        },
        "body": {
          "name": "Inter",
          "weights": [400, 500, 600],
          "usage": "Body, labels, UI"
        },
        "numeric": {
          "name": "IBM Plex Mono",
          "weights": [400, 500, 600],
          "usage": "Gage height, discharge, timestamps"
        }
      },
      "scale": {
        "h1": "text-4xl sm:text-5xl lg:text-6xl",
        "h2": "text-base md:text-lg",
        "kpi": "text-3xl sm:text-4xl",
        "kpi_unit": "text-xs sm:text-sm",
        "body": "text-sm sm:text-base",
        "label": "text-xs uppercase tracking-[0.14em]",
        "mono_small": "text-xs font-mono tracking-[0.08em]"
      }
    }
  },

  "layout": {
    "grid": {
      "dashboard_container": "max-w-7xl mx-auto",
      "station_grid": "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3",
      "station_grid_gap": "gap-4 sm:gap-5",
      "hero_layout": "flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4",
      "roadmap_layout": "grid grid-cols-1 lg:grid-cols-12 gap-6"
    },
    "navigation": {
      "pattern": "Top nav (thin) + optional compact right-side status cluster. Avoid heavy sidebars in Phase 1.",
      "sticky": "sticky top-0 z-40",
      "height": "h-14"
    }
  },

  "background_and_texture": {
    "approach": "Solid deep navy canvas + subtle topographic/noise overlay + very small gradient accent only in hero header area (<=20% viewport).",
    "css_scaffold": {
      "noise_overlay": "Use a pseudo-element on body or main container: background-image: url(data:image/svg+xml,...noise) OR a tiny repeating noise png; opacity 0.06; mix-blend-mode: overlay; pointer-events:none.",
      "topo_overlay": "Use an SVG contour pattern as a masked overlay at 6–10% opacity; keep it subtle and non-distracting."
    },
    "gradient_rule_compliance": "Only allow a mild cyan→blue→navy diagonal wash behind the hero status panel header strip; never behind dense text blocks."
  },

  "risk_state_mapping_table": {
    "columns": ["state", "accent", "card_rim", "badge_style", "motion_intensity", "contrast_shift"],
    "rows": [
      {
        "state": "calm",
        "accent": "cascade-cyan",
        "card_rim": "1px hairline + calm glow",
        "badge_style": "cool cyan pill",
        "motion_intensity": "low (ambient shimmer only)",
        "contrast_shift": "baseline"
      },
      {
        "state": "watch",
        "accent": "amber-watch",
        "card_rim": "hairline + warm rim highlight",
        "badge_style": "amber pill + subtle pulse",
        "motion_intensity": "medium-low",
        "contrast_shift": "+5–8% (text + borders)"
      },
      {
        "state": "elevated",
        "accent": "amber-elevated",
        "card_rim": "stronger rim + persistent glow",
        "badge_style": "amber pill + persistent pulse",
        "motion_intensity": "medium",
        "contrast_shift": "+10–12%"
      },
      {
        "state": "flood",
        "accent": "flood-red",
        "card_rim": "strong rim + red glow",
        "badge_style": "red pill + low-frequency pulse",
        "motion_intensity": "medium-high (still restrained)",
        "contrast_shift": "+14–18%"
      },
      {
        "state": "unknown",
        "accent": "neutral-unknown",
        "card_rim": "neutral hairline only",
        "badge_style": "gray pill",
        "motion_intensity": "none",
        "contrast_shift": "baseline"
      }
    ]
  },

  "component_path": {
    "shadcn_primary": {
      "card": "/app/frontend/src/components/ui/card.jsx",
      "badge": "/app/frontend/src/components/ui/badge.jsx",
      "button": "/app/frontend/src/components/ui/button.jsx",
      "tooltip": "/app/frontend/src/components/ui/tooltip.jsx",
      "dialog": "/app/frontend/src/components/ui/dialog.jsx",
      "drawer": "/app/frontend/src/components/ui/drawer.jsx",
      "separator": "/app/frontend/src/components/ui/separator.jsx",
      "tabs": "/app/frontend/src/components/ui/tabs.jsx",
      "scroll_area": "/app/frontend/src/components/ui/scroll-area.jsx",
      "skeleton": "/app/frontend/src/components/ui/skeleton.jsx",
      "sonner": "/app/frontend/src/components/ui/sonner.jsx"
    },
    "recommended_patterns": {
      "detail_view": "Prefer Drawer on mobile, Dialog on desktop (same content component).",
      "badges": "Use shadcn Badge with custom variants via className (no raw HTML pills)."
    }
  },

  "component_guidance": {
    "NavBar": {
      "purpose": "Thin technical top bar: brand mark + routes + refresh cluster.",
      "structure": [
        "Left: wordmark ‘Cascade Oracle’ + sublabel ‘Watershed Foresight’",
        "Center (optional): breadcrumb-like location ‘Washington • Puget Sound / Cascades’",
        "Right: last-updated + refresh button"
      ],
      "tailwind": {
        "container": "sticky top-0 z-40 border-b border-white/10 bg-[hsl(var(--bg-canvas)/0.72)] backdrop-blur-xl",
        "inner": "mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-14 flex items-center justify-between",
        "brand": "font-[var(--font-display)] tracking-tight text-sm sm:text-base text-white/90",
        "sublabel": "ml-2 hidden sm:inline text-xs uppercase tracking-[0.18em] text-white/50"
      },
      "interactions": {
        "refresh_button": "IconButton with hover rim light; press scale 0.98; show spinner while fetching.",
        "tooltips": "Use Tooltip for ‘Auto-refresh every 5 min’ and ‘Manual refresh’"
      },
      "data_testids": {
        "refresh": "data-testid=\"nav-refresh-button\"",
        "last_updated": "data-testid=\"nav-last-updated\"",
        "roadmap_link": "data-testid=\"nav-roadmap-link\""
      }
    },

    "HeroStatusPanel": {
      "purpose": "System overview: calm/watch counts + updated time + disclaimer hint.",
      "layout": "Full-width glass panel with a thin ‘status beam’ header strip (mild gradient <=20% viewport).",
      "tailwind": {
        "panel": "rounded-2xl border border-white/10 bg-white/[0.06] backdrop-blur-xl shadow-[var(--shadow-glass)]",
        "header_strip": "rounded-t-2xl px-4 sm:px-5 py-3 border-b border-white/10 bg-[linear-gradient(135deg,rgba(64,224,255,0.10),rgba(64,224,255,0.04),rgba(10,14,26,0))]",
        "content": "px-4 sm:px-5 py-4 flex flex-col lg:flex-row lg:items-end lg:justify-between gap-4"
      },
      "content_blocks": {
        "headline": "All Watersheds Calm / X stations on watch",
        "kpis": ["Stations monitored", "On watch", "Elevated", "Flood risk"],
        "meta": ["Updated 4 min ago", "Auto-refresh 5 min"]
      },
      "motion": {
        "ambient": "Slow shimmer on header strip using Framer Motion opacity 0.85↔1.0 over 2.4s (disabled for reduced motion).",
        "state_transition": "When overall state changes, animate border/glow color over 520ms using easing.standard."
      },
      "data_testids": {
        "headline": "hero-status-headline",
        "updated": "hero-status-updated",
        "kpi_calm": "hero-status-kpi-calm",
        "kpi_watch": "hero-status-kpi-watch"
      }
    },

    "RiverGaugeCard": {
      "purpose": "Primary station tile: name + gage height + discharge + risk + source + last updated + sparkline.",
      "layout": "Bento-like card: top row identity + badges; middle numeric KPI; bottom sparkline + timestamps.",
      "tailwind": {
        "card": "group relative overflow-hidden rounded-2xl border border-white/10 bg-white/[0.055] backdrop-blur-xl",
        "hover": "hover:border-white/20",
        "inner": "p-4 sm:p-5",
        "title": "text-sm sm:text-base font-semibold text-white/90",
        "subtitle": "mt-0.5 text-xs text-white/55",
        "kpi": "mt-4 flex items-baseline gap-2",
        "kpi_value": "font-mono text-3xl sm:text-4xl tracking-tight text-white",
        "kpi_unit": "text-xs sm:text-sm text-white/55",
        "meta_row": "mt-4 flex items-center justify-between gap-3",
        "timestamp": "font-mono text-xs text-white/55",
        "stale": "text-xs text-[hsl(var(--risk-watch))]"
      },
      "micro_interactions": {
        "hover": "Increase glass brightness slightly (bg alpha +0.02) + add subtle rim glow via pseudo-element; DO NOT use transition: all.",
        "press": "scale-[0.99] on tap/click",
        "focus": "ring-2 ring-[hsl(var(--focus-ring)/0.55)] ring-offset-0"
      },
      "sparkline": {
        "implementation": "Use Recharts LineChart in a 72px-tall area; hide axes; show last point dot only on hover/focus.",
        "colors": "Observed line uses calm cyan; if risk is watch/elevated/flood, tint line toward that accent."
      },
      "data_testids": {
        "card": "station-card",
        "station_name": "station-card-name",
        "gage_height": "station-card-gage-height",
        "discharge": "station-card-discharge",
        "risk_badge": "station-card-risk-badge",
        "source_badge": "station-card-source-badge",
        "last_updated": "station-card-last-updated",
        "open_detail": "station-card-open-detail"
      }
    },

    "RiskBadge": {
      "purpose": "Single, unmistakable risk label: calm/watch/elevated/flood/unknown.",
      "component": "shadcn Badge",
      "variants": {
        "calm": "bg-[hsl(191_92%_55%/0.14)] text-[hsl(191_92%_70%)] border border-[hsl(191_92%_55%/0.35)]",
        "watch": "bg-[hsl(38_92%_58%/0.12)] text-[hsl(38_92%_72%)] border border-[hsl(38_92%_58%/0.30)]",
        "elevated": "bg-[hsl(32_96%_56%/0.12)] text-[hsl(32_96%_72%)] border border-[hsl(32_96%_56%/0.32)]",
        "flood": "bg-[hsl(6_86%_56%/0.12)] text-[hsl(6_86%_72%)] border border-[hsl(6_86%_56%/0.34)]",
        "unknown": "bg-white/[0.06] text-white/70 border border-white/15"
      },
      "motion": {
        "watch": "pulse opacity 0.85↔1.0 every 1.8s",
        "elevated": "pulse every 1.2s",
        "flood": "pulse every 1.0s (subtle)"
      },
      "data_testids": {
        "badge": "risk-badge"
      }
    },

    "SourceBadge": {
      "purpose": "Trust UI: explicit authority level. Must never be confused with official.",
      "component": "shadcn Badge",
      "rules": [
        "Always show SourceBadge adjacent to RiskBadge.",
        "Official badge uses verified-blue/cyan styling and a check icon.",
        "Configured threshold badge uses muted amber-gray (less authoritative).",
        "Thresholds not configured is neutral gray; never amber/red."
      ],
      "icons": {
        "official": "lucide-react: BadgeCheck",
        "configured": "lucide-react: SlidersHorizontal",
        "unavailable": "lucide-react: MinusCircle"
      },
      "data_testids": {
        "badge": "source-badge"
      }
    },

    "HydrographDetailView": {
      "container": "Drawer (mobile) / Dialog (desktop)",
      "content": [
        "Station identity header",
        "Risk + Source badges",
        "24h hydrograph with thresholds bands",
        "Legend: Observed vs Official forecast vs Modeled vs Demo/Fallback (if ever)"
      ],
      "chart_guidance": {
        "threshold_bands": "Use ReferenceArea or ReferenceLine to show watch/elevated/flood thresholds; label them with small mono tags.",
        "tooltip": "Dark glass tooltip with mono values + timestamp; include source label in tooltip when hovering forecast lines.",
        "axes": "Use minimal ticks; grid lines at low opacity; ensure readability on dark background."
      },
      "tailwind": {
        "surface": "rounded-2xl border border-white/10 bg-[hsl(222_42%_12%/0.78)] backdrop-blur-2xl shadow-[var(--shadow-glass)]",
        "header": "px-4 sm:px-6 py-4 border-b border-white/10",
        "body": "px-4 sm:px-6 py-5"
      },
      "data_testids": {
        "open": "station-detail-open",
        "close": "station-detail-close",
        "chart": "station-detail-hydrograph-chart"
      }
    },

    "PhaseRoadmap": {
      "purpose": "Compact Phase 1–5 strip on dashboard; full narrative on /roadmap.",
      "dashboard_variant": {
        "layout": "Horizontal steps with current phase highlighted; others subdued.",
        "tailwind": "rounded-2xl border border-white/10 bg-white/[0.04] backdrop-blur-xl p-4 sm:p-5"
      },
      "roadmap_page": {
        "layout": "Left: narrative; Right: vertical timeline cards.",
        "do_not": "Do not render future feature UI components; only describe phases with text + simple icons."
      },
      "data_testids": {
        "phase_rail": "phase-roadmap-rail",
        "phase_current": "phase-roadmap-current"
      }
    },

    "SystemDisclaimer": {
      "purpose": "Persistent trust disclaimer at bottom of dashboard.",
      "style": "Low-contrast but unmistakable; always visible; not hidden behind modals.",
      "tailwind": {
        "container": "mt-6 rounded-2xl border border-white/10 bg-white/[0.035] backdrop-blur-xl p-4",
        "text": "text-xs sm:text-sm text-white/60 leading-relaxed"
      },
      "data_testids": {
        "disclaimer": "system-disclaimer"
      }
    }
  },

  "states": {
    "loading": {
      "pattern": "Use shadcn Skeleton inside cards; keep layout stable.",
      "data_testids": {
        "loading": "dashboard-loading"
      }
    },
    "empty": {
      "pattern": "If station list empty: show a single glass panel with explanation + retry.",
      "copy": "No stations available. Check connectivity or try refresh.",
      "data_testids": {
        "empty": "dashboard-empty"
      }
    },
    "error": {
      "pattern": "Use shadcn Alert (subtle) inside hero panel; do not use full-screen red.",
      "copy": "Data fetch failed. Showing last known observations.",
      "data_testids": {
        "error": "dashboard-error"
      }
    },
    "stale": {
      "rule": "If last-updated > 15 min: mark station as stale.",
      "ui": "Show ‘STALE’ tag (neutral or amber-watch depending on risk) + tooltip explaining.",
      "data_testids": {
        "stale": "station-stale-indicator"
      }
    }
  },

  "responsive": {
    "mobile_first": true,
    "breakpoints": {
      "sm": "640px",
      "md": "768px",
      "lg": "1024px",
      "xl": "1280px"
    },
    "rules": [
      "On mobile: station cards become single column; detail view uses Drawer.",
      "Hero KPIs wrap into 2x2 grid.",
      "Keep nav minimal; move roadmap link into a small button if space constrained.",
      "Avoid horizontal scroll in charts: use responsive container and fewer ticks."
    ]
  },

  "libraries": {
    "framer_motion": {
      "install": "npm i framer-motion",
      "usage": "Use motion.div for hero shimmer, risk pulses, and card hover lift. Provide reduced-motion fallback.",
      "variants_js_scaffold": {
        "riskPulse": "const riskPulse = (intensity=1)=>({ animate:{ opacity:[0.85,1,0.9], transition:{ duration: intensity===3?1.0:intensity===2?1.2:1.8, repeat: Infinity, ease: 'easeInOut' } } });",
        "cardHover": "const cardHover = { initial:{ y:0 }, whileHover:{ y:-2, transition:{ duration:0.22 } }, whileTap:{ scale:0.99 } };"
      }
    },
    "recharts": {
      "install": "npm i recharts@3.6",
      "usage": "LineChart for sparkline + full hydrograph. Use ReferenceLine/ReferenceArea for thresholds."
    }
  },

  "image_urls": {
    "hero_background_photography": [
      {
        "url": "https://images.unsplash.com/photo-1575953344655-1c8ecbe1f1c6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MTN8MHwxfHNlYXJjaHwxfHxwYWNpZmljJTIwbm9ydGh3ZXN0JTIwcml2ZXIlMjBhZXJpYWwlMjBtaXN0eXxlbnwwfHx8Ymx1ZXwxNzc3Njc3NzI5fDA&ixlib=rb-4.1.0&q=85",
        "description": "Misty river valley aerial; use as very subtle blurred hero backdrop (opacity 0.08–0.12) behind topo/noise."
      },
      {
        "url": "https://images.unsplash.com/photo-1595017334467-8d7110d79844?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1MTN8MHwxfHNlYXJjaHwzfHxwYWNpZmljJTIwbm9ydGh3ZXN0JTIwcml2ZXIlMjBhZXJpYWwlMjBtaXN0eXxlbnwwfHx8Ymx1ZXwxNzc3Njc3NzI5fDA&ixlib=rb-4.1.0&q=85",
        "description": "Forest + water aerial; alternate background for /roadmap header (even lower opacity)."
      }
    ],
    "abstract_texture_optional": [
      {
        "url": "https://images.unsplash.com/photo-1552598538-12bd9dc90c37?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NTYxODd8MHwxfHNlYXJjaHwxfHx0b3BvZ3JhcGhpYyUyMG1hcCUyMGNvbnRvdXIlMjBsaW5lc3xlbnwwfHx8YmxhY2t8MTc3NzY3NzczNnww&ixlib=rb-4.1.0&q=85",
        "description": "Monochrome terrain texture; can be used as a masked overlay (opacity 0.05) if you can’t source topo SVG quickly. Avoid red variants."
      }
    ]
  },

  "implementation_notes": {
    "css_variables_plan": {
      "where": "Update /app/frontend/src/index.css :root and .dark tokens to match this system; set body to dark by default (apply .dark on html).",
      "must_fix": "Remove/avoid App.css centered header styles; do not center the app container."
    },
    "glassmorphism_recipe": {
      "tailwind": "bg-white/[0.055] backdrop-blur-xl border border-white/10 shadow-[0_18px_50px_rgba(0,0,0,0.55)]",
      "note": "Keep text on glass at >= white/80 for headings; use a stronger glass surface for dense chart tooltips."
    },
    "data_traceability": {
      "rules": [
        "Every station card shows: source badge + last-updated.",
        "Every chart legend distinguishes observed vs official forecast vs modeled vs fallback/demo.",
        "Fallback/demo data must be visually de-emphasized (dashed line + neutral color + explicit label)."
      ]
    },
    "testids": {
      "convention": "kebab-case describing role",
      "examples": [
        "data-testid=\"station-card-open-detail\"",
        "data-testid=\"hydrograph-tooltip\"",
        "data-testid=\"phase-roadmap-current\""
      ]
    }
  },

  "instructions_to_main_agent": [
    "Set the app to dark mode by default (apply class 'dark' on <html> or root wrapper) and replace shadcn tokens in index.css with the cinematic navy system.",
    "Implement risk-state theming as a small mapping object (state -> accent HSL + glow + pulse intensity) used by HeroStatusPanel, RiverGaugeCard, RiskBadge, and chart colors.",
    "Use shadcn components only for interactive primitives (Button, Badge, Card, Dialog/Drawer, Tooltip, Tabs, Skeleton).",
    "Ensure every station card includes SourceBadge + LastUpdated + Stale indicator; never allow fallback data to look official.",
    "Use Framer Motion for ambient shimmer and risk pulses; respect prefers-reduced-motion.",
    "Keep gradients minimal and only in hero header strip; never on text-heavy areas; never exceed 20% viewport.",
    "Add data-testid to all interactive and key informational elements (buttons, links, badges, KPIs, timestamps, charts)."
  ],

  "general_ui_ux_design_guidelines_appendix": "<General UI UX Design Guidelines>\n    - You must **not** apply universal transition. Eg: `transition: all`. This results in breaking transforms. Always add transitions for specific interactive elements like button, input excluding transforms\n    - You must **not** center align the app container, ie do not add `.App { text-align: center; }` in the css file. This disrupts the human natural reading flow of text\n   - NEVER: use AI assistant Emoji characters like`🤖🧠💭💡🔮🎯📚🎭🎬🎪🎉🎊🎁🎀🎂🍰🎈🎨🎰💰💵💳🏦💎🪙💸🤑📊📈📉💹🔢🏆🥇 etc for icons. Always use **FontAwesome cdn** or **lucid-react** library already installed in the package.json\n\n **GRADIENT RESTRICTION RULE**\nNEVER use dark/saturated gradient combos (e.g., purple/pink) on any UI element.  Prohibited gradients: blue-500 to purple 600, purple 500 to pink-500, green-500 to blue-500, red to pink etc\nNEVER use dark gradients for logo, testimonial, footer etc\nNEVER let gradients cover more than 20% of the viewport.\nNEVER apply gradients to text-heavy content or reading areas.\nNEVER use gradients on small UI elements (<100px width).\nNEVER stack multiple gradient layers in the same viewport.\n\n**ENFORCEMENT RULE:**\n    • Id gradient area exceeds 20% of viewport OR affects readability, **THEN** use solid colors\n\n**How and where to use:**\n   • Section backgrounds (not content backgrounds)\n   • Hero section header content. Eg: dark to light to dark color\n   • Decorative overlays and accent elements only\n   • Hero section with 2-3 mild color\n   • Gradients creation can be done for any angle say horizontal, vertical or diagonal\n\n- For AI chat, voice application, **do not use purple color. Use color like light green, ocean blue, peach orange etc**\n\n</Font Guidelines>\n\n- Every interaction needs micro-animations - hover states, transitions, parallax effects, and entrance animations. Static = dead. \n   \n- Use 2-3x more spacing than feels comfortable. Cramped designs look cheap.\n\n- Subtle grain textures, noise overlays, custom cursors, selection states, and loading animations: separates good from extraordinary.\n   \n- Before generating UI, infer the visual style from the problem statement (palette, contrast, mood, motion) and immediately instantiate it by setting global design tokens (primary, secondary/accent, background, foreground, ring, state colors), rather than relying on any library defaults. Don't make the background dark as a default step, always understand problem first and define colors accordingly\n    Eg: - if it implies playful/energetic, choose a colorful scheme\n           - if it implies monochrome/minimal, choose a black–white/neutral scheme\n\n**Component Reuse:**\n\t- Prioritize using pre-existing components from src/components/ui when applicable\n\t- Create new components that match the style and conventions of existing components when needed\n\t- Examine existing components to understand the project's component patterns before creating new ones\n\n**IMPORTANT**: Do not use HTML based component like dropdown, calendar, toast etc. You **MUST** always use `/app/frontend/src/components/ui/ ` only as a primary components as these are modern and stylish component\n\n**Best Practices:**\n\t- Use Shadcn/UI as the primary component library for consistency and accessibility\n\t- Import path: ./components/[component-name]\n\n**Export Conventions:**\n\t- Components MUST use named exports (export const ComponentName = ...)\n\t- Pages MUST use default exports (export default function PageName() {...})\n\n**Toasts:**\n  - Use `sonner` for toasts\"\n  - Sonner component are located in `/app/src/components/ui/sonner.tsx`\n\nUse 2–4 color gradients, subtle textures/noise overlays, or CSS-based noise to avoid flat visuals.\n</General UI UX Design Guidelines>"
}
