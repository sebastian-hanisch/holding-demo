"""Aussagen gegen Zählungen (DEMO-PLAYBOOK §11a): jede Zahl der README wird hier aus der Ergebnisdatei (data/hld_results.json) nachgerechnet und im Wortlaut der README gesucht.

Die Namen der Tests stehen in der letzten Spalte der Befundtabelle der README; ein Test dort ohne Funktion hier fällt in `test_jeder_genannte_test_existiert`."""

import re
import subprocess
import sys
from pathlib import Path

import pytest

import hld_constants as C
import hld_knowledge as K
import hld_results as R
import hld_sim as S

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")


def has(text):
    assert text in README, f"nicht in der README: {text!r}"


def n(x, d=1):
    return R.num(x, d)


def test_wer_gewinnt_mit_fristkenntnis():
    wc = R.winner_counts()
    assert wc["allein"] == {"S": 0, "Q": 0, "T": 0, "QT": 0, "F": 53}
    assert wc["sieger_oder_gleichauf"]["F"] == 68
    by_span, by_lam = R.f_sole_by("span"), R.f_sole_by("lam")
    assert by_span["eng"] == [24, 24] and by_span["mittel"] == [19, 24] and by_span["weit"] == [10, 24]
    assert [by_lam[lam] for lam in C.LAM_OPTIONS] == [[18, 18], [16, 18], [11, 18], [8, 18]]
    has("**F gewinnt in 53 von 72 Zellen allein** (Sieger oder gleichauf in 68)")
    has("nach Fristspanne eng 24 von 24, mittel 19 von 24, weit 10 von 24")
    has("nach Rate λ = 0,5 / 1 / 2 / 4: 18 / 16 / 11 / 8 von je 18")


def test_wer_gewinnt_ohne_fristkenntnis():
    wf = R.without_f_winner()
    assert wf == {"S": 2, "Q": 27, "T": 72, "QT": 72}
    qt = R.qt_vs_t()
    assert qt["max"] == pytest.approx(0.0, abs=1e-9) and qt["ueber_1"] == 0 and qt["schlechter"] == 0
    # QT hat in allen 72 Zellen exakt dieselben mittleren Kosten wie T (Mengenschwelle greift nie)
    assert R.qt_equals_t() == 72 and all(c["params"]["QT"]["T"] == c["params"]["T"]["T"] for c in R.cells())
    has("die **Zeitregel T ist in 72 von 72 Zellen Sieger oder gleichauf**, Menge-oder-Zeit in 72, die Menge in 27, sofort in 2")
    has("Menge-oder-Zeit hat mit den abgestimmten Parametern in allen 72 Zellen dieselben Kosten wie die Zeitregel; die Mengenschwelle greift nie")


def test_wann_ist_die_frist_egal():
    assert len(R.frist_egal()) == 19
    assert R.frist_egal_by("span") == {"mittel": 5, "weit": 14}
    assert R.frist_egal_by("lam") == {1.0: 2, 2.0: 7, 4.0: 10}
    has("**In 19 von 72 Zellen liegen Q, T, QT und F alle höchstens 2 % über 1/C**: Frist eng 0, mittel 5, weit 14; nach λ = 0,5 / 1 / 2 / 4: 0 / 2 / 7 / 10 Zellen")
    # „sofort“ kostet dort 1,000, also C-mal 1/C (8- bis 16-fach); die vier anderen Regeln liegen höchstens 2 % über 1/C
    for c in R.frist_egal():
        assert c["cost"]["S"] == pytest.approx(1.0) and all(c["cost"][r] <= 1.02 / c["C"] for r in ("Q", "T", "QT", "F")) and c["C"] in (8, 16)
    has("„sofort“ ist dort weiter 8- bis 16-mal so teuer (Kosten 1,000 gegen 1/C)")


def test_wert_der_fristkenntnis():
    f = R.saving_f()
    assert (n(f["median"]), n(f["min"]), n(f["max"])) == ("28,0", "0,7", "33,9") and f["zellen"] == 53
    has("**Median 28,0 %** (Minimum 0,7 %, Maximum 33,9 %;")
    sv = R.savings_vs_sofort_by_span()
    got = {k: " / ".join(n(sv[s][k], 0) for s in C.SPAN_OPTIONS) for k in ("Q", "T", "F", "opt")}
    assert got == {"Q": "20 / 57 / 84", "T": "57 / 82 / 89", "F": "69 / 86 / 90", "opt": "69 / 86 / 90"}
    has("Q 20 / 57 / 84 %, T 57 / 82 / 89 %, F 69 / 86 / 90 %, Optimum 69 / 86 / 90 %")


def test_naehe_zum_optimum():
    g, b = R.gap_to_opt("F"), R.gap_to_opt("best_simple")
    assert (n(g["median"]), n(g["q3"]), n(g["max"]), g["ueber_1"]) == ("0,0", "1,5", "6,6", 23)
    assert (n(b["median"]), n(b["max"])) == ("31,2", "51,4")
    has("F liegt im Median 0,0 % über dem Offline-Optimum (drittes Quartil 1,5 %, Maximum 6,6 %), in 23 von 72 Zellen mehr als 1 %")
    has("die beste zulässige einfache Regel im Median 31,2 % (Maximum 51,4 %)")
    # Grenzen: zwei Zellen mit einer zulässigen einfachen Regel unter dem Optimum, höchstens 0,03 % darunter
    below = [c for c in R.cells() if c["cost"][c["best_simple"]] < c["opt"]["cost"] - 1e-12]
    assert len(below) == 2 and max(100.0 * (c["opt"]["cost"] - c["cost"][c["best_simple"]]) / c["opt"]["cost"] for c in below) <= 0.03
    has("zwei Zellen haben eine zulässige einfache Regel bis 0,03 % unter dem Optimum")


def test_mengenregel_versagt():
    q = R.q_equals_s()
    assert q["zellen"] == 22 and q["span"] == {"eng": 16, "mittel": 6} and q["ca2"] == {0.0: 2, 1.0: 8, 4.0: 12} and q["lam"] == {0.5: 10, 1.0: 6, 2.0: 4, 4.0: 2}
    assert R.t_equals_s() == 2
    has("**Q ist in 22 von 72 Zellen gleich „sofort“**")
    has("Frist eng 16, mittel 6, weit 0; ca² = 0 / 1 / 4: 2 / 8 / 12; λ = 0,5 / 1 / 2 / 4: 10 / 6 / 4 / 2")
    has("Die Zeitregel T ist nur in 2 von 72 Zellen gleich „sofort“")


def test_zeitregel_bei_stossweisen_ankuenften():
    ub = R.util_by_ca2()
    assert " / ".join(n(ub[k]["util"]) for k in C.CA2_OPTIONS) == "59,4 / 58,6 / 62,6"
    assert " / ".join(n(ub[k]["saving"]) for k in C.CA2_OPTIONS) == "73,3 / 75,8 / 79,5"
    has("mittlere Auslastung von T bei ca² = 0 / 1 / 4: 59,4 / 58,6 / 62,6 %, mittlere Ersparnis gegen „sofort“ 73,3 / 75,8 / 79,5 %")


def test_genauigkeitsleiter():
    keys = ("exakt", "verr05_kl", "verr10_kl", "grob", "verr25_kl", "verr50_kl")
    rows = {k: R.ladder_row(k) for k in keys}
    assert [R.sgn(rows[k]["median"], 2) for k in keys] == ["1,00", "0,78", "0,52", "0,00", "−0,48", "−2,07"]
    assert [rows[k]["ab_05"] for k in keys] == [53, 51, 34, 0, 3, 3]
    assert [sum(1 for c in R.z53() if c["A"][k] > 0.001) for k in ("verr05_kl", "verr10_kl", "verr25_kl", "verr50_kl")] == [53, 51, 9, 3]
    assert [n(rows[k]["kosten"], 4) for k in keys] == ["0,2093", "0,2276", "0,2487", "0,2868", "0,3314", "0,4424"]
    assert all(rows[k]["unzulaessig"] == 0 for k in keys)
    has("exakt 1,00; **Schätzfehler 5 %: 0,78**; **10 %: 0,52**; nur die Fristklasse 0,00; **25 %: −0,48**; 50 %: −2,07")
    has("A ≥ 0,5 in 53 / 51 / 34 / 0 / 3 / 3 Zellen (in dieser Reihenfolge)")
    has("in 53 / 51 / 9 / 3 Zellen billiger als die abgestimmte Zeitregel (A über 0,001)")
    has("Mittlere Kosten je Sendung (Z53): 0,2093 / 0,2276 / 0,2487 / 0,2868 / 0,3314 / 0,4424")


def test_urteil_der_vorab_festgelegten_variante():
    r = R.ladder_row("verr25")
    assert R.sgn(r["median"], 2) == "−1,03" and sum(1 for c in R.z53() if c["A"]["verr25"] < 0) == 49 and r["ab_05"] == 0
    assert R.sgn(R.ladder_row("verr25_kl")["median"], 2) == "−0,48"
    # Schwelle der Restmessung: „lohnt nur, wenn genau“ bei Median A höchstens 0,5
    assert r["median"] <= 0.5
    has("Median A = −1,03, F in 49 von 53 Zellen teurer als die abgestimmte Zeitregel; Urteil **„Fristkenntnis lohnt nur, wenn sie genau ist“**")
    has("(Median A = −0,48, nur Vergleich)")


def test_gegen_eine_praxisregel():
    got = {k: n(R.saving_vs_praxis(k)["median"]) for k in ("exakt", "verr05_kl", "verr10_kl", "grob", "verr25_kl", "verr25")}
    assert got == {"exakt": "62,1", "verr05_kl": "61,8", "verr10_kl": "59,6", "grob": "49,9", "verr25_kl": "47,7", "verr25": "38,3"}
    has("exakt 62,1 %, Schätzfehler 5 % 61,8 %, 10 % 59,6 %, nur die Fristklasse 49,9 %, 25 % 47,7 % (Variante ohne Klassenwissen: 38,3 %)")


def test_praxisregel():
    v1, v2 = R.praxis_stats("T", "V1"), R.praxis_stats("T", "V2")
    assert (v1["zellen"], v1["unzulaessig"], n(v1["aufschlag"])) == (48, 24, "64,1") and R.praxis_unzulaessig_by_span("T", "V1") == {"eng": [24, 24], "weit": [0, 24]}
    assert (v2["zellen"], v2["unzulaessig"], n(v2["aufschlag"])) == (72, 0, "147,4")
    assert [n(v2["nach_spanne"][s]) for s in C.SPAN_OPTIONS] == ["0,0", "140,7", "301,4"]
    has("**in 24 von 48 Zellen unzulässig** (Frist eng 24 von 24, weit 0 von 24); in den zulässigen Zellen (weit) kostet sie im Mittel 64,1 % mehr")
    has("in allen 72 Zellen zulässig und kostet im Mittel 147,4 % mehr (Frist eng 0,0 %, mittel 140,7 %, weit 301,4 %)")
    # Schwelle „Obergrenze zu optimistisch“: mehr als 25 % der 48 Zellen unzulässig (12) oder Aufschlag über 15 %
    assert v1["unzulaessig"] > 12 or v1["aufschlag"] > 15
    # Q (ohne Urteil)
    q1 = R.praxis_stats("Q", "V1")
    assert (q1["zellen"], q1["unzulaessig"]) == (48, 18)


def test_reihenfolge_der_stufen():
    mean_cost = {k: R.ladder_row(k)["kosten"] for k in ("exakt", "verr05_kl", "verr10_kl", "verr25_kl", "verr50_kl", "grob")}
    assert mean_cost["exakt"] <= mean_cost["verr05_kl"] <= mean_cost["verr10_kl"] <= mean_cost["verr25_kl"] <= mean_cost["verr50_kl"]
    assert mean_cost["verr10_kl"] < mean_cost["grob"] < mean_cost["verr25_kl"]
    z = R.z53()
    assert sum(1 for c in z if c["levels"]["verr25_kl"]["cost"] > c["levels"]["grob"]["cost"] + 1e-9) == 42
    assert sum(1 for c in z if c["levels"]["verr50_kl"]["cost"] > c["levels"]["grob"]["cost"] + 1e-9) == 47
    has("Kosten(25 %) > Kosten(nur die Fristklasse) in 42 und Kosten(50 %) > Kosten(nur die Fristklasse) in 47 von 53 Zellen")
    has("Die Kette Kosten(exakt) ≤ Kosten(5 %) ≤ Kosten(10 %) ≤ Kosten(25 %) ≤ Kosten(50 %) gilt im Mittel über Z53")


def test_nur_die_fristklasse_ist_die_abgestimmte_zeitregel_bis_auf_eine_zelle():
    z = R.z53()
    gleich = [c for c in z if abs(c["levels"]["grob"]["cost"] - c["cost"]["T"]) < 1e-6]
    assert len(gleich) == 52
    rest = [c for c in z if c not in gleich]
    assert [(c["lam"], c["ca2"], c["span"], c["C"], c["params"]["T"]["T"]) for c in rest] == [(1.0, 4.0, "weit", 8, 16.0)]
    has("in 52 von 53 Zellen (Z53) gleich denen der abgestimmten Zeitregel, die einzige Ausnahme ist λ = 1, ca² = 4, Frist weit, C = 8 (abgestimmtes T = 16)")


def test_die_meldung_stuetzt_sich_auf_die_zelle():
    import hld_evaluation as E
    for name, p in C.PRESETS.items():
        cell = R.cell_of(p["lam"], p["ca2"], p["span"], p["cap"])
        _, text = E.verdict_state(cell)
        assert R.cell_text(cell) in text and f"Mittel über {cell['runs']} Läufe" in text, name
    has("die Meldungen der App stützen sich auf das Zellmittel, nicht auf den einen Lauf")


def test_standardzelle_und_zustaende_im_abschnitt_korrekturen():
    c = R.cell_of(2.0, 1.0, "mittel", 16)
    assert n(c["saving_F"]) == "28,7" and n(R.saving_f()["median"]) == "28,0"
    c1 = R.cell_of(1.0, 1.0, "mittel", 16)
    assert n(c1["saving_F"]) == "33,9" and n(max(x["saving_F"] for x in R.z53())) == "33,9"
    # eine der Zellen mit dem größten F-Vorteil, nicht die einzige: 33,901 % gegen 33,948 % in zwei anderen Zellen
    assert n(c1["saving_F"], 3) == "33,901" and n(max(x["saving_F"] for x in R.z53()), 3) == "33,948" and c1["saving_F"] < max(x["saving_F"] for x in R.z53())
    assert R.class_counts()["sonst"] == 0
    has("eine der Zellen mit dem größten F-Vorteil (33,9 %; Maximum 33,9 %)")
    has("Der Standard ist λ = 2, ca² = 1, Frist mittel, C = 16 mit 28,7 % Ersparnis, nahe am Median (28,0 %)")


def test_frist_zaehlt_heisst_nur_abstand_zu_eins_durch_c():
    """Das Beispiel der README: Zelle λ = 1, ca² = 4, Frist weit, C = 8 wird als „Frist zählt“ gemeldet bei nur 0,73 % Ersparnis."""
    c = R.cell_of(1.0, 4.0, "weit", 8)
    assert c["klass"] == "F" and n(c["saving_F"], 2) == "0,73"
    assert c["cost"]["T"] > 1.02 / 8  # nicht alle vier Regeln höchstens 2 % über 1/C (T liegt 2,4 % darüber, F 1,7 %)
    has("Beispiel λ = 1, ca² = 4, Frist weit, C = 8: Ersparnis von F gegenüber der besten einfachen Regel 0,73 %")


def test_grenzen_nach_der_aussagenpruefung_im_wortlaut():
    """Die vom unabhängigen Prüfer verlangten Einschränkungen stehen im Wortlaut in der README; die Zahlen des Prüfer-Neulaufs sind als solche gekennzeichnet (nicht Teil der Messreihe, hier nicht nachgerechnet)."""
    has("Prüfer-Neulauf, nicht Teil der Messreihe: mit einem feineren Raster, T mit 68 Werten, gewinnt F in 52 statt 53 Zellen allein")
    has("ein kleineres m wäre in vielen Fällen noch zulässig, 120 von 279 Prüfungen")
    has("Deshalb ist A = 0 in 52 der 53 Zellen (in der Ausnahme −4,17)")
    has("ausgewertet werden die Abfahrten im Fenster von Ankunft Nr. 200 bis 2 000 (rund 1 800 Sendungen")
    has("von Ralfs, Kiesmüller (2022, OR Spectrum) wurde nur der Titel gefunden")
    has("auf Windows (MSVC) und im Linux-Docker-Lauf gleich; weitere Plattformen sind nicht nachgerechnet")
    assert S.N_WARM == 200 and S.N_WARM + S.N_EVAL == 2000
    ex = R.cell_of(1.0, 4.0, "weit", 8)
    assert ex["params"]["T"]["T"] == 16.0 and abs(ex["levels"]["grob"]["cost"] - ex["cost"]["T"]) > 1e-6
    assert round(100 * (ex["cost"]["T"] - ex["levels"]["grob"]["cost"]) / (ex["cost"]["T"] - ex["cost"]["F"]), 2) == -4.17 or round(ex["A"]["grob"], 2) == -4.17


def test_claim_neu_rechnen_als_band():
    """Zwei Zellen (ca² = 1 und ca² = 4) werden mit den Zufalls-Seeds 100000 bis 100029 neu gerechnet; die mittleren Kosten liegen im Band um die Ergebnisdatei
    (Band statt Gleichheit: der Logarithmus der Ziehungen ist plattformfest, aber die Vormessung rechnete mit `math.log`, die Rundung der Datei ist 7 Stellen)."""
    for lam, ca2, span, cap in ((2.0, 1.0, "mittel", 16), (1.0, 4.0, "eng", 16)):
        cell = R.cell_of(lam, ca2, span, cap)
        sums = {r: 0.0 for r in C.RULES}
        for seed in range(C.MESS_SEEDS[0], C.MESS_SEEDS[1] + 1):
            a, dl = S.make_arrivals(lam, ca2, C.SPANS[span], S.N_TOTAL, seed)
            t_lo, t_hi = S.window(a)
            for r in C.RULES:
                p = cell["params"][r]
                qq, TT, ud = S.rule_params(r, cap, p.get("q"), p.get("T"))
                sums[r] += S.metrics(S.simulate(a, dl, cap, qq, TT, ud, t_lo, t_hi), cap)["cost"]
        for r in C.RULES:
            assert sums[r] / 30 == pytest.approx(cell["cost"][r], abs=1e-4), (cell["key"], r)
    # und eine Stufe der Fristkenntnis (nur die Fristklasse, ohne Rauschen)
    cell = R.cell_of(2.0, 1.0, "mittel", 16)
    tot = 0.0
    for seed in range(C.MESS_SEEDS[0], C.MESS_SEEDS[1] + 1):
        a, dl = S.make_arrivals(2.0, 1.0, C.SPANS["mittel"], S.N_TOTAL, seed)
        out = K.run_est(a, dl, "mittel", "grob", 16, cell["levels"]["grob"]["m"], [0.0] * len(a))
        tot += out["cost"]
    assert tot / 30 == pytest.approx(cell["levels"]["grob"]["cost"], abs=1e-4)


def test_readme_nennt_die_testzahl_und_jeder_genannte_test_existiert():
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")], capture_output=True, text=True, cwd=ROOT).stdout
    m = re.search(r"(\d+) tests? collected", out)
    assert m, out[-300:]
    assert f"{m.group(1)} Tests (`pytest --collect-only -q tests`)" in README
    me = Path(__file__).read_text(encoding="utf-8")
    for name in re.findall(r"\| `(test_[a-z_0-9]+)` \|", README):
        assert f"def {name}(" in me, name


def test_readme_ohne_umgebungsaussagen_und_verbotene_woerter():
    for wort in ("läuft lokal", "Saatwert", " trägt ", " tragen ", "Seed ", "TODO nach dem Deploy: direkt hierher den Live-Link setzen"):
        if wort.startswith("TODO"):
            continue
        if wort == "Seed ":
            assert not re.search(r"(?<!Zufalls-)Seed ", README), wort
        else:
            assert wort not in README, wort
    assert "Zufalls-Seed" in README


def test_literatur_nur_als_abstract_gekennzeichnet():
    has("Nur Zusammenfassungen gelesen")
    has("nichts davon ist hier als neu oder bestätigt bezeichnet")
