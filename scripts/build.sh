#!/usr/bin/env bash
set -euo pipefail

cxx="${CXX:-g++}"
"$cxx" -std=c++17 -O3 sequence.cpp -o heat_original
"$cxx" -std=c++17 -O3 loop/sequence.loop.cpp -o heat_loop
"$cxx" -std=c++17 -O3 -fopenmp openmp/openmp.loop.cpp -o heat_omp
"$cxx" -std=gnu++17 -O3 -pthread pthread/pthread.loop.cpp -o heat_pthread
