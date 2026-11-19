#!/usr/bin/env bash
set -euo pipefail

# Запускать в каталоге репозитория на узле с компилятором и системными заголовками.
# Для каждого профиля программы собираются один раз до отправки заданий Slurm.
cxx="${CXX:-g++}"
if ! command -v "$cxx" >/dev/null 2>&1; then
  echo "Компилятор $cxx не найден. Загрузите GCC на узле входа." >&2
  exit 1
fi

arch="${ARCH:-skylake-avx512}"
out="${BUILD_DIR:-build_profiles}"

for profile in ${PROFILES:-O2 O3 native unroll novec}; do
  case "$profile" in
    O2) flags="-O2" ;;
    O3) flags="-O3" ;;
    native) flags="-O3 -march=$arch" ;;
    unroll) flags="-O3 -march=$arch -funroll-loops" ;;
    novec) flags="-O3 -march=$arch -fno-tree-vectorize" ;;
    *) echo "Неизвестный профиль: $profile" >&2; exit 1 ;;
  esac

  echo "Сборка $profile: $flags"
  OPT_FLAGS="$flags" bash scripts/build.sh

  mkdir -p "$out/$profile"
  cp heat_original heat_loop heat_omp heat_pthread "$out/$profile/"
done

echo "Готовые программы сохранены в $out/"
