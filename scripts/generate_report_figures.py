#!/usr/bin/env python3
"""Восстановление графиков исходного отчёта по новой серии из 6000 измерений.

Вход: results/2026/summary_1200.csv (1200 медиан пяти повторов).
Выход: figures/2026/classic/*.png.
Все сравнения фиксируют одинаковые сетку, число шагов, профиль и q;
для ускорения используется однопоточная версия того же метода.
"""
from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "results/2026/summary_1200.csv"
OUT = ROOT / "figures/2026/classic"
GRIDS = (512, 1024, 2048, 4096)
THREADS = (1, 2, 4, 8, 16, 18, 36)
QS = (1, 2, 4, 8)
PROFILES = ("O2", "O3", "native", "unroll", "novec")
COLORS = {"loop": "#777777", "openmp": "#1764ad", "pthread": "#de7825"}
METHOD_LABELS = {"loop": "Последовательная", "openmp": "OpenMP", "pthread": "Pthreads"}

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10.5,
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.labelsize": 10.5,
    "figure.dpi": 140,
    "savefig.dpi": 180,
})


def load():
    with SOURCE.open(newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    if len(rows) != 1200:
        raise ValueError(f"Ожидалось 1200 конфигураций, получено {len(rows)}")
    data = {}
    for row in rows:
        key = (row["profile"], int(row["nx"]), row["method"],
               int(row["threads"]), int(row["unroll"]))
        if key in data:
            raise ValueError(f"Дубль конфигурации: {key}")
        data[key] = {"time": float(row["median_time_s"]),
                     "mlups": float(row["median_mlups"])}
    return data


def val(data, grid, method, *, profile="O3", threads=None, q=8, metric="mlups"):
    if threads is None:
        threads = 1 if method == "loop" else 36
    return data[(profile, grid, method, threads, q)][metric]


def acceleration(data, grid, method, p, q=8):
    return val(data, grid, method, threads=1, q=q, metric="time") / val(
        data, grid, method, threads=p, q=q, metric="time")


def newfig(figsize=(10.4, 5.7)):
    fig, ax = plt.subplots(figsize=figsize, layout="constrained")
    ax.grid(axis="y", color="#d9e0e8", linewidth=0.8, alpha=0.85)
    ax.set_axisbelow(True)
    return fig, ax


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, facecolor="white")
    plt.close(fig)


def grouped(data, name, title, ylabel, methods, extractor, *, subtitle):
    fig, ax = newfig()
    xs = np.arange(len(GRIDS))
    width = 0.75 / len(methods)
    for i, method in enumerate(methods):
        heights = [extractor(grid, method) for grid in GRIDS]
        ax.bar(xs + (i - (len(methods) - 1) / 2) * width, heights,
               width=width * 0.94, label=METHOD_LABELS[method],
               color=COLORS[method])
    ax.set_xticks(xs, [f"{grid}²" for grid in GRIDS])
    ax.set_xlabel("Размер квадратной сетки")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend(ncol=len(methods), loc="upper left")
    save(fig, name)


def compare_by_q(data, method, name, title, threads):
    fig, ax = newfig()
    for grid in GRIDS:
        ys = [val(data, grid, method, threads=threads, q=q) for q in QS]
        ax.plot(QS, ys, marker="o", markersize=5.5, linewidth=2.2,
                label=f"{grid}²")
    ax.set_xticks(QS)
    ax.set_xlabel("Параметр группировки цикла q")
    ax.set_ylabel("Производительность, MLUPS")
    ax.set_title(title)
    ax.legend(title="Сетка", ncol=2)
    save(fig, name)


def compare_compiler(data, method, name, title, threads):
    fig, axes = plt.subplots(2, 2, figsize=(11.6, 7.7), layout="constrained")
    for grid, ax in zip(GRIDS, axes.flat):
        ys = [val(data, grid, method, profile=pr, threads=threads) for pr in PROFILES]
        ax.bar(PROFILES, ys, color="#3472a5", width=0.66)
        ax.set_title(f"Сетка {grid}²")
        ax.set_ylabel("MLUPS")
        ax.grid(axis="y", alpha=0.45)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelrotation=15)
    fig.suptitle(title + " · q=8, медиана 5 запусков", fontsize=15, fontweight="bold")
    save(fig, name)


def speed_curves(data, method, name):
    fig, ax = newfig(figsize=(10.5, 6.1))
    for grid in GRIDS:
        ys = [acceleration(data, grid, method, p) for p in THREADS]
        ax.plot(THREADS, ys, marker="o", linewidth=2, label=f"{grid}²")
    ax.plot(THREADS, THREADS, linestyle="--", color="#808996",
            linewidth=1.6, label="Идеальное S(P)=P")
    ax.set_xticks(THREADS)
    ax.set_xlabel("Число потоков P")
    ax.set_ylabel("Ускорение S(P)")
    ax.set_title(f"{METHOD_LABELS[method]}: ускорение при увеличении числа потоков")
    ax.legend(ncol=2)
    save(fig, name)


def main():
    d = load()
    subtitle = "Профиль O3, q=8; параллельные версии — 36 потоков; медиана 5 запусков"
    grouped(d, "time.png", "Нормированное время одного обновления", "Время на узел, нс",
            ("loop", "openmp", "pthread"),
            lambda grid, method: 1000.0 / val(d, grid, method),
            subtitle=subtitle)
    grouped(d, "mlups.png", "Производительность трёх реализаций", "MLUPS",
            ("loop", "openmp", "pthread"),
            lambda grid, method: val(d, grid, method),
            subtitle=subtitle)
    grouped(d, "speedup.png", "Ускорение на 36 потоках", "Ускорение S(36)",
            ("openmp", "pthread"),
            lambda grid, method: acceleration(d, grid, method, 36),
            subtitle="Профиль O3, q=8; база — один поток того же метода")
    grouped(d, "efficiency.png", "Эффективность на 36 потоках", "Эффективность, %",
            ("openmp", "pthread"),
            lambda grid, method: 100 * acceleration(d, grid, method, 36) / 36,
            subtitle="Профиль O3, q=8; ускорение относительно одного потока")
    compare_by_q(d, "loop", "loop_unroll_comparison.png",
                 "Последовательная версия: влияние группировки q", 1)
    compare_compiler(d, "loop", "loop_compiler_comparison.png",
                     "Последовательная версия: профили компиляции", 1)
    compare_by_q(d, "openmp", "openmp_unroll_comparison.png",
                 "OpenMP: влияние группировки q", 36)
    compare_by_q(d, "pthread", "pthread_unroll_comparison.png",
                 "Pthreads: влияние группировки q", 36)
    speed_curves(d, "openmp", "openmp_speedup.png")
    speed_curves(d, "pthread", "pthread_speedup.png")

    # На одной диаграмме сравниваем профили компиляции обеих параллельных версий
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.0), layout="constrained")
    for grid, ax in zip(GRIDS, axes.flat):
        x = np.arange(len(PROFILES))
        width = 0.38
        for i, method in enumerate(("openmp", "pthread")):
            values = [val(d, grid, method, profile=pr) for pr in PROFILES]
            ax.bar(x + (i - .5) * width, values, width=width * .96,
                   label=METHOD_LABELS[method], color=COLORS[method])
        ax.set_xticks(x, PROFILES, rotation=15)
        ax.set_title(f"Сетка {grid}²")
        ax.set_ylabel("MLUPS")
        ax.grid(axis="y", alpha=.4)
        ax.set_axisbelow(True)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=2, bbox_to_anchor=(.5, .965))
    fig.suptitle("Профили компиляции: OpenMP и Pthreads · 36 потоков, q=8",
                 fontsize=14, fontweight="bold", y=0.995)
    save(fig, "compiler_comparison.png")
    print(f"Сформированы 11 графиков в {OUT}")


if __name__ == "__main__":
    main()
