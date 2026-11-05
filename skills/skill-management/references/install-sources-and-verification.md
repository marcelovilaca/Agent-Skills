# Install sources and verification

## Source matrix

| Source | Recommended command | Notes |
|---|---|---|
| Hub skill | `hermes skills install <source>/<path>` | Use the full hub path, not a short display name. |
| Direct HTTPS URL | `hermes skills install https://.../SKILL.md` | Use when the repository exposes a standalone skill file. |
| Existing local install | `hermes skills list` | Confirms what is already available in the active profile. |

## Scan handling

1. Read the installer's verdict.
2. If it is blocked, stop and report the block.
3. If the user explicitly accepts the risk or wants to override a false positive, rerun with `--force`.
4. Verify the install after the override; do not rely on the retry output alone.

## Verification checklist

- `hermes skills list` shows the new skill.
- If there are duplicate names, use `hermes skills inspect <full identifier>`.
- If the skill came from a URL, confirm the installed name matches the intended skill.
- If the install target is a profile-specific skill tree, assume the active profile only.

## Name collisions

When multiple skills share the same short name:

1. Prefer the full identifier from the source.
2. Avoid bare-name inspection or installation.
3. Verify the source and trust level before using the skill in a workflow.

## Common failure mode to avoid

A warning, quarantine, or blocked-scan message is not the same thing as a successful install. Only the post-install listing verifies that the skill is usable.