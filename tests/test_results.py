"""Die vorgerechnete Ergebnisdatei (data/hld_results.json): Aufbau, Zählungen, innere Stimmigkeit. Die Zahlen der README und der App rechnet tests/test_claims.py nach."""

import json

import pytest

import hld_constants as C
import hld_results as R


def test_aufbau_72_zellen_mit_allen_feldern():
    cs = R.cells()
    assert len(cs) == 72 and len({c["key"] for c in cs}) == 72
    for c in cs:
        assert set(c["cost"]) == set(C.RULES) and set(c["viol"]) == set(C.RULES) and set(c["util"]) == set(C.RULES) and set(c["delay"]) == set(C.RULES)
        assert set(c["levels"]) == set(C.LEVEL_KEYS_ALL) and {"T_V1", "T_V2", "Q_V1", "Q_V2"} == set(c["praxis"])
        assert c["runs"] == 30 and c["klass"] in ("F", "gleich", "sonst")
        assert c["lam"] in C.LAM_OPTIONS and c["ca2"] in C.CA2_OPTIONS and c["span"] in C.SPAN_OPTIONS and c["C"] in C.CAP_OPTIONS


def test_jede_einstellung_der_regler_hat_genau_eine_zelle():
    for lam in C.LAM_OPTIONS:
        for ca2 in C.CA2_OPTIONS:
            for span in C.SPAN_OPTIONS:
                for cap in C.CAP_OPTIONS:
                    c = R.cell_of(lam, ca2, span, cap)
                    assert (c["lam"], c["ca2"], c["span"], c["C"]) == (lam, ca2, span, cap)
    with pytest.raises(KeyError):
        R.cell_of(3.0, 1.0, "mittel", 16)


def test_klassen_53_f_19_frist_egal_und_keine_sonstigen():
    cc = R.class_counts()
    assert (cc["F"], cc["gleich"], cc["sonst"], cc["zellen"]) == (53, 19, 0, 72)
    assert len(R.z53()) == 53 and len(R.frist_egal()) == 19


def test_frist_egal_ist_das_kriterium_zwei_prozent_ueber_eins_durch_c():
    for c in R.cells():
        fills = all(c["cost"][r] <= C.FILL_FACTOR / c["C"] for r in ("Q", "T", "QT", "F"))
        assert (c["klass"] == "gleich") == fills, c["key"]


def test_kosten_liegen_zwischen_eins_durch_c_und_eins_und_f_zwischen_optimum_und_sofort():
    for c in R.cells():
        assert c["cost"]["S"] == pytest.approx(1.0, abs=1e-6)
        assert c["opt"]["cost"] <= c["cost"]["F"] + 1e-9 <= 1.0 + 1e-9
        assert c["cost"]["F"] >= 1.0 / c["C"] - 1e-9 and c["viol"]["F"] == 0 and c["viol"]["S"] == 0
        for r in C.RULES:
            assert 0.0 <= c["viol"][r] <= 1.0 and c["cost"][r] <= 1.0 + 1e-9


def test_a_gibt_es_nur_in_den_53_zellen_und_exakt_ist_eins():
    for c in R.cells():
        if c["klass"] == "F":
            assert c["A"]["exakt"] == 1.0 and set(c["A"]) == set(C.LEVEL_KEYS_ALL)
        else:
            assert c["A"] is None


def test_a_wird_aus_den_kosten_neu_gerechnet():
    for c in R.z53():
        den = c["cost"]["T"] - c["cost"]["F"]
        assert den > 0
        for level in C.LEVEL_KEYS_ALL:
            lv = c["levels"][level]
            want = 1.0 if level == "exakt" else ((c["cost"]["T"] - lv["cost"]) / den if lv["zulaessig"] else 0.0)
            assert c["A"][level] == pytest.approx(want, abs=2e-6 / max(den, 1e-3)), (c["key"], level)


def test_stufen_der_fristkenntnis_alle_zulaessig_und_grob_ist_fast_immer_die_abgestimmte_zeitregel():
    for c in R.cells():
        assert all(lv["zulaessig"] for lv in c["levels"].values())

    def gleich(cs):
        return [c for c in cs if abs(c["levels"]["grob"]["cost"] - c["cost"]["T"]) < 1e-6]
    # grob ist die Zeitregel mit T gleich dem unteren Rand der Spanne; sie weicht nur dort von der abgestimmten Regel ab, wo deren Parameter nicht der untere Rand ist
    assert len(gleich(R.z53())) == 52 and len(gleich(R.cells())) == 63
    rest = [c["key"] for c in R.z53() if c not in gleich(R.z53())]
    assert rest == ["lam=1|ca2=4|span=weit|C=8"]


def test_datei_ist_klein_genug_und_enthaelt_keine_rohdaten():
    path = R.DATA / "hld_results.json"
    assert path.stat().st_size < 150_000
    d = json.loads(path.read_text(encoding="utf-8"))
    assert set(d) == {"meta", "cells"} and "per_run" not in path.read_text(encoding="utf-8")


def test_formatierung_mit_komma_und_minuszeichen():
    assert R.num(1.26, 1) == "1,3"
    assert R.num(0.5, 2, True) == "+0,50" and R.sgn(-0.481) == "−0,48" and R.sgn(0.52) == "0,52"
    assert R.cell_text(R.cells()[0]).startswith("λ = ")
