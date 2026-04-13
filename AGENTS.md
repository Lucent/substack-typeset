# AGENTS.md

## Overview

This is a book-building pipeline that typesets Substack blog posts into a print-quality PDF using Pandoc, XeLaTeX, and the `memoir` document class. It compiles a series of essays into a multi-part, two-sided print layout.

The final output is `output/book.pdf`.

## Build Pipeline

The build runs in two stages, orchestrated by `typeset.sh`:

1. **`python3 build.py`** — Preprocesses raw Substack HTML exports into clean Markdown chapters in `output/chapters/`.
2. **`pandoc`** — Typesets the Markdown into a PDF via XeLaTeX, applying metadata, LaTeX preamble, Lua filters, and front/back matter.

Run the full build with:
```sh
bash typeset.sh
```

## File Roles

| File | Role |
|---|---|
| `typeset.sh` | Build orchestrator: cleans output, runs build.py, invokes Pandoc |
| `build.py` | Python preprocessor: HTML to Markdown conversion and cleanup |
| `header.tex` | LaTeX preamble: page layout, fonts, chapter/part/TOC styling |
| `links-to-footnotes.lua` | Pandoc Lua filter: converts hyperlinks to print-friendly footnotes |
| `copyright.tex` | Front matter: copyright and edition info, inserted before body |
| `colophon.tex` | Back matter: typesetting credits, inserted after body |
| `data/metadata.yaml` | Pandoc metadata: title, author, document class, font config, TOC settings |
| `data/footnotes.tsv` | Tab-separated URL-to-title lookup table for footnote generation |
| `parts/*.tex` | Part divider pages with `\part{}` titles and `\epigraph{}` descriptions |
| `fonts/*.ttf` | Subsetted typeface files (regular, italic, bold) |

## build.py Features

- **Source reading**: Reads `posts.csv` and per-post HTML from a Substack export directory. Filters to published posts, sorted by date.
- **HTML-to-Markdown**: Converts each post via `pandoc -f html -t markdown`.
- **Substack cleanup**: Strips subscribe/footer boilerplate (content after last horizontal rule), removes stray `<div>` tags, converts Substack's custom LaTeX fence syntax to standard `$$...$$` math blocks.
- **Character substitution**: Replaces glyphs missing from the font subset with compatible alternatives.
- **URL title fetching**: Scans Markdown for external URLs, fetches page titles via `curl`, and caches them in `data/footnotes.tsv` for the Lua filter.
- **Drop cap injection**: Wraps the first letter of each chapter's opening paragraph with `\lettrine{}{}`, handling leading quotation marks via the `ante=` argument.
- **Part break injection**: If a `parts/N.tex` file exists for chapter N, its raw LaTeX is prepended to that chapter's Markdown.
- **Chapter assembly**: Each chapter gets a `# Title` heading, optional `\chapterprecishere{subtitle}`, and the processed body. All chapters are also concatenated into `output/combined.md`.
- **Timezone conversion**: Post dates are converted from UTC to Pacific Time for file naming.

## links-to-footnotes.lua Features

Operates on the Pandoc AST during rendering:

- **Internal Substack links**: Stripped entirely, replaced by plain text. Cross-references between essays are meaningless in print.
- **Wikipedia links** where the link text matches the article name: Text is kept with a superscript blackletter W (`𝔚`) attribution marker instead of a footnote.
- **All other external links**: Converted to footnotes using titles from `data/footnotes.tsv`, formatted as `\footnote{Title – URL}`.
- **Horizontal rules**: Replaced with `\pfbreak` (memoir's centered `* * *` ornamental scene break).

## header.tex Configuration

- **Page size**: Configurable stock and trimmed dimensions with bleed and binding offset.
- **Fonts**: Subsetted main font with a Unicode fallback font for glyphs outside the subset.
- **Chapter style**: `article` style (no "Chapter N" prefix). Subtitles via `\chapterprecishere`.
- **Part style**: Part number and "Part" label suppressed; only the part title is displayed.
- **TOC**: Custom title, chapter-only depth, dot leaders. Self-entry suppressed.
- **Half-title page**: Injected before the full title page via `\pretitle`.
- **Footnotes**: Counter resets per chapter. Ragged-right alignment for readability.
- **Drop caps**: Enabled via the `lettrine` package.
- **Line spacing**: 115% single spacing.

## Parts Structure

Parts are defined by `parts/N.tex` files, where N is the chapter number the part precedes. Each file contains a `\part{}` title, an `\epigraph{}{}` with a prose summary of the part's theme, and a `\clearpage`. Add or remove part files to change the book's structure.

## Design Decisions

- **build.py as glue**: Heavy preprocessing (HTML cleanup, character substitution, drop caps, part injection) is done in Python rather than Lua filters, keeping the Pandoc filter focused on link transformation.
- **Raw LaTeX in Markdown**: Part headers, chapter subtitles, and drop caps are raw LaTeX strings that Pandoc passes through to XeLaTeX verbatim.
- **Pre-fetched URL titles**: `footnotes.tsv` is populated once by build.py and read offline by the Lua filter, avoiding network calls at render time.
- **Font subsetting + fallbacks**: The main font is subsetted for size. Missing glyphs are handled across three layers: Python substitution, LaTeX math mode, and `newunicodechar` font fallback.
