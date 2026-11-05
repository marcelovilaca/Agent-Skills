---
name: "local-stack-testing"
description: "Test against a running local stack safely and repeatably."
license: "MIT"
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_related_skills: "react-vite-miniapp-setup"
  hermes_tags: "local-dev, testing, integration, ports, dev-auth, hygiene"
  version: "1.0.0"
---

# Local stack testing

Run a project's services locally, test against them for real, and leave the
user's environment exactly as you found it.

## When to Use

- Starting a service (API, bot, worker) locally and running integration
  tests against it.
- Writing or repairing a live test suite that talks to a running service.
- A setup where the client silently falls back to placeholder/offline data
  and you cannot tell config from broken code.

## Always-on rules

1. **Run the service on its documented default port.** A separate "dev" port
   means a second build variant and a second set of URL overrides, and when
   the fetch fails the client usually falls back to placeholder data — which
   reads as a broken feature rather than a config mismatch.
   *Why:* the API base is baked in at build time and the fallback is silent.

2. **A development auth bypass must be opt-in.** If a service accepts
   unauthenticated requests so a browser can poke at it, gate that behind an
   explicit env flag *and* a non-production environment check. Never make it
   the default.
   *Why:* a convenience that is on by default silently disables auth for
   anything that can reach the service.

3. **Assert the invariant that always holds, not the one that depends on
   your flags.** Test "a forged or expired credential is rejected" rather
   than "an anonymous request is rejected" — the latter stops being true the
   moment the dev bypass is enabled, and the usual "fix" is to weaken the
   assertion instead of the code.
   *Why:* the second test fails for a legitimate configuration.

4. **Make live tests repeatable: use a throwaway identity per run.** A test
   that reads a per-user counter must use a fresh id, and the *mutating*
   call must carry the same identity as the read.
   *Why:* state left by a previous run silently changes the expected value,
   so the second run of a passing suite fails.

5. **Give each content domain its own progress table.** A ratio that counts
   one collection against another's length measures nothing while looking
   entirely plausible. Per-domain tables (books, tapes, briefing items) are
   the only way the number means what its label says.
   *Why:* a shared table permits cross-domain joins, and a wrong join
   produces a confident wrong number rather than an error.

6. **Keep each command's side effects to its purpose.** Do not chain a
   state-changing operation into a read-only command — initialising a repo,
   deleting a directory, rewriting a config — just because it was
   convenient on the same shell line.
   *Why:* the side effect lands in the user's project unasked and has to be
   detected and undone later.

7. **Put tooling scratch state in the system temp directory, in one shared
   location.** Per-tool profiles and caches in the project root look like
   project files and get committed or wiped by mistake. One directory per
   project under the temp dir, plus a `.gitignore` entry for the pattern.
   *Why:* the project tree should contain only what the project is.

8. **Collapse one-off diagnostics into the permanent tools.** Several
   near-duplicate probe scripts rot into dead code; keep one general
   diagnostic plus the automated checks, and delete the rest once the
   question is answered.
   *Why:* every leftover script is a maintenance surface and a way to run
   stale code.

9. **Every user-visible state must come from the server.** A control that
   unlocks on a local timer and reveals nothing is a bug; a badge hardcoded
   to "LOCKED" beside an already-open element is a lie. Derive the label,
   the affordance and the animation from the same server answer.
   *Why:* the client can only guess, and a guess that looks successful is
   worse than an honest error.

10. **A browser client must be able to address a specific identity.** The
    dev bypass lets a browser call the service at all, which is useless if
    every request is then attributed to the same default viewer. Have the
    client read the identity from the page URL and pass it on every
    request — reads *and* mutations — so one session can exercise both
    sides of a conditional (entitled and not, owner and not).
    *Why:* a service that attributes every caller to one identity cannot be
    driven into the state you did not already ship, and the state you
    cannot reach is the one that ships broken. It is inert in production,
    where the identity comes from the signed credential instead.

11. **Demo seed data must yield to a real generator.** Seed rows for
    content something else produces (today's digest, a generated index)
    must insert without overwriting, and must be skipped entirely when the
    generator is configured.
    *Why:* a seeded row sharing the generator's key wins the race, the
    generator never runs, and the feature silently stays on demo copy
    forever — while still looking like it works.

## Procedure

1. Start the dependencies (database, queue), then apply migrations and
   seed. Seed idempotently, and delete rows that dropped out of the seed
   set so a placeholder never survives next to real content.
2. Start the service on its default port, with the dev bypass explicitly
   enabled if a browser needs it. Long-running services need a session that
   survives the command wrapper (a pty), and readiness must be confirmed by
   hitting a health endpoint — never by trusting a process exit code.
3. Run the live suite. Run it **twice in a row**: the second run is what
   exposes order-dependence and leftover state.
4. Check the working tree afterwards. Only the intended outputs should
   have changed.

## Pitfalls

- A service can print "listening" and still be unable to reach its
  database. The health endpoint must exercise the dependency, not just the
  socket.
- A dev-only build variant left in the output directory means the next
  session tests the wrong artifact. Rebuild before verifying.
- A static test suite and a live suite can disagree. When they do, the live
  one is right — the static one is asserting against the wrong model.
