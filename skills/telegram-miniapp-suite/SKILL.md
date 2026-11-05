---
name: "telegram-miniapp-suite"
description: "Build Telegram Mini App suites with grammy and Fastify."
license: "MIT"
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_related_skills: "react-vite-miniapp-setup"
  hermes_tags: "telegram, miniapp, grammy, fastify, monorepo, 8bit"
  version: "1.0.0"
---

# Telegram Mini App suite — proven build recipe

## When to Use

- Building or extending a Telegram Mini App suite: a grammy bot hub that launches
  several mini apps, plus a Fastify API and React/Vite frontends.
- Working on the Pixel Archive Suite project; configure its root for the current checkout.
- Debugging grammy Bot API calls, Drizzle migrations, or mini app auth.

Built as a multi-app workspace (four mini apps, grammY hub, Fastify API,
Postgres). Keep its project root configurable; see its `docs/ARCHITECTURE.md`.

## Stack that works on this machine

- **npm workspaces**, NOT pnpm — `pnpm` is broken here because of a Corepack path-resolution issue.
- React 19 + Vite 7 + `@vitejs/plugin-react` 5 (Vite 8 requires plugin-react 6, which needs `oxc-transform-react`).
- grammY 1.46, `@grammyjs/runner` 2.0.3, Fastify 5, Drizzle 0.45, `postgres` 3.4 (postgres.js).
- TypeScript 5.9 (npm `latest` is 7.0.2 — not what the ecosystem expects yet).
- Node 26.7 is present; `pnpm` is not usable.

## Pitfalls hit and fixed (do not repeat)

1. **grammY `row()` starts a new row.** `keyboard.row().text(...)` as the *first*
   call produces an empty leading row. Put the first button on the implicit row,
   call `row()` only *between* buttons.
2. **grammY `sendInvoice` has no `subscription_period` in its typed payload** in
   1.46. Use `createInvoiceLink(..., "XTR", prices, { subscription_period: 2_592_000 })`
   and send the returned URL as a button. `subscription_period` must be exactly
   2592000 (30 days) and only works with XTR.
3. **Business bot rights are `can_edit_name` / `can_edit_bio` / `can_delete_sent_messages`**,
   not `can_change_name`. `setBusinessAccountName(id, name, other)` needs the
   third `other` arg explicitly (`{}`).
4. **`drizzle-kit push` demands an interactive TTY** and dies in scripts/CI.
   Use numbered plain-`.sql` migrations applied by your own runner (see
   `services/api/src/db/migrate.ts` + a `_migrations` ledger table).
5. **`drizzle-kit generate` fails with "No schema files found"** if the config
   uses a relative path and cwd differs — resolve `schema`/`out` from
   `import.meta.url` instead.
6. **Fastify + `pino-pretty` transport throws at boot** unless `pino-pretty` is an
   actual dependency (it is not bundled with fastify).
7. **Background audio in a mini app**: Telegram suspends HTML5 audio when the app
   is minimised. Deliver a native Telegram audio message via `bot.api.sendAudio`
   instead — Telegram's player keeps playing in the background.
8. **`User.is_premium` is unreliable for bots.** Use a Telegram Stars
   subscription (`XTR`) as the entitlement source of truth; treat `is_premium`
   as a bonus signal only.
9. **tsx/esbuild compiles JSX to the classic runtime** → `React is not defined`
   in SSR scripts. Set `globalThis.React = React` before importing components.
10. **Importing a CSS-only package from TS** needs a `types` condition in
    `package.json` exports plus a `src/index.d.ts` (`export {}`).
11. **`exports` map with a `.ts` file** works for bundlers (Vite) but `tsc` with
    `NodeNext` needs the extension in the import path.
12. **grammY's `Api` class methods are positional** (`sendInvoice(chatId, title,
    description, payload, currency, prices, other)`), while `bot.api.raw.*` and
    the `@grammyjs/types` method args are object-shaped. Read the actual
    `.d.ts` before writing a call.
13. **epubjs 0.3.93's shipped `.d.ts` files are older than its source.** At
    runtime there is no `rendition.locations` (it's `book.locations`), no
    `currentItem()`, no `flowMode` option, and `themes.override(name, obj)`
    takes a CSS *string*, not a rules object — use
    `themes.registerCss(name, css)` + `themes.select(name)`. Declare a narrow
    local interface for the runtime instead of importing the stale types.
14. **epub.js needs `book.locations.generate(chars)`** or `percentage` stays
    undefined and the reader cannot resume.
15. **epub.js outside a browser** needs jsdom with `pretendToBeVisual: true`
    (its location queue uses `requestAnimationFrame`) plus a
    `URL.createObjectURL` shim, and `globalThis.NodeFilter` /
    `globalThis.HTMLElement` must be exposed. Node 26's `navigator` is
    getter-only and cannot be assigned.
16. **pdf.js in Node**: use `pdfjs-dist/legacy/build/pdf.mjs` and set
    `GlobalWorkerOptions.workerSrc` to a `file://` URL (an absolute Windows
    path is not a valid ESM specifier).
17. **EPUB validity**: `epub:type` requires `xmlns:epub="http://www.idpf.org/2007/ops"`
    on the root element, or every chapter fails to parse as XHTML. Generate
    sample media with a script and verify it opens, don't hand-write it.
18. **Docker Desktop can stop its daemon on its own** (it did mid-session).
    Symptom: `ECONNREFUSED` on the DB port and `docker compose ps` failing
    with "The system cannot find the path specified". Restart
    `Docker Desktop.exe`, wait for `docker version` to report a server, then
    `compose up -d` — the container comes back with its volume intact.
19. **MP3 files start with an ID3 tag, not a frame sync** — skip the tag
    (`10 + synchsafe size`) before looking for `0xFF 0xE0`.
20. **ffmpeg writes filter metadata to stderr, not stdout** — `astats` +
    `ametadata=print` output lands on stderr; capturing stdout finds nothing.
21. **For a real VU meter, route audio through an AnalyserNode**
    (`<audio> → MediaElementSource → AnalyserNode → destination`) and read
    `getByteFrequencyData` per frame. Keep the band-shaping maths in a pure
    exported function so it can be unit-tested without an AudioContext.
22. **A mini app cannot post to the user on its own** — background play needs
    a chat id. Persist it (`users.chat_id`) when the bot sees the user, and
    let the API ask the bot to `sendAudio` through a secret-guarded internal
    HTTP endpoint bound to 127.0.0.1.
23. **The browser tool can be dead for a whole project.** Drive headless
    Chrome over CDP instead: launch
    `chrome.exe --headless=new --remote-debugging-port=9222 --user-data-dir=...`,
    read `http://127.0.0.1:9222/json/list` for the page target, and talk CDP
    over a `WebSocket` (Node 22+ has a global `WebSocket`). `Page.capture
    Screenshot` gives PNGs; `Runtime.evaluate` gives measurements. Prefer a
    *measurement* script (clipped text, collapsed boxes that still paint,
    elements wider than the viewport) over eyeballing screenshots.
24. **Vite apps served from a subpath need `base: "./"`.** The default
    absolute `/assets/...` URLs 404 when the app lives at `/archive/`, and
    the app renders blank. Nothing else catches this.
25. **Chrome's UA stylesheet applies `font: 400 13.33px Arial` to buttons**,
    and that shorthand RESETS `line-height` to `normal` and cascades
    `font-family` into every descendant. Multi-line text inside a button
    overlaps itself and prose renders in the wrong font. Reset
    `font-family`/`font-size`/`line-height` on form controls and make the
    display font opt-in.
26. **`max-height: 0` hides content but not padding** — a collapsed drawer
    still paints a strip. Collapse the padding with it.
27. **Avoid emoji for UI icons.** They render as missing-glyph boxes
    wherever an emoji font is absent, and they clash with a pixel aesthetic.
    Geometric glyphs (`◀◀`, `|◀`, `■`, `▶▶`) are safe everywhere.
28. **A layout audit that never fails is worthless.** Give it a self-test:
    inject known breakage (text too wide for a clipping parent, a box
    collapsed with `max-height: 0` that still paints) and assert it is
    caught. The self-test found that comparing a text rect only against its
    *own* element misses the common case — an ancestor clipping a
    descendant. Compare against the nearest clipping ancestor instead.
29. **CSS animations beat inline styles.** An element whose keyframes
    animate `opacity` cannot be hidden by setting `style.opacity = "0"`.
    Use `display: none`, or a class.
30. **Overlapping siblings hide text without any CSS clipping.** Text that
    is *painted over* by the next element looks exactly like clipped text
    but no layout rule reports it. If sheets overlap, the overlap must be
    smaller than the content, or the row must be split.
31. **PNG from scratch, without an image library.** Write raw RGB scanlines
    with a zero filter byte, zlib-compress them, and wrap them in IHDR
    (width, height, bit depth 8, colour type 2), IDAT and IEND with CRC32
    chunks. Take the dimensions from the pixel data, not from constants —
    a hardcoded IHDR size silently corrupts any image that is not that
    size.
32. **`drizzle-kit migrate` needs a journal.** This project applies plain
    SQL files with `npm run db:migrate` instead; a hand-written
    `drizzle/000N_*.sql` is silently ignored by drizzle-kit.
33. **Tell a reasoning model not to think.** Qwen3-class models spend tens of
    thousands of tokens on `reasoning_content` for tasks that need none —
    a 10-headline summarisation went from 12s to 104s and timed out. Send
    `enable_thinking: false` and the same request finishes in seconds.
34. **A CSS animation in a template literal ends the literal.** A backtick
    inside a comment in a `const X = \`...\`` block terminates the string.
    Write "overflow:hidden", not "overflow:`hidden`".
35. **`dotenv/config` reads `process.cwd()`, not the repo root.** A service
    run from `services/api/` never sees the root `.env`. Load it explicitly:
    `dotenv.config({ path: resolve(here, "../../../.env") })`.
36. **A mini app cannot create a Telegram invoice.** Only the bot can, since
    it holds the session. Route it: app → API → bot internal endpoint →
    `createInvoiceLink` → open the returned `t.me` link with
    `openTelegramLink`.
37. **A scrollable region is not a clipped region.** A layout audit that
    flags `overflow: hidden` should not flag `overflow: auto` — the content
    is reachable by scrolling.

## User workflow preferences from this session (always-on)

- **Confirmation gate:** Before any new task, propose "**Next action:** [description]. Confirm to proceed? (Yes/Change/Skip)" — wait for the answer; never start unprompted.
- **Development paper:** After every completed change, append to `README.md`'s Development Paper tracking section with date, what changed, verification results, defects found, and screenshot status. Do not skip — future sessions read the paper to know current state.
- **README structure for this project:** Full manual (4 apps, user + admin sections), deployment guide (local + production env vars), development paper (all phases with status), Moby Dick / reference books section with cover illustrations noted, visual previews list (screenshots at `docs/screenshots/`), and the tracking section at bottom.
- **Git identity:** Use `marcelovilaca@users.noreply.github.com` (GitHub noreply) for commit email so real address isn't published; private repo; force-push only when diverged.
- **Reference books:** When adding a real EPUB (e.g., Moby Dick from Internet Archive / Project Gutenberg), also save the cover illustration (`mobydick-cover.jpg` from `archive.org/download/...`) in `services/api/media/books/` and document both files in seed data with drawer, coverHue, page count.
- **Combined preview page:** For visual verification of all apps together, create `docs/preview-all.html` as a 4-panel grid referencing `docs/screenshots/` (each state shown: Archive drawer/open, Cassette shelf/box+boombox, Newsstand stand/open, Quest Board board/scroll). Use verified PNGs from headless Chrome / CDP (`chrome.exe --headless=new --remote-debugging-port=9222`). This replaces per-app eyeballing with one referenced layout audit.
- **Clarification on ambiguous choices:** When the user selects "something else" (D) for a new feature, do not proceed — ask specifically which of the listed options (A/B/C/D/E) or a new description; confirm with "Confirm: A/B/C/D/E?" before work starts.
- **Visual audit without browser:** When the interactive browser is unresponsive, use headless Chrome over CDP (`chrome.exe --headless=new --remote-debugging-port=9222`) with `Page.captureScreenshot` and measurement scripts (`scripts/audit-layout.mjs`). Give the audit a self-test with injected broken cases.

## Verification without a browser

The browser tool was unresponsive in this session, so the suite proves itself with
scripts in `scripts/`:

- `verify-initdata.mjs` — HMAC validation accepts/rejects correctly.
- `verify-bot.mjs` — hub keyboard shape (rows, `web_app` payloads, HTTPS URLs).
- `verify-design-system.mjs` — static checks on the *built* CSS per app.
- `verify-render.tsx` — `renderToStaticMarkup` the real components and assert on
  the markup (catches crashes without a browser).
- `verify-api.mjs` — live API + Postgres: auth 401, internal 403, entitlement
  grant → unlock, progress round-trip, bookmark create/list/delete, media
  serving with the right content type.
- `verify-reader.ts` — pdf.js opens the real PDF and extracts its text;
  epub.js opens the real EPUB, reads the spine/nav/chapters and round-trips a
  position through a CFI.

Server-rendering the components is the reliable substitute for screenshots.

## Local Postgres

`docker compose up -d` from the repo root; the DB container is
`pixel-archive-db` (postgres:17-alpine, user/pixel/pixel, db pixel_archive).
Migrate with `npm run db:migrate`, seed with `npm run db:seed`
(run from `services/api` with `DATABASE_URL` set, since the root script name
is `db:migrate` only).
