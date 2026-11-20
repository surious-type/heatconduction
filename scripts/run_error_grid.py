#!/usr/bin/env python3
"""Таблицы ошибок для 4 пространственных и 4 временных шагов.

Использует результаты из errors.csv, если они имеются, и выполняет
только ещё не измеренные устойчивые сочетания параметров.
Никаких внешних пакетов Python не требуется.
"""
import argparse
import csv
import math
import re
import subprocess
from pathlib import Path

NX_VALUES = (101, 201, 401, 801)
N_VALUES = (10, 40, 160, 640)
T0 = 0.0
T1 = 0.01
A = 0.1
LX = LY = 1.0


def fmt(value):
    return format(value, ".9g")


def existing_results(path):
    cache = {}
    if not path.is_file():
        print(f"Файл {path} отсутствует: будут вычислены все 10 допустимых сочетаний.")
        return cache

    with path.open(newline="", encoding="utf-8-sig") as file:
        for row in csv.DictReader(file):
            try:
                nx = int(row["nx"])
                ny = int(row["ny"])
                steps = int(row["steps"])
                t1 = float(row["t1"])
                a = float(row["a"])
                error_c = float(row["error_c"])
                error_l2 = float(row["error_l2"])
            except (KeyError, ValueError, TypeError) as exc:
                raise ValueError(f"Некорректная строка в {path}: {row}") from exc
            if (nx == ny and nx in NX_VALUES and steps in N_VALUES
                    and math.isclose(t1, T1) and math.isclose(a, A)
                    and math.isfinite(error_c) and math.isfinite(error_l2)):
                cache[(nx, steps)] = (error_c, error_l2)
    print(f"Найдено подходящих ранее измеренных сочетаний: {len(cache)}")
    return cache


def run_case(executable, nx, steps):
    command = [
        str(executable), "--Nx", str(nx), "--Ny", str(nx),
        "--N", str(steps), "--t0", fmt(T0), "--t1", fmt(T1),
        "--a", fmt(A), "--Lx", fmt(LX), "--Ly", fmt(LY),
        "--debug", "1",
    ]
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    if done.returncode:
        raise RuntimeError(
            f"Расчёт Nx={nx}, N={steps} завершился с кодом {done.returncode}:\n"
            + done.stdout + "\n" + done.stderr
        )
    c = re.search(r"^C-норма:\s*([+\-\d.eE]+)", done.stdout, re.MULTILINE)
    l2 = re.search(r"^l2-норма:\s*([+\-\d.eE]+)", done.stdout, re.MULTILINE)
    if not c or not l2:
        raise RuntimeError(f"Не найдены нормы для Nx={nx}, N={steps}:\n{done.stdout}")
    return float(c.group(1)), float(l2.group(1))


def write_csv(path, header, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", default="./heat_loop",
                        help="собранная версия программы (по умолчанию ./heat_loop)")
    parser.add_argument("--existing", default="errors.csv",
                        help="четыре ранее полученных результата (по умолчанию errors.csv)")
    parser.add_argument("--output-dir", default=".",
                        help="каталог результатов")
    args = parser.parse_args()

    program = Path(args.program).resolve()
    if not program.is_file():
        parser.error(f"Нет программы {program}. Сначала соберите heat_loop.")
    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    cache = existing_results(Path(args.existing))

    headers = ["h/tau"] + [fmt((T1 - T0) / n) for n in N_VALUES]
    c_matrix, l2_matrix, long_rows = [], [], []
    calculated = reused = unstable = 0

    for nx in NX_VALUES:
        h = LX / (nx - 1)
        c_row = [fmt(h)]
        l2_row = [fmt(h)]
        for steps in N_VALUES:
            tau = (T1 - T0) / steps
            # Тот же критерий устойчивости, что и в C++ validate():
            # N >= 2*a*a*T*(1/hx^2 + 1/hy^2).
            n_min = 2 * A * A * (T1 - T0) * (2 / (h * h))
            if steps < n_min:
                c_row.append("-")
                l2_row.append("-")
                long_rows.append([nx, nx, fmt(h), fmt(tau), steps,
                                  fmt(T1), fmt(A), "-", "-", "unstable", "-"])
                unstable += 1
                continue

            if (nx, steps) in cache:
                err_c, err_l2 = cache[(nx, steps)]
                source = "existing"
                reused += 1
            else:
                print(f"Вычисляем Nx=Ny={nx}, N={steps}, h={fmt(h)}, tau={fmt(tau)}",
                      flush=True)
                err_c, err_l2 = run_case(program, nx, steps)
                source = "computed"
                calculated += 1

            c_row.append(fmt(err_c))
            l2_row.append(fmt(err_l2))
            long_rows.append([nx, nx, fmt(h), fmt(tau), steps,
                              fmt(T1), fmt(A), fmt(err_c), fmt(err_l2),
                              "ok", source])
        c_matrix.append(c_row)
        l2_matrix.append(l2_row)

    write_csv(out / "errors_matrix_c.csv", headers, c_matrix)
    write_csv(out / "errors_matrix_l2.csv", headers, l2_matrix)
    write_csv(out / "errors_grid_full.csv",
              ["nx", "ny", "h", "tau", "steps", "t1", "a",
               "error_c", "error_l2", "status", "source"], long_rows)
    print(f"Готово: {reused} взято из {args.existing}, "
          f"{calculated} вычислено, {unstable} неустойчивых сочетаний.")
    print("Файлы: " + ", ".join(str(out / name) for name in (
        "errors_matrix_c.csv", "errors_matrix_l2.csv", "errors_grid_full.csv")))


if __name__ == "__main__":
    main()
