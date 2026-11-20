#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

for program in pandoc xelatex rsvg-convert; do
  if ! command -v "$program" >/dev/null 2>&1; then
    echo "Не найдена команда $program. Для Ubuntu установите: sudo apt install pandoc texlive-xetex texlive-lang-cyrillic texlive-fonts-recommended lmodern librsvg2-bin fonts-dejavu-core" >&2
    exit 1
  fi
done

pandoc report/report.md -o report/report.pdf \
  --from markdown+tex_math_dollars+tex_math_single_backslash \
  --pdf-engine=xelatex \
  --resource-path=report:. \
  -V mainfont="DejaVu Serif" \
  -V sansfont="DejaVu Sans" \
  -V monofont="DejaVu Sans Mono" \
  -V lang=ru-RU \
  -V geometry:margin=2cm

echo "PDF создан: $root/report/report.pdf"
