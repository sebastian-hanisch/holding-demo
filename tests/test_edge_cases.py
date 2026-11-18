"""Randfälle: alle Reglerränder, Zufalls-Seeds an den Rändern, leere und winzige Läufe, Nenner-0-Zweige, Reproduzierbarkeit."""

import math

import pytest

import hld_constants as C
import hld_evaluation as E
import hld_results as R
import hld_sim as S


def test_alle_72_zellen_laufen_mit_exakter_frist_und_f_ist_nie_verspaetet():
    for c in R.cells():
        an = E.analyse(E.Settings(c["lam"], c["ca2"], c["span"], c["C"], "exakt", 500001))
        assert an["rules"]["F"]["viol"] == 0.0 and an["rules"]["S"]["viol"] == 0.0
        assert an["opt"]["cost"] <= an["rules"]["F"]["cost"] + 1e-12 and an["rules"]["F"]["cost"] <= 1.0
        assert an["stage"]["cost"] == an["rules"]["F"]["cost"]


@pytest.mark.parametrize("wissen", C.WISSEN_OPTIONS)
def test_jede_stufe_an_den_reglerraendern(wissen):
    for lam in (C.LAM_OPTIONS[0], C.LAM_OPTIONS[-1]):
        for span in (C.SPAN_OPTIONS[0], C.SPAN_OPTIONS[-1]):
            for seed in (0, C.SEED_MAX):
                an = E.analyse(E.Settings(lam, C.CA2_OPTIONS[-1], span, C.CAP_OPTIONS[0], wissen, seed))
                assert math.isfinite(an["stage"]["cost"]) and 0.0 <= an["stage"]["viol"] <= 1.0 and 0.0 < an["stage"]["util"] <= 1.0


def test_gleicher_seed_gleiche_zahlen_und_anderer_seed_andere_zahlen():
    a1 = E.analyse(E.Settings(seed=12345, wissen="s25"))
    a2 = E.analyse(E.Settings(seed=12345, wissen="s25"))
    a3 = E.analyse(E.Settings(seed=12346, wissen="s25"))
    assert a1 == a2 and a1 != a3


def test_leerer_und_winziger_lauf():
    m = S.metrics(S.simulate([], [], 4, 1, S.INF, False), 4)
    assert math.isnan(m["cost"]) and m["trips"] == 0 and m["ships"] == 0
    a, dl = S.make_arrivals(1.0, 1.0, (1.0, 3.0), 1, 3)
    assert S.simulate(a, dl, 4, 1, S.INF, False)[:2] == (1, 1)
    assert S.simulate(a, dl, 4, 4, S.INF, False)[:2] == (0, 0)          # eine Sendung, Menge 4, keine Zeitgrenze: fährt nie
    assert S.simulate(a, dl, 4, 4, S.INF, True)[:2] == (1, 1)           # die Frist löst die Abfahrt aus
    assert len(S.optimum_departures(a, dl, 4)) == 1 and S.optimum_trips_dp(a, dl, 4) == 1
    assert S.optimum_departures([], [], 4) == []


def test_unbekannte_regel_und_unbekannte_stufe_werfen_fehler():
    with pytest.raises(ValueError):
        S.rule_params("X", 4)
    import hld_knowledge as K
    with pytest.raises(ValueError):
        K.estimate_deadlines([0.0], [2.0], "eng", "unbekannt", [0.0])


def test_kapazitaet_eins_macht_alle_regeln_gleich_sofort():
    a, dl = S.make_arrivals(2.0, 1.0, (1.0, 3.0), 400, 8)
    base = S.simulate(a, dl, 1, 1, S.INF, False)
    for rule, args in (("Q", (4, None)), ("T", (None, 2.0)), ("QT", (3, 2.0)), ("F", (None, None))):
        q, T, ud = S.rule_params(rule, 1, *args)
        assert S.simulate(a, dl, 1, q, T, ud)[:2] == base[:2], rule


def test_ausschnitt_der_zeitleiste_hat_so_viele_zeilen_wie_angefordert():
    st = E.Settings()
    a, dl, deps = E.trace_of(st, "stufe")
    rows = E.excerpt(a, dl, deps)
    assert len(rows) == C.EXCERPT_ARRIVALS and rows[0][0] == S.N_WARM
    assert all(r[3] is None or r[3] >= r[1] for r in rows)                 # keine Abfahrt vor der Ankunft
    assert all((r[3] is not None and r[3] > r[2]) == r[4] for r in rows)   # verspätet heißt: Abfahrt nach der Frist
