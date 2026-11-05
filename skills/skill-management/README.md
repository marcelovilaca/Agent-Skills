# Skill Management — How-to Guide

This guide explains how the `skill-management` skill helps install, update, inspect, and verify Hermes skills or plugins. For the complete source rules, see [SKILL.md](SKILL.md).

## How to Use

### Overview and triggers

Use this skill when a request is to install, update, inspect, or verify a Hermes skill. First establish the requested artifact and scope: a repository may contain a standalone skill, a plugin, or both. A companion MCP connection is a separate configuration task, not part of installing the skill itself.

### Inputs and prerequisites

Have the source and intended artifact identified before choosing an install route:

- For a hub skill, use its full hub path.
- For a standalone file, use the direct HTTPS URL to `SKILL.md`.
- For a skill inside a Git repository, identify the exact skill path and pin the repository commit before constructing the raw-file URL.
- For a Hermes plugin repository, use its repository identifier and review the installer's source/dependency prompts; choose enablement explicitly.

The commands below require the Hermes CLI in the terminal. Remote sources must be reachable for remote installs. Installs target the active Hermes profile.

### Quick start

For a hub skill, use the canonical form shown by the skill source, then verify the active profile:

```text
hermes skills install <source>/<path>
hermes skills list
```

For a standalone skill, the form is `hermes skills install https://.../SKILL.md`. For a skill bundled in a Git repository, first resolve its current commit and exact path, then use a pinned URL shaped like `https://raw.githubusercontent.com/<owner>/<repo>/<commit>/<path-to-SKILL.md>`.

For a plugin repository, use `hermes plugins install <owner>/<repo>` and verify with `hermes plugins list`. Replace angle-bracketed values with the real source identifiers; they are placeholders, not literal commands.

### Workflow and verification

1. Confirm whether the request is for a skill, plugin, or both. If the URL is a repository rather than a standalone `SKILL.md`, inspect its README and file tree to locate the actual artifact.
2. Choose the matching canonical install form; do not substitute a plugin install for a skill-only request.
3. Read the installer's scan result. A blocked or quarantined result is not a successful install. Retry with the documented `--force` override only when the user explicitly accepts the risk or requests an override.
4. Verify using the matching inventory: `hermes skills list` or `hermes plugins list`. If names collide, inspect the full identifier with `hermes skills inspect <full identifier>`. For URL installs, check that the installed name matches the intended skill.
5. Treat a successful listing in the active profile as the install check. Installed artifacts become available to new sessions in that profile.

The expected observable result is the relevant Hermes inventory showing the intended artifact. This skill does not prescribe a separate generated output file or a specific local installation path.

### Safety and limits

- Do not claim success based only on an install command or URL; verify the matching inventory.
- Do not treat a scan warning, quarantine, or block as a completed install. Use an override only with explicit user acceptance, then verify again.
- When the user asks for a bundled skill plus MCP, configure the MCP endpoint, transport, and documented headers separately. A saved MCP entry is not proof that the connection or tools have been tested; tool discovery occurs when Hermes starts.
- Avoid interactive MCP setup when no terminal input channel is available; use the documented noninteractive configuration and inspect the saved entry.
- The skill gives no automatic credential, endpoint, or source-discovery values. Use the source's documented information rather than guessing.

## Technical Details

### Source files and tools

The source procedure is [SKILL.md](SKILL.md). Its linked reference, [`references/install-sources-and-verification.md`](references/install-sources-and-verification.md), contains the source matrix, scan handling, verification checklist, name-collision guidance, and blocked-scan warning. No helper scripts are included in this skill directory.

The workflow uses the Hermes CLI through `terminal`. The inventory commands are `hermes skills list` and `hermes plugins list`; `hermes skills inspect <full identifier>` resolves ambiguous names. The procedure does not define a filesystem layout for installed skills, so this guide intentionally does not claim one.

### Artifact boundaries

- A skill install and a plugin install are distinct operations and have distinct inventory commands.
- A bundled skill URL should point to the actual `SKILL.md`, not just a repository landing page; pin the Git commit for a repository-contained skill.
- The active profile is the install target. A listing verifies that profile only.
- MCP configuration is separate from skill/plugin installation and should be verified as configuration separately from a tested connection.
