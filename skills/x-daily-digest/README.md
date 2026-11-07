# X Daily Digest

Compile recent posts from a configurable X-account watchlist into a Portuguese Obsidian digest with local snapshots. See [SKILL.md](SKILL.md) for the complete output contract and procedure; the default watchlist is in [references/watchlist.md](references/watchlist.md).

## How to Use

Use when the user requests a time-bounded digest of posts from named X accounts or the default watchlist, especially a daily diplomatic/geopolitical digest to save in Obsidian. It is not intended for a single-post lookup or an RSS/blog watch.

Quick start: configure `OBSIDIAN_VAULT_PATH`, then request: “Create the usual last-24-hours X digest, use the default watchlist, include accounts with no posts, translate repost copy into Brazilian Portuguese, and save it in my Obsidian vault.” Specify a different watchlist or time window when needed.

## Technical Details

### Prerequisites and outputs

- Requires network access to public `x.com` profile pages and `api.fxtwitter.com`, a configured `OBSIDIAN_VAULT_PATH`, and local write access to the vault. The host must be able to render and save PNG snapshots; no companion script is included.
- The default watchlist is `references/watchlist.md`; user-supplied handles override it when requested.
- Each run writes a date-stamped note, `tweets_raw.json`, and one local PNG snapshot per captured in-window post under `<vault>/Daily Digest/𝕏 Twitter/<YYYY-MM-DD>/`. It also adds a wikilink to the digest index README.
- Posts are filtered by the timestamp encoded in each status ID (snowflake), not by card labels. Reposts retain the listed status URL for attribution, even when the fetched payload resolves to the original post.

### Verification, safety, and limitations

- Confirm the UTC window, all captured in-window IDs, local snapshot links, note structure, and the index entry. Keep silent watchlist accounts and state the reason when no post was captured.
- The skill fetches public post content for summarization/translation and saves raw payloads and snapshots locally. Preserve URLs and handles; do not imply an inference about coordination is proven by timing or wording alone.
- Profile pages expose only about five posts; high-volume accounts may have additional posts in the window that are not captured. This is not a complete X archive or a guaranteed exhaustive search. Older pinned or popular posts must be excluded by status-ID timestamp.
- Another host must provide equivalent web extraction, image rendering, and vault file-writing tools. If an endpoint or post payload is unavailable, report the gap rather than claiming a complete digest.
