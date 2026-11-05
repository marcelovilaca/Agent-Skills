---
name: "skill-management"
description: "Use when installing or verifying Hermes skills. Confirm."
metadata:
  author: "marcelovilaca, Hermes Agent"
  version: "1.0.0"
---

# Skill management

Use this when the task is to install, update, inspect, or verify Hermes skills.

## Always-on workflow

1. Identify the artifact type and requested scope before choosing an installer. A repository may contain a skill, a plugin, or both; inspect its README and tree when the URL is not a standalone `SKILL.md` or the skill installer cannot fetch it. If the user asks for only the bundled skill and an MCP connection, do not install the companion plugin: install the repository's raw `SKILL.md` URL at a pinned commit, then configure the MCP server separately from its documented endpoint, transport, and required headers.
2. Use the source's canonical install form.
   - Hub skill: `hermes skills install <source>/<path>`
   - Direct URL skill: `hermes skills install https://.../SKILL.md`
   - Hermes plugin repository: `hermes plugins install <owner>/<repo>`; review the plugin installer’s source/dependency prompts and choose enablement explicitly.
   - For a skill bundled in a Git repository, inspect its README for the exact skill path, resolve and pin the repository's current commit, then install `https://raw.githubusercontent.com/<owner>/<repo>/<commit>/<path-to-SKILL.md>` so the direct-URL installer receives the actual Markdown file. Verify with `hermes skills list`.
3. Read the installer output before claiming success.
   - If the scan blocks the skill or plugin, do not report it as installed.
   - If the user explicitly wants to proceed anyway, retry with the documented override and verify afterward.
   - Distinguish a failed install from a setup/environment error; do not present an unsuccessful alternate path as a working installation.
4. Verify the result using the matching inventory (`hermes skills list` or `hermes plugins list`). If both artifacts were intended, verify both. If the name is ambiguous or duplicated, inspect the full identifier instead of the bare name.
5. Treat the active profile as the install target. Installed artifacts become available to new sessions in that profile.

## Pitfalls

- Use the full identifier when names collide; bare names can resolve to the wrong skill.
- A quarantined or blocked scan is not a successful install.
- Direct URL installs still need verification; the URL alone is not proof that the skill is usable.
- Configure a requested MCP endpoint as a separate artifact from a related plugin; use the documented MCP URL and headers, then verify the configured entry. MCP tool discovery occurs when Hermes starts, so distinguish saved configuration from a tested connection/tool list.
- Avoid interactive MCP setup commands when no terminal input channel is available; they may block at authentication/tool-selection prompts. Use noninteractive config commands for the endpoint and each documented header, then inspect the resulting MCP entry.

See `references/install-sources-and-verification.md` for the install-source matrix, scan-handling rules, and verification commands.
