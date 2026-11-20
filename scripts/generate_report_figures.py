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



# Classic Matplotlib layout reconstructed after comparing the legacy diagrams.
# The series are computed from the 1200 medians (five repetitions per config).
from matplotlib.lines import Line2D

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 10,
    "axes.labelsize": 10,
    "lines.linewidth": 1.55,
    "lines.markersize": 3.3,
    "figure.facecolor": "white",
    "savefig.facecolor": "white",
})

def classic_axis(ax):
    ax.grid(True, color="#b0b0b0", linewidth=.65, alpha=.28)
    ax.set_axisbelow(True)
    ax.tick_params(labelsize=8, length=3)

def classic_save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=210, bbox_inches="tight", pad_inches=.15)
    plt.close(fig)

def classic_comparison(d, kind):
    meta = {
        "time": ("Comparative time / O3 / all grids and unroll", "ns / update"),
        "mlups": ("Comparative mlups / O3 / all grids and unroll", "MLUPS"),
        "speedup": ("Comparative speedup / O3 / all grids and unroll", "Speedup"),
        "efficiency": ("Comparative efficiency / O3 / all grids and unroll", "Efficiency"),
        "compiler_comparison": ("Comparative compiler_comparison / O3 / all grids and unroll", "MLUPS / O3"),
    }
    title, ylabel = meta[kind]
    fig, axs = plt.subplots(4, 4, figsize=(18, 14.4))
    fig.suptitle(title, fontsize=16, y=.992)
    for row, grid in enumerate(GRIDS):
        for col, q in enumerate(QS):
            ax = axs[row, col]
            ax.set_title(f"{grid}² ×{q}", fontsize=9, pad=7)
            classic_axis(ax)
            if kind != "compiler_comparison":
                if kind == "time":
                    op = [1000 / val(d, grid, "openmp", threads=p, q=q) for p in THREADS]
                    pt = [1000 / val(d, grid, "pthread", threads=p, q=q) for p in THREADS]
                    ax.axhline(1000 / val(d, grid, "loop", q=q),
                               color="C0", ls="--", lw=1.25)
                elif kind == "mlups":
                    op = [val(d, grid, "openmp", threads=p, q=q) for p in THREADS]
                    pt = [val(d, grid, "pthread", threads=p, q=q) for p in THREADS]
                    ax.axhline(val(d, grid, "loop", q=q),
                               color="C0", ls="--", lw=1.25)
                elif kind == "speedup":
                    op = [acceleration(d, grid, "openmp", p, q=q) for p in THREADS]
                    pt = [acceleration(d, grid, "pthread", p, q=q) for p in THREADS]
                    ax.plot(THREADS, THREADS, color=".3", ls=":", lw=.95)
                    ax.set_ylim(0, 39)
                else:
                    op = [acceleration(d, grid, "openmp", p, q=q) / p for p in THREADS]
                    pt = [acceleration(d, grid, "pthread", p, q=q) / p for p in THREADS]
                    ax.axhline(1, color=".35", ls=":", lw=.95)
                ax.plot(THREADS, op, "-o", color="C0", label="openmp")
                ax.plot(THREADS, pt, "-o", color="C1", label="pthread")
                ax.set_xlim(.3, 37.5)
                ax.set_xticks(THREADS if kind in ("speedup", "efficiency")
                              else (1, 4, 8, 16, 18, 36))
                if kind in ("speedup", "efficiency"):
                    ax.tick_params(axis="x", labelsize=7)
            else:
                xpos = np.arange(len(PROFILES))
                for method, color in (("loop", "C0"), ("openmp", "C1"), ("pthread", "C2")):
                    threads = 1 if method == "loop" else 36
                    baseline = val(d, grid, method, profile="O3", threads=threads, q=q)
                    yy = [val(d, grid, method, profile=pr, threads=threads, q=q) / baseline
                          for pr in PROFILES]
                    ax.plot(xpos, yy, "-o", color=color, label=method)
                ax.set_xticks(xpos, PROFILES, fontsize=8)
                ax.axhline(1, color=".45", ls=":", lw=.9)
            if col == 0:
                ax.set_ylabel(ylabel, fontsize=9)
            if row == 3 and kind != "compiler_comparison":
                ax.set_xlabel("Threads", fontsize=9)
    if kind == "compiler_comparison":
        handles = [Line2D([0], [0], color=c, marker="o", lw=1.5, label=m)
                   for m,c in (("loop","C0"),("openmp","C1"),("pthread","C2"))]
    else:
        handles = [Line2D([0], [0], color=c, marker="o", lw=1.5, label=m)
                   for m,c in (("openmp","C0"),("pthread","C1"))]
        if kind in ("time", "mlups"):
            handles.append(Line2D([0], [0], color="C0", ls="--", label="loop"))
    fig.legend(handles=handles, loc="lower center", ncol=len(handles),
               bbox_to_anchor=(.5,.004), frameon=False)
    fig.subplots_adjust(top=.955,bottom=.060,left=.047,right=.987,
                        wspace=.14,hspace=.26)
    classic_save(fig, kind+".png")

def classic_unroll(d, method):
    fig, axes = plt.subplots(2, 2, figsize=(12.8, 9.0))
    fig.suptitle(f"{method.upper()} unrolling / all grids and compiler profiles",
                 fontsize=16, y=.995)
    for grid, ax in zip(GRIDS, axes.flat):
        ax.set_title(f"{grid}²", fontsize=11)
        classic_axis(ax)
        for i, pr in enumerate(PROFILES):
            threads = 1 if method == "loop" else 36
            y = [val(d, grid, method, profile=pr, threads=threads, q=q) for q in QS]
            ax.plot(QS, y, "-o", color=f"C{i}", lw=1.9, ms=5, label=pr)
        ax.set_xticks(QS)
        ax.set_xlabel("Unroll factor",fontsize=10)
        ax.set_ylabel("MLUPS",fontsize=10)
    handles, labels = axes.flat[0].get_legend_handles_labels()
    fig.legend(handles,labels,ncol=5,loc="lower center",frameon=False,
               bbox_to_anchor=(.5,.007))
    fig.subplots_adjust(top=.932,bottom=.100,left=.08,right=.985,
                        wspace=.14,hspace=.22)
    classic_save(fig,method+"_unroll_comparison.png")

def classic_loop_compiler(d):
    fig,axes=plt.subplots(4,4,figsize=(18.0,14.4))
    fig.suptitle("LOOP compiler profiles / all grids and unroll",
                 fontsize=16,y=.992)
    for row,grid in enumerate(GRIDS):
        for col,q in enumerate(QS):
            ax=axes[row,col]
            classic_axis(ax)
            ax.set_title(f"{grid}² ×{q}",fontsize=9,pad=7)
            base=val(d,grid,"loop",profile="O3",threads=1,q=q)
            y=[val(d,grid,"loop",profile=pr,threads=1,q=q)/base
               for pr in PROFILES]
            ax.bar(PROFILES,y,color="C0",width=.8)
            ax.axhline(1,color="black",ls=":",lw=1.3)
            ax.tick_params(axis="x",labelrotation=27)
            if col==0: ax.set_ylabel("Relative MLUPS / O3",fontsize=9)
    fig.subplots_adjust(top=.955,bottom=.052,left=.047,right=.987,
                        wspace=.14,hspace=.21)
    classic_save(fig,"loop_compiler_comparison.png")

def classic_method_speedup(d,method):
    fig,axes=plt.subplots(4,4,figsize=(18.0,14.4))
    fig.suptitle(f"{method.upper()} / speedup / all grids and unroll",
                 fontsize=16,y=.992)
    for row,grid in enumerate(GRIDS):
        for col,q in enumerate(QS):
            ax=axes[row,col]
            classic_axis(ax)
            ax.set_title(f"{grid}² ×{q}",fontsize=9,pad=7)
            ax.plot(THREADS,THREADS,color=".3",ls=":",lw=1)
            for i,pr in enumerate(PROFILES):
                y=[acceleration(d,grid,method,p,q=q,profile=pr) for p in THREADS]
                ax.plot(THREADS,y,"-o",color=f"C{i}",label=pr)
            ax.set_ylim(0,39)
            ax.set_xticks(THREADS)
            ax.tick_params(axis="x",labelsize=7)
            if col==0:ax.set_ylabel("Speedup",fontsize=9)
            if row==3:ax.set_xlabel("Threads",fontsize=9)
    handles=[Line2D([0],[0],color=f"C{i}",marker="o",label=pr)
             for i,pr in enumerate(PROFILES)]
    fig.legend(handles=handles,loc="lower center",ncol=5,frameon=False,
               bbox_to_anchor=(.5,.007))
    fig.subplots_adjust(top=.955,bottom=.060,left=.047,right=.987,
                        wspace=.14,hspace=.26)
    classic_save(fig,method+"_speedup.png")

def main():
    d=load()
    for kind in ("time","mlups","speedup","efficiency","compiler_comparison"):
        classic_comparison(d,kind)
    for method in ("loop","openmp","pthread"):
        classic_unroll(d,method)
    classic_loop_compiler(d)
    for method in ("openmp","pthread"):
        classic_method_speedup(d,method)
    print("Сформированы 11 классических графиков Matplotlib:", OUT)

if __name__ == "__main__":
    main()
