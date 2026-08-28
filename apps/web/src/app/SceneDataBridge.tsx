/**
 * SceneDataBridge: the single React effect set that pushes query data into the SceneController
 * (geography, basin outlines per LOD, hazard categories, forecast points). Renders nothing.
 */
import { useEffect, useMemo } from 'react';
import { useBasinGeometries, useBasinGeometry, useBasins, useVizBasins, useVizRivers } from '../api/hooks';
import type { FloodCategory, GeoFeature } from '../contracts/schemas';
import type { BasinSusceptibility } from '../layers/susceptibility/BasinSusceptibilityLayer';
import type { SceneController } from '../scene/SceneController';
import { useSceneStore } from '../state/store';

interface Props { controller: SceneController }

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
    controller.setData('basins', { stateLod, basinLod, categories });
  }, [controller, stateLod, selectedBasinId, selectedGeometry.data, categories]);

  useEffect(() => {
    controller.setData('basin_susceptibility', { geometry: stateLod, surfaces: susceptibility });
  }, [controller, stateLod, susceptibility]);

  useEffect(() => { if (rivers.data) controller.setData('rivers', rivers.data); }, [controller, rivers.data]);

  return null;
}
