---
name: "react-vite-miniapp-setup"
description: "Setup React Vite mini‑apps in a monorepo."
license: "MIT"
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_related_skills: "local-stack-testing"
  hermes_tags: "react, vite, miniapp, frontend, monorepo"
  version: "1.1.1"
---

# React Vite Mini‑App Setup

## Always‑on rules
- **Project layout**: each mini‑app lives under `apps/<app-name>/` with a `src/` folder containing `main.tsx`, `App.tsx`, and a `vite.config.ts`. The shared design system resides at the repository root `design-system/`.
- **Root component import** (`src/main.tsx`):
  ```tsx
  import App from './src/App';
  ```
  *Pitfall*: using `./App` fails because the component lives in `src/`.
- **Design‑system stylesheet**: Vite resolves imports relative to the app root, so the correct relative import is:
  ```tsx
  import '../../design-system/index.scss';
  ```
  *Pitfall*: using `../../../design-system/...` goes beyond the project root and cannot be resolved.
- **Recommended Vite alias** – add to each app’s `vite.config.ts`:
  ```ts
  import { defineConfig } from 'vite';
  import react from '@vitejs/plugin-react';
  import { resolve } from 'path';

  export default defineConfig({
    plugins: [react()],
    resolve: { alias: { '@design': resolve(__dirname, '../../design-system') } },
    build: { outDir: '../../public/<app-name>', emptyOutDir: true },
    server: { port: 517X, strictPort: true },
  });
  ```
  Then import the stylesheet with `import '@design/index.scss';`.

## Procedure for adding a new mini‑app
1. **Create folder**:
   ```bash
   mkdir -p apps/<app-name>/src
   ```
2. **Create `package.json`** – match React 18, Vite, TypeScript versions of existing apps.
3. **Create `vite.config.ts`** – use the alias snippet above, substituting `<app-name>` in `outDir` and picking a unique `port` (e.g., 5173, 5174, …).
4. **Write `src/main.tsx`** – include the correct imports for the root component and stylesheet (see Always‑on rules).
5. **Write `src/App.tsx`** – UI code specific to the mini‑app.
6. **Install dependencies**:
   ```bash
   cd apps/<app-name>
   npm install --silent
   ```
7. **Build for production**:
   ```bash
   npm run build --silent
   ```
   *Pitfall*: run the build only after fixing imports; otherwise Vite will emit “Could not resolve … index.scss” or “./src/App”.
8. **Verify output** – the compiled bundle appears under `public/<app-name>` and is served by the backend.
9. **Verify it renders** – a successful build is not a rendered page. Load each app in a headless browser and measure the layout (clipped text, collapsed boxes that still paint, page overflow); see `references/visual-verification.md`. Run the live API tests against the running service; see the `local-stack-testing` skill.

## Common pitfalls & fixes
- **Incorrect root component import** → `Could not resolve "./src/App"`.
- **Design‑system import too deep** → `Could not resolve "../../../design-system"`.
- **Missing Vite alias** → `@design` import fails; ensure `resolve.alias` is present.
- **Port conflict** → give each app a distinct port.
- **Build fails after `npm install`** → confirm Node version and that all dependencies installed.
- **App served from a subpath renders blank** → Vite emits absolute
  `/assets/...` URLs by default, which 404 when the app is served at
  `/<app-name>/`. Add `base: "./"` to that app's `vite.config.ts`. Nothing
  else catches this: the build succeeds and the unit tests pass.
- **Multi-line text inside a button overlaps itself** → the browser's UA
  stylesheet applies `font: 400 13.33px Arial` to buttons, and that
  shorthand resets `line-height` to `normal` and cascades `font-family`
  into every descendant. Reset `font-family`/`font-size`/`line-height` on
  form controls and make any display font opt-in.
- **The build succeeds but the app shows placeholder/offline content** → the
  API base is baked in at build time and the client fell back silently.
  Rebuild with the right base, and serve the service on the port the build
  expects.
- **A control unlocks locally but reveals nothing** → a state that comes
  from a local timer rather than the server is a bug, and a badge hardcoded
  to `LOCKED` beside an already-open element is a lie. Derive every visible
  state from the same server answer.

## References
- `references/vite-alias.md` – the alias, the shared output root, and serving each app from its own subpath.
- `references/react-vite-common-errors.md` – symptom → cause → fix table.
- `references/visual-verification.md` – headless-Chrome layout measurement, the audit rules and their self-test, and screenshot capture.

## Related skills
- `local-stack-testing` – running the service locally, dev auth, repeatable live tests, and leaving the working tree clean.

## Telegram WebApp integration
- **Initialization** – In every app's root component, call:
  ```tsx
  import { WebApp } from '@twa-dev/sdk';
  useEffect(() => {
    WebApp.ready();
    WebApp.setHeaderColor('#000000'); // match 8‑bit black theme
    WebApp.expand();                 // fill the screen
  }, []);
  ```
- **Haptic feedback** – Use `WebApp.HapticFeedback.impactOccurred('light')` for button clicks and `notificationOccurred('success')` for successful actions. This gives the required 8‑bit tactile feel.
- **Background‑play workaround** – When playing audio (e.g., in Cassette Vault), after starting playback send a small payload to keep Telegram audio alive while the user minimizes the WebApp:
  ```tsx
  WebApp.sendData(JSON.stringify({ action: 'play', id: cassetteId }));
  ```
- **User‑premium flag** – Extract `premium` query param on app start:
  ```tsx
  const isPremium = new URLSearchParams(window.location.search).get('premium') === 'true';
  ```
  Use this flag to conditionally render premium‑only UI.
- **Asset placement** – Put all static assets (EPUBs, audio files, images) under the app's `public/` directory. Vite automatically copies them to the build output, preserving relative URLs (e.g., `/audio/file.mp3`).
