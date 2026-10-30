-- Титульная страница по образцу отчёта филиала МГУ в Сарове.
-- В GitHub виден HTML-блок .report-cover из report.md; при
-- конвертации в XeLaTeX вместо него создаётся титульная страница.
-- Вставка через Meta('include-before') гарантирует, что титульник
-- окажется ПЕРЕД автоматически генерируемым оглавлением.
local cover = [=[
\begin{titlepage}
\thispagestyle{empty}
\begin{center}
{\normalsize МОСКОВСКИЙ ГОСУДАРСТВЕННЫЙ УНИВЕРСИТЕТ\par}
\vspace{0.1cm}
{\normalsize ИМЕНИ М. В. ЛОМОНОСОВА\par}
\vspace{0.35cm}
{\normalsize ФИЛИАЛ МОСКОВСКОГО ГОСУДАРСТВЕННОГО УНИВЕРСИТЕТА\par}
\vspace{0.1cm}
{\normalsize ИМЕНИ М. В. ЛОМОНОСОВА В ГОРОДЕ САРОВЕ\par}
\vspace{0.85cm}
\includegraphics[width=7.2cm]{assets/msu-building.png}\par
\end{center}
\vspace*{\fill}
\begin{center}
{\large Отчёт:\par}
\vspace{0.35cm}
{\large «Численное решение двумерного уравнения\par
теплопроводности: последовательная оптимизация,\par
OpenMP и Pthreads»\par}
\end{center}
\vspace*{\fill}
\begin{flushright}
Выполнил студент\\
2-го курса магистратуры\\
Василенко Д.О.\\
Группа: СКТ-225
\end{flushright}
\vspace*{\fill}
\begin{center}
Саров 2026
\end{center}
\end{titlepage}
\setcounter{page}{1}
]=]

function Meta(meta)
  meta['include-before'] = pandoc.MetaList({
    pandoc.MetaBlocks({pandoc.RawBlock('latex', cover)})
  })
  return meta
end

function Div(el)
  if el.classes:includes('report-cover') then
    return {}
  end
end


-- Печатная верстка: большие разделы начинаются с новой страницы,
-- а подразделы переносятся целиком с началом следующего абзаца.
-- На HTML-предпросмотр GitHub команды LaTeX не влияют.
local first_chapter_seen = false

function Header(el)
  if el.level == 1 then
    if not first_chapter_seen then
      first_chapter_seen = true
      return el
    end
    return { pandoc.RawBlock('latex', '\\clearpage'), el }
  elseif el.level == 2 then
    return { pandoc.RawBlock('latex', '\\Needspace{9\\baselineskip}'), el }
  end
end

-- Фиксированные относительные ширины колонок таблицы параметров.
-- Без этого Pandoc может выделить слишком мало места длинным заголовкам.
function Table(el)
  local rows = el.head.rows
  if #rows > 0 and #rows[1].cells > 0 then
    local first = pandoc.utils.stringify(rows[1].cells[1].contents)
    if first == 'Параметр' and #el.colspecs == 4 then
      el.colspecs = {
        {pandoc.AlignLeft, 0.17},
        {pandoc.AlignLeft, 0.15},
        {pandoc.AlignRight, 0.20},
        {pandoc.AlignLeft, 0.48},
      }
      return el
    end
  end
end
