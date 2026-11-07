# Source filtering and chunking

Use this reference when turning a prepared Markdown source and its exclusion sidecar into TTS track text. The audiobook skill's always-on limits and delivery gate remain authoritative.

## Validate and map the source

1. Require exactly one `.md` file in `Source/` and its matching, valid UTF-8 `metadata_and_exclusions.json`. This skill supports pt-BR only; require the prepared source language to be `pt-BR` and stop otherwise. Read only that prepared Markdown; never switch to the raw PDF/TXT.
2. Inspect the actual heading hierarchy and exact titles. Recognize numbered `# Chapter N: ...` headings, authored `## Proémio`/`## Livro ...` structures, and a consistent repeated top-level heading sequence when no chapter scheme exists. Preserve source titles and order. Do not invent source chapter numbers from playback sequence.
3. Inspect the text before the first track and after the last one, plus `excluded_sections` metadata. Exclude title/publisher matter, TOC, preface, references, index, and other sections identified as non-narrative. Keep an included authored proemio/prologue/introduction or coda as its own track. A pre-chapter position alone does not prove a prologue is excluded.
4. Build ordered track boundaries first. For each track, map its stable track ID to the exact label used by JSON records (such as `1` to `Chapter 1`). Attribute an exclusion to a track only from its exact source line range within validated boundaries, never from record order or ID.
5. Validate every complete, including multiline, `EXCLUDE_FROM_AUDIO` marker. Match each marker range to its `inline_exclusions` or `unreadable_or_non_narrative_blocks` record and compare counts per track. Add a missing JSON record only if its exact source range and excluded text can be recovered; otherwise stop before TTS. When a footnote is covered by a larger exclusion, record the overlap rather than requiring a duplicate marker.

## Filter without rewriting the prepared book

- Remove the complete HTML exclusion comment before Markdown cleanup, but use its range and metadata during the audit.
- Audit for non-narrative translator/editor glosses, editorial notes, page furniture, and OCR debris that were not marked inline. For each confidently identified span, record exact source lines, section, target text, and reason in an audio-only sidecar field; filter it only from the TTS payload and leave the prepared Markdown unchanged. Verify that each target occurs once in ordered source context and is absent from the final payload.
- Preserve uncertain text verbatim in metadata. Do not silently narrate an unclear exclusion or delete ambiguous prose; pause the affected track for resolution. Do not complete a truncated OCR word by joining across footnotes or page furniture. Omit a fragment only when its boundaries are clear and the exact omission is recorded; otherwise stop.
- Strip Markdown formatting, raw HTML, decorative image markup, URLs, footnote call markers, and isolated printed page numbers without dropping narrative words. Remove obvious printed-page citations such as `(p. 89)` or `(pág. 89 «source»)` while preserving adjacent sentence punctuation; retain meaningful narrative numbers and list numbering. Track how many page citations were removed.
- If a normalized spoken-title prefix is added, remove the matching source H1 from the body so the title is spoken only once. Keep meaningful subheadings and readable list text.

## Book-wide preflight and chunking

Before sending any book text, preflight every included track: unique ordered boundaries; no unassigned preface/epilogue; no malformed comments; exact marker-to-metadata counts; every audio-only exclusion mapped; no residual excluded text; and all chunks under the configured/provider limit. Store source and filtered-text hashes, track sequence, source chapter number (if present), title, filtered character/UTF-8 counts, exclusion counts, and estimated chunk count in the progress catalog.

Chunk at sentence boundaries (`.`, `!`, `?`, `…`), keeping closing quotes/brackets with the sentence. Avoid decimal and common-abbreviation splits; treat initials case-sensitively and distinguish uppercase Roman numerals from lowercase unit abbreviations such as `m.`. Before applying the splitter to a whole book, test multi-initial names (`J. C. Name`), honorifics (`Sr.`, `Dr.`), decimals, lowercase `m.`, uppercase Roman headings (`I.`, `II.`, `XVIII.`), ellipses, and quoted sentence endings; inspect the resulting sentence arrays.

Enforce both Unicode code-point and UTF-8-byte counts against the 5,000 ceiling on every payload, or obey a lower provider limit. If one sentence is too long, split first at the nearest comma/semicolon under the ceiling, then at a safe word boundary. Record every exceptional split and recount the final payload immediately before each API request.
