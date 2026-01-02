rm -rf output/chapters
python3 build.py
pandoc -f markdown+smart data/metadata.yaml output/chapters/*.md \
  -o output/book.pdf \
  --pdf-engine=xelatex \
  --top-level-division=chapter \
  --include-in-header=header.tex \
  --lua-filter=links-to-footnotes.lua \
  --lua-filter=chapter-subtitles.lua
