# Line-Preserving Localization

Translate a specified source-line range while preserving its layout and OCR artifacts. See [SKILL.md](SKILL.md) for the authoritative workflow and guardrails.

## How to Use

Use when a translation or locale edit is limited to an exact line range and the output must preserve line breaks, blank lines, and line-level alignment.

Quick start:

1. Provide the source file, inclusive first and last line numbers, target locale, and exact output path.
2. Example request: “Translate lines 25–48 of `<source-file>` into French (`fr-FR`), preserve every line and blank line, keep damaged OCR unchanged, and save to `<output-file>`.”
3. Follow [SKILL.md](SKILL.md): read only the requested range, translate intelligible text without reflow, write the complete result, then verify alignment against the same range.

## Technical Details

- **Inputs:** a readable source text file, an exact line range, a target locale, and an output path.
- **Tools:** the host must provide safe file-reading and file-writing operations. In Hermes, use `read_file` and `write_file`; another host can use equivalent local file tools. No companion scripts are included.
- Treat line-number prefixes returned by a file-reading tool as metadata, not source text. Verify the result line-by-line, including blank-line positions, and check that no prefixes remain. Report the output path and byte size.
- Preserve names, quotations, meaning, tone, foreign-language passages, and visibly corrupted OCR. Do not summarize, omit, or infer OCR repairs.
- Use only the translation provider selected by the user. Approval for one provider does not authorize sending source text to another.
- If the requested layout cannot be maintained, stop and explain the blocker instead of reflowing the text.
