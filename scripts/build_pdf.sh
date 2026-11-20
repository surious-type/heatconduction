#!/usr/bin/env bash
set -euo pipefail

# Запуск из любого каталога. Титульный лист и оглавление оформляются
# исходным Lua-фильтром report/titlepage.lua (из старой версии отчёта).
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

for program in pandoc xelatex rsvg-convert; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "Отсутствует $program. Установите: sudo apt install pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended lmodern librsvg2-bin fonts-dejavu-core" >&2
    exit 1
  fi
done

# Для Markdown/GitHub и PDF используются PNG, а не SVG.
# Источники SVG сохраняются в проекте как редактируемые графики.
for svg in "$root"/figures/2026/*.svg; do
  [[ -f "$svg" ]] || continue
  png="${svg%.svg}.png"
  if [[ ! -s "$png" || "$svg" -nt "$png" ]]; then
    rsvg-convert --format png --output "$png" "$svg"
  fi
done

# Здесь важен каталог report/: рисунок на титульном листе в Lua-фильтре
# использует относительный путь assets/msu-building.png.
cd "$root/report"
pandoc report.md -o report.pdf \
  --standalone --toc --toc-depth=2 \
  --lua-filter=titlepage.lua \
  --from markdown+tex_math_dollars+tex_math_single_backslash \
  --pdf-engine=xelatex \
  --resource-path=.:.. \
  -V mainfont="DejaVu Serif" \
  -V sansfont="DejaVu Sans" \
  -V monofont="DejaVu Sans Mono" \
  -V lang=ru-RU \
  -V papersize=a4 -V geometry:margin=2cm

echo "Готовый PDF: $root/report/report.pdf"
