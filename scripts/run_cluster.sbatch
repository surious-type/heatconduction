#!/usr/bin/env bash
#SBATCH --job-name=heatcond
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=36
#SBATCH --output=heatcond-%j.log

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:-.}"

# Один профиль на задание: PROFILES=O2/O3/native/unroll/novec.
PROFILES="${PROFILES:-O3}" \
ARCH="${ARCH:-skylake-avx512}" \
REPEATS="${REPEATS:-5}" \
THREADS="${THREADS:-1 2 4 8 16 18 36}" \
bash scripts/run_profiles.sh
