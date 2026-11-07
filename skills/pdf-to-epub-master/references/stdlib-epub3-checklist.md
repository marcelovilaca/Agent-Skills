# EPUB 3 package and content verification

Use this recipe only when a reflowable EPUB is required and no available EPUB generator is suitable. Prefer an installed Pandoc/EbookLib workflow; do not install packages or converters without approval.

## Package structure

Create a ZIP with `mimetype` as the first entry, stored without compression and containing exactly `application/epub+zip`. Include `META-INF/container.xml` pointing to the OPF package, plus an `OEBPS/` tree containing `content.opf`, an XHTML navigation document at a manifest-registered path (for example, `nav.xhtml`), the XHTML reading sections, and any stylesheet/assets.

In `content.opf`, explicitly set title, creator, `pt-BR` language, a stable unique identifier, and modified timestamp. Put the nav document and stylesheet in the manifest; mark the EPUB 3 nav item with `properties="nav"`, add every XHTML reading section to the manifest and spine in reading order, and make the nav TOC link to actual XHTML files and stable anchors. Leave `spine/@toc` unset unless a valid NCX resource is included; that legacy attribute references an NCX, not the XHTML nav item.

## Build from verified Markdown

1. Derive the EPUB section list from the verified Markdown headings, not from a separately typed, drifting list.
2. Map each expected section to one XHTML reading section and one TOC entry. Do not emit a wrapper heading and then retain the same Markdown heading inside the body; that creates duplicate chapter titles.
3. Preserve visible narrative text, paragraph boundaries, dialogue labels, and intentional line-break handling. Remove HTML exclusion comments from rendered prose while keeping their full excluded text in the JSON sidecar.
4. Keep figures unavailable in the text source out of the XHTML; retain their raw OCR and source line ranges in `metadata_and_exclusions.json` and disclose the omission.

## Required audit

Use Python's standard library (`zipfile`, `xml.etree.ElementTree`, and `posixpath`) to verify:

- `mimetype` is first, uncompressed, and exact; `ZipFile.testzip()` returns `None`.
- `container.xml`, OPF, nav XHTML, and every content XHTML parse as XML.
- The OPF declares the expected title, author, and `pt-BR`; every spine `idref` points to a manifest item and every manifest resource exists in the ZIP.
- Each TOC link resolves to an included XHTML file; if it has a fragment, that ID exists in the target document.
- The EPUB chapter/TOC titles match the Markdown section list exactly, with no missing or duplicated sections; each reading section contains non-empty visible text.
- Inspect extracted visible text from the first and last section and at least one middle section to catch empty pages, duplicate headings, or conversion that emitted structure but lost prose.
- Recheck the original source hash after building, and confirm Markdown, JSON, and EPUB paths and sizes.

Run `epubcheck` if already available, but do not install it without approval. If it is unavailable, report the checks actually performed; ZIP integrity and XML parsing alone do not establish full EPUB conformance. A structurally valid EPUB is not evidence that a MOBI exists; MOBI requires a genuine converter output and separate verification.