"""Laden und Auswerten der vorgerechneten Messreihe (data/hld_results.json, erzeugt von tools/dump_results.py).

Alle Zahlen der App stammen aus dieser Datei (`tests/test_claims.py` rechnet sie nach):
  cells  72 Zellen der Vormessung (4 Raten × 3 Streuungen × 3 Fristspannen × 2 Kapazitäten), je 30 Läufe (Zufalls-Seeds 100000 bis 100029), mit
         - Kosten, Wartezeit, Verspätung und Auslastung je Regel (S, Q, T, QT, F) und dem Offline-Optimum,
         - Sieger, Gleichauf-Regeln und Klasse („F“: F gewinnt allein; „gleich“: Q, T, QT und F liegen alle höchstens 2 % über 1/C),
         - den Stufen der Fristkenntnis der Restmessung AP 0 (Kosten, Verspätung, Sicherheitsabstand m, Zulässigkeit),
         - dem Anteil A des F-Vorteils gegenüber der abgestimmten Regel T (nur in den 53 Zellen der Klasse „F“),
         - den Praxisregeln T und Q ohne Kenntnis der Fristverteilung (V1: auf „mittel“ abgestimmt, V2: auf die Mischung der drei Spannen).
"""

import json
import pathlib
from functools import lru_cache

import hld_constants as C

DATA = pathlib.Path(__file__).resolve().parent / "data"


@lru_cache(maxsize=1)
def load():
    return json.loads((DATA / "hld_results.json").read_text(encoding="utf-8"))


def cells():
    return load()["cells"]


def cell_of(lam, ca2, span, cap):
    """Die gemessene Zelle zu einer Einstellung (alle Regler stehen auf gemessenen Stufen, also gibt es immer genau eine)."""
    for c in cells():
        if abs(c["lam"] - lam) < 1e-9 and abs(c["ca2"] - ca2) < 1e-9 and c["span"] == span and c["C"] == cap:
            return c
    raise KeyError((lam, ca2, span, cap))


def z53():
    """Die 53 Zellen, in denen F in der Vormessung allein Sieger war (Klasse „F“)."""
    return [c for c in cells() if c["klass"] == "F"]


def frist_egal():
    """Die 19 Zellen, in denen Q, T, QT und F alle höchstens 2 % über 1/C liegen (das Fahrzeug füllt sich fast immer vor der Frist; Deutung)."""
    return [c for c in cells() if c["klass"] == "gleich"]


def median(xs):
    xs = sorted(xs)
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def mean(xs):
    xs = list(xs)
    return sum(xs) / len(xs)


# ------------------------------------------------------------------------------------------------ Zählungen

def class_counts():
    cs = cells()
    return {"F": sum(1 for c in cs if c["klass"] == "F"), "gleich": sum(1 for c in cs if c["klass"] == "gleich"), "sonst": sum(1 for c in cs if c["klass"] == "sonst"), "zellen": len(cs)}


def frist_egal_by(key):
    """Zahl der Zellen „Frist egal“ nach Fristspanne ('span'), Rate ('lam') oder Streuung ('ca2')."""
    out = {}
    for c in frist_egal():
        out[c[key]] = out.get(c[key], 0) + 1
    return out


def f_sole_by(key):
    """Zahl der Zellen mit F als alleinigem Sieger nach Stufe des Faktors `key` und Zahl der Zellen dieser Stufe."""
    out = {}
    for c in cells():
        e = out.setdefault(c[key], [0, 0])
        e[1] += 1
        if c["klass"] == "F":
            e[0] += 1
    return out


def winner_counts():
    """Zellen, in denen die Regel Sieger oder gleichauf ist, und Zellen mit alleinigem Sieg."""
    cs = cells()
    inw = {r: sum(1 for c in cs if r == c["win"] or r in c["ties"]) for r in C.RULES}
    sole = {r: sum(1 for c in cs if c["win"] == r and not c["ties"]) for r in C.RULES}
    return {"sieger_oder_gleichauf": inw, "allein": sole}


def without_f_winner():
    """Ohne Fristkenntnis (nur S, Q, T, QT; Ampel B der Vormessung): Zellen, in denen die Regel Sieger oder gleichauf ist (gleichauf: Unterschied der gepaarten Kosten unter 2 Standardfehlern)."""
    out = {r: 0 for r in ("S", "Q", "T", "QT")}
    for c in cells():
        for r in [c["win_ohne_F"]] + list(c["ties_ohne_F"]):
            out[r] += 1
    return out


def q_equals_s():
    """Zellen, in denen die Mengenregel Q nach der Abstimmung gleich „sofort“ ist (Kosten 1,000) und ihre Verteilung nach Frist, Streuung und Rate."""
    zs = [c for c in cells() if c["cost"]["Q"] >= 1.0 - 1e-9]
    by = {k: {} for k in ("span", "ca2", "lam")}
    for c in zs:
        for k in by:
            by[k][c[k]] = by[k].get(c[k], 0) + 1
    return {"zellen": len(zs), **by}


def t_equals_s():
    return sum(1 for c in cells() if c["cost"]["T"] >= 1.0 - 1e-9)


def qt_vs_t():
    """Größte relative Ersparnis von QT gegenüber T über die 72 Zellen (Prozent) und Zahl der Zellen mit Unterschied über 1 %."""
    rel = [100.0 * (c["cost"]["T"] - c["cost"]["QT"]) / c["cost"]["T"] for c in cells()]
    return {"max": max(rel), "min": min(rel), "ueber_1": sum(1 for r in rel if r > 1.0), "schlechter": sum(1 for r in rel if r < -1e-9)}


def qt_equals_t():
    """Zahl der Zellen, in denen Menge-oder-Zeit mit den abgestimmten Parametern dieselben mittleren Kosten hat wie die Zeitregel (Mengenschwelle greift nie)."""
    return sum(1 for c in cells() if abs(c["cost"]["QT"] - c["cost"]["T"]) < 1e-12)


def saving_f():
    """Ersparnis von F gegenüber der besten einfachen Regel in den 53 Zellen mit F als Sieger (Prozent): Median, Minimum, Maximum."""
    xs = [c["saving_F"] for c in z53()]
    return {"median": median(xs), "min": min(xs), "max": max(xs), "zellen": len(xs)}


def savings_vs_sofort_by_span():
    """Mittlere Ersparnis gegen „sofort“ (Prozent) je Fristspanne für Q, T, F und das Optimum (Mittel über die Zellen der Spanne)."""
    out = {}
    for span in C.SPAN_OPTIONS:
        cs = [c for c in cells() if c["span"] == span]
        out[span] = {r: mean(100.0 * (1.0 - c["cost"][r]) for c in cs) for r in ("Q", "T", "F")}
        out[span]["opt"] = mean(100.0 * (1.0 - c["opt"]["cost"]) for c in cs)
        out[span]["zellen"] = len(cs)
    return out


def saving_by_lam():
    """Mittlere Ersparnis gegen „sofort“ (Prozent) je Rate λ für Q, T, F und das Optimum."""
    out = {}
    for lam in C.LAM_OPTIONS:
        cs = [c for c in cells() if abs(c["lam"] - lam) < 1e-9]
        out[lam] = {r: mean(100.0 * (1.0 - c["cost"][r]) for c in cs) for r in ("Q", "T", "F")}
        out[lam]["opt"] = mean(100.0 * (1.0 - c["opt"]["cost"]) for c in cs)
    return out


def util_by_ca2():
    """Mittlere Auslastung und mittlere Ersparnis gegen „sofort“ der Zeitregel T je Streuung ca² (Prozent)."""
    out = {}
    for ca2 in C.CA2_OPTIONS:
        cs = [c for c in cells() if abs(c["ca2"] - ca2) < 1e-9]
        out[ca2] = {"util": 100.0 * mean(c["util"]["T"] for c in cs), "saving": mean(100.0 * (1.0 - c["cost"]["T"]) for c in cs), "zellen": len(cs)}
    return out


def gap_to_opt(rule="F"):
    """Abstand (Kosten − Optimum) / Optimum in Prozent über die 72 Zellen: Median, drittes Quartil, Maximum, Zahl der Zellen über 1 % und die größten drei Zellen."""
    if rule == "best_simple":
        gs = [(100.0 * (c["cost"][c["best_simple"]] - c["opt"]["cost"]) / c["opt"]["cost"], c) for c in cells()]
    else:
        gs = [(100.0 * (c["cost"][rule] - c["opt"]["cost"]) / c["opt"]["cost"], c) for c in cells()]
    vals = sorted(g for g, _ in gs)
    n = len(vals)
    q3 = vals[int(0.75 * n)]
    top = sorted(gs, key=lambda t: -t[0])[:3]
    return {"median": median(vals), "q3": q3, "max": vals[-1], "ueber_1": sum(1 for v in vals if v > 1.0), "top3": [(g, c) for g, c in top], "min": vals[0]}


# ------------------------------------------------------------------------------------------------ Stufen der Fristkenntnis

def ladder_row(level):
    """Kennzahlen einer Stufe über die 53 Zellen mit F als Sieger: Median von A, Zahl der Zellen mit A ≥ 0,5, mittlere Kosten, Zahl unzulässiger Zellen, Zahl der Zellen mit A > 0."""
    zs = z53()
    a = [c["A"][level] for c in zs]
    return {"median": median(a), "ab_05": sum(1 for x in a if x >= 0.5), "ab_08": sum(1 for x in a if x >= 0.8), "positiv": sum(1 for x in a if x > 0),
            "kosten": mean(c["levels"][level]["cost"] for c in zs), "unzulaessig": sum(1 for c in zs if not c["levels"][level]["zulaessig"]), "min": min(a), "max": max(a), "zellen": len(zs)}


def saving_vs_praxis(level):
    """Ersparnis der Regel F mit der Stufe `level` gegenüber der Praxisregel T (V2) in Prozent über die 53 Zellen mit F als Sieger: Median und Zahl der Zellen mit positiver Ersparnis."""
    xs = [100.0 * (c["praxis"]["T_V2"]["cost"] - c["levels"][level]["cost"]) / c["praxis"]["T_V2"]["cost"] for c in z53()]
    return {"median": median(xs), "positiv": sum(1 for x in xs if x > 0), "min": min(xs), "max": max(xs), "zellen": len(xs)}


def praxis_stats(rule="T", variant="V2"):
    """Praxisregel T oder Q: Zahl der Zellen, Zahl unzulässiger Zellen, mittlerer Kostenaufschlag gegen die auf die Zelle abgestimmte Regel (Prozent, Mittel über die zulässigen Zellen)
    und nach Fristspanne. V1 (auf „mittel“ abgestimmt) zählt nur die Zellen eng und weit (die Zellen „mittel“ sind dort gleich der Vormessung)."""
    key = f"{rule}_{variant}"
    cs = [c for c in cells() if key in c["praxis"] and not (variant == "V1" and c["span"] == "mittel")]
    zul = [c for c in cs if c["praxis"][key]["zulaessig"]]
    by = {}
    for span in C.SPAN_OPTIONS:
        sub = [c for c in zul if c["span"] == span]
        if sub:
            by[span] = mean(100.0 * (c["praxis"][key]["cost"] / c["cost"][rule] - 1.0) for c in sub)
    return {"zellen": len(cs), "unzulaessig": len(cs) - len(zul),
            "aufschlag": mean(100.0 * (c["praxis"][key]["cost"] / c["cost"][rule] - 1.0) for c in zul) if zul else None,
            "median": median([100.0 * (c["praxis"][key]["cost"] / c["cost"][rule] - 1.0) for c in zul]) if zul else None, "nach_spanne": by}


def praxis_unzulaessig_by_span(rule="T", variant="V1"):
    key = f"{rule}_{variant}"
    out = {}
    for c in cells():
        if key in c["praxis"] and not (variant == "V1" and c["span"] == "mittel"):
            e = out.setdefault(c["span"], [0, 0])
            e[1] += 1
            if not c["praxis"][key]["zulaessig"]:
                e[0] += 1
    return out


def aufschlag(cell, rule="T", variant="V2"):
    """Kostenaufschlag der Praxisregel in Prozent gegen die auf die Zelle abgestimmte Regel dieser Zelle."""
    return 100.0 * (cell["praxis"][f"{rule}_{variant}"]["cost"] / cell["cost"][rule] - 1.0)


# ------------------------------------------------------------------------------------------------ Formatierung

def num(x, digits=1, sign=False):
    return (f"{x:+.{digits}f}" if sign else f"{x:.{digits}f}").replace(".", ",")


def sgn(x, digits=2):
    """Zahl mit echtem Minuszeichen (U+2212) bei negativen Werten, ohne Plus bei positiven, mit Dezimalkomma."""
    return num(x, digits).replace("-", "−")


def lam_text(lam):
    return num(lam, 1)


def cell_text(cell):
    """Beschreibung einer Zelle in Worten (Rate, Streuung, Frist, Kapazität)."""
    return (f"λ = {lam_text(cell['lam'])} Sendungen je Fahrzeugzeit, {C.CA2_TEXT[cell['ca2']]} (ca² = {num(cell['ca2'], 0)}), Frist {cell['span']}, "
            f"Kapazität {cell['C']}")


def cell_short(cell):
    """Kurzbeschreibung einer Zelle: λ, ca², Frist, Kapazität."""
    return f"λ = {lam_text(cell['lam'])}, ca² = {num(cell['ca2'], 0)}, Frist {cell['span']}, C = {cell['C']}"
