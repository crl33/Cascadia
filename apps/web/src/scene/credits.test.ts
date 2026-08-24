import { describe, expect, it } from 'vitest';
import { CESIUM_RENDERER_CREDIT_HTML, containsIonCredit, creditContainerProblems } from './credits';

/**
 * The exact markup Cesium 1.144 builds in CreditDisplay.getDefaultCredit()
 * (node_modules/cesium/Build/CesiumUnminified/index.js) — the ion logo this app must not show
 * (docs/research/spike-report-2026-08-22.md gap 7).
 */
const STOCK_ION_CREDIT_HTML =
  '<a href="https://cesium.com/" target="_blank"><img src="/cesiumStatic/Assets/Images/ion-credit.png" style="vertical-align: -7px" title="Cesium ion"/></a>';

/** Fixture of the basemap credit the OSM imagery provider renders on screen. */
const OSM_ATTRIBUTION = '© OpenStreetMap contributors';
const osmScreenCredit = `<span class="cesium-credit-textContainer"><span>${OSM_ATTRIBUTION}</span></span>`;

describe('the replacement renderer credit', () => {
  it('names CesiumJS as text, with no logo image and no ion mark', () => {
    expect(CESIUM_RENDERER_CREDIT_HTML).toContain('CesiumJS');
    expect(CESIUM_RENDERER_CREDIT_HTML).not.toMatch(/<img/i);
    expect(containsIonCredit(CESIUM_RENDERER_CREDIT_HTML)).toBe(false);
  });
  it('recognises the stock ion logo credit it replaces', () => {
    expect(containsIonCredit(STOCK_ION_CREDIT_HTML)).toBe(true);
  });
});

describe('creditContainerProblems (credit-strip honesty gate)', () => {
  it('accepts the replaced credit rendered next to the OSM attribution', () => {
    const container = `<div class="cesium-credit-logoContainer">${CESIUM_RENDERER_CREDIT_HTML}</div>${osmScreenCredit}`;
    expect(creditContainerProblems(container, OSM_ATTRIBUTION)).toEqual([]);
  });
  it('flags a container still carrying the ion logo', () => {
    const container = `<div class="cesium-credit-logoContainer">${STOCK_ION_CREDIT_HTML}</div>${osmScreenCredit}`;
    const problems = creditContainerProblems(container, OSM_ATTRIBUTION);
    expect(problems.some((p) => p.includes('ion'))).toBe(true);
  });
  it('flags the CSS-hack failure mode: hiding the logo must not also hide the basemap attribution', () => {
    const container = `<div class="cesium-credit-logoContainer">${CESIUM_RENDERER_CREDIT_HTML}</div>`;
    expect(creditContainerProblems(container, OSM_ATTRIBUTION)).toEqual([
      `basemap attribution "${OSM_ATTRIBUTION}" missing`,
    ]);
  });
  it('flags a container with no renderer attribution at all', () => {
    expect(creditContainerProblems(osmScreenCredit, OSM_ATTRIBUTION)).toEqual(['renderer attribution (CesiumJS) missing']);
  });
});
