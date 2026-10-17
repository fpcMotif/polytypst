local function trim(s)
  return (s:gsub("^%s+", ""):gsub("%s+$", ""))
end

local function split_tag(text)
  return text:match("^(.-)%s*\\tag%s*{([^}]*)}%s*$")
end

local function normalize_typst_math(s)
  s = s:gsub("upright%(d%)", "dif")
  s = s:gsub('delim:%s*"||"', 'delim: "|"')
  s = s:gsub("planck%.reduce", "planck")
  s = s:gsub("angle%.l", "chevron.l")
  s = s:gsub("angle%.r", "chevron.r")
  s = s:gsub("([^a-zA-Z0-9_])sect([^a-zA-Z0-9_])", "%1section%2")
  s = s:gsub("^sect([^a-zA-Z0-9_])", "section%1")
  s = s:gsub("([^a-zA-Z0-9_])sect$", "%1section")
  s = s:gsub('cases%(delim:%s*"{",([^\n]+)%)', function(inner)
    local fixed = inner:gsub("([^\\]);", "%1\\;"):gsub("^;", "\\;")
    return 'cases(delim: "{",' .. fixed .. ")"
  end)
  return s
end

local function tex_to_typst_math_inner(tex)
  local trimmed = trim(tex)
  if trimmed == "" then
    return ""
  end
  local out = pandoc.write(pandoc.Pandoc({ pandoc.Plain({ pandoc.Math("DisplayMath", trimmed) }) }), "typst")
  out = trim(out)
  out = out:gsub("^%$%s*", ""):gsub("%s*%$$", "")
  out = out:gsub("([^\\]);", "%1\\;"):gsub("^;", "\\;")
  return normalize_typst_math(out)
end

local function split_align_rows(inner)
  local rows = {}
  local pos = 1
  while true do
    local s, e = inner:find("\\\\", pos, true)
    if not s then
      local tail = trim(inner:sub(pos))
      if tail ~= "" then
        table.insert(rows, tail)
      end
      break
    end
    table.insert(rows, trim(inner:sub(pos, s - 1)))
    pos = e + 1
  end
  return rows
end

local function split_cells(row)
  local cells = {}
  local pos = 1
  while true do
    local s, e = row:find("&", pos, true)
    if not s then
      table.insert(cells, row:sub(pos))
      break
    end
    table.insert(cells, row:sub(pos, s - 1))
    pos = e + 1
  end
  return cells
end

function Math(el)
  if el.mathtype ~= "DisplayMath" then
    if FORMAT:match("typst") then
      local inline_eq = pandoc.write(pandoc.Pandoc({ pandoc.Plain({ el }) }), "typst"):gsub("%s+$", "")
      local fixed_inline = normalize_typst_math(inline_eq)
      if fixed_inline ~= inline_eq then
        return pandoc.RawInline("typst", fixed_inline)
      end
    end
    return nil
  end

  local align_inner = el.text:match("^%s*\\begin{align%*}(.-)\\end{align%*}%s*$")
    or el.text:match("^%s*\\begin{aligned}(.-)\\end{aligned}%s*$")
  if align_inner and (el.text:find("\\tag%s*{") or el.text:find("&&", 1, true)) then
    if FORMAT:match("typst") then
      local raw_rows = split_align_rows(align_inner)
      local parsed_rows = {}
      local max_cols = 0
      for _, r in ipairs(raw_rows) do
        local body, tag = split_tag(r)
        if not tag then
          body = r
        end
        local cells = split_cells(body)
        if #cells > max_cols then
          max_cols = #cells
        end
        table.insert(parsed_rows, { cells = cells, tag = tag })
      end

      local col_specs = { "1fr" }
      local align_specs = { "right + horizon" }
      for c = 1, max_cols do
        table.insert(col_specs, "auto")
        if c % 2 == 1 then
          table.insert(align_specs, "right + horizon")
        else
          table.insert(align_specs, "left + horizon")
        end
      end
      table.insert(col_specs, "1fr")
      table.insert(align_specs, "right + horizon")

      local grid_items = {}
      for _, pr in ipairs(parsed_rows) do
        table.insert(grid_items, "[]")
        for c = 1, max_cols do
          local cell_tex = pr.cells[c] or ""
          local typ_inner = tex_to_typst_math_inner(cell_tex)
          if typ_inner == "" then
            table.insert(grid_items, "[]")
          elseif c % 2 == 0 then
            if c >= 4 then
              table.insert(grid_items, "$ quad " .. typ_inner .. " $")
            else
              table.insert(grid_items, "$ #h(0.25em) " .. typ_inner .. " $")
            end
          else
            table.insert(grid_items, "rmath[$ " .. typ_inner .. " $]")
          end
        end
        if pr.tag then
          table.insert(grid_items, "[(" .. pr.tag .. ")]")
        else
          table.insert(grid_items, "[]")
        end
      end

      local code = "#block(width: 100%, breakable: false, inset: (y: 0.3em), {\n"
        .. "  let rmath(body) = { show math.equation.where(block: true): set align(right); body }\n"
        .. "  show math.equation.where(block: true): set align(left)\n"
        .. "  grid(\n"
        .. "    columns: (" .. table.concat(col_specs, ", ") .. "),\n"
        .. "    row-gutter: 0.65em,\n"
        .. "    align: (" .. table.concat(align_specs, ", ") .. "),\n    "
        .. table.concat(grid_items, ", ")
        .. "\n  )\n})"
      return pandoc.RawInline("typst", code)
    end
    if el.text:find("\\tag%s*{") and (FORMAT:match("html") or FORMAT:match("epub")) then
      local raw_rows = split_align_rows(align_inner)
      local new_rows = {}
      for _, r in ipairs(raw_rows) do
        local body, tag = split_tag(r)
        if tag then
          table.insert(new_rows, body .. " && \\text{(" .. tag .. ")}")
        else
          table.insert(new_rows, r)
        end
      end
      return pandoc.Math(
        "DisplayMath",
        "\\begin{aligned}\n" .. table.concat(new_rows, " \\\\\n") .. "\n\\end{aligned}"
      )
    end
    return nil
  end

  local body, tag = split_tag(el.text)
  if not tag then
    if FORMAT:match("typst") then
      local eq = pandoc.write(pandoc.Pandoc({ pandoc.Plain({ el }) }), "typst"):gsub("%s+$", "")
      local fixed_eq = normalize_typst_math(eq)
      if fixed_eq ~= eq then
        return pandoc.RawInline("typst", fixed_eq)
      end
    end
    return nil
  end
  if FORMAT:match("typst") then
    local equation = pandoc.write(pandoc.Pandoc({ pandoc.Plain({ pandoc.Math("DisplayMath", body) }) }), "typst")
    equation = normalize_typst_math(equation:gsub("%s+$", ""))
    return pandoc.RawInline("typst", "#[#set math.equation(numbering: _ => [(" .. tag .. ")]); " .. equation .. "]")
  end
  if FORMAT:match("html") or FORMAT:match("epub") then
    return pandoc.Span({
      pandoc.Math("DisplayMath", body),
      pandoc.Span({ pandoc.Str("(" .. tag .. ")") }, { class = "eqno" }),
    }, { class = "numbered-equation" })
  end
  return nil
end
