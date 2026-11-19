#!/usr/bin/env bash
#SBATCH --job-name=heatcond
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=36
#SBATCH --array=1-5%1
#SBATCH --output=heatcond-%A_%a.log

set -euo pipefail

# Модуль компилятора согласно конфигурации кластера.
# В CI без реального Slurm проверяется логика скрипта на системном GCC.
if [[ -n "${SLURM_JOB_ID:-}" ]]; then
  module load gcc/gcc-7.4
fi

project="${SLURM_SUBMIT_DIR:?Нет SLURM_SUBMIT_DIR}"
repeat="${SLURM_ARRAY_TASK_ID:?Скрипт нужно запускать через sbatch --array=1-5}"
job_id="${SLURM_ARRAY_JOB_ID:?Нет SLURM_ARRAY_JOB_ID}"
result_dir="$project/bench_profiles/job_$job_id"

# Каждый элемент массива собирается в собственном временном каталоге:
# параллельные задания не перезаписывают исполняемые файлы и временные CSV.
workdir=$(mktemp -d "${SLURM_TMPDIR:-${TMPDIR:-/tmp}}/heatcond_XXXXXX")
trap 'rm -rf -- "$workdir"' EXIT
mkdir -p "$workdir"/{loop,openmp,pthread,scripts} "$result_dir"
cp "$project/sequence.cpp" "$workdir/"
cp "$project/loop/sequence.loop.cpp" "$workdir/loop/"
cp "$project/openmp/openmp.loop.cpp" "$workdir/openmp/"
cp "$project/pthread/pthread.loop.cpp" "$workdir/pthread/"
cp "$project/scripts/"{build.sh,run_bench.sh,run_profiles.sh} "$workdir/scripts/"
cd "$workdir"

# Один запуск каждой конфигурации в элементе массива; номер повтора
# переносится в колонку repeat выходного CSV.
RESULT_DIR="$result_dir" \
REPEAT_INDEX="$repeat" \
REPEATS=1 \
PROFILES="${PROFILES:-O3}" \
ARCH="${ARCH:-skylake-avx512}" \
THREADS="${THREADS:-1 2 4 8 16 18 36}" \
bash scripts/run_profiles.sh
