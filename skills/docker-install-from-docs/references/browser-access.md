# Browser-access diagnosis (Docker service installs)

When a self-hosted service container is running (`docker compose ps` shows Up) but the browser shows nothing / error / timeout:

1. Verify service is actually serving with `curl` to the exact URL first (not just root):
   `curl -s -o /dev/null -w "%{http_code}" --max-time 10 "http://127.0.0.1:PORT/PATH/"`
   Expected `200`; `404` means missing subpath (`/tt-rss`); `502`/`503` means nginx upstream not ready.
2. Check bind address: `docker port <web-nginx>` — if `127.0.0.1:PORT`, browser using `localhost` (resolves to IPv6 `::1`) will fail. Fix: edit `.env` `HTTP_PORT=PORT` (remove `127.0.0.1:`), then `docker compose up -d --force-recreate web-nginx` (`restart` alone will NOT re-read `.env` port mapping).
3. Confirm URL parts: protocol `http` (not `https`), include subpath (`/tt-rss`), correct port.
4. Only after curl verifies `200` should you tell the user the service is live; never assume browser failure = container failure.
5. If user explicitly asks for browser confirmation (or `curl` 200 but they still report failure), verify with `browser-use` (`new_tab(url)` → `wait_for_load()` → `page_info()` / screenshot). If `browser-use` hangs but `curl` is fast (<0.5s), the page has resource/JS loading issues — check nginx static-file serving (e.g., `/tt-rss/css/default.css`) and `docker compose ps` health before declaring full access.
