/**
 * SceneDataBridge: the single React effect set that pushes query data into the SceneController
 * (geography, basin outlines per LOD, hazard categories, forecast points). Renders nothing.
 */
import { useEffect, useMemo } from 'react';
import { useBasinGeometries, useBasinGeometry, useBasins, useCameras, useFloodGeography, useLabels, useRiverNetwork, useVizBasins, useVizField, useVizRivers } from '../api/hooks';
import type { FieldRasterState, FloodCategory, GeoFeature } from '../contracts/schemas';
import type { BasinSusceptibility } from '../layers/susceptibility/BasinSusceptibilityLayer';
import { cameraAttentionByBasin } from '../layers/cameras/attention';
import { riverIntensities } from '../layers/network/match';
import type { SceneController } from '../scene/SceneController';
import { useSceneStore } from '../state/store';
import { createWeatherHold } from './weather-hold';

interface Props { controller: SceneController }

/**
 * Store-free DOM stamps for tests and tooling (like data-tiles-pending): the count of weather
 * setData calls that reached the renderer, and '1' while a document is held for the settle.
 */
function stampWeatherApplied(): void {
  const root = document.documentElement;
  root.dataset.weatherSetData = String(Number(root.dataset.weatherSetData ?? '0') + 1);
}
function stampWeatherDeferred(holding: boolean): void {
  const root = document.documentElement;
  if (holding) root.dataset.weatherDeferred = '1';
  else delete root.dataset.weatherDeferred;
}

export function SceneDataBridge({ controller }: Props) {
  const basins = useBasins();
  const basinIds = useMemo(() => basins.data?.items.map((b) => b.id) ?? [], [basins.data]);
  const stateGeometries = useBasinGeometries(basinIds, 'state');
  const selectedBasinId = useSceneStore((s) => s.selectedBasinId);
  const selectedGeometry = useBasinGeometry(selectedBasinId, 'basin');
  const vizBasins = useVizBasins();
  const rivers = useVizRivers(selectedBasinId);

  const stateLod = useMemo(() => {
    const out: Record<string, GeoFeature> = {};
    stateGeometries.forEach((feature, i) => { const id = basinIds[i]; if (feature && id) out[id] = feature; });
    return out;
  }, [basinIds, stateGeometries]);

  const categories = useMemo(() => {
    const out: Record<string, FloodCategory> = {};
    vizBasins.data?.items.forEach((b) => { out[b.id] = b.surfaces.hazard.official_category; });
    return out;
  }, [vizBasins.data]);

  // Alert PRESENCE only (any event type): the edge dash says "an official advisory names this
  // basin"; what it is, and how severe, lives in the panel where the words fit.
  const alerted = useMemo(() => {
    const out: Record<string, boolean> = {};
    vizBasins.data?.items.forEach((b) => { out[b.id] = (b.official_alerts?.length ?? 0) > 0; });
    return out;
  }, [vizBasins.data]);

  // The Cascade-derived susceptibility, read straight off the surface the envelope already carried. Nothing is
  // computed here: `state`, `confidence`, `experimental` and `reason` are the backend's own
  // fields, and a basin the backend refused arrives as `unknown` WITH its reason rather than
  // being dropped — the layer renders that as incomplete, never as calm.
  const susceptibility = useMemo(() => {
    const out: Record<string, BasinSusceptibility> = {};
    vizBasins.data?.items.forEach((b) => {
      const s = b.surfaces.susceptibility;
      out[b.id] = {
        state: s.state,
        confidence: s.confidence ?? 'unknown',
        experimental: s.experimental ?? true,
        reason: s.reason ?? null,
      };
    });
    return out;
  }, [vizBasins.data]);

  useEffect(() => { if (basins.data) controller.setGeography(basins.data.items); }, [controller, basins.data]);

  useEffect(() => {
    const basinLod: Record<string, GeoFeature> = {};
    if (selectedBasinId && selectedGeometry.data) basinLod[selectedBasinId] = selectedGeometry.data;
    controller.setData('basins', { stateLod, basinLod, categories, alerted });
  }, [controller, stateLod, selectedBasinId, selectedGeometry.data, categories, alerted]);

  useEffect(() => {
    controller.setData('basin_susceptibility', { geometry: stateLod, surfaces: susceptibility });
  }, [controller, stateLod, susceptibility]);

  useEffect(() => { if (rivers.data) controller.setData('rivers', rivers.data); }, [controller, rivers.data]);
  // Weather fields ride the arrival, not the flight (film rule 3): a document that lands while
  // the camera is flying is held by weather-hold.ts and applied on settle — one effect keyed on
  // the store's coarse flightState, never per frame. The hold instance is bound to the
  // controller it feeds; the DOM stamps let an e2e observe the deferral without React state.
  const flightState = useSceneStore((s) => s.flightState);
  const weatherHold = useMemo(
    () => createWeatherHold<FieldRasterState | null>((layer, doc) => { controller.setData(layer, doc); stampWeatherApplied(); }, stampWeatherDeferred),
    [controller],
  );
  useEffect(() => { weatherHold.setFlying(flightState === 'flying'); }, [weatherHold, flightState]);

  const precipField = useVizField('precip_observed');
  useEffect(() => {
    // A 404 ("nothing current to draw") pushes null: the layer clears rather than letting a
    // stale hour linger as if it were now. While loading, push nothing — no flicker to empty.
    if (precipField.data) weatherHold.offer('precip_observed', precipField.data);
    else if (precipField.isError) weatherHold.offer('precip_observed', null);
  }, [weatherHold, precipField.data, precipField.isError]);

  const snowField = useVizField('snow_cover');
  useEffect(() => {
    if (snowField.data) weatherHold.offer('snow_cover', snowField.data);
    else if (snowField.isError) weatherHold.offer('snow_cover', null);
  }, [weatherHold, snowField.data, snowField.isError]);

  const labelSet = useLabels();
  useEffect(() => {
    if (labelSet.data) controller.setData('labels', { labels: labelSet.data.labels });
  }, [controller, labelSet.data]);

  const cameraSet = useCameras();
  const pinnedCameraId = useSceneStore((s) => s.pinnedCameraId);
  // Official evidence only: alerts + the official 72 h hazard category, straight off the
  // envelope the map already fetches. Derived surfaces never light a camera.
  const cameraAttention = useMemo(() => cameraAttentionByBasin(vizBasins.data), [vizBasins.data]);
  useEffect(() => {
    if (cameraSet.data) controller.setData('cameras', { cameras: cameraSet.data.cameras, pinnedCameraId, attention: cameraAttention });
  }, [controller, cameraSet.data, pinnedCameraId, cameraAttention]);

  const flood = useFloodGeography();
  useEffect(() => {
    if (flood.data) {
      controller.setData('floodplain', flood.data);
      controller.setData('levees', flood.data);
    }
  }, [controller, flood.data]);

  const network = useRiverNetwork();
  // The rivers-respond join: the selected basin's per-station flow_visual_intensity (already
  // fetched for the panel) matched onto the network's river names. Pure derivation (match.ts);
  // unmatched or unknown rivers simply keep their cartographic base.
  const riverFlow = useMemo(
    () => (network.data && rivers.data ? riverIntensities(network.data, rivers.data.items) : {}),
    [network.data, rivers.data],
  );
  useEffect(() => {
    if (network.data) controller.setData('river_network', { network: network.data, intensities: riverFlow });
  }, [controller, network.data, riverFlow]);

  return null;
}
