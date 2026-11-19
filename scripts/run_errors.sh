#!/usr/bin/env bash
set -euo pipefail

program="${1:-./heat_loop}"
output="${2:-errors.csv}"
echo "nx,ny,steps,t1,a,error_c,error_l2" > "$output"

for config in "101 10" "201 40" "401 160" "801 640"; do
  read -r nx steps <<< "$config"
  result=$("$program" --Nx "$nx" --Ny "$nx" --N "$steps" \
    --t0 0 --t1 0.01 --a 0.1 --Lx 1 --Ly 1 --debug 1)
  error_c=$(awk '/^C-норма:/ {print $2}' <<< "$result")
  error_l2=$(awk '/^l2-норма:/ {print $2}' <<< "$result")
  [[ -n "$error_c" && -n "$error_l2" ]] || { echo "Не удалось извлечь ошибку: $nx" >&2; exit 1; }
  echo "$nx,$nx,$steps,0.01,0.1,$error_c,$error_l2" >> "$output"
done

echo "Результаты: $output"
