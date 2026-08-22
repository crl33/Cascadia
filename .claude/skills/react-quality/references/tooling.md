# Tooling reference

## React Doctor (static scan)

```bash
npx react-doctor@latest                       # full audit, prints score
npx react-doctor@latest --verbose --scope changed   # only issues introduced vs base branch
npx react-doctor@latest --scope lines         # only changed lines
npx react-doctor@latest --json --json-out react-doctor-report.json  # structured evidence (delete after use)
npx react-doctor@latest design --verbose      # UI composition / a11y / motion rules only
npx react-doctor@latest rules explain <rule>  # rationale for a rule
npx react-doctor@latest rules disable|set|category|ignore-tag …   # edits doctor.config.*
npx react-doctor@latest install               # installs the agent skill into the repo
npx react-doctor@latest ci install            # GitHub Actions workflow: PR-scoped findings
```

Rule recipes: `https://www.react.doctor/prompts/rules/<plugin>/<rule>.md`.
Full triage playbook (fetched on demand, never cached): `https://www.react.doctor/prompts/react-doctor-agent.md`.
Telemetry opt-out: `--no-telemetry`.

Config lives in `doctor.config.ts` (or `package.json#reactDoctor`) at `apps/web/`.

## React Doctor runtime trace

```bash
npx react-doctor@latest scan http://localhost:5173 --format json
# authenticated session: start Chrome with --remote-debugging-port=9222 in a dedicated profile
npx react-doctor@latest scan https://staging.example --cdp http://127.0.0.1:9222 --format json
```

Opens an isolated Chrome, records a DevTools trace while you reproduce the interaction,
flashes component names on render, stops on Enter (≤5 min). Output: summary + `.json.gz`
trace — local, potentially sensitive (URLs, source paths); never upload without approval.

## React Scan (dev-only render highlighting)

Vite (`apps/web/index.html`, dev only — gate on `import.meta.env.DEV` or a separate
`index.dev.html`):

```html
<!-- paste BEFORE any other script; dev only -->
<script crossOrigin="anonymous" src="//unpkg.com/react-scan/dist/auto.global.js"></script>
```

Or programmatic, in `src/main.tsx` behind `import.meta.env.DEV`:

```ts
if (import.meta.env.DEV) {
  const { scan } = await import('react-scan')
  scan({ enabled: true, log: false, showToolbar: true, animationSpeed: 'fast' })
}
```

API: `scan(options)`, `useScan(options)`, `setOptions()`, `getOptions()`,
`onRender(Component, cb)`. Options: `enabled`, `log`, `showToolbar`, `animationSpeed`,
`onCommitStart/onRender/onCommitFinish`. `dangerouslyForceRunInProduction` must stay `false`.

Note: the react-scan README recommends React Doctor as the successor for agents; keep React
Scan for the live "what is re-rendering right now" loop during Cesium integration work.

## Context7 (current docs)

```bash
npx ctx7@latest library "CesiumJS" "camera flyTo with terrain and easing"
npx ctx7@latest docs /cesiumgs/cesium "Camera.flyTo options easingFunction"
npx ctx7@latest login        # higher rate limits (optional)
export CONTEXT7_API_KEY=...  # alternative to login
```

Rules: resolve the library first (IDs are `/org/project`), one concept per `docs` query, at
most 3 commands per question, no secrets in queries, say so if quota is exhausted.

Library IDs to try first (verify with `library`; IDs can change):

| Library | Likely ID |
|---|---|
| CesiumJS | `/cesiumgs/cesium` |
| React | `/facebook/react` (or `/reactjs/react.dev`) |
| Vite | `/vitejs/vite` |
| TanStack Query | `/tanstack/query` |
| Zustand | `/pmndrs/zustand` |
| Zod | `/colinhacks/zod` |
| Vitest | `/vitest-dev/vitest` |
| Playwright | `/microsoft/playwright` |
| Tailwind CSS | `/tailwindlabs/tailwindcss` |

Context7 MCP is an alternative to the CLI (`https://mcp.context7.com/mcp`, tools
`resolve-library-id` and `query-docs`); same workflow.
