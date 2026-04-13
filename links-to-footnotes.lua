-- OVERRIDE: Converts hyperlinks into footnotes for print output. Three behaviors:
--   1. Internal links (lucent.substack.com): strips the link, keeps plain text
--   2. Wikipedia links where link text matches the article name: appends a
--      superscript "W" (blackletter) instead of a footnote
--   3. All other links: converts to footnote with title + URL
-- Titles are looked up from data/footnotes.tsv (pre-fetched); falls back to
-- the link text if no TSV entry exists.

-- Load titles from TSV file
local titles = {}
local f = io.open("data/footnotes.tsv", "r")
if f then
  for line in f:lines() do
    local url, title = line:match("([^\t]+)\t(.+)")
    if url and title then
      titles[url] = title
    end
  end
  f:close()
end

function Link(el)
  -- Skip internal cross-references (lucent.substack.com links)
  if string.match(el.target, "lucent%.substack%.com") then
    return el.content
  end

  -- Wikipedia links: superscript W if text matches article, otherwise footnote
  if string.match(el.target, "wikipedia%.org") then
    local article = string.match(el.target, "/wiki/([^#?]+)")
    if article then
      -- Decode URL: underscores to spaces
      article = string.gsub(article, "_", " ")
      local linktext = string.lower(pandoc.utils.stringify(el.content))
      local article_lower = string.lower(article)
      if string.sub(linktext, -#article_lower) == article_lower then
        return el.content .. { pandoc.Superscript({pandoc.Str("𝔚")}) }
      end
    end
    -- Text doesn't match article name, fall through to footnote
  end

  -- Use title from TSV, or fall back to link text
  local t = titles[el.target] or pandoc.utils.stringify(el.content)

  local note = pandoc.Note(pandoc.Blocks{
    pandoc.Plain({
      pandoc.Str(t),
      pandoc.Str(" – "),
      pandoc.Str(el.target)
    })
  })

  return el.content .. { note }
end

-- Scene breaks: replace horizontal rules with memoir's \pfbreak (centered * * *)
function HorizontalRule()
  return pandoc.RawBlock("latex", "\\pfbreak")
end
