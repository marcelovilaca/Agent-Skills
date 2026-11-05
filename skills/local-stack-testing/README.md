# Local stack testing

A safe, repeatable method for testing a project against its real locally running services while leaving the user's environment as found. See the companion [SKILL.md](SKILL.md) for the full invariants and pitfalls.

## Overview

Start required dependencies, migrate and seed, run the service on its documented default port, prove readiness through a health endpoint that exercises its dependencies, and run the live suite twice. A process saying “listening” is not proof that its database or other dependencies work. Finish by checking that only intended project outputs changed.

## Triggers and Inputs

Use when starting an API, bot, worker, or other service for integration tests; writing or repairing live tests; or diagnosing a client that may silently fall back to placeholder/offline data.

Inputs come from the actual project: dependency startup method, migrations, idempotent seed, service command and documented default port, health endpoint, test-suite command, environment/configuration, and any required identity or auth settings. This skill does not prescribe specific commands, ports, frameworks, test runners, endpoints, or environment variable names.

## Prerequisites

- The project's documented local setup and an identified default service port.
- Required dependencies (such as the database or queue), migrations, seeds, service, and live tests.
- A health endpoint that checks relevant dependencies, not just the listening socket.
- A development-auth bypass only if needed, gated by an explicit opt-in flag and a non-production environment check.
- A shared per-project scratch directory under the system temp directory for tooling state; keep scratch profiles/caches out of the project tree and add an appropriate `.gitignore` entry for any project-facing scratch pattern.

## How to Use

### Quick start

1. Read the project's setup instructions and identify the normal dependency, migration, seed, service, health-check, and test commands. Do not substitute a second “dev” port or a separate build variant.
2. Start only the required dependencies. Apply migrations and seed idempotently; delete rows that dropped out of the seed set so placeholders do not remain beside real content.
3. Start the service on its documented default port. Enable a development auth bypass only when needed, and only with both explicit opt-in and a non-production environment check. Use a persistent terminal session for a long-running process.
4. Request the project's health endpoint and confirm that it exercises its dependencies before running tests.
5. Run the live integration suite. Run it twice in a row; the second pass detects order-dependent assumptions and state left by the first.
6. Inspect the working tree and confirm that only intended outputs changed.

### Example: make a stateful live test repeatable

For a per-user counter, create a fresh throwaway identity for each test run. Read the counter for that identity, perform the mutating request with the same identity, and assert the expected invariant. Do not reuse a prior run's identity or use a different identity for the write; leftover state otherwise makes reruns unreliable. This is an example of test logic, not a project-specific endpoint or runnable test command.

For browser-driven checks, the client should be able to select an identity from the page URL and pass it on every read and mutation. This lets one session test both sides of an ownership/entitlement condition. In production, identity must come from the signed credential rather than the development bypass.

## Technical Details

### Project files, tools, and outputs

There is no bundled test runner, diagnostic script, stack configuration, or fixed set of project files in this skill. Use the project's existing dependency configuration, migration and seed code, service health endpoint, live tests, and development auth configuration. Keep one general diagnostic plus permanent automated checks rather than leaving several one-off probes behind.

Scratch profiles and caches belong under one shared project-specific directory in the system temp area, not in the repository. If any project-facing scratch pattern is needed, ignore it. Run commands with side effects only for their intended purpose; do not chain repository initialization, deletion, or config rewrites into a read-only diagnostic command.

Every user-visible state must be derived from the server response, including labels, affordances, and animations. Keep progress tables separated by content domain so ratios compare like collections. Seed data for generated content must not overwrite generated rows and should be skipped when a real generator is configured.

### Verification

- The service is responsive at the documented default port.
- The health check exercises the database/queue or other required dependency, rather than merely confirming that a port is open.
- The live test suite passes twice consecutively with fresh identities and consistent identity on reads and mutations.
- Authentication tests assert stable invariants, such as rejecting forged or expired credentials, rather than assuming anonymous requests are always rejected when an explicit development bypass may be enabled.
- The final working-tree review shows only intended outputs; no stale dev-only build variant or scratch cache remains in the project tree.

When a static test and the live suite disagree, investigate against the running service: a static test may be asserting the wrong configuration or model of runtime behavior.

### Safety and limitations

- Never make an unauthenticated development bypass the default. Require an explicit flag and a non-production check; keep production identity tied to signed credentials.
- Use the project's documented default port so the client exercises the intended build-time API base. A second port or dev-only build can cause silent placeholder fallback and test the wrong artifact.
- Keep live tests repeatable and state-isolated. Use a throwaway identity per run and the same identity for its reads and writes.
- Do not mutate or delete user data merely to simplify a diagnostic. Keep each command's side effects limited to its purpose and inspect changes afterward.
- A health response that checks only the socket can pass while a dependency is broken. The skill cannot supply project-specific commands or endpoint names; consult the project's docs rather than guessing them.