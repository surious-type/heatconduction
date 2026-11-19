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

  mkdir -p "$out/$profile/lib"
  cp heat_original heat_loop heat_omp heat_pthread "$out/$profile/"

  # Компилятор GCC 7.4 использует собственные библиотеки времени выполнения.
  # Копируем их рядом с бинарниками: на вычислительном узле системная libstdc++
  # может быть старее и не содержать нужных версий GLIBCXX и CXXABI.
  for library in libstdc++.so.6 libgcc_s.so.1 libgomp.so.1; do
    path=$("$cxx" -print-file-name="$library")
    if [[ "$path" != /* || ! -f "$path" ]]; then
      echo "Не удалось найти $library для $cxx: $path" >&2
      exit 1
    fi
    cp -L "$path" "$out/$profile/lib/$library"
  done
done

echo "Готовые программы сохранены в $out/"
