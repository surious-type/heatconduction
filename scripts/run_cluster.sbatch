#!/usr/bin/env bash
#SBATCH --job-name=heatcond
#SBATCH --time=1:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=36
#SBATCH --array=1-5%1
#SBATCH --output=heatcond-%A_%a.log

set -euo pipefail

# На вычислительных узлах только запуск: GCC и modulecmd не требуются.
project="${SLURM_SUBMIT_DIR:?Нет SLURM_SUBMIT_DIR}"
repeat="${SLURM_ARRAY_TASK_ID:?Нет SLURM_ARRAY_TASK_ID}"
job_id="${SLURM_ARRAY_JOB_ID:?Нет SLURM_ARRAY_JOB_ID}"
profile="${PROFILES:-O3}"

case "$profile" in
  O2|O3|native|unroll|novec) ;;
  *) echo "Нужно выбрать один профиль: O2, O3, native, unroll или novec" >&2; exit 1 ;;
esac

build_dir="$project/${BUILD_DIR:-build_profiles}/$profile"
for exe in heat_loop heat_omp heat_pthread; do
  if [[ ! -x "$build_dir/$exe" ]]; then
    echo "Нет готовой программы: $build_dir/$exe" >&2
    echo "Сначала выполните PROFILES=$profile bash scripts/prepare_binaries.sh на узле входа." >&2
    exit 1
  fi
done

result_dir="$project/bench_profiles/job_$job_id"
mkdir -p "$result_dir"

# Каждый элемент массива получает собственный каталог, но не компилирует код.
workdir=$(mktemp -d "${SLURM_TMPDIR:-${TMPDIR:-/tmp}}/heatcond_XXXXXX")
trap 'rm -rf -- "$workdir"' EXIT
cp "$build_dir"/{heat_loop,heat_omp,heat_pthread} "$workdir/"
cp "$project/scripts/run_bench.sh" "$workdir/"
cd "$workdir"

echo "Профиль: $profile; повторение: $repeat"
echo "Запуск предварительно собранных программ из $build_dir"

# Номер Slurm-элемента становится номером повторения в CSV.
PROFILE="$profile" REPEAT_INDEX="$repeat" REPEATS=1 \
THREADS="${THREADS:-1 2 4 8 16 18 36}" \
bash ./run_bench.sh "$result_dir/${profile}_rep${repeat}.csv"
