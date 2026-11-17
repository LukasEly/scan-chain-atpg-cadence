#!/usr/bin/env python3
"""
Gera os gráficos do relatório a partir de results/results.csv e
results/atpg_curves.csv. Requer matplotlib.

Uso: python3 plot.py <dir_results>      (figuras em <dir_results>/figs/)
"""
import csv
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RES = sys.argv[1] if len(sys.argv) > 1 else "results"
FIG = os.path.join(RES, "figs")
os.makedirs(FIG, exist_ok=True)

# paleta categórica validada para daltonismo (azul, laranja, água)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": MUTED, "axes.labelcolor": INK,
    "xtick.color": MUTED, "ytick.color": MUTED, "axes.grid": True,
    "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
    "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "figure.dpi": 130,
})


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


rows = [{k: (num(v) if k != "tag" else v) for k, v in r.items()}
        for r in csv.DictReader(open(os.path.join(RES, "results.csv")))]
curves = list(csv.DictReader(open(os.path.join(RES, "atpg_curves.csv"))))
base = [r for r in rows if (r["NCHAINS"] or 1) == 1]


def sweep(key, fix):
    return sorted([r for r in base if all(r[k] == v for k, v in fix.items())], key=lambda r: r[key])


SW = [("DATA_W", sweep("DATA_W", {"DEPTH": 8, "WMAX": 7})),
      ("DEPTH", sweep("DEPTH", {"DATA_W": 32, "WMAX": 7})),
      ("WMAX", sweep("WMAX", {"DATA_W": 32, "DEPTH": 8}))]


def save(fig, name):
    fig.tight_layout()
    fig.savefig(os.path.join(FIG, name), bbox_inches="tight")
    plt.close(fig)


# 1) área de células antes/depois do scan, por parâmetro
fig, axs = plt.subplots(1, 3, figsize=(11, 3.4), sharey=False)
for ax, (key, sw) in zip(axs, SW):
    x = range(len(sw))
    ax.bar([i - 0.2 for i in x], [r["pre_cell_area"] for r in sw], 0.38, color=BLUE, label="sem scan")
    ax.bar([i + 0.2 for i in x], [r["post_cell_area"] for r in sw], 0.38, color=ORANGE, label="com scan")
    ax.set_xticks(list(x), [str(int(r[key])) for r in sw])
    ax.set_xlabel(key)
    ax.grid(axis="x", visible=False)
axs[0].set_ylabel("área de células (µm²)")
axs[0].legend(loc="upper left")
save(fig, "area_por_parametro.png")

# 2) curva de inserção: acréscimo de área x nº de flip-flops
pts = sorted(base, key=lambda r: r["post_g_sequential_inst"])
xs = [r["post_g_sequential_inst"] for r in pts]
ys = [r["post_cell_area"] - r["pre_cell_area"] for r in pts]
n = len(xs)
mx, my = sum(xs) / n, sum(ys) / n
a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
b = my - a * mx
fig, axs = plt.subplots(1, 2, figsize=(11, 3.6))
axs[0].plot([0, max(xs) * 1.05], [b, b + a * max(xs) * 1.05], color=MUTED, lw=1, ls="--",
            label=f"ajuste: Δ = {a:.2f}·N_FF {'+' if b >= 0 else '−'} {abs(b):.0f}")
axs[0].scatter(xs, ys, s=36, color=ORANGE, edgecolor="white", linewidth=1.5, zorder=3, label="rodadas")
axs[0].set_xlabel("flip-flops (N_FF)")
axs[0].set_ylabel("Δ área de células (µm²)")
axs[0].legend(loc="upper left")
axs[1].scatter(xs, [r["area_overhead_pct"] for r in pts], s=36, color=ORANGE, edgecolor="white", linewidth=1.5, zorder=3)
axs[1].set_xlabel("flip-flops (N_FF)")
axs[1].set_ylabel("acréscimo de área (%)")
axs[1].set_ylim(0, 25)
save(fig, "curva_insercao.png")

# 3) potência antes/depois
fig, axs = plt.subplots(1, 3, figsize=(11, 3.4))
for ax, (key, sw) in zip(axs, SW):
    x = range(len(sw))
    ax.bar([i - 0.2 for i in x], [r["pre_p_total"] for r in sw], 0.38, color=BLUE, label="sem scan")
    ax.bar([i + 0.2 for i in x], [r["post_p_total"] for r in sw], 0.38, color=ORANGE, label="com scan")
    ax.set_xticks(list(x), [str(int(r[key])) for r in sw])
    ax.set_xlabel(key)
    ax.grid(axis="x", visible=False)
axs[0].set_ylabel("potência total (mW)")
axs[0].legend(loc="upper left")
save(fig, "potencia_por_parametro.png")

# 4) falhas e testes por parâmetro (dois gráficos: escalas diferentes)
fig, axs = plt.subplots(2, 3, figsize=(11, 5.6))
for j, (key, sw) in enumerate(SW):
    labels = [str(int(r[key])) for r in sw]
    axs[0][j].bar(labels, [r["faults"] or 0 for r in sw], color=BLUE, width=0.6)
    axs[1][j].bar(labels, [r["seq_total"] or 0 for r in sw], color=AQUA, width=0.6)
    for i, r in enumerate(sw):
        axs[1][j].text(i, (r["seq_total"] or 0) + 2, f"{int(r['seq_total'])}", ha="center", fontsize=9, color=INK)
    axs[1][j].set_xlabel(key)
    for k in (0, 1):
        axs[k][j].grid(axis="x", visible=False)
axs[0][0].set_ylabel("falhas stuck-at")
axs[1][0].set_ylabel("testes gerados")
save(fig, "falhas_e_testes.png")

# 5) curvas de cobertura x testes, variando DEPTH
fig, ax = plt.subplots(figsize=(7.5, 3.8))
dep = [("D32_P2_W7", "DEPTH=2"), ("D32_P8_W7", "DEPTH=8"), ("D32_P32_W7", "DEPTH=32")]
for (tag, lab), col in zip(dep, (BLUE, ORANGE, AQUA)):
    c = [x for x in curves if x["tag"] == tag]
    t = [0] + [int(x["tests"]) for x in c]
    v = [0] + [float(x["global_cov"]) for x in c]
    ax.plot(t, v, color=col, lw=2, marker="o", ms=5, label=lab)
ax.set_xlabel("testes aplicados")
ax.set_ylabel("cobertura stuck-at (%)")
ax.set_ylim(0, 102)
ax.legend(loc="lower right")
save(fig, "cobertura_x_testes.png")

# 6) número de cadeias: ciclos de shift
ch = sorted([r for r in rows if r["DATA_W"] == 32 and r["DEPTH"] == 8 and r["WMAX"] == 7],
            key=lambda r: r["n_chains"])
fig, ax = plt.subplots(figsize=(6, 3.4))
cyc = [(r["seq_total"] + 1) * -(-r["scan_flops"] // r["n_chains"]) for r in ch]
ax.bar([str(int(r["n_chains"])) for r in ch], cyc, color=BLUE, width=0.6)
for i, c in enumerate(cyc):
    ax.text(i, c + 200, f"{int(c):,}".replace(",", "."), ha="center", fontsize=9, color=INK)
ax.set_xlabel("nº de cadeias de scan")
ax.set_ylabel("ciclos de shift (estimado)")
ax.grid(axis="x", visible=False)
save(fig, "cadeias_ciclos.png")

print(f"figuras em {FIG}  (ajuste linear: {a:.3f} µm²/FF, intercepto {b:.1f})")
