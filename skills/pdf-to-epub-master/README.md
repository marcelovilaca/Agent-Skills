# PDF to EPUB Master

## Overview

PDF to EPUB Master turns a book PDF into cleaned UTF-8 Markdown, a metadata/exclusions JSON file, and a reflowable EPUB. It translates the full narrative into Brazilian Portuguese (`pt-BR`) when needed and creates a legacy MOBI only when an installed converter supports a genuine conversion. The authoritative procedure is in [SKILL.md](SKILL.md).

The workflow preserves the source PDF, keeps non-narrative material traceable for audiobook use, and prefers local processing. It does not fabricate unreadable text, bibliographic facts, or unsupported output formats.

## How to Use

### Inputs and defaults

- PDF route: provide `pdf_file_path` and confirm the author/title when metadata and title page do not settle them.
- Target language defaults to Brazilian Portuguese (`pt-BR`). If the source is another language, translate every narrative chunk, not just a sample.
- Existing-Markdown fast path: use a supplied Markdown note only when the user explicitly skips PDF-to-Markdown conversion. Verify the note's path; make a backup before in-place edits. Keep the original front/back matter unless a narration-only edition is requested.
- Output root is configured as `<AUDIOBOOKS_ROOT>/<Author Name>/<Book Title>/`. Use Windows-safe author/title path components and report substitutions.

### Practical example

For a supplied PDF, confirm its identity, inspect the title/author from metadata or the title page, and then follow this sequence:

1. Extract text with layout and page information; use OCR for scanned pages when necessary.
2. Review representative pages near the beginning, middle, and end for reading order, missing text, tables, columns, and OCR errors.
3. Translate all narrative chunks to `pt-BR` when required, and separate non-narrative sections and remaining footnotes/citations.
4. Write the Markdown and JSON, then build and inspect the EPUB. Attempt MOBI conversion only with an available converter.

There is no single bundled command or conversion script in this skill directory. Discover the installed tools first; do not assume a particular OCR or ebook converter is present.

## Prerequisites

Inspect the source and environment before processing. Candidate local tools named by the skill are:

- PyMuPDF (`fitz`) for PDFs with a usable text layer.
- A layout-aware OCR tool such as Marker or Surya; for scanned/image-only documents, an available OCR pipeline such as OCRmyPDF/Tesseract.
- Pandoc or another EPUB writer.
- Calibre's `ebook-convert` or another EPUB-to-MOBI converter for the optional MOBI output.
- A suitable translation method if the book is not already in `pt-BR`.

These are discovery candidates, not guaranteed installed dependencies. Prefer local processing. Ask before installing software or sending a private PDF to a cloud OCR or translation service. Stop at the blocked stage if no usable local tool or translation method is available.

## Technical Details

### Workflow and files

Deliverables use this layout, with actual author/title names substituted for placeholders:

```text
<AUDIOBOOKS_ROOT>/<Author Name>/<Book Title>/
├── Source/
│   ├── <Title>.md
│   └── metadata_and_exclusions.json
└── Ebooks/
    ├── <Title>.epub
    └── <Title>.mobi   (only when a real conversion succeeds)
```

- **`Source/<Title>.md`:** UTF-8 narrative, with chapter/subchapter headings, preserved numbering, paragraph boundaries, lists, verse, and dialogue. Citation/footnote locations that remain in the narration use concise `<!-- EXCLUDE_FROM_AUDIO: ... -->` comments.
- **`Source/metadata_and_exclusions.json`:** valid UTF-8 JSON containing bibliographic/language metadata, excluded front/back matter, inline exclusions, removed artifacts and affected pages, and processing notes. Store the full text of an excluded note here even when a Markdown comment marks its location.
- **`Ebooks/<Title>.epub`:** reflowable EPUB with explicit title, author, and `pt-BR` metadata, navigable chapter TOC, and resolvable TOC targets.
- **`Ebooks/<Title>.mobi`:** optional genuine conversion from the verified EPUB. Never rename an EPUB to `.mobi`.

Keep intermediate extraction, OCR, translation, and build files outside the final output folders. Preserve the input PDF unchanged.

### Extraction and editorial rules

- Retain page numbers, text blocks, and bounding boxes in working data. A text layer may still have scrambled reading order; inspect it before trusting it.
- Remove a repeating header/footer only with both positional and repetition evidence. The skill gives an example threshold of at least three pages and at least 25% of pages; preserve uncertain text and log removals.
- Detect language from narrative text, not page furniture. Track chunk/page ranges and confirm every narrative chunk was translated when required.
- Isolate a table of contents, preface, foreword, publication details, bibliography/references, index, and other clearly non-narrative matter in JSON instead of silently discarding it.
- Preserve the source's chapter titles and numbering. Repair only obvious OCR/punctuation issues without changing meaning.

### Verification

- Confirm the source PDF is readable and unchanged; disclose unresolved or unreadable pages.
- Check extraction/OCR quality across representative early, middle, and late pages. Confirm the reading order and every narrative translation chunk.
- Validate the Markdown and JSON as non-empty; parse the JSON and account for the exclusions and removed artifacts.
- Validate the EPUB as a readable ZIP/package with the required navigation/package files, correct metadata, valid XHTML, and resolving TOC targets.
- Verify every created output path and nonzero file size. For MOBI, verify that the file is a real conversion; otherwise report why it was unavailable.

### Safety and limitations

- Never upload a private PDF to external OCR or translation without the user's approval. Ask before installing software.
- Do not invent author, title, missing text, or source details. Ask if bibliographic identity remains uncertain before creating the final directory.
- Repeated passages are not automatically artifacts. Preserve uncertain material and log it for review.
- OCR quality and complete translation are acceptance criteria, not assumptions. Do not present a partial sample as a finished book.
- MOBI is a legacy format and may not be supported by current converter installations. A verified Markdown/JSON/EPUB set may be delivered without MOBI, with the reason stated.
- HTML comments may be stripped by ebook converters; the JSON remains the traceable source for excluded text.
