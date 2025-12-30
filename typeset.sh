pandoc metadata.yaml chapters/*.md \
  -o book.pdf \
  --pdf-engine=xelatex \
  --top-level-division=chapter \
  --include-in-header=header.tex \
  --lua-filter=links-to-footnotes.lua \
  --lua-filter=chapter-subtitles.lua
