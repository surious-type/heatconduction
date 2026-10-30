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
