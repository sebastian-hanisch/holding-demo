"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jedes Preset, fährt jeden Regler an seine Stufen und
prüft, dass kein Python-Fehler auftritt (insbesondere `StreamlitDuplicateElementId` bei Charts mit gleichem Inhalt). Keine Zeit-Assertions."""

import os
import re

import pytest
from streamlit.testing.v1 import AppTest

import hld_constants as C
import hld_results as R

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [w.value for w in list(at.info) + list(at.success) + list(at.warning)]


def _first(at):
    return next(t for t in _texts(at) if t.startswith("**Hier "))


def test_app_loads_without_exception_and_shows_the_three_expanders():
    at = _fresh_app()
    labels = [e.label for e in at.expander]
    assert "🔧 Wie wir das erreichen – vollständiger Methodenvergleich" in labels
    assert "Wie funktioniert diese Demo?" in labels and "📐 Mathematische Formulierung" in labels
    assert _first(at).startswith("**Hier zählt die Frist.**")
    assert [m.label for m in at.metric] == ["Kosten je Sendung (gewählte Fristkenntnis)", "Auslastung der Fahrzeuge", "Mittlere Wartezeit (in Fahrzeiten)", "Anteil verspäteter Sendungen"]


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_laeuft_und_zeigt_die_zelle_des_presets(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    p = C.PRESETS[name]
    cell = R.cell_of(p["lam"], p["ca2"], p["span"], p["cap"])
    first = _first(at)
    assert R.cell_text(cell) in first
    assert ("Hier ist die Frist egal" in first) == (cell["klass"] == "gleich")


@pytest.mark.parametrize("key", ["lam_slider"])
def test_jede_stufe_der_diskreten_regler_laeuft(key):
    at = _fresh_app()
    for value in C.LAM_OPTIONS:
        at.sidebar.select_slider(key=key).set_value(value).run(timeout=TIMEOUT)
        assert not at.exception, (key, value, [str(e) for e in at.exception])


@pytest.mark.parametrize("key,options", [("ca2_radio", C.CA2_OPTIONS), ("span_radio", C.SPAN_OPTIONS), ("cap_radio", C.CAP_OPTIONS)])
def test_jede_option_der_radios_laeuft(key, options):
    at = _fresh_app()
    for option in options:
        at.sidebar.radio(key=key).set_value(option).run(timeout=TIMEOUT)
        assert not at.exception, (key, option, [str(e) for e in at.exception])
        assert at.sidebar.radio(key=key).value == option


def test_jede_stufe_der_fristkenntnis_laeuft_und_aendert_die_gewaehlte_regel():
    at = _fresh_app()
    costs = {}
    for w in C.WISSEN_OPTIONS:
        at.sidebar.selectbox(key="wissen_select").set_value(w).run(timeout=TIMEOUT)
        assert not at.exception, (w, [str(e) for e in at.exception])
        costs[w] = at.metric[0].value
    assert len(set(costs.values())) == len(C.WISSEN_OPTIONS)   # jede Stufe zeigt eine andere Zahl für die Kosten je Sendung


def test_zufalls_seed_an_den_raendern_und_der_zufalls_knopf():
    at = _fresh_app()
    for value in (0, C.SEED_MAX):
        at.sidebar.number_input(key="seed_input").set_value(value).run(timeout=TIMEOUT)
        assert not at.exception, (value, [str(e) for e in at.exception])
    at.sidebar.button[-1].click().run(timeout=TIMEOUT)   # 🎲 Neuen Lauf generieren (letztes Element der Seitenleiste)
    assert not at.exception, [str(e) for e in at.exception]
    assert 0 <= at.sidebar.number_input(key="seed_input").value <= C.SEED_MAX


def test_beide_meldungszustaende_kommen_vor():
    at = _fresh_app()
    assert any("Hier zählt die Frist" in w.value for w in at.success)
    at.sidebar.button(key="preset_Fahrzeug füllt sich").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Hier ist die Frist egal" in w.value for w in at.info) and not any("Hier zählt die Frist" in w.value for w in at.success)


def test_erste_meldung_nennt_informationsvorsprung_und_obergrenze():
    first = _first(_fresh_app())
    assert "Informationsvorsprung" in first and "günstige Annahme" in first and "über dem Optimum" in first


def test_jede_ansicht_der_zeitleiste_und_das_pdf_stuerzen_nicht_ab():
    at = _fresh_app()
    options = list(at.selectbox(key="view_select").options)
    assert len(options) == 6
    for option in options:
        at.selectbox(key="view_select").set_value(option).run(timeout=TIMEOUT)
        assert not at.exception, (option, [str(e) for e in at.exception])


def test_permalink_rastet_auf_stufen_und_verwirft_unbekanntes():
    at = AppTest.from_file(APP_PATH)
    at.query_params["lam"] = "3.5"
    at.query_params["frist"] = "oben"
    at.query_params["cap"] = "13"
    at.query_params["wissen"] = "s99"
    at.query_params["ca2"] = "2"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.select_slider(key="lam_slider").value == 4.0 and at.sidebar.radio(key="span_radio").value == C.DEFAULT_SPAN
    assert at.sidebar.radio(key="cap_radio").value == 16 and at.sidebar.selectbox(key="wissen_select").value == C.DEFAULT_WISSEN
    assert at.sidebar.radio(key="ca2_radio").value == 1.0


def test_keine_toten_dateilinks_und_keine_umgebungsaussagen_in_der_app():
    text = open(APP_PATH, encoding="utf-8").read()
    assert not re.search(r"\]\([A-Za-z0-9_./-]+\.(py|json|md|txt)\)", text)
    for wort in ("läuft lokal", "Saatwert", " trägt ", " tragen "):
        assert wort not in text, wort
