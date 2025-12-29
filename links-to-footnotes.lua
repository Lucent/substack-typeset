function Link(el)
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
