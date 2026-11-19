#!/usr/bin/env bash
set -euo pipefail

output="${1:-bench_$(date +%Y%m%d_%H%M%S).csv}"
repeats="${REPEATS:-5}"
threads="${THREADS:-1 2 4 8 16 18 36}"
profile="${PROFILE:-O3}"
echo "profile,method,nx,ny,steps,t1,a,threads,unroll,repeat,time_s,mlups,checksum" > "$output"

for config in "512 10000" "1024 2000" "2048 800" "4096 800"; do
  read -r nx steps <<< "$config"
  for method in loop openmp pthread; do
    for p in $threads; do
      [[ "$method" == "loop" && "$p" != 1 ]] && continue
      for q in 1 2 4 8; do
        for ((rep=1; rep<=repeats; ++rep)); do
          args=(--Nx "$nx" --Ny "$nx" --N "$steps" --t0 0 --t1 0.001 \
                --a 0.1 --Lx 1 --Ly 1 --loop "$q" --debug 0)
          case "$method" in
            loop) result=$(./heat_loop "${args[@]}") ;;
            openmp) result=$(OMP_NUM_THREADS="$p" OMP_PLACES=cores \
              OMP_PROC_BIND=close ./heat_omp "${args[@]}") ;;
            pthread) result=$(./heat_pthread --threads "$p" "${args[@]}") ;;
          esac
          time_s=$(awk '/^Time:/ {print $2}' <<< "$result")
          mlups=$(awk '/^MLUPS:/ {print $2}' <<< "$result")
          checksum=$(awk '/^Checksum:/ {print $2}' <<< "$result")
          [[ -n "$time_s" && -n "$mlups" && -n "$checksum" ]] || exit 1
          echo "$profile,$method,$nx,$nx,$steps,0.001,0.1,$p,$q,$rep,$time_s,$mlups,$checksum" >> "$output"
        done
      done
    done
  done
done

echo "Результаты: $output"
