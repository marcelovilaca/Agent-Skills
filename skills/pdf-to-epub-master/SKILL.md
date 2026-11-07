---
name: "pdf-to-epub-master"
description: "Convert PDFs into clean, audiobook-aware Portuguese ebooks."
license: "MIT"
compatibility: "Requires Windows."
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_tags: "pdf, OCR, EPUB, MOBI, translation, audiobook"
  version: "0.1.4"
---

# PDF to EPUB Master

Turn a user-provided PDF into clean Brazilian Portuguese Markdown, an EPUB, and a legacy MOBI when the available converter supports it. Keep front matter and other non-narrative material in a separate JSON file, and mark remaining exclusions so audiobook workflows can skip them. Prefer local processing; never upload a private PDF to an external OCR or translation service without the user's approval.

## When to Use

- The user wants a PDF cleaned, translated to Brazilian Portuguese, and exported as EPUB/MOBI.
- The user needs non-narrative material isolated for later audiobook generation.
- The user supplies an existing plain-text book and asks to format it for a later audiobook; use the text-source fast path without OCR.
- Don't use for editing an existing EPUB only, or for OCR/transcription of images unrelated to a book.

## Inputs and Defaults

- Required for the PDF route: `pdf_file_path`.
- **Existing-Markdown fast path:** If the user supplies an existing Markdown note and explicitly skips PDF-to-Markdown conversion, treat that note as the source. Resolve and verify its path, skip PDF inspection/extraction/OCR, and record that no PDF conversion occurred. Before in-place edits, preserve a backup; keep the original book's front/back matter in the edited note unless the user asks for a narration-only edition. Do not infer or fabricate missing text or bibliographic facts.
- **Plain-text fast path:** If the user supplies a `.txt` book and asks to format it or skip OCR, use that exact file as the source; do not search for or substitute a neighboring PDF/ZIP. Preserve the original file unchanged and create derived Markdown plus `metadata_and_exclusions.json`. Skip PDF inspection and new OCR; skip translation only when the text is already in the target language. A TXT (including DjVu output) may itself be OCR-derived, so inspect representative text and layout zones as described in Step 1, preserve ambiguous material in JSON, and record the source SHA-256. Use source line ranges, not invented page numbers. Resolve title/author from the supplied filename and text; ask only if they remain uncertain.
- `target_language`: Brazilian Portuguese (`pt-BR`); translate the complete narrative when the source is another language.
- Determine author/title from the PDF metadata or title page. If either remains uncertain, ask before creating the final directory. Do not invent bibliographic facts.
- Output root: `<AUDIOBOOKS_ROOT>\<Author Name>\<Book Title>\`. Make path components Windows-safe (replace invalid path characters) and report any substitutions.
- Preserve the source PDF unchanged. Keep intermediate extracts and conversion assets outside the final output folders.

## Prerequisites

Use `terminal` to inspect the source file and discover installed tools before processing. For PDFs, check PyMuPDF (`fitz`), layout-aware OCR (Marker/Surya or OCRmyPDF/Tesseract for scans), an EPUB writer, and Calibre `ebook-convert` for MOBI. For an explicitly selected `.txt` or `.md` fast path, skip OCR-tool requirements and check only the EPUB/MOBI tools needed for requested outputs. Do not assume a command or package is installed. Prefer local tools; request approval before installing software or sending the document to a cloud service. If no usable tool exists for a requested output, report the exact blocker rather than fabricating it.

## Procedure

1. **Route and inspect the source.** Confirm the supplied path exists and is readable. For PDF input, use a layout-aware extractor, retain page number/block text/bounding boxes, and inspect representative early, middle, and late pages; use layout-aware OCR for scans and do not silently drop unreadable pages. For the plain-text fast path, read the exact supplied `.txt`, preserve its encoding/content, record its hash, and skip PDF extraction and new OCR. Still inspect the opening, middle, ending, chapter boundaries, and figure/table zones: a supplied text dump can already contain OCR damage or garbled diagram text. Preserve uncertain or unreadable blocks verbatim in JSON with source line ranges, and disclose missing figures; do not silently repair or discard them. Do not pick a different source file merely because a similarly named archive or PDF is nearby.

2. **Remove recurring artifacts conservatively.** Normalize whitespace and digit runs when comparing candidate blocks. Treat a short block as a removable header/footer only when its top/bottom position and repeated wording strongly indicate a running artifact (for example, it appears on at least three pages and on at least 25% of pages). Detect page-number-varying watermarks similarly by position and normalized text. Do not remove a passage merely because it repeats; preserve uncertain material and log it for review. For a supplied OCR-derived TXT, also audit short isolated tokens at apparent page boundaries for nonnumeric page-number OCR variants. If a token cannot be confirmed, do not label it a proven recurring header/footer; exclude it from narration only when context strongly indicates page furniture, and preserve the exact token and source lines in JSON as uncertain. Record all removed recurring strings and affected page numbers in the JSON.

3. **Detect language and translate.** Detect the primary language from clean narrative text, not page furniture. If it is not Brazilian Portuguese, translate every narrative chunk into natural pt-BR, in paragraph/section order with enough surrounding context to preserve names, terminology, tone, and references. Do not translate isolated artifacts. Honor any model/provider the user explicitly selects; get approval before routing source text to another external service. Process large books in bounded chunks and record exact source line/page ranges. When assembly depends on source alignment, create a manifest covering each intended range exactly once, verify chunk coverage and line/blank positions before assembly, and recheck the source hash; do not impose line-preservation when the user requested normal paragraph reflow. Confirm every narrative chunk was processed; never imply a full translation if only a sample or subset was translated. Preserve proper names and bibliographic facts. If the source is too large for the available translation method, continue in bounded chunks using working files; if no suitable translation method is available, stop and explain rather than outputting a partial book as complete.

4. **Parse structure and isolate non-narrative text.** Identify and remove from the main narration: table of contents, preface, foreword, editor/translator/publisher details, bibliography or reference lists, index, and other clearly non-narrative front/back matter. Put each section in `Source\metadata_and_exclusions.json` with its type, source page range when known, and extracted text. Also record title/author/language, extraction notes, and removed headers/footers/watermarks. Use valid UTF-8 JSON with a stable structure, for example:
   ```json
   {
     "metadata": {"title": "...", "author": "...", "language": "pt-BR", "source_language": "..."},
     "excluded_sections": [{"type": "table_of_contents", "pages": [1, 3], "text": "..."}],
     "inline_exclusions": [{"type": "footnote", "page": 12, "text": "..."}],
     "removed_artifacts": [{"type": "header", "text": "...", "pages": [1, 2, 3]}],
     "notes": []
   }
   ```
   Add citation notes and footnotes that remain in the narrative to `inline_exclusions` and wrap their corresponding locations in Markdown using `<!-- EXCLUDE_FROM_AUDIO: ... -->`. Keep the marker concise and ensure the full excluded note is stored in JSON. Do not put ordinary narrative sentences inside exclusion markers. Before rendering, detect overlaps among footnote, page-artifact, and unreadable-block ranges. A broad OCR-block marker may cover a footnote only if the complete note remains in JSON; cross-check every sidecar exclusion against a Markdown marker at that range or an enclosing marker, and account for overlaps rather than reporting inconsistent counts.

5. **Format Markdown.** Write `Source\<Title>.md` as UTF-8. Use `# Chapter 1: Title` for chapters and `##` for subchapters; preserve source numbering and titles rather than inventing them. For wrapped TXT/PDF text, treat blank lines as candidate paragraph breaks, not automatic ones: defer the decision until the next narrative text is available, remove verified page furniture first, and assess both sides for a completed sentence, a continuing clause, a hyphenated word, a new list item, or a heading. Join hard wraps only when syntax supports continuation; preserve genuine paragraph breaks. If footnotes or page markers interrupt a sentence, keep their full text in JSON/comments and rejoin narrative pieces only when source syntax clearly shows continuation; log the source ranges. Exclusion comments must not influence this decision: strip comment markup before evaluating paragraph boundaries or comparing visible EPUB text. Preserve intentional verse, lists, dialogue, and real paragraph breaks. After EPUB generation, compare the visible paragraph sequence against Markdown exactly after removing audio-exclusion comments. Correct only unambiguous structural/OCR substitutions (for example, a damaged chapter numeral uniquely resolved by the complete chapter sequence), and log the original, replacement, and occurrence count in JSON; do not guess at prose corrections. After formatting, compare the expected source headings with Markdown, ensure template headings are not duplicated by retained source headings, and inspect the first/last paragraphs and section transitions. When this skill's verified Markdown/JSON is explicitly requested as audiobook input, hand its book directory to `ebook_to_audiobook_master`; do not start TTS until that skill's book-wide preflight passes. Use emphasis/italics only where supported by the source, and blockquotes for letters or clearly distinct inserted voices. Put `---` between major narrative sections. Ensure no isolated page numbers, running headers, or excluded front/back matter remain in the narration. Preserve citations/footnote locations as audio-exclusion comments.

6. **Build the EPUB.** Create `Ebooks\<Title>.epub` from the finished Markdown using an available EPUB generator (prefer Pandoc/EPUB 3 if present). Set title, author, and language explicitly (`pt-BR`); include a navigable chapter TOC, sensible chapter breaks, and readable typography. Do not rely on converter defaults for metadata. If Pandoc/EbookLib is unavailable but a reflowable EPUB is still required, a small Python-stdlib EPUB 3 ZIP writer is acceptable only when the package, navigation, and XHTML parse successfully, the ZIP integrity test passes, metadata is verified, and every TOC target resolves. Follow `references/stdlib-epub3-checklist.md` for package construction and content-level checks. If metadata cannot be set, a chapter is missing/duplicated, or the EPUB content diverges from the verified Markdown, correct the build before proceeding.

7. **Build the MOBI.** Convert the verified EPUB to `Ebooks\<Title>.mobi` with the installed Calibre `ebook-convert` or another available EPUB-to-MOBI converter. MOBI is a legacy format and some current toolchains may no longer support it. Do not rename an EPUB or other file to `.mobi`; if conversion is unsupported, deliver the valid Markdown/JSON/EPUB and state clearly that MOBI was not created and why.

8. **Verify and report.** Check that Markdown and JSON are non-empty and valid, all expected sections/exclusions are accounted for, and the source hash is unchanged. Compare the Markdown section list with EPUB chapters, ensuring each expected section appears once in the reading order and TOC; verify ZIP integrity, package/navigation/XML, metadata, and every TOC target. Check that footnote references remaining in visible narrative are intentionally mapped to exclusion comments (ignore reference numbers inside those comments); verify every footnote or other exclusion is covered either by its own comment or by an enclosing exclusion range whose full text is in JSON. Compare comment ranges against sidecar records and resolve overlaps before declaring counts complete. Verify every output path and nonzero file size, and that MOBI is a real conversion rather than a renamed file. If `epubcheck` is unavailable, describe ZIP/XML/TOC checks as internal structural validation, not as a full standards-conformance test. Report exact paths for all files created, explicitly highlighting `metadata_and_exclusions.json`; distinguish verified files from blocked outputs. Do not claim completion for outputs that were not produced.

## Output Layout

```text
<AUDIOBOOKS_ROOT>\<Author Name>\<Book Title>\
├── Source\
│   ├── <Title>.md
│   └── metadata_and_exclusions.json
└── Ebooks\
    ├── <Title>.epub
    └── <Title>.mobi
```

Use the actual resolved author and title in every path. Create `Source` and `Ebooks` as needed. Keep temporary OCR, translation, and build files outside this deliverable structure.

## Pitfalls

- A PDF text layer can be present but scrambled, and a supplied TXT can itself be OCR output; inspect reading order, representative passages, and diagram/table regions before trusting either.
- Do not strip recurring text without layout-and-repeat evidence; record all removals for traceability.
- OCR quality and translation completeness are acceptance criteria, not assumptions. Preserve uncertain text and disclose unresolved pages or unreadable figure blocks.
- A valid EPUB ZIP/XML package can still have missing or duplicate book content; compare its chapters and TOC against the verified Markdown.
- EPUB and MOBI are different formats. MOBI conversion may fail on modern toolchains; report that honestly.
- HTML comments are exclusion markers for downstream audiobook processing. Keep the full excluded text in JSON as well, so it is not lost if a converter strips comments.

## Verification Checklist

- [ ] Correct input PDF/TXT; source unchanged and hash recorded for the text-source fast path.
- [ ] Text extraction/OCR checked across the document; OCR-derived corruption and unreadable pages/figures disclosed.
- [ ] Language detected; every narrative chunk translated to pt-BR when required.
- [ ] Repeating artifacts removed only with evidence and logged.
- [ ] Required non-narrative sections and inline notes isolated in JSON/comments.
- [ ] Markdown chapters, paragraphs, punctuation, and exclusions reviewed.
- [ ] EPUB opens and declares title, author, and `pt-BR`.
- [ ] MOBI verified as a real conversion, or its absence and reason reported.
- [ ] Exact paths and created-file checks included in the completion report.
