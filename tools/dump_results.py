"""Erzeugt data/hld_results.json aus den Rohdaten der Vormessung (Abfahrtsregeln, 72 Zellen) und der Restmessung AP 0 (Stufen der Fristkenntnis, Praxisregeln).

Rohdaten liegen NICHT im Repo. Quellordner per Umgebungsvariable HLD_RAW_DIR (Standard: ../tourenplanung-planung neben dem Repo); darin:
  messreihe_holding/sweep_data.json
  messreihe_holding_ap0/sweep_a.jsonl, sweep_a2.jsonl, sweep_a2b.jsonl, sweep_b.jsonl

Aufruf:  python tools/dump_results.py           (schreibt data/hld_results.json und gibt Größe und Zählungen aus)
Alle Zahlen der App und der README kommen aus dieser Datei; tests/test_claims.py rechnet sie nach.
"""
import json
import math
import os
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent
RAW = pathlib.Path(os.environ.get("HLD_RAW_DIR", REPO.parent / "tourenplanung-planung"))
MAIN = RAW / "messreihe_holding"
AP0 = RAW / "messreihe_holding_ap0"
OUT = REPO / "data" / "hld_results.json"
RULES = ("S", "Q", "T", "QT", "F")
FILL_FACTOR = 1.02
VIOL_MESS = 0.01
DIGITS = 7


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def mean(xs):
    return sum(xs) / len(xs)


def r8(x):
    return None if x is None else round(x, DIGITS)


def cell_key(lam, ca2, span, cap):
    return f"lam={lam:g}|ca2={ca2:g}|span={span}|C={cap}"


def classify(v, rules=RULES):
    """Sieger, Gleichauf-Regeln und zulässige Regeln einer Zelle nach den Kriterien der Vormessung (zulässig: höchstens 1,0 % verspätet;
    gleichauf: Unterschied der gepaarten Kosten unter 2 Standardfehlern der Differenz über die 30 Läufe)."""
    mess = v["mess"]
    mc = {r: mean(mess[r]["cost"]) for r in RULES}
    viol = {r: mean(mess[r]["viol"]) for r in RULES}
    ok = [r for r in rules if viol[r] <= VIOL_MESS]
    win = min(ok, key=lambda r: mc[r])
    ties = []
    for r in ok:
        if r == win:
            continue
        diff = [a - b for a, b in zip(mess[r]["cost"], mess[win]["cost"])]
        m = mean(diff)
        sd = math.sqrt(sum((x - m) ** 2 for x in diff) / (len(diff) - 1))
        se = sd / math.sqrt(len(diff))
        if abs(m) < 2 * se or (sd == 0 and abs(m) < 1e-12):
            ties.append(r)
    return mc, viol, ok, win, ties


def main():
    base = json.loads((MAIN / "sweep_data.json").read_text(encoding="utf-8"))
    levels_by_cell = {}
    for fname in ("sweep_a.jsonl", "sweep_a2.jsonl", "sweep_a2b.jsonl"):
        for row in read_jsonl(AP0 / fname):
            k = cell_key(row["lam"], row["ca2"], row["span"], row["C"])
            for name, d in row["levels"].items():
                entry = {"m": r8(d["m"]), "cost": r8(d["cost"]), "viol": r8(d["viol"]), "zulaessig": bool(d["zulaessig"])}
                if not d["tune_feasible"]:
                    entry["tune_feasible"] = False
                levels_by_cell.setdefault(k, {})[name] = entry
    praxis_by_cell = {}
    for row in read_jsonl(AP0 / "sweep_b.jsonl"):
        for span, cells in row["cells"].items():
            k = cell_key(row["lam"], row["ca2"], span, row["C"])
            praxis_by_cell[k] = {name.replace("|", "_"): {"param": d["param"], "cost": r8(d["cost"]), "viol": r8(d["viol"]), "zulaessig": bool(d["zulaessig"])} for name, d in cells.items()}
    cells = []
    for k in sorted(base, key=lambda s: (base[s]["C"], base[s]["ca2"], base[s]["lam"], ["eng", "mittel", "weit"].index(base[s]["span"]))):
        v = base[k]
        mc, viol, ok, win, ties = classify(v)
        _mc, _viol, ok_b, win_b, ties_b = classify(v, ("S", "Q", "T", "QT"))   # Ampel B: ohne Fristkenntnis
        cap = v["C"]
        best_simple = min((r for r in ("Q", "T", "QT", "S") if r in ok), key=lambda r: mc[r])
        fills = all(mc[r] <= FILL_FACTOR / cap for r in ("Q", "T", "QT", "F"))
        klass = "gleich" if fills else ("F" if (win == "F" and not ties) else "sonst")
        levels = levels_by_cell[k]
        lv = {"exakt": {"m": 0.0, "cost": r8(mc["F"]), "viol": r8(viol["F"]), "zulaessig": True}}
        lv.update(levels)
        a_vals = None
        if klass == "F":
            den = mc["T"] - mc["F"]
            a_vals = {}
            for name, d in lv.items():
                if name == "exakt":
                    a_vals[name] = 1.0
                else:
                    a_vals[name] = r8((mc["T"] - d["cost"]) / den) if d["zulaessig"] else 0.0
        pr = praxis_by_cell[k]
        cells.append({
            "key": k, "lam": v["lam"], "ca2": v["ca2"], "span": v["span"], "C": cap,
            "params": v["params"],
            "cost": {r: r8(mc[r]) for r in RULES}, "viol": {r: r8(viol[r]) for r in RULES},
            "delay": {r: r8(mean(v["mess"][r]["delay"])) for r in RULES}, "util": {r: r8(mean(v["mess"][r]["util"])) for r in RULES},
            "opt": {"cost": r8(mean(v["opt"]["cost"])), "util": r8(mean(v["opt"]["util"]))},
            "ok": ok, "win": win, "ties": ties, "win_ohne_F": win_b, "ties_ohne_F": ties_b, "klass": klass, "best_simple": best_simple,
            "saving_F": r8(100.0 * (mc[best_simple] - mc["F"]) / mc[best_simple]),
            "levels": lv, "A": a_vals, "praxis": pr,
            "runs": len(v["mess"]["F"]["cost"]),
        })
    data = {
        "meta": {"quellen": ["messreihe_holding", "messreihe_holding_ap0"], "laeufe_je_zelle": 30, "zufalls_seeds_messung": "100000 bis 100029", "zufalls_seeds_abstimmung": "1000 bis 1029",
                 "ankuenfte_je_lauf": 2200, "fenster_ankuenfte": 1800},
        "cells": cells,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    n_f = sum(1 for c in cells if c["klass"] == "F")
    n_eq = sum(1 for c in cells if c["klass"] == "gleich")
    print(OUT, OUT.stat().st_size, "Bytes;", len(cells), "Zellen; F allein", n_f, "; Frist egal", n_eq)


if __name__ == "__main__":
    main()
