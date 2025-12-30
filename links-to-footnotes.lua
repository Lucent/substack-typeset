function Link(el)
  -- Skip internal cross-references (lucent.substack.com links)
  if string.match(el.target, "lucent%.substack%.com") then
    return el.content
  end

  local t = el.title
  if t == "" then
    t = pandoc.utils.stringify(el.content)
  end

  local note = pandoc.Note(pandoc.Blocks{
    pandoc.Plain({
      pandoc.Str(t),
      pandoc.Str(" – "),
      pandoc.Str(el.target)
    })
  })

  return el.content .. { note }
end
