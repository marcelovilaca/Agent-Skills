---
name: "pdf-to-epub-master"
description: "Convert PDFs into clean, audiobook-aware Portuguese ebooks."
license: "MIT"
compatibility: "Requires Windows."
metadata:
  author: "marcelovilaca, Hermes Agent"
  hermes_tags: "pdf, OCR, EPUB, MOBI, translation, audiobook"
  version: "0.1.0"
---

# PDF to EPUB Master

Turn a user-provided PDF into clean Brazilian Portuguese Markdown, an EPUB, and a legacy MOBI when the available converter supports it. Keep front matter and other non-narrative material in a separate JSON file, and mark remaining exclusions so audiobook workflows can skip them. Prefer local processing; never upload a private PDF to an external OCR or translation service without the user's approval.

## When to Use

- The user wants a PDF cleaned, translated to Brazilian Portuguese, and exported as EPUB/MOBI.
- The user needs non-narrative material isolated for later audiobook generation.
- Don't use for editing an existing EPUB only, or for OCR/transcription of images unrelated to a book.

## Inputs and Defaults

- Required for the PDF route: `pdf_file_path`.
- **Existing-Markdown fast path:** If the user supplies an existing Markdown note and explicitly skips PDF-to-Markdown conversion, treat that note as the source. Resolve and verify its path, skip PDF inspection/extraction/OCR, and record that no PDF conversion occurred. Before in-place edits, preserve a backup; keep the original book's front/back matter in the edited note unless the user asks for a narration-only edition. Do not infer or fabricate missing text or bibliographic facts.
- `target_language`: Brazilian Portuguese (`pt-BR`); translate the complete narrative when the source is another language.
- Determine author/title from the PDF metadata or title page. If either remains uncertain, ask before creating the final directory. Do not invent bibliographic facts.
- Output root: `<AUDIOBOOKS_ROOT>\<Author Name>\<Book Title>\`. Make path components Windows-safe (replace invalid path characters) and report any substitutions.
- Preserve the source PDF unchanged. Keep intermediate extracts and conversion assets outside the final output folders.

## Prerequisites

Use `terminal` to inspect the source file and discover installed tools before processing: check for PyMuPDF (`fitz`), a layout-aware OCR option (Marker or Surya; for scanned PDFs, an available OCR pipeline such as OCRmyPDF/Tesseract), Pandoc or another EPUB writer, and Calibre's `ebook-convert` for MOBI. Do not assume a command or package is installed. Prefer local tools; request approval before installing software or sending the document to a cloud service. If no usable tool exists, stop at that stage and report the exact blocker rather than fabricating output.

## Procedure

1. **Inspect and extract.** Confirm the input exists and is a readable PDF. Use a layout-aware extractor and retain page number, block text, and bounding boxes in working data. With a usable text layer, PyMuPDF blocks are acceptable; for scanned/image-only pages, OCR with a layout-aware tool. Check representative early, middle, and late pages for missing text, reading-order errors, columns, tables, and OCR corruption. Re-run OCR or correct extraction when needed; do not silently drop unreadable pages.

2. **Remove recurring artifacts conservatively.** Normalize whitespace and digit runs when comparing candidate blocks. Treat a short block as a removable header/footer only when its top/bottom position and repeated wording strongly indicate a running artifact (for example, it appears on at least three pages and on at least 25% of pages). Detect page-number-varying watermarks similarly by position and normalized text. Do not remove a passage merely because it repeats; preserve uncertain material and log it for review. Record all removed recurring strings and affected page numbers in the JSON.

3. **Detect language and translate.** Detect the primary language from clean narrative text, not page furniture. If it is not Brazilian Portuguese, translate every narrative chunk into natural pt-BR, in paragraph/section order with enough surrounding context to preserve names, terminology, tone, and references. Do not translate isolated artifacts. Track chunk/page ranges and confirm that all narrative chunks were processed; never imply a full translation if only a sample or subset was translated. Preserve proper names and bibliographic facts. If the source is too large for the available translation method, continue in bounded chunks using working files; if no suitable translation method is available, stop and explain rather than outputting a partial book as complete.

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
   Add citation notes and footnotes that remain in the narrative to `inline_exclusions` and wrap their corresponding locations in Markdown using `<!-- EXCLUDE_FROM_AUDIO: ... -->`. Keep the marker concise and ensure the full excluded note is stored in JSON. Do not put ordinary narrative sentences inside exclusion markers.

5. **Format Markdown.** Write `Source\<Title>.md` as UTF-8. Use `# Chapter 1: Title` for chapters and `##` for subchapters; preserve source numbering and titles rather than inventing them. Merge OCR line wraps into continuous paragraphs, but retain paragraph boundaries, intentional verse, lists, and dialogue. Repair punctuation spacing and obvious OCR errors without changing meaning. Use emphasis/italics only where supported by the source, and blockquotes for letters or clearly distinct inserted voices. Put `---` between major narrative sections. Ensure no isolated page numbers, running headers, or excluded front/back matter remain in the narration. Preserve citations/footnote locations as audio-exclusion comments.

6. **Build the EPUB.** Create `Ebooks\<Title>.epub` from the finished Markdown using an available EPUB generator (prefer Pandoc/EPUB 3 if present). Set title, author, and language explicitly (`pt-BR`); include a navigable chapter TOC, sensible chapter breaks, and readable typography. Do not rely on converter defaults for metadata. If Pandoc/EbookLib is unavailable but a reflowable EPUB is still required, a small Python-stdlib EPUB 3 ZIP writer is acceptable only when the package, navigation, and XHTML parse successfully, the ZIP integrity test passes, metadata is verified, and every TOC target resolves. If metadata cannot be set or a chapter is missing, correct the build before proceeding.

7. **Build the MOBI.** Convert the verified EPUB to `Ebooks\<Title>.mobi` with the installed Calibre `ebook-convert` or another available EPUB-to-MOBI converter. MOBI is a legacy format and some current toolchains may no longer support it. Do not rename an EPUB or other file to `.mobi`; if conversion is unsupported, deliver the valid Markdown/JSON/EPUB and state clearly that MOBI was not created and why.

8. **Verify and report.** Check that Markdown and JSON are non-empty and valid, all expected sections/exclusions are accounted for, EPUB is a readable ZIP with required package/navigation files and correct metadata, and MOBI is a real MOBI output (not a renamed file). Verify every output path and nonzero file size. Report exact paths for all files created, explicitly highlighting `metadata_and_exclusions.json`; distinguish successfully verified files from any blocked output. Do not claim completion for outputs that were not produced.

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

- A PDF text layer can be present but scrambled; inspect reading order and representative pages before trusting it.
- Do not strip recurring text without layout-and-repeat evidence; record all removals for traceability.
- OCR quality and translation completeness are acceptance criteria, not assumptions. Preserve uncertain text and disclose unresolved pages.
- EPUB and MOBI are different formats. MOBI conversion may fail on modern toolchains; report that honestly.
- HTML comments are exclusion markers for downstream audiobook processing. Keep the full excluded text in JSON as well, so it is not lost if a converter strips comments.

## Verification Checklist

- [ ] Correct input PDF; source unchanged.
- [ ] Text extraction/OCR checked across the document; unreadable pages disclosed.
- [ ] Language detected; every narrative chunk translated to pt-BR when required.
- [ ] Repeating artifacts removed only with evidence and logged.
- [ ] Required non-narrative sections and inline notes isolated in JSON/comments.
- [ ] Markdown chapters, paragraphs, punctuation, and exclusions reviewed.
- [ ] EPUB opens and declares title, author, and `pt-BR`.
- [ ] MOBI verified as a real conversion, or its absence and reason reported.
- [ ] Exact paths and created-file checks included in the completion report.
