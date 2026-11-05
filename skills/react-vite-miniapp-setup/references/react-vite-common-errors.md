# Common React + Vite errors and their causes

| Symptom | Cause | Fix |
|---|---|---|
| `Could not resolve "./src/App"` | The root component is at `src/App.tsx`, so `main.tsx` (also in `src/`) imports `./App` | `import App from './App'` |
| `Could not resolve "../../../design-system"` | A relative path that walks past the project root | Use the `@design` alias from `vite.config.ts` |
| `Could not resolve "@design/index.scss"` | The alias is missing, or the design system's `exports` map has no matching entry | Add `resolve.alias` **and** the `types` condition + a `src/index.d.ts` |
| `tsc` rejects a CSS import | A CSS-only package has no type declarations | `exports: { ".": { "types": "./src/index.d.ts", "default": "./src/index.css" } }` and `export {}` in that file |
| `React is not defined` when server-rendering components | tsx/esbuild compiles JSX with the classic runtime, which expects `React` in scope | `globalThis.React = React` before importing the components |
| The page renders blank, `index.html` returns 200 | Vite emitted absolute `/assets/...` URLs and the app is served from a subpath | `base: "./"` in the app's `vite.config.ts` |
| Multi-line text inside a button overlaps itself | The UA stylesheet's `font: 400 13.33px Arial` on buttons resets `line-height` to `normal` and cascades `font-family` into children | Reset `font-family`/`font-size`/`line-height` on form controls; make the display font opt-in |
| An element is clipped by its own scroll container | A decoration positioned inside an `overflow: auto` box | Move the decoration outside the scrolling element, or position it on a wrapper |
| An element will not hide when you set `opacity: 0` | A CSS keyframe animation on `opacity` overrides the inline style | Use `display: none`, or toggle a class |
| Dev server starts on a different port than expected | Vite moves to the next free port when the requested one is taken | `server: { strictPort: true }` so it fails loudly |
| One app's build deletes another app's output | `emptyOutDir` removes the whole outDir, and apps share a parent | Give each app a distinct `outDir` subdirectory, and check `emptyOutDir` is scoped to it |
| The build succeeds but the app shows placeholder/offline content | The API base is baked in at build time and the client fell back silently | Rebuild with the right base, and serve the service on the port the build expects |
