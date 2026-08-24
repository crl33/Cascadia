/**
 * Attribution honesty for the credit strip (docs/research/spike-report-2026-08-22.md, known
 * gap 7): the viewer is constructed ion-free, yet Cesium's default `CreditDisplay.cesiumCredit`
 * is the Cesium ion logo — a claim about a service this app never calls. Decision: replace that
 * default through the supported static `CreditDisplay.cesiumCredit` API with a text credit
 * naming CesiumJS as the renderer (SceneController performs the assignment before the Viewer is
 * constructed, so the ion default is never even built). Never hide the credit container with
 * CSS: the basemap's own credit (OSM) renders in the same container and its tile policy
 * requires that attribution to stay visible.
 * This module is renderer-free so the decision is testable in the node test environment.
 */

/** Accurate replacement for the default ion logo credit: the renderer, as text, no ion mark. */
export const CESIUM_RENDERER_CREDIT_HTML =
  '<a href="https://cesium.com/cesiumjs/" target="_blank" rel="noopener noreferrer">CesiumJS</a> (renderer)';

/** Markers of the stock ion credit that Cesium 1.144 builds in CreditDisplay.getDefaultCredit(). */
const ION_CREDIT_MARKERS = ['ion-credit.png', 'Cesium ion'] as const;

export const containsIonCredit = (html: string): boolean =>
  ION_CREDIT_MARKERS.some((marker) => html.includes(marker));

/**
 * Assertion helper (unit and e2e): given the credit container's innerHTML and the active
 * basemap's attribution string, list every attribution-honesty violation. Empty array = honest:
 * no ion logo, the renderer is credited, and the basemap attribution is still visible.
 */
export function creditContainerProblems(containerHtml: string, basemapAttribution: string): string[] {
  const problems: string[] = [];
  if (containsIonCredit(containerHtml)) problems.push('ion logo credit rendered although ion is never used');
  if (!containerHtml.includes('CesiumJS')) problems.push('renderer attribution (CesiumJS) missing');
  if (!containerHtml.includes(basemapAttribution)) problems.push(`basemap attribution "${basemapAttribution}" missing`);
  return problems;
}
