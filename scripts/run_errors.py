#!/usr/bin/env python3
"""Измерение погрешностей на сетке 4x4 по (h, tau).

Запуск из корня проекта: python3 scripts/run_errors.py
Скрипт сам компилирует последовательную реализацию и создаёт каталог errors/.
"""

import argparse
import csv
import math
import os
import re
import shlex
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
T0, T1 = 0.0, 0.01
A, LX, LY = 0.1, 1.0, 1.0
DEFAULT_GRIDS = (101, 201, 401, 801)
DEFAULT_STEPS = (10, 40, 160, 640)


def fmt(number):
    return format(number, ".9g")


def error_norms(program, nx, steps):
    command = [
        str(program), "--Nx", str(nx), "--Ny", str(nx),
        "--N", str(steps), "--t0", fmt(T0), "--t1", fmt(T1),
        "--a", fmt(A), "--Lx", fmt(LX), "--Ly", fmt(LY), "--debug", "1",
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    values = []
    for label in ("C-норма", "l2-норма"):
        match = re.search(r"^" + re.escape(label) + r":\s*([+\-\d.eE]+)",
                          result.stdout, re.MULTILINE)
        if not match:
            raise RuntimeError(f"Не удалось найти {label} для Nx={nx}, N={steps}:\n"
                               + result.stdout)
        value = float(match.group(1))
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"Недопустимая {label}: {value}")
        values.append(value)
    return values


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def run(program, grids, steps_values, destination):
    header = ["h/tau"] + [fmt((T1 - T0) / n) for n in steps_values]
    c_rows, l2_rows, all_rows = [], [], []
    done = skipped = 0

    for nx in grids:
        h = LX / (nx - 1)
        c_row, l2_row = [fmt(h)], [fmt(h)]
        for steps in steps_values:
            tau = (T1 - T0) / steps
            # Условие устойчивости из validate() C++:
            # N >= 2*a^2*(t1-t0)*(1/hx^2 + 1/hy^2).
            min_steps = 2 * A**2 * (T1 - T0) * (1 / h**2 + 1 / h**2)
            if steps + 1e-9 < min_steps:
                c_row.append("-")
                l2_row.append("-")
                all_rows.append([nx, nx, fmt(h), fmt(tau), steps,
                                 fmt(T1), fmt(A), "-", "-", "unstable", "-"])
                skipped += 1
                continue

            print(f"Расчёт {done + 1}: Nx=Ny={nx}, N={steps}, "
                  f"h={fmt(h)}, tau={fmt(tau)}", flush=True)
            err_c, err_l2 = error_norms(program, nx, steps)
            c_row.append(fmt(err_c))
            l2_row.append(fmt(err_l2))
            all_rows.append([nx, nx, fmt(h), fmt(tau), steps,
                             fmt(T1), fmt(A), fmt(err_c), fmt(err_l2),
                             "ok", "computed"])
            done += 1
        c_rows.append(c_row)
        l2_rows.append(l2_row)

    destination.mkdir(parents=True, exist_ok=True)
    write_csv(destination / "errors_grid_full.csv",
              ["nx", "ny", "h", "tau", "steps", "t1", "a",
               "error_c", "error_l2", "status", "source"], all_rows)
    write_csv(destination / "errors_matrix_c.csv", header, c_rows)
    write_csv(destination / "errors_matrix_l2.csv", header, l2_rows)
    print(f"Готово: {done} расчётов, {skipped} сочетаний исключены "
          "по условию устойчивости.")
    print(f"Результаты: {destination.resolve()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "errors",
                        help="папка результатов (по умолчанию errors/ в проекте)")
    parser.add_argument("--program", type=Path,
                        help="существующая программа; без этого аргумента собирается автоматически")
    parser.add_argument("--grids", type=int, nargs="+", default=DEFAULT_GRIDS,
                        help="размеры квадратных сеток (для тестирования)")
    parser.add_argument("--steps", type=int, nargs="+", default=DEFAULT_STEPS,
                        help="числа временных шагов (для тестирования)")
    args = parser.parse_args()
    if any(n < 4 for n in args.grids) or any(n < 1 for n in args.steps):
        parser.error("Размеры сеток должны быть >=4, а числа шагов >=1")

    if args.program is not None:
        program = args.program.resolve()
        if not program.is_file():
            parser.error(f"Файл программы отсутствует: {program}")
        run(program, args.grids, args.steps, args.output_dir)
        return

    with tempfile.TemporaryDirectory(prefix="heat_errors_") as tmp:
        program = Path(tmp) / "heat_errors"
        compiler = shlex.split(os.environ.get("CXX", "g++"))
        if not compiler:
            parser.error("Переменная CXX пуста")
        command = compiler + ["-std=c++17", "-O3", str(ROOT / "loop/sequence.loop.cpp"),
                              "-o", str(program)]
        print("Компиляция:", shlex.join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
        run(program, args.grids, args.steps, args.output_dir)


if __name__ == "__main__":
    main()
