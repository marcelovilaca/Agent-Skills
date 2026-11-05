# Verifying a Vite front end in a real browser

A unit test and a server-rendered markup assertion cannot see a blank page,
a text overlap, a mis-sized sheet or a clipped caption. Only a rendered
browser can. This is the recipe for one that needs no browser tool: headless
Chrome driven over the DevTools Protocol.

## When to use

- Before calling a front-end build done.
- When a screenshot is needed as evidence.
- When a layout regression must be caught automatically, not by eye.

## The CDP client

Chrome exposes a WebSocket per page target. Node 22+ has a global
`WebSocket`, so no dependency is needed.

```js
const CHROME = process.env.CHROME_EXECUTABLE || "chromium"; // override with the installed browser executable
const chrome = spawn(CHROME, [
  "--headless=new", "--disable-gpu", "--no-sandbox", "--hide-scrollbars",
  "--remote-debugging-port=9222",
  `--window-size=${WIDTH},${HEIGHT}`,
  "--user-data-dir=" + profileDir,   // ONE shared dir under the temp dir
  "about:blank",
], { stdio: "ignore" });

// wait for http://127.0.0.1:9222/json/version to answer
const targets = await (await fetch("http://127.0.0.1:9222/json/list")).json();
const socket = new WebSocket(targets.find((t) => t.type === "page").webSocketDebuggerUrl);

class Cdp {
  constructor(socket) {
    this.socket = socket; this.id = 0; this.pending = new Map();
    socket.addEventListener("message", (event) => {
      const message = JSON.parse(event.data);
      const entry = this.pending.get(message.id);
      if (!entry) return;
      this.pending.delete(message.id);
      message.error ? entry.reject(new Error(message.error.message)) : entry.resolve(message.result);
    });
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.socket.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
}
```

Then `Page.enable`, `Runtime.enable` and
`Emulation.setDeviceMetricsOverride({ width, height, deviceScaleFactor: 2, mobile: true })`
to get a phone-sized viewport at 2x.

- `Page.navigate` + wait → load a page.
- `Runtime.evaluate` with `returnByValue: true` → run JS in the page and
  read a JSON value back. This is how you *measure*.
- `Page.captureScreenshot` → a PNG you can look at or attach.

## Measure, do not squint

A screenshot tells you something looks wrong; a measurement tells you which
rule is wrong. Run both: measure to find the defect, screenshot to judge the
result.

The rules worth measuring, in the order they bite:

| Rule | How to measure | What it catches |
|---|---|---|
| Clipped text | For each element with a direct text node, union its `Range.getClientRects()`, then find the **nearest ancestor whose overflow is `hidden`** and compare | Text cut off by its own box *or* by an ancestor — the ancestor case is the common one and no `scrollWidth` check finds it |
| Collapsed but still painting | Element with `max-height: 0` whose `getBoundingClientRect().height > 2` | A closed drawer leaving a strip of background (padding survives `max-height: 0`) |
| Page overflow | `documentElement.scrollWidth - clientWidth` | Horizontal scroll on a phone |
| Wider than the viewport | Any element's rect wider than `window.innerWidth` | A sheet that overflows its screen |

Exclusions, each of which is a false positive you will otherwise chase:

- A **marquee/ticker** is deliberately wider than its window and clipped.
  Skip anything inside it.
- A box collapsed with `max-height: 0` is hiding its content on purpose.
- Decorative pseudo-elements (a scalloped awning, a lamp glow) overflow
  their parent without anything being wrong — so compare *text* rects, not
  element boxes.
- **A scrollable region is not a clipped region.** `overflow: auto` and
  `overflow: scroll` keep the content reachable by scrolling, so only
  `overflow: hidden` loses it. Matching "not `visible`" instead of
  "`hidden`" reports every scroll container as a defect: an internally
  scrolling panel and a horizontally scrolling carousel are both reported,
  and both are correct.

## The audit needs a self-test

An audit that never fails is worthless, and a heuristic audit fails on
intentional styling until it is tuned. Prove it works by injecting known
breakage and asserting it is caught:

```js
// inject: text wider than a clipping parent, and a collapsed box that paints
wrap.innerHTML =
  '<div style="width:120px;height:20px;overflow:hidden">' +
  '<div style="width:400px;height:20px;white-space:nowrap">TOO WIDE</div></div>' +
  '<div style="max-height:0;overflow:hidden;padding:10px;background:#f00">' +
  '<div style="height:40px"></div></div>';
```

Then assert the results contain one `text-clipped-*` and one
`collapsed-but-painting`. Remove the injection afterwards, and do not count
the injected findings in the total.

This self-test is what exposed the ancestor-clipping gap: comparing a text
rect only against its own element reports nothing when the *parent* is the
thing cutting it off.

## Screenshotting states, not just pages

One script should capture each app plus its interesting states, so a
regression is visible in the diff: the landing view, a drawer open, a box
open, a paper open, a scrolled/pulled state. Navigate, wait, optionally
click, then capture.

Put the PNGs somewhere the project keeps them (`docs/screenshots/`) so they
can be referenced in a report.

## Scratch state

One shared Chrome profile directory for every script, under the system temp
dir (`TMPDIR`/`TEMP`), never one per script inside the project — otherwise
the repo fills with directories that look like project files. Add the
pattern to `.gitignore` anyway.

## What this finds that nothing else does

- **Blank pages from a missing `base`.** Vite emits absolute `/assets/...`
  URLs; an app served from a subpath 404s every asset and renders nothing.
  The build succeeds and the unit tests pass.
- **Text overlapping itself inside a button.** The browser's UA stylesheet
  applies `font: 400 13.33px Arial` to buttons, and that shorthand resets
  `line-height` to `normal` and cascades `font-family` into every
  descendant.
- **One element painting over another's text.** Overlapping siblings hide
  content with no CSS clipping at all, so no layout rule reports it.
- **A scroll container clipping its own decoration.** An element positioned
  inside an `overflow: auto` box is clipped by it.
- **A hint that will not hide.** A CSS keyframe animation beats an inline
  `opacity: 0`; use `display: none` or a class.
