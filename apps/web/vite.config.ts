/**
 * Vite configuration for the Cascadia Papsukkal web spike.
 * Owns: the React plugin, the ion-free Cesium static asset copy (Workers/ThirdParty/Assets/Widgets)
 * with CESIUM_BASE_URL defined at build time — the pattern from Cesium's official Vite example —
 * and the vitest settings. No proxies, no external scripts: the API base is a runtime env value.
 */
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { viteStaticCopy } from 'vite-plugin-static-copy';

const CESIUM_SOURCE = 'node_modules/cesium/Build/Cesium';
const CESIUM_BASE_URL = 'cesiumStatic';

export default defineConfig({
  define: { CESIUM_BASE_URL: JSON.stringify(`/${CESIUM_BASE_URL}`) },
  plugins: [
    react(),
    viteStaticCopy({
      // vite-plugin-static-copy v4 preserves the source directory structure; stripBase drops
      // `node_modules/cesium/Build/Cesium/` (4 segments) so the output is dist/cesiumStatic/{ThirdParty,Workers,Assets,Widgets}.
      targets: ['ThirdParty', 'Workers', 'Assets', 'Widgets'].map((dir) => ({
        src: `${CESIUM_SOURCE}/${dir}`,
        dest: CESIUM_BASE_URL,
        rename: { stripBase: 4 },
      })),
    }),
  ],
  server: { port: 5173, strictPort: true },
  build: { chunkSizeWarningLimit: 5000 }, // CesiumJS is one ~4.4 MB chunk by nature; code-splitting it is a later optimisation
  test: {
    include: ['src/**/*.test.ts'],
    environment: 'node',
  },
});
