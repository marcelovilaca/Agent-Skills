# React + Vite Mini-App Setup

## Overview

This guide covers adding one React/Vite mini-app under `apps/<app-name>/` in a monorepo, sharing the repository-root design system, building into `public/<app-name>/`, and checking the rendered app rather than treating a successful build as sufficient. See [SKILL.md](SKILL.md) for the workflow and Telegram WebApp examples.

The companion references provide the alias/subpath details ([vite-alias.md](references/vite-alias.md)), common fixes ([react-vite-common-errors.md](references/react-vite-common-errors.md)), and browser-based visual verification ([visual-verification.md](references/visual-verification.md)).

## How to Use

### Inputs and prerequisites

- A monorepo checkout with a root `design-system/` and an existing frontend setup whose React, Vite, TypeScript, and plugin versions can be matched. The skill's procedure calls out React 18; use the versions already established by the target repository rather than upgrading them incidentally.
- A unique app name and development port, plus the app-specific UI and any API base expected at build time.
- Node.js and npm compatible with the repository. A running backend is needed to verify server/API behavior, but not to compile the frontend.
- For visual checks, an installed Chrome/Chromium executable. The linked CDP recipe uses Node 22+ if relying on its built-in global `WebSocket`.

### Quick start

Create the app scaffold first:

```bash
mkdir -p apps/<app-name>/src
```

Once those files exist, install and build from the new app directory:

```bash
cd apps/<app-name>
npm install --silent
npm run build --silent
```

The required files and import pattern should follow this shape:

```text
apps/<app-name>/
├── package.json
├── vite.config.ts
└── src/
    ├── main.tsx
    └── App.tsx
```

`src/main.tsx` and `src/App.tsx` are siblings, so import the component as `./App`. Import the shared stylesheet through the Vite alias:

```tsx
import App from './App';
import '@design/index.scss';
```

This uses the linked reference's path resolution. The SKILL.md contains a conflicting `./src/App` / relative stylesheet snippet; that path does not match the stated file layout. Use `./App` and the configured `@design` alias.

A recommended Vite configuration is:

```ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';

export default defineConfig({
  base: './',
  plugins: [react()],
  resolve: { alias: { '@design': resolve(__dirname, '../../design-system') } },
  build: { outDir: '../../public/<app-name>', emptyOutDir: true },
  server: { port: 5174, strictPort: true },
});
```

The example uses port 5174; choose a distinct unused port for each app. Resolve the alias from the config file's location so builds work from different current directories. `base: './'` is important when the backend serves the app at `/<app-name>/`.

## Technical Details

### Workflow and outputs

1. Create the app folder and required source/config files. Keep app-specific UI in `src/App.tsx`.
2. Match dependency versions already used by sibling apps; add the alias and scoped build output in `vite.config.ts`.
3. Install dependencies with npm and run the app's configured production build.
4. Check that the generated bundle is under `public/<app-name>/` and that the backend serves it at the intended path.
5. Open the served page in a real/headless browser and measure layout defects. Run live API checks against the running service when the app depends on it; the related `local-stack-testing` skill supplies that separate workflow.

The intended build output is the app-specific public directory; it is not evidence that the page loads, fetches the right API, or renders correctly.

### Telegram WebApp integration

When the app is embedded in Telegram, the skill shows initialization using `@twa-dev/sdk`: call `WebApp.ready()`, optionally set the header color, and expand the viewport. It also demonstrates light impact/success notification haptics, using a `premium=true` query parameter for conditional presentation, and sending a JSON `play` payload to the bot when playback starts.

Treat a query-string flag as display input only, never as authorization or entitlement proof. A `sendData` payload does not itself guarantee browser audio will continue while Telegram suspends a minimized WebApp. For actual background audio, the related Telegram suite guide routes playback through a native Telegram audio message sent by the bot.

Static assets such as EPUBs, audio, and images belong under the app's `public/` directory and are copied into the build output. Confirm the final relative asset URLs at the deployed subpath.

### Verification

A real browser check is required in addition to `npm run build`:

- Navigate to the built app at its served subpath and confirm assets load and visible app content renders.
- Measure direct text against its nearest `overflow: hidden` ancestor, detect collapsed `max-height: 0` boxes that still paint, check horizontal page overflow, and identify elements wider than the viewport. Do not flag `overflow: auto`/`scroll` as clipped content.
- Give an automated layout audit a self-test by injecting known clipped text and a collapsed-but-painting box; confirm both are reported, then remove the injected cases.
- Capture screenshots of meaningful app states when visual evidence is needed.
- If the page is blank but `index.html` returns successfully, inspect built asset URLs and check for `base: './'`.

The linked visual-verification reference provides a Chrome DevTools Protocol approach; the skill directory does not ship a standalone audit executable. A build or server-rendered markup check alone cannot prove browser layout correctness.

### Common limits and safety

- Use a unique port with `strictPort: true`; Vite should fail loudly on a conflict rather than silently switching ports.
- Give every app a distinct `outDir`; `emptyOutDir: true` must not erase another app's build.
- The API base may be baked into the build. Rebuild with the correct base and run the service on the expected port if the app silently shows fallback/offline content.
- Derive visible unlock/entitlement state from the server response. A local timer or hard-coded badge is not a substitute for a server decision.
- Buttons can inherit browser default font settings that alter line-height and descendant fonts; explicitly reset form-control font properties when text overlaps.
- The linked files document known failure modes, not a universal test suite or guarantee that every host project has the same backend and scripts.
