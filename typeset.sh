pandoc metadata.yaml combined.md \
  -o book.pdf \
  --pdf-engine=xelatex \
  --top-level-division=chapter \
  --toc --toc-depth=2 \
  --include-in-header=header.tex \
  --lua-filter=chapter-subtitles.lua
