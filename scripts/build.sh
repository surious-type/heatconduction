#!/usr/bin/env bash
set -euo pipefail

cxx="${CXX:-g++}"
read -r -a flags <<< "${OPT_FLAGS:--O3}"
"$cxx" -std=c++17 "${flags[@]}" sequence.cpp -o heat_original
"$cxx" -std=c++17 "${flags[@]}" loop/sequence.loop.cpp -o heat_loop
"$cxx" -std=c++17 "${flags[@]}" -fopenmp openmp/openmp.loop.cpp -o heat_omp
"$cxx" -std=c++17 "${flags[@]}" -pthread pthread/pthread.loop.cpp -o heat_pthread
