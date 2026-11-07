---
name: "line-preserving-localization"
description: "Use to translate line-ranged text. Preserve layout and OCR."
license: "MIT"
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_tags: "translation, localization, OCR, text"
  version: "1.0.0"
---

# Line-preserving localization

Use for translating or localizing a specified range from a source text file when the output must retain the source layout.

## When to Use

Use when a user requests translation or locale editing for a fixed source-line range and requires the output to preserve line structure and OCR artifacts.

## Workflow

1. Read the exact requested source range with `read_file`; treat its line prefixes as metadata, not text. Confirm the first and last source lines and the requested line count.
2. Translate only intelligible text into the requested locale. Use the model/provider the user explicitly selects; do not switch to another provider without approval. Preserve meaning, tone, names, quotations, and foreign-language passages. Keep visibly corrupted or garbled OCR verbatim; never infer a repair from context.
3. Keep the source line structure fixed: preserve every line break and blank line, and avoid reflowing or merging text lines. Preserve meaningful line-end hyphenation while localizing spelling and grammar.
4. Write the complete result to the exact requested output path with `write_file`. If the target already exists, read it before overwriting.
5. Verify the artifact against the same source range: compare line count and blank-line positions index by index (matching blank-line counts alone is insufficient), confirm no source line-number prefixes remain, inspect the first and last lines, and correct any alignment drift before assembly. Report output path and byte size. Note conspicuous OCR-damaged source line ranges without altering them.

## Guardrails

- Do not summarize, omit, or repair OCR, even when the intended reading appears obvious.
- Treat approval to translate as scoped to the selected provider; it does not authorize sending source text to a different service.
- If exact layout cannot be maintained, stop and identify the concrete blocker rather than silently reflowing the text.
