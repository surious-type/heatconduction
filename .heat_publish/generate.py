import csv,lzma,statistics,math,json,pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from collections import defaultdict

G=[512,1024,2048,4096]; U=[1,2,4,8]; P=["O2","O3","native","unroll","novec"]; T=[1,2,4,8,16,18,36]
METHODS=["loop","openmp","pthread"]
STEPS={"loop":[10000,2000,800,250],"openmp":[20000,4000,1600,500],"pthread":[10000,2000,800,250]}
END=[.001,.0001,.00001,.000001]; CH=[62998.9,261111.,1048160.,4194140.]
JOBS={"loop":"18477","pthread":"18483","openmp":"18478/18488"}
FLAGS={"O2":"-O2","O3":"-O3","native":"-O3 -march=skylake-avx512","unroll":"-O3 -march=skylake-avx512 -funroll-loops","novec":"-O3 -march=skylake-avx512 -fno-tree-vectorize"}
M={}
for m in METHODS:
    times=list(map(float,lzma.decompress(pathlib.Path(".heat_publish/"+m+".xz").read_bytes()).decode().splitlines()))
    th=[1] if m=="loop" else T
    assert len(times)==len(G)*len(P)*len(U)*len(th)*5,(m,len(times))
    it=iter(times); buckets=defaultdict(list); raw=[]
    for i,g in enumerate(G):
        for p in sorted(P):
            for u in U:
                for t in th:
                    for rep in range(1,6):
                        sec=next(it); assert math.isfinite(sec) and sec>0
                        ml=(STEPS[m][i]-1)*(g-2)**2/sec/1e6
                        job=("18488" if u==1 else "18478") if m=="openmp" else JOBS[m]
                        raw.append([p,u,t,g,g,STEPS[m][i],END[i],rep,sec,ml,CH[i],job])
                        buckets[g,p,u,t].append(sec)
    dst=pathlib.Path(m)/"results";dst.mkdir(parents=True,exist_ok=True)
    with (dst/"results.csv").open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["profile","unroll","threads","nx","ny","steps","t1","repeat","time_s","mlups_derived","checksum","source_job"]);w.writerows(raw)
    agg={}
    with (dst/"summary.csv").open("w",newline="") as f:
        w=csv.writer(f);w.writerow(["nx","ny","steps","t1","profile","unroll","threads","runs","median_time_s","median_mlups","min_time_s","max_time_s","std_time_s"])
        for (g,p,u,t),values in sorted(buckets.items()):
            v=statistics.median(values); med=(STEPS[m][G.index(g)]-1)*(g-2)**2/v/1e6
            agg[g,p,u,t]={"time":v,"mlups":med,"steps":STEPS[m][G.index(g)]}
            w.writerow([g,g,STEPS[m][G.index(g)],END[G.index(g)],p,u,t,5,v,med,min(values),max(values),statistics.stdev(values)])
    M[m]=agg
    (dst/"metadata.json").write_text(json.dumps({"method":m,"source_jobs":JOBS[m],"measurements":len(raw),"configurations":len(agg),"repetitions":5,"grids":G,"unroll":U,"compiler_profiles":FLAGS,"threads":th,"source":"Original measured time_s values preserved from experiment archives; MLUPS recomputed from counts and time_s.","limitation":"Original per-run timestamps and hosts are not included in compact transfer; originals remain in experiment archives.","comparability":"OpenMP used 2x more time steps than loop and pthread; compare MLUPS or normalized ns/update, not wall time."},indent=2,ensure_ascii=False)+"\n")
plt.rcParams.update({"font.size":9,"axes.titlesize":9,"figure.titlesize":15})
def save(fig,p):
    p=pathlib.Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    fig.savefig(p,dpi=112,bbox_inches="tight",pad_inches=.13);plt.close(fig)
for m in METHODS:
    a=M[m];th=[1] if m=="loop" else T
    for metric in (["time","mlups"] if m=="loop" else ["time","speedup","efficiency","mlups"]):
        if m=="loop":
            fig,axs=plt.subplots(2,2,figsize=(13,9),layout="constrained")
            for ax,g in zip(axs.flat,G):
                for p in P:ax.plot(U,[a[g,p,u,1][metric] for u in U],"-o",label=p)
                ax.set_title(str(g)+"²");ax.set_xticks(U);ax.set_xlabel("Unroll factor");ax.set_ylabel(metric);ax.grid(alpha=.25)
        else:
            fig,axs=plt.subplots(4,4,figsize=(20,14),layout="constrained")
            for i,g in enumerate(G):
                for j,u in enumerate(U):
                    ax=axs[i,j]
                    for p in P:
                        v=[a[g,p,u,t] for t in T]
                        y=([x[metric] for x in v] if metric in ("time","mlups") else [v[0]["time"]/x["time"]/(t if metric=="efficiency" else 1) for t,x in zip(T,v)])
                        ax.plot(T,y,"-o",markersize=2.5,lw=1.3,label=p)
                    ax.set_title(str(g)+"²  ×"+str(u));ax.set_xticks(T);ax.grid(alpha=.25)
                    if i==3:ax.set_xlabel("Threads")
                    if j==0:ax.set_ylabel(metric)
                    if metric=="speedup":ax.plot([1,36],[1,36],":",color="black",lw=.8)
                    if metric=="efficiency":ax.axhline(1,ls=":",color="black",lw=.8)
        fig.suptitle(m.upper()+" / "+metric+" / all grids and unroll")
        fig.legend(*axs.flat[0].get_legend_handles_labels(),loc="outside lower center",ncol=5,frameon=False)
        save(fig,m+"/figures/"+metric+".png")
    fig,axs=plt.subplots(4,4,figsize=(20,14),layout="constrained")
    t=1 if m=="loop" else 36
    for i,g in enumerate(G):
        for j,u in enumerate(U):
            ax=axs[i,j];ys=[a[g,p,u,t]["mlups"] for p in P]
            ax.bar(P,[v/ys[1] for v in ys]);ax.axhline(1,ls=":",color="black");ax.grid(axis="y",alpha=.2)
            ax.set_title(str(g)+"²  ×"+str(u));ax.tick_params(axis="x",rotation=30)
            if j==0:ax.set_ylabel("Relative MLUPS / O3")
    fig.suptitle(m.upper()+" compiler profiles / all grids and unroll")
    save(fig,m+"/figures/compiler_comparison.png")
    fig,axs=plt.subplots(2,2,figsize=(13,9),layout="constrained")
    for ax,g in zip(axs.flat,G):
        for p in P:ax.plot(U,[a[g,p,u,t]["mlups"] for u in U],"-o",label=p)
        ax.set_title(str(g)+"²");ax.set_xticks(U);ax.set_xlabel("Unroll factor");ax.set_ylabel("MLUPS");ax.grid(alpha=.25)
    fig.suptitle(m.upper()+" unrolling / all grids and compiler profiles")
    fig.legend(*axs.flat[0].get_legend_handles_labels(),loc="outside lower center",ncol=5,frameon=False)
    save(fig,m+"/figures/unroll_comparison.png")
for metric in ["time","mlups","speedup","efficiency","compiler_comparison"]:
    fig,axs=plt.subplots(4,4,figsize=(20,14),layout="constrained")
    for i,g in enumerate(G):
        for j,u in enumerate(U):
            ax=axs[i,j]
            if metric=="compiler_comparison":
                for m in METHODS:
                    t=1 if m=="loop" else 36
                    yy=[M[m][g,p,u,t]["mlups"] for p in P]
                    ax.plot(P,[v/yy[1] for v in yy],"-o",markersize=3,label=m)
                if j==0:ax.set_ylabel("MLUPS / O3")
            else:
                for m in ["openmp","pthread"]:
                    yy=[M[m][g,"O3",u,t] for t in T]
                    if metric=="mlups":vals=[v["mlups"] for v in yy]
                    elif metric=="time":vals=[1000/v["mlups"] for v in yy]
                    else:vals=[yy[0]["time"]/v["time"]/(t if metric=="efficiency" else 1) for t,v in zip(T,yy)]
                    ax.plot(T,vals,"-o",markersize=2.5,lw=1.3,label=m)
                if metric in ["time","mlups"]:
                    ml=M["loop"][g,"O3",u,1]["mlups"]
                    ax.axhline(1000/ml if metric=="time" else ml,ls="--",label="loop")
                if metric=="speedup":ax.plot([1,36],[1,36],":",color="black",lw=.8)
                if metric=="efficiency":ax.axhline(1,ls=":",color="black",lw=.8)
                if i==3:ax.set_xlabel("Threads")
                if j==0:ax.set_ylabel({"time":"ns / update","mlups":"MLUPS","speedup":"Speedup","efficiency":"Efficiency"}[metric])
            ax.set_title(str(g)+"²  ×"+str(u));ax.grid(alpha=.25)
    fig.suptitle("Comparative "+metric+"  / O3 / all grids and unroll")
    fig.legend(*axs.flat[0].get_legend_handles_labels(),loc="outside lower center",ncol=4,frameon=False)
    save(fig,"figures/"+metric+".png")
with open("comparison_summary.csv","w",newline="") as f:
    w=csv.writer(f);w.writerow(["method","nx","profile","unroll","threads","steps","median_time_s","median_mlups","ratio_to_seq_O3_U4"])
    for g in G:
        base=M["loop"][g,"O3",4,1]["mlups"]
        for m in METHODS:
            t=1 if m=="loop" else 36;v=M[m][g,"O3",4,t]
            w.writerow([m,g,"O3",4,t,v["steps"],v["time"],v["mlups"],v["mlups"]/base])
pathlib.Path("RESULTS.md").write_text("""# Heat conduction benchmark results

Three C++ implementations: sequential (loop), OpenMP, and POSIX threads.

Each implementation has results/results.csv with 5 timings per configuration, results/summary.csv with median values, and figures/ containing ready-to-use PNG plots. Root figures/ compares implementations at -O3.

Grids: 512², 1024², 2048², 4096². Unroll factors: 1, 2, 4, 8. Compiler profiles: O2, O3, native, unroll, novec. Pthreads and OpenMP: 1, 2, 4, 8, 16, 18, 36 threads.

OpenMP values for unroll=1 are corrected reruns (Slurm 18488); unroll=2/4/8 come from Slurm 18478. Loop and pthread use jobs 18477 and 18483.

Important: OpenMP ran twice as many time steps as loop and pthread. Direct wall times are not comparable across implementations. Root time.png shows normalized ns per update. Speedup and efficiency use each parallel implementation's own 1-thread baseline. Sequential speedup/efficiency are undefined.

Original time_s values are preserved exactly; MLUPS values are recalculated from time_s, steps and grid size. Original job timestamps and hostnames are not part of the compact import; source archives contain those.
""",encoding="utf-8")
print("Generated complete data and 21 PNG charts")
