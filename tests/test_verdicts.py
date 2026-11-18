"""Verdikte (reine Funktionen in hld_evaluation.py) an handgesetzten Werten: Zustände, jede Zahl im Text, Nenner-0-Zweige."""

import copy

import hld_constants as C
import hld_evaluation as E
import hld_results as R


def _cell(klass):
    base = next(c for c in R.cells() if c["klass"] == klass) if klass != "sonst" else copy.deepcopy(R.cells()[0])
    c = copy.deepcopy(base)
    c["klass"] = klass
    return c


def test_zwei_zustaende_und_der_nie_vorkommende_dritte():
    kind, text = E.verdict_state(_cell("F"))
    assert kind == "success" and "Hier zählt die Frist" in text
    kind, text = E.verdict_state(_cell("gleich"))
    assert kind == "info" and "Hier ist die Frist egal" in text
    kind, text = E.verdict_state(_cell("sonst"))
    assert kind == "info" and "keine Regel klar" in text   # kommt in den 72 Zellen nicht vor, die Funktion fängt es trotzdem ab


def test_erste_meldung_nennt_informationsvorsprung_obergrenze_und_zahlen():
    c = R.cell_of(2.0, 1.0, "mittel", 16)
    _, text = E.verdict_state(c)
    assert "Informationsvorsprung" in text and "günstige Annahme" in text and "Zeitregel mit einem Parameter für alle Fristspannen" in text
    assert E.pct(c["saving_F"]) in text and E.pct(R.aufschlag(c, "T", "V2")) in text
    assert R.cell_text(c) in text and f"Mittel über {c['runs']} Läufe" in text
    for r in ("S", "Q", "T", "QT", "F"):
        assert E.fmt_cost(c["cost"][r]) in text
    assert E.fmt_cost(c["opt"]["cost"]) in text and "2 %" in text
    assert "über dem Optimum" in text   # Bezugsgröße des Abstands ist genannt


def test_frist_egal_meldung_nennt_ein_durch_c():
    c = R.cell_of(4.0, 1.0, "weit", 8)
    kind, text = E.verdict_state(c)
    assert kind == "info" and f"1/C = {E.fmt_cost(1.0 / 8)}" in text and "Hier ist die Frist egal" in text


def test_live_verdikt_nennt_alle_regeln_und_die_gewaehlte_stufe():
    an = E.analyse(E.Settings(wissen="s10"))
    kind, text = E.verdict_live(an)
    assert kind == "info" and "ein Lauf, kein Beleg" in text and "2200 Ankünfte" in text and "Ankunft Nr. 200 bis 2000" in text and "rund 1800 Sendungen" in text
    for r in ("S", "Q", "T", "QT", "F"):
        assert E.fmt_cost(an["rules"][r]["cost"]) in text
    assert E.fmt_cost(an["opt"]["cost"]) in text and E.fmt_cost(an["stage"]["cost"]) in text and C.WISSEN_LABELS["s10"] in text


def test_ladder_verdikt_je_stufe_und_ohne_a_in_den_frist_egal_zellen():
    c = R.cell_of(2.0, 1.0, "mittel", 16)
    for w in C.WISSEN_OPTIONS:
        kind, text = E.verdict_ladder(c, E.Settings(wissen=w))
        assert kind == "info" and text
        if w == "praxis":
            assert "Keine Kenntnis" in text and E.pct(R.aufschlag(c, "T", "V2")) in text
        elif w != "exakt":
            level = C.WISSEN_LEVEL[w]
            assert R.sgn(c["A"][level], 2) in text and E.fmt_cost(c["levels"][level]["cost"]) in text and R.sgn(R.ladder_row(level)["median"], 2) in text
    eg = R.cell_of(4.0, 1.0, "weit", 8)
    _, text = E.verdict_ladder(eg, E.Settings(wissen="s10"))
    assert "nur in den 53 Zellen" in text


def test_genauigkeitsleiter_nennt_jede_stufe_und_die_variante_ohne_klassenwissen():
    kind, text = E.verdict_ladder_overall()
    for level in C.LADDER_KEYS:
        assert C.LEVEL_LABELS[level] in text and R.sgn(R.ladder_row(level)["median"], 2) in text and E.pct(R.saving_vs_praxis(level)["median"]) in text
    assert R.sgn(R.ladder_row("verr25")["median"], 2) in text and "lohnt nur, wenn sie genau ist" in text and "53 Zellen" in text


def test_regeln_und_optimum_verdikt_zaehlungen():
    _, text = E.verdict_regeln()
    wc, wf = R.winner_counts(), R.without_f_winner()
    assert f"gewinnt F in {wc['allein']['F']} von 72 Zellen allein" in text and f"in {wf['T']} von 72 Zellen Sieger oder gleichauf" in text and f"Menge in {wf['Q']}" in text
    _, text = E.verdict_optimum()
    g = R.gap_to_opt("F")
    assert R.num(g["max"], 1) in text and f"über 1 % in {g['ueber_1']} Zellen" in text and "nicht bewiesen" in text


def test_nenner_null_zweige():
    assert E.pct(0.0) == "0,0 %" and E.late_text(0.0) == "0,00 %"
    c = _cell("F")
    c["cost"]["T"] = c["cost"]["F"]   # kein Vorteil: A hätte den Nenner 0; die Meldung rechnet nicht mit A, sondern mit den Kosten und bleibt ein Text
    kind, text = E.verdict_state(c)
    assert text
    # Praxis-Aufschlag mit Kosten 0 in der abgestimmten Regel gibt es in den Messdaten nicht; der Aufschlag ist dann undefiniert (Division durch 0) und nicht Teil der Meldung
    assert all(c["cost"]["T"] > 0 for c in R.cells())
