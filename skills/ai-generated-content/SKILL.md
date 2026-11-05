---
name: "ai-generated-content"
description: "Features whose content a model writes from live sources."
license: "MIT"
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_related_skills: "grounded-citations, rss-feeds, local-stack-testing"
  hermes_tags: "ai, llm, content, digest, summary, generation, rss"
  version: "1.0.0"
---

# AI-generated content

Features that show content the user expects to be *current* — a daily
digest, a news summary, a generated index, a rewrite of a live feed — must
not be seeded copy. This is the recipe for one that is genuinely written,
and that degrades honestly when the machine that writes it is unavailable.

## When to Use

- A product feature that stores model-written text and serves it to users.
- A daily or on-demand digest, summary, briefing, or generated index.
- Any "AI writes it" surface where the user might reasonably assume the
  content is current and real.

Not for: one-off questions answered in chat (that is ordinary work), and
not for a deliverable you write once — for a written report with citations
use `grounded-citations` instead.

## The shape

```
sources (RSS / feeds)  →  reader  →  model  →  store  →  app
```

Four stages, each of which can fail. The **store** is the seam: the app only
ever reads what was stored, so every failure upstream is invisible to it.

## Always-on rules

1. **The model writes; it does not source.** Hand it the material and take
   the attribution from the retrieval, never from the model. A model that
   receives a list of source items must emit only what it was given — not a
   source name, a link, a number or a name it did not receive.
   *Why:* a model asked to cite will produce a plausible citation, and the
   plausible one is the hardest to notice.

2. **The app never calls the model.** Generate, then store; serve the
   stored row.
   *Why:* a client that calls the model on read makes every page view
   depend on a third party's latency and mood, and gives you no record of
   what the user was shown.

3. **Fail to the stored copy, never to an invention.** If the reader or the
   model fails, serve what was already stored and return a reason with it.
   *Why:* a missing digest is a disappointment; a fabricated one is a lie,
   and it is the kind the reader has no way to check.

4. **Switch the thinking off.** Reasoning models spend tens of thousands of
   tokens on `reasoning_content` for work that needs none. A ten-item
   digest from live headlines took 104 seconds with thinking on and 12
   seconds with it off. Send the provider's flag (`enable_thinking: false`
   for the Qwen3 family) and allow a 60-second client timeout.
   *Why:* the cost is invisible in the response — you see a timeout, not a
   cause.

5. **The prompt must demand specificity.** A model asked for "the day's
   headline" will answer "Daily Briefing" and consider it done. Ask for the
   *subject*, and give two worked examples of the shape you want.
   *Why:* a title for the publication is what a model produces when the
   instruction is about format rather than content.

6. **Constrain a closed vocabulary in code, not only in the prompt.** If
   items carry a topic, pass the exact allowed list and map anything else
   to a default.
   *Why:* a prompt that says "pick one of these" still produces a fifth
   option occasionally, and the schema then has nowhere to put it.

7. **Interleave the sources.** Round-robin the items across feeds before
   the model sees them.
   *Why:* one busy feed otherwise fills the whole window, and the other
   sources never appear — which reads as a broken second source rather than
   a sampling accident.

8. **The demo seed must yield to the generator.** Seed rows for generated
   content must insert without overwriting, and must be skipped entirely
   when a generator is configured.
   *Why:* a seeded row sharing the generator's key wins the race, the
   generator never runs, and the feature stays on demo copy forever while
   still looking like it works.

9. **One endpoint shape does not need an SDK.** A plain `fetch` keeps the
   dependency list honest, and the model must be asked for JSON and then
   parsed defensively — models wrap JSON in prose or fences even when told
   not to.
   *Why:* a dependency added for one call shape is a dependency to keep
   patched for the life of the project.

10. **Keep the key out of the repository.** The endpoint is three
    environment variables; the key belongs in the gitignored env file.
    *Why:* a key in a committed config is a key in every clone and every
    build log.

## Procedure

1. Fix the shape and the store's key (usually the date). Everything else
   follows from it.
2. Write the **reader** first and test it against a live feed *and* a feed
   that fails. A reader that is only ever tested against a working feed
   hides the failure path.
3. Write the prompt as a contract: what it may use, what it must not
   invent, the allowed vocabulary, the output shape, and the length limits.
4. Write the model client and **measure one call**. If it is slow, check
   whether the model is reasoning before you touch anything else.
5. Store the result under the day's key; make the write idempotent, and
   never let a seeded row occupy a generated key.
6. Serve the stored row. Generate on read only when the row is absent.
7. Test: the generated headline is specific; every item carries a value
   from the allowed list; the attribution came from the feed; and the
   fallback path serves the stored copy with a reason.

## Pitfalls

- **A headline that names the publication.** Assert the generated title is
  not the title of the publication, or the feature ships a placeholder
  that looks deliberate.
- **Attribution from the model.** Read the source name and link off the
  item you fed in, positionally. Never let the model choose.
- **A feed that silently returns nothing.** A 200 with zero items is a
  failure, not an empty day; treat it as one or the digest goes out blank.
- **Retrying a slow model by raising the timeout.** If the call takes
  100 seconds, the answer is usually thinking, not the timeout.
- **Testing the generator against a mock only.** A mock proves the JSON
  shape; only a live call proves the latency, the token usage and the
  prompt's actual behaviour.

## References

- `references/openai-compatible-endpoints.md` — the client shape, defensive
  JSON extraction, the provider flags, and pointing at a locally
  configured endpoint.
