#!/usr/bin/env bash
set -euo pipefail

dir="${RESULT_DIR:-bench_profiles}"
arch="${ARCH:-skylake-avx512}"
mkdir -p "$dir"

for profile in ${PROFILES:-O2 O3 native unroll novec}; do
  case "$profile" in
    O2) flags="-O2" ;;
    O3) flags="-O3" ;;
    native) flags="-O3 -march=$arch" ;;
    unroll) flags="-O3 -march=$arch -funroll-loops" ;;
    novec) flags="-O3 -march=$arch -fno-tree-vectorize" ;;
    *) echo "Неизвестный профиль: $profile" >&2; exit 1 ;;
  esac

  echo "Профиль $profile: $flags"
  OPT_FLAGS="$flags" bash scripts/build.sh
  PROFILE="$profile" bash scripts/run_bench.sh "$dir/${profile}${REPEAT_INDEX:+_rep${REPEAT_INDEX}}.csv"
done
