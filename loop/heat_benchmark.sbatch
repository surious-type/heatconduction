#!/bin/bash -l
#SBATCH --job-name=heat-loop
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --time=04:00:00
#SBATCH --output=heat_%j.out
#SBATCH --error=heat_%j.err

set -Eeuo pipefail

cd "${SLURM_SUBMIT_DIR:?Запускать через sbatch из каталога проекта}"

# По умолчанию загружаем GCC из примера лекции ЦХАБД.
# GCC_MODULE=none позволит использовать компилятор по умолчанию.
GCC_MODULE="${GCC_MODULE:-gcc/gcc-12.2}"
if [[ "$GCC_MODULE" != none ]]; then
  if type module >/dev/null 2>&1; then
    module load "$GCC_MODULE"
  else
    echo "Ошибка: команда module недоступна; проверь окружение кластера либо задай GCC_MODULE=none" >&2
    exit 1
  fi
fi

# Настраиваемые переменные:
#   BENCH_MODE=smoke|quick|full (по умолчанию quick)
#   BENCH_SOURCE=./sequence.loop.bench.cpp
#   BENCH_THREADS=1 (для OpenMP — например 1,2,4,8,16,36)
#   BENCH_LOOPS=1,2,4,8
#   BENCH_PROFILES=O2,O3,native,unroll,novec
#   BENCH_REPEATS=3
BENCH_MODE="${BENCH_MODE:-quick}"
BENCH_SOURCE="${BENCH_SOURCE:-./sequence.loop.bench.cpp}"
BENCH_THREADS="${BENCH_THREADS:-1}"
BENCH_LOOPS="${BENCH_LOOPS:-1,2,4,8}"
if [[ -z "${BENCH_PROFILES:-}" ]]; then
  case "$BENCH_MODE" in
    smoke) BENCH_PROFILES=O2,O3 ;;
    quick) BENCH_PROFILES=O3,native ;;
    full)  BENCH_PROFILES=O2,O3,native,unroll ;;
    *) echo "Ошибка: BENCH_MODE должен быть smoke, quick или full" >&2; exit 1 ;;
  esac
fi
if [[ -z "${BENCH_REPEATS:-}" ]]; then
  case "$BENCH_MODE" in
    smoke) BENCH_REPEATS=1 ;;
    quick) BENCH_REPEATS=3 ;;
    full)  BENCH_REPEATS=5 ;;
    *) echo "Ошибка: BENCH_MODE должен быть smoke, quick или full" >&2; exit 1 ;;
  esac
fi

# Не разрешаем больше потоков, чем выделено Slurm.
IFS=, read -r -a THREAD_COUNTS <<< "$BENCH_THREADS"
for p in "${THREAD_COUNTS[@]}"; do
  if [[ ! "$p" =~ ^[1-9][0-9]*$ ]] || (( p > SLURM_CPUS_PER_TASK )); then
    echo "Ошибка: BENCH_THREADS='$BENCH_THREADS' превышает выделенные CPU: ${SLURM_CPUS_PER_TASK}" >&2
    exit 1
  fi
done

export OMP_PLACES="${OMP_PLACES:-cores}"
export OMP_PROC_BIND="${OMP_PROC_BIND:-close}"

echo "Job ID: ${SLURM_JOB_ID}"
echo "Node: ${SLURMD_NODENAME:-$(hostname)}"
echo "CPU per task: ${SLURM_CPUS_PER_TASK}"
echo "G++: $(g++ --version | head -1)"
echo "Source: ${BENCH_SOURCE}"
echo "Mode: ${BENCH_MODE}"

# Всё — включая компиляцию с -march=native — выполняется на вычислительном узле.
srun --ntasks=1 --cpus-per-task="${SLURM_CPUS_PER_TASK}" bash ./benchmark_loop.sh \
  "--${BENCH_MODE}" \
  --source "$BENCH_SOURCE" \
  --compiler g++ \
  --loops "$BENCH_LOOPS" \
  --profiles "$BENCH_PROFILES" \
  --threads "$BENCH_THREADS" \
  --repeats "$BENCH_REPEATS" \
  --out "./bench_results/${SLURM_JOB_ID}"

echo "Результаты: ${SLURM_SUBMIT_DIR}/bench_results/${SLURM_JOB_ID}"
