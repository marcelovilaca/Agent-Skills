---
name: "x-daily-digest"
description: "Use when compiling last-24h X posts into an Obsidian digest."
license: "MIT"
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_category: "research"
  hermes_related_skills: "obsidian, grounded-citations, rss-feeds"
  hermes_tags: "X, Twitter, digest, Obsidian, translation, geopolitics"
  version: "1.0.0"
---

# X / Twitter daily digest

Compile posts from a watchlist of X accounts over a time window (default last 24 hours), translate them to Brazilian Portuguese, render local snapshots, and save a copy-ready note in Obsidian.

Default watchlist: `references/watchlist.md`.

## When to Use

Use when the user asks for tweets/posts from X (Twitter) accounts in a time window, a daily diplomatic/geopolitical digest, or to save that digest into Obsidian. Skip for a single tweet lookup with no digest, and for RSS/blog watches (`rss-feeds`).

## Output contract (every run)

- Persist under `{VAULT}/Daily Digest/𝕏 Twitter/YYYY-MM-DD/` where `VAULT` is `OBSIDIAN_VAULT_PATH` resolved to an absolute path and `YYYY-MM-DD` is the digest run date.
- Files: `YYYY-MM-DD.md` (the note), `snapshots/` (one PNG per in-window post), `tweets_raw.json` (raw payloads).
- Add the day to `Daily Digest/𝕏 Twitter/README.md` as a wikilink.
- Every in-window post is an **isolated** block so it can be copied and reposted independently. Required pieces, in order: account display name + `@handle`, original URL, UTC time, local snapshot image, original text, then a fenced `text` block titled for copy (`Copiar para postar (pt-BR)`).
- Translate every republication body to **pt-BR** (`você`, not `tu`). Keep `@handles`, URLs, and proper names. If the source is already pt-BR, copy it as-is.
- After the posts: list watchlist accounts with **no** in-window post (and the reason), then an investigative digest of relations between posts (same event, same vocabulary, coordinated timing, conspicuous silence).
- State the UTC window and that profile pages only surface ~5 posts, so high-volume accounts may have extra in-window posts not captured.

## Procedure

1. Resolve `now` in UTC (`date -u`) and `cutoff = now - 24h`. Create `{VAULT}/Daily Digest/𝕏 Twitter/YYYY-MM-DD/snapshots/`.
2. For each handle, extract `https://x.com/{handle}` (batch up to 5 URLs). Collect every `status/{id}` plus visible text and dates. Treat pinned/popular posts as candidates only.
3. Filter with the tweet snowflake, not the calendar label on the card:

```python
from datetime import datetime, timezone
ts = datetime.fromtimestamp(((int(status_id) >> 22) + 1288834974657) / 1000, tz=timezone.utc)
in_window = ts >= cutoff
```

4. For every in-window id, fetch the full payload from `https://api.fxtwitter.com/{handle}/status/{id}` (JSON `tweet`: `text`, `author`, `media`, `quote`, `reposted_by`, `created_timestamp`, stats). Use that text as the original. Attribute RTs from `reposted_by`; keep the listed URL (the RT) as the post link even when the payload canonicalizes to the original.
5. Render a dark X-style snapshot PNG per post (avatar, name, handle, optional “repostou” banner, body, quote box, first photo, UTC time, stats). Save as `snapshots/{nn}_{handle}_{id}.png`. Embed with a relative markdown image `![](snapshots/...)`.
6. Translate, write the note, update the README index, leave `tweets_raw.json` next to the note.

## Pitfalls

- Decode the snowflake before including a post whose card says “today” or “Nov N” — X mixes pins and high-engagement old posts into the same latest-5 list, so a morning post on the cutoff date is often outside a mid-afternoon window.
- Do not use web search (`from:handle`, `site:x.com/...`) as the 24h source — results are not recency-ranked; always snowflake-decode any id you still keep.
- Filter on the listed status id (the URL you will cite). FxTwitter resolves a repost to the inner tweet’s id and URL; using only the inner timestamp/link drops RT attribution.
- Keep silent watchlist accounts in the note. Absence is a finding; dropping them looks like the fetch failed.
- Write snapshot PNGs into that day's `snapshots/` folder. Remote card/OG URLs rot and Obsidian needs files on disk.
