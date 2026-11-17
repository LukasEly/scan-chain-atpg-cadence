#!/usr/bin/env python3
"""
Coleta os resultados de todas as rodadas em runs/<TAG>/ e gera:
  results/results.csv           uma linha por configuração
  results/reports/<TAG>/...     cópia dos relatórios de área/potência/DFT/ATPG

Só usa a biblioteca padrão (roda no servidor do laboratório sem instalar nada).

Uso: python3 collect.py <dir_runs> <dir_results>
"""
import csv
import os
import re
import shutil
import sys

NUM = r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?"


def read(path):
    try:
        with open(path, errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def nums(line):
    return [float(x) for x in re.findall(NUM, line)]


def parse_params(txt):
    d = {}
    for line in txt.splitlines():
        if "=" in line:
            k, v = line.strip().split("=", 1)
            d[k] = int(v)
    return d


def parse_area(txt):
    """report_area: linha do design -> cell count, cell area, net area, total."""
    for line in txt.splitlines():
        if line.strip().startswith("stream_merge"):
            n = nums(line.split(None, 1)[1] if len(line.split()) > 1 else "")
            if len(n) >= 4:
                return {"cells": int(n[0]), "cell_area": n[1],
                        "net_area": n[2], "total_area": n[3]}
            if len(n) >= 2:
                return {"cells": int(n[0]), "cell_area": n[1]}
    return {}


def parse_gates(txt):
    """report_gates: tabela-resumo 'sequential / inverter / logic / total'."""
    out = {}
    for line in txt.splitlines():
        s = line.strip()
        for key in ("sequential", "inverter", "buffer", "logic", "total"):
            if s.startswith(key + " ") or s == key:
                n = nums(s[len(key):])
                if len(n) >= 2:
                    # prefixo "g_" para não colidir com total_area do report_area
                    out["g_" + key + "_inst"] = int(n[0])
                    out["g_" + key + "_area"] = n[1]
    return out


def parse_power(txt):
    """report_power (Genus 21): linha 'Subtotal' = leakage internal switching total.
    Formato antigo: linha do design com Leakage / Dynamic / Total (nW)."""
    for line in txt.splitlines():
        s = line.strip()
        if s.startswith("Subtotal"):
            n = nums(s)
            if len(n) >= 4:
                return {"p_leak": n[0], "p_int": n[1], "p_sw": n[2], "p_total": n[3]}
    for line in txt.splitlines():
        if line.strip().startswith("stream_merge"):
            n = nums(line.split(None, 1)[1])
            if len(n) >= 4:
                return {"p_leak": n[1], "p_dyn": n[2], "p_total": n[3]}
    return {}


def parse_chains(txt):
    """Soma o comprimento das cadeias (scan flops) e conta cadeias."""
    lengths = [int(x) for x in re.findall(r"length\s*[:=]?\s*(\d+)", txt, re.I)]
    if not lengths:
        lengths = [int(x) for x in re.findall(r"(\d+)\s+scan\s+(?:flops|registers|bits)", txt, re.I)]
    return {"n_chains": len(lengths), "scan_flops": sum(lengths)} if lengths else {}


def parse_modus(txt):
    """Última linha 'Total Static' da tabela de estatísticas do Modus:
    #Faults #Tested #Possibly #Redund #Untested %TCov %ATCov"""
    out = {}
    lines = [l for l in txt.splitlines() if re.search(r"Total\s+Static", l)]
    if lines:
        n = nums(lines[-1])
        if len(n) >= 7:
            out.update(faults=int(n[0]), tested=int(n[1]), possibly=int(n[2]),
                       redund=int(n[3]), untested=int(n[4]),
                       tcov=n[5], atcov=n[6])
        elif len(n) >= 2:
            out.update(faults=int(n[0]), tcov=n[-2], atcov=n[-1])
    # tabela "Final Pattern Statistics": Scan / Logic / Total (# Test Sequences)
    fps = txt.rfind("Final Pattern Statistics")
    if fps >= 0:
        block = txt[fps:fps + 1500]
        for key in ("Scan", "Logic", "Total"):
            m = re.search(r"^\s*" + key + r"\s+(\d+)\s*$", block, re.M)
            if m:
                out["seq_" + key.lower()] = int(m.group(1))
    return out


def parse_atpg_curve(txt):
    """Linhas de progresso do ATPG (TDA-220): #testes simulados x cobertura.
    Retorna lista de (fase, testes, cobertura%)."""
    curve, phase = [], ""
    for line in txt.splitlines():
        if "Starting Scan Test" in line:
            phase = "scan"
        elif "Starting Static Logic Test" in line:
            phase = "logic"
        m = re.search(r"TDA-220\):\s+(\d+)\s+(\d+)\s+(\d+)\s+([\d.]+)%\s+([\d.]+)%", line)
        if m:
            curve.append((phase, int(m.group(1)), float(m.group(5))))
    return curve


def main():
    runs_dir = sys.argv[1] if len(sys.argv) > 1 else "runs"
    res_dir = sys.argv[2] if len(sys.argv) > 2 else "results"
    os.makedirs(os.path.join(res_dir, "reports"), exist_ok=True)

    rows, curves = [], []
    for tag in sorted(os.listdir(runs_dir)):
        run = os.path.join(runs_dir, tag)
        rep = os.path.join(run, "reports")
        if not os.path.isdir(rep):
            continue
        row = {"tag": tag}
        row.update(parse_params(read(os.path.join(rep, "params.txt"))))
        for phase in ("pre", "post"):
            for parser, name in ((parse_area, "area"), (parse_gates, "gates"),
                                 (parse_power, "power")):
                d = parser(read(os.path.join(rep, f"{phase}_dft_{name}.txt")))
                row.update({f"{phase}_{k}": v for k, v in d.items()})
        row.update(parse_chains(read(os.path.join(rep, "dft_chains.txt"))))

        # O Modus roda com "-STDOUT summary": as estatísticas de cobertura ficam
        # nos logs internos de cada etapa (testresults/logs/log_<etapa>_...).
        logdir = os.path.join(run, "logs")
        mlogdir = os.path.join(run, "outputs", "dft", "modus_atpg", "testresults", "logs")
        modus_logs = []
        if os.path.isdir(mlogdir):
            modus_logs = [os.path.join(mlogdir, f) for f in sorted(os.listdir(mlogdir))]
        atpg_txt = "\n".join(read(p) for p in modus_logs
                             if os.path.basename(p).startswith("log_create_logic_tests"))
        row.update(parse_modus(atpg_txt or read(os.path.join(logdir, "modus_stdout.log"))))
        # curva cobertura x nº de testes (scan + logic acumulados)
        offset = 0
        for phase, n, cov in parse_atpg_curve(atpg_txt):
            if phase == "logic" and offset == 0:
                offset = row.get("seq_scan", 0)
            curves.append({"tag": tag, "phase": phase, "tests": n + offset, "global_cov": cov})

        # simulação dos padrões: procura erros/miscompares no log do xrun
        sim = read(os.path.join(logdir, "sim_stdout.log"))
        if sim:
            errs = len(re.findall(r"\*E,|miscompare|mismatch", sim, re.I))
            row["sim_errors"] = errs

        # overhead de área causado pelo scan
        if row.get("pre_cell_area") and row.get("post_cell_area"):
            row["area_overhead_pct"] = round(
                100.0 * (row["post_cell_area"] - row["pre_cell_area"]) / row["pre_cell_area"], 2)
        rows.append(row)

        # cópia dos relatórios (texto) para versionar no git
        dst = os.path.join(res_dir, "reports", tag)
        os.makedirs(dst, exist_ok=True)
        for f in os.listdir(rep):
            shutil.copy(os.path.join(rep, f), dst)
        for f in ("modus_stdout.log", "genus_stdout.log", "sim_stdout.log"):
            p = os.path.join(logdir, f)
            if os.path.isfile(p):
                shutil.copy(p, dst)
        # logs internos do Modus (sem o carimbo de data no nome)
        mdst = os.path.join(dst, "modus_logs")
        os.makedirs(mdst, exist_ok=True)
        for p in modus_logs:
            name = re.sub(r"_\d{12}-\d+$", "", os.path.basename(p))
            shutil.copy(p, os.path.join(mdst, name + ".txt"))

    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    out = os.path.join(res_dir, "results.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(res_dir, "atpg_curves.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["tag", "phase", "tests", "global_cov"])
        w.writeheader()
        w.writerows(curves)
    print(f"{len(rows)} rodadas -> {out}")
    for r in rows:
        print(f"  {r['tag']:<16} flops={r.get('post_g_sequential_inst','?'):>5} "
              f"area +{r.get('area_overhead_pct','?')}%  TCov={r.get('tcov','?')} "
              f"testes={r.get('seq_total','?')} sim_err={r.get('sim_errors','-')}")


if __name__ == "__main__":
    main()
