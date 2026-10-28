# Heat conduction benchmark results

Three C++ implementations: sequential (loop), OpenMP, and POSIX threads.

Each implementation has results/results.csv with 5 timings per configuration, results/summary.csv with median values, and figures/ containing ready-to-use PNG plots. Root figures/ compares implementations at -O3.

Grids: 512², 1024², 2048², 4096². Unroll factors: 1, 2, 4, 8. Compiler profiles: O2, O3, native, unroll, novec. Pthreads and OpenMP: 1, 2, 4, 8, 16, 18, 36 threads.

OpenMP values for unroll=1 are corrected reruns (Slurm 18488); unroll=2/4/8 come from Slurm 18478. Loop and pthread use jobs 18477 and 18483.

Important: OpenMP ran twice as many time steps as loop and pthread. Direct wall times are not comparable across implementations. Root time.png shows normalized ns per update. Speedup and efficiency use each parallel implementation's own 1-thread baseline. Sequential speedup/efficiency are undefined.

Original time_s values are preserved exactly; MLUPS values are recalculated from time_s, steps and grid size. Original job timestamps and hostnames are not part of the compact import; source archives contain those.
