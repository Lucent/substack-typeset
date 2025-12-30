function Pandoc(doc)
  local out = pandoc.List:new()
  local blocks = doc.blocks
  local i = 1

  while i <= #blocks do
    local b = blocks[i]
    out:insert(b)

    if b.t == "Header" and b.level == 1 then
      local n = blocks[i + 1]
      if n and n.t == "Para"
         and #n.content == 1
         and n.content[1].t == "Emph" then
        local subtitle = pandoc.utils.stringify(n.content[1].content)
        out:insert(pandoc.RawBlock("latex", "\\chaptersubtitle{" .. subtitle .. "}"))
        i = i + 1 -- skip the subtitle paragraph
      end
    end

    i = i + 1
  end

  doc.blocks = out
  return doc
end
