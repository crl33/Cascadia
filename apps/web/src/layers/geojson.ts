/** GeoJSON ring extraction shared by layers: outer rings of Polygon/MultiPolygon/GeometryCollection. */
import type { GeoFeature } from '../contracts/schemas';

type Position = [number, number, ...number[]];

interface Geometry { type: string; coordinates?: unknown; geometries?: Geometry[] }

export function outerRings(feature: GeoFeature): Position[][] {
  const rings: Position[][] = [];
  const visit = (geometry: Geometry) => {
    switch (geometry.type) {
      case 'Polygon': {
        const ring = (geometry.coordinates as Position[][])[0];
        if (ring && ring.length >= 4) rings.push(ring);
        break;
      }
      case 'MultiPolygon':
        for (const polygon of geometry.coordinates as Position[][][]) if (polygon[0] && polygon[0].length >= 4) rings.push(polygon[0]);
        break;
      case 'GeometryCollection':
        geometry.geometries?.forEach(visit);
        break;
      default:
        // LineString slivers in the WBD union output are artefacts, not boundaries: skipped.
        break;
    }
  };
  visit(feature.geometry as Geometry);
  return rings;
}
