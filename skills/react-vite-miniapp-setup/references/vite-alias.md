# Vite alias and subpath serving

## The alias

Each mini app imports the shared design system through one alias, so the
path is written once and never drifts between apps.

```ts
// apps/<app-name>/vite.config.ts
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "path";

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { "@design": resolve(__dirname, "../../design-system") } },
  build: { outDir: "../../public/<app-name>", emptyOutDir: true },
  server: { port: 517X, strictPort: true },
});
```

Then in the app:

```tsx
import "@design/index.scss";
```

Resolve `__dirname` from the config file's own location, not from the cwd —
the same config must work when the build is invoked from the repo root and
from inside the app.

## Serving from a subpath

`build.outDir` puts every app under `public/<app-name>/`, so the built app
is served at `/<app-name>/`. Vite's default asset URLs are absolute
(`/assets/...`), which 404 at that path and leave the app blank.

```ts
export default defineConfig({
  base: "./",              // relative asset URLs: ./assets/...
  plugins: [react()],
  build: { outDir: "../../public/<app-name>", emptyOutDir: true },
});
```

`base: "./"` makes the built `index.html` reference `./assets/...`, which
resolves correctly from `/<app-name>/` and from the domain root.

**This failure is silent.** The build succeeds, the bundle is emitted, the
server returns 200 for `index.html` — and the page renders empty because
the script never loads. Nothing else in the toolchain catches it. If a page
has no DOM nodes, check the asset URLs in the built HTML first.

## Where the app must import from

- The root component lives at `src/App.tsx`; `src/main.tsx` imports it as
  `./App` (both are inside `src/`). `../App` is wrong.
- The design-system stylesheet is imported through the alias, not by a
  relative path. A relative path has to be written correctly from every
  app's depth, and it breaks the moment an app moves.
- Shared packages that ship CSS only need a `types` condition in their
  `exports` map plus a `src/index.d.ts` containing `export {}`, or `tsc`
  rejects the import.

## Multiple apps, one server

Each app needs its own dev port (`strictPort: true` so a conflict fails
loudly instead of silently moving to the next port), and each needs its own
directory under the shared output root. Building one app must not empty
another's output: `emptyOutDir: true` is safe only because every app
targets a distinct subdirectory.
