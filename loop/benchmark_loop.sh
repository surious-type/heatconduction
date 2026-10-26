#!/usr/bin/env bash
# Benchmark for the 2D heat equation solver (sequential/OpenMP).
# Usage: ./benchmark_loop.sh --source ./sequence.loop.cpp --quick
set -Eeuo pipefail
export LC_ALL=C

usage() {
    cat <<'HELP'
benchmark_loop.sh — compile and benchmark heat equation C++ solver

Usage:
  ./benchmark_loop.sh [--smoke | --quick | --full] [options]

Modes:
  --smoke      Very small correctness/sanity run (not for performance).
  --quick      Default: two grids, 2 build profiles, 3 repetitions.
  --full       Four grids, 4 build profiles, 5 repetitions (many jobs!).

Options:
  --source FILE       C++ source (default: ./sequence.loop.cpp)
  --compiler CMD      Compiler command, e.g. g++ or clang++ (default: g++)
  --out DIR           Output directory (default: ./bench_results/TIMESTAMP-PID)
  --grid SPEC         Add a test grid; multiple allowed. SPEC: NxXNy:N:t1
                      e.g. --grid 1024x1024:2000:0.0001
                      First --grid replaces mode's default grid set.
  --loops LIST        Unroll factors, comma-separated (default: 1,2,4,8)
  --profiles LIST     Build profiles: O2,O3,native,unroll,novec
  --threads LIST      OpenMP thread counts (default: 1), e.g. 1,2,4,8
  --repeats N         Number of repetitions (default: depends on mode)
  --a NUM             Positive diffusion parameter a (default: 1)
  --lx NUM            Positive domain length Lx (default: 1)
  --ly NUM            Positive domain length Ly (default: 1)
  --t0 NUM            Initial time t0 (default: 0)
  --dry-run           Validate and show planned matrix without running
  -h, --help          Print this help

Build profiles:
  O2       -O2
  O3       -O3
  native   -O3 -march=native
  unroll   -O3 -march=native -funroll-loops
  novec    -O3 -march=native -fno-tree-vectorize
  Common flags: -std=c++17 -fopenmp

Results:
  results.csv      One record per successful run, with all parameters
  summary.csv      Median measured time and derived MLUPS per configuration
  logs/            Each run's captured stdout/stderr
  build/           Binaries and compilation logs
  system.txt       Compiler, source checksum, host details

IMPORTANT: compare versions only after validating their numerical outputs.
If your program prints `Checksum: NUMBER`, runs on the same grid will
be checked for checksum consistency (relative tolerance 1e-8).
The script refuses missing timing output and failed program invocations.
HELP
}

fail() {
    printf 'Ошибка: %s\n' "$*" >&2
    exit 1
}
info() { printf '%s\n' "$*" >&2; }
require_value() { (($# >= 2)) || fail "Нужно значение для $1"; }
number_is_positive() { awk -v n="$1" 'BEGIN{ exit !(n+0 > 0 && n ~ /^[+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/) }'; }
number_is_nonnegative() { awk -v n="$1" 'BEGIN{ exit !(n+0 >= 0 && n ~ /^[+]?([0-9]+\.?[0-9]*|\.[0-9]+)([eE][-+]?[0-9]+)?$/) }'; }

MODE=quick
SOURCE=./sequence.loop.cpp
CXX=g++
OUT=
LOOPS_INPUT=1,2,4,8
THREADS_INPUT=1
PROFILES_INPUT=
REPEATS=
A=1
LX=1
LY=1
T0=0
DRY_RUN=0
CUSTOM_GRIDS=0
GRIDS=()

while (($#)); do
    case "$1" in
    --smoke)
        MODE=smoke
        shift
        ;;
    --quick)
        MODE=quick
        shift
        ;;
    --full)
        MODE=full
        shift
        ;;
    --source)
        require_value "$@"
        SOURCE=$2
        shift 2
        ;;
    --compiler)
        require_value "$@"
        CXX=$2
        shift 2
        ;;
    --out)
        require_value "$@"
        OUT=$2
        shift 2
        ;;
    --grid)
        require_value "$@"
        if ((CUSTOM_GRIDS == 0)); then
            GRIDS=()
            CUSTOM_GRIDS=1
        fi
        GRIDS+=("$2")
        shift 2
        ;;
    --loops)
        require_value "$@"
        LOOPS_INPUT=$2
        shift 2
        ;;
    --profiles)
        require_value "$@"
        PROFILES_INPUT=$2
        shift 2
        ;;
    --threads)
        require_value "$@"
        THREADS_INPUT=$2
        shift 2
        ;;
    --repeats)
        require_value "$@"
        REPEATS=$2
        shift 2
        ;;
    --a)
        require_value "$@"
        A=$2
        shift 2
        ;;
    --lx)
        require_value "$@"
        LX=$2
        shift 2
        ;;
    --ly)
        require_value "$@"
        LY=$2
        shift 2
        ;;
    --t0)
        require_value "$@"
        T0=$2
        shift 2
        ;;
    --dry-run)
        DRY_RUN=1
        shift
        ;;
    -h | --help)
        usage
        exit 0
        ;;
    *) fail "Неизвестная опция: $1 (см. --help)" ;;
    esac
done

case "$MODE" in
smoke)
    if ((CUSTOM_GRIDS == 0)); then GRIDS=("64x64:20:0.00001"); fi
    [[ -n "$PROFILES_INPUT" ]] || PROFILES_INPUT=O2,O3
    [[ -n "$REPEATS" ]] || REPEATS=1
    ;;
quick)
    if ((CUSTOM_GRIDS == 0)); then GRIDS=("512x512:10000:0.001" "1024x1024:2000:0.0001"); fi
    [[ -n "$PROFILES_INPUT" ]] || PROFILES_INPUT=O3,native
    [[ -n "$REPEATS" ]] || REPEATS=3
    ;;
full)
    if ((CUSTOM_GRIDS == 0)); then
        GRIDS=("512x512:10000:0.001" "1024x1024:2000:0.0001" "2048x2048:800:0.00001" "4096x4096:250:0.000001")
    fi
    [[ -n "$PROFILES_INPUT" ]] || PROFILES_INPUT=O2,O3,native,unroll
    [[ -n "$REPEATS" ]] || REPEATS=5
    ;;
esac

[[ "$REPEATS" =~ ^[1-9][0-9]*$ ]] || fail "--repeats должно быть положительным целым"
number_is_positive "$A" || fail "--a должно быть положительным числом"
number_is_positive "$LX" || fail "--lx должно быть положительным числом"
number_is_positive "$LY" || fail "--ly должно быть положительным числом"
number_is_nonnegative "$T0" || fail "--t0 должно быть неотрицательным числом"

IFS=, read -r -a LOOPS <<<"$LOOPS_INPUT"
IFS=, read -r -a THREADS <<<"$THREADS_INPUT"
IFS=, read -r -a PROFILES <<<"$PROFILES_INPUT"
((${#LOOPS[@]} > 0 && ${#THREADS[@]} > 0 && ${#PROFILES[@]} > 0)) || fail 'Пустой список loops/threads/profiles'
for factor in "${LOOPS[@]}"; do
    case "$factor" in 1 | 2 | 4 | 8) ;; *) fail "Некорректная раскрутка: $factor" ;; esac
done
for threads in "${THREADS[@]}"; do
    [[ "$threads" =~ ^[1-9][0-9]*$ ]] || fail "Некорректное число потоков: $threads"
done
for profile in "${PROFILES[@]}"; do
    case "$profile" in O2 | O3 | native | unroll | novec) ;; *) fail "Неизвестный профиль: $profile" ;; esac
done

# Validate every grid and check explicit scheme stability *before* compilation.
for spec in "${GRIDS[@]}"; do
    [[ "$spec" =~ ^([0-9]+)x([0-9]+):([0-9]+):([+]?[0-9]+\.?[0-9]*|[+]?\.[0-9]+)([eE][-+]?[0-9]+)?$ ]] || fail "Неверный формат --grid '$spec'; ожидается NxXNy:N:t1"
    nx=${BASH_REMATCH[1]}
    ny=${BASH_REMATCH[2]}
    steps=${BASH_REMATCH[3]}
    t1=${spec##*:}
    ((10#$nx >= 4 && 10#$ny >= 3 && 10#$steps >= 2)) || fail "Сетка/шаги вне допустимых диапазонов: $spec"
    awk -v nx="$nx" -v ny="$ny" -v n="$steps" -v t0="$T0" -v t1="$t1" -v a="$A" -v lx="$LX" -v ly="$LY" 'BEGIN {
      dt=t1-t0;
      nmin=2*a*a*dt*((nx-1)*(nx-1)/(lx*lx)+(ny-1)*(ny-1)/(ly*ly));
      if (!(dt>0) || n<nmin) {
        printf "Ошибка: нарушена устойчивость для %dx%d, N=%d, t1=%.9g; требуется N>=%.0f\n", nx,ny,n,t1,nmin > "/dev/stderr";
        exit 1;
      }
    }' || exit 1
done

jobs=$((${#GRIDS[@]} * ${#LOOPS[@]} * ${#THREADS[@]} * ${#PROFILES[@]} * REPEATS))
info "Режим: $MODE | компилятор: $CXX | источник: $SOURCE"
info "Сетки: ${GRIDS[*]}"
info "Раскрутка: ${LOOPS[*]} | Профили: ${PROFILES[*]} | Потоки: ${THREADS[*]}"
info "Повторений: $REPEATS | Всего запусков: $jobs"

if ((DRY_RUN)); then
    info 'Проверка параметров завершена. Компиляция и запуски не выполнялись.'
    exit 0
fi
[[ -f "$SOURCE" ]] || fail "Файл исходника не найден: $SOURCE"
command -v "$CXX" >/dev/null 2>&1 || fail "Компилятор не найден: $CXX"
SOURCE="$(realpath "$SOURCE")"
# Guard against two actual bugs in the previously shared source code.
if grep -Eq 'value[[:space:]]*!=[[:space:]]*"1"[[:space:]]*\|\|' "$SOURCE"; then
    fail "В исходнике обнаружена ошибка проверки --loop: использовано || вместо &&. Исправь программу или используй sequence.loop.bench.cpp."
fi
if grep -q 'switch (loop)' "$SOURCE" && ! grep -q 'break;' "$SOURCE"; then
    fail "В исходнике обнаружен switch(loop) без break. Это приводит к ошибочным обновлениям; исправь файл перед измерениями."
fi

[[ -n "$OUT" ]] || OUT="./bench_results/$(date +%Y%m%d_%H%M%S)-$$"
mkdir -p "$OUT/build" "$OUT/logs"
OUT="$(realpath "$OUT")"
CSV="$OUT/results.csv"
SUMMARY="$OUT/summary.csv"
SYSTEM="$OUT/system.txt"
printf 'timestamp_utc,host,compiler,profile,cflags,source,nx,ny,steps,t0,t1,a,lx,ly,loop,threads,repeat,time_s,mlups,checksum\n' >"$CSV"
{
    printf 'date_utc=%s\nhost=%s\ncompiler=%s\ncompiler_version=%s\nsource=%s\n' "$(date -u +%FT%TZ)" "$(hostname)" "$CXX" "$("$CXX" --version | head -1)" "$SOURCE"
    printf 'source_sha256=%s\n' "$(sha256sum "$SOURCE" | awk '{print $1}')"
    printf 'kernel=%s\n' "$(uname -srmo)"
    if command -v lscpu >/dev/null 2>&1; then lscpu | grep -E 'Model name:|Architecture:|CPU\(s\):|Socket\(s\):|Core\(s\) per socket:' || true; fi
    printf 'mode=%s\ngrids=%s\nloops=%s\nprofiles=%s\nthreads=%s\nrepeats=%s\n' "$MODE" "${GRIDS[*]}" "$LOOPS_INPUT" "$PROFILES_INPUT" "$THREADS_INPUT" "$REPEATS"
} >"$SYSTEM"

info "Результаты: $OUT"

# Build each profile once and retain its compilation log.
declare -A EXES FLAGS
for profile in "${PROFILES[@]}"; do
    case "$profile" in
    O2) flagtext='-O2' ;;
    O3) flagtext='-O3' ;;
    native) flagtext='-O3 -march=native' ;;
    unroll) flagtext='-O3 -march=native -funroll-loops' ;;
    novec) flagtext='-O3 -march=native -fno-tree-vectorize' ;;
    esac
    FLAGS["$profile"]="$flagtext"
    read -r -a build_flags <<<"$flagtext"
    exe="$OUT/build/heat_$profile"
    info "Компиляция [$profile]: $CXX -std=c++17 -fopenmp $flagtext"
    if ! "$CXX" -std=c++17 -fopenmp "${build_flags[@]}" "$SOURCE" -o "$exe" >"$OUT/build/$profile.log" 2>&1; then
        cat "$OUT/build/$profile.log" >&2
        fail "Компиляция профиля $profile не удалась"
    fi
    EXES["$profile"]="$exe"
done

declare -A CHECKSUM_REF
warned_missing_checksum=0
counter=0
for spec in "${GRIDS[@]}"; do
    dims=${spec%%:*}
    tail=${spec#*:}
    steps=${tail%%:*}
    t1=${spec##*:}
    nx=${dims%x*}
    ny=${dims#*x}
    for rep in $(seq 1 "$REPEATS"); do
        for profile in "${PROFILES[@]}"; do
            for threads in "${THREADS[@]}"; do
                for factor in "${LOOPS[@]}"; do
                    ((counter += 1))
                    log="$OUT/logs/${nx}x${ny}_N${steps}_${profile}_T${threads}_U${factor}_R${rep}.log"
                    info "[$counter/$jobs] ${nx}x${ny} N=$steps t1=$t1 $profile threads=$threads loop=$factor repeat=$rep"
                    if ! (cd "$OUT" && OMP_NUM_THREADS="$threads" OMP_PLACES="${OMP_PLACES:-cores}" OMP_PROC_BIND="${OMP_PROC_BIND:-close}" "${EXES[$profile]}" \
                        --debug 0 --loop "$factor" --Nx "$nx" --Ny "$ny" --N "$steps" \
                        --t0 "$T0" --t1 "$t1" --a "$A" --Lx "$LX" --Ly "$LY") >"$log" 2>&1; then
                        tail -n 40 "$log" >&2
                        fail "Запуск завершился ошибкой; лог: $log"
                    fi
                    time_s=$(awk '/^Time:[[:space:]]/ {print $2; exit}' "$log")
                    mlups=$(awk '/^MLUPS:[[:space:]]/ {print $2; exit}' "$log")
                    checksum=$(awk '/^Checksum:[[:space:]]/ {print $2; exit}' "$log")
                    [[ -n "$time_s" && -n "$mlups" ]] || fail "Нет Time/MLUPS в $log"
                    number_is_positive "$time_s" || fail "Некорректное Time: '$time_s' в $log"
                    number_is_positive "$mlups" || fail "Некорректное MLUPS: '$mlups' в $log"
                    if [[ -n "$checksum" ]]; then
                        number_is_nonnegative "$checksum" || fail "Некорректное Checksum в $log"
                        key="${spec}|${threads}"
                        if [[ -z "${CHECKSUM_REF[$key]+x}" ]]; then
                            CHECKSUM_REF["$key"]="$checksum"
                        else
                            ref=${CHECKSUM_REF[$key]}
                            awk -v a="$ref" -v b="$checksum" 'BEGIN {
                d=a-b; if(d<0)d=-d; aa=a; if(aa<0)aa=-aa;
                exit !(d <= 1e-8*(1+aa));
              }' || fail "Разные контрольные суммы на сетке $dims: $ref против $checksum. Лог: $log"
                        fi
                    elif ((warned_missing_checksum == 0)); then
                        info 'ПРЕДУПРЕЖДЕНИЕ: программа не печатает Checksum:, сравнение численных результатов НЕ выполняется.'
                        warned_missing_checksum=1
                    fi
                    printf '%s,%s,%s,%s,"%s",%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s\n' \
                        "$(date -u +%FT%TZ)" "$(hostname)" "$CXX" "$profile" "${FLAGS[$profile]}" "$(basename "$SOURCE")" \
                        "$nx" "$ny" "$steps" "$T0" "$t1" "$A" "$LX" "$LY" "$factor" "$threads" "$rep" "$time_s" "$mlups" "$checksum" >>"$CSV"
                done
            done
        done
    done
done

# Calculate grouped medians using a lightweight Python standard-library helper.
if command -v python3 >/dev/null 2>&1; then
    python3 - "$CSV" "$SUMMARY" <<'PY'
import csv
import statistics
import sys
from collections import defaultdict

raw_file, summary_file = sys.argv[1:]
groups = defaultdict(list)
with open(raw_file, newline="") as f:
    for row in csv.DictReader(f):
        key = (row["host"], row["compiler"], row["profile"], row["nx"], row["ny"],
               row["steps"], row["t1"], row["loop"], row["threads"])
        groups[key].append(row)
with open(summary_file, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["host", "compiler", "profile", "nx", "ny", "steps", "t1", "loop", "threads", "runs", "median_time_s", "median_mlups", "min_time_s", "max_time_s"])
    for key, rows in sorted(groups.items()):
        times = [float(r["time_s"]) for r in rows]
        speeds = [float(r["mlups"]) for r in rows]
        w.writerow([*key, len(rows), f"{statistics.median(times):.10g}",
                    f"{statistics.median(speeds):.10g}", f"{min(times):.10g}", f"{max(times):.10g}"])
PY
    info "Готово: $CSV и $SUMMARY"
else
    info "Готово: $CSV (нет python3, summary.csv не сформирован)"
fi
