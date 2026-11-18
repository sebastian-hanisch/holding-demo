"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, gemessene Zelle je Preset, Geschichte auf dem angezeigten Lauf."""

import pytest

import hld_constants as C
import hld_evaluation as ev
import hld_presets as P
import hld_results as R
import hld_stories as S


def _settings(name):
    p = C.PRESETS[name]
    return ev.Settings(p["lam"], p["ca2"], p["span"], p["cap"], p["wissen"], p["seed"])


def test_every_preset_has_help_story_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP) == set(S.STORIES)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_stages_of_the_controls():
    for name, p in C.PRESETS.items():
        assert p["lam"] in C.LAM_OPTIONS and p["ca2"] in C.CA2_OPTIONS and p["span"] in C.SPAN_OPTIONS and p["cap"] in C.CAP_OPTIONS and p["wissen"] in C.WISSEN_OPTIONS, name
        assert 0 <= p["seed"] <= C.SEED_MAX


def test_preset_seeds_liegen_ausserhalb_aller_messbereiche():
    for p in C.PRESETS.values():
        assert p["seed"] >= 500000          # Messreihen: 1000-1029 (Abstimmung), 100000-100029 (Messung)
    assert C.DEFAULT_SEED >= 500000


def test_default_preset_equals_the_default_settings():
    assert _settings("Standard") == ev.Settings()
    assert next(iter(C.PRESETS)) == "Standard"


def test_setting_specs_cover_every_preset_key_and_option_stages_match_constants():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    assert P.options("lam_slider") == C.LAM_OPTIONS and P.options("ca2_radio") == C.CA2_OPTIONS and P.options("span_radio") == C.SPAN_OPTIONS
    assert P.options("cap_radio") == C.CAP_OPTIONS and P.options("wissen_select") == C.WISSEN_OPTIONS


def test_clamp_rastet_auf_die_naechste_stufe_und_verwirft_unbekanntes():
    spec = P.SETTING_SPECS
    assert P.clamp_value(spec["lam_slider"], 3.5) == 4.0 and P.clamp_value(spec["lam_slider"], 0.1) == 0.5
    assert P.clamp_value(spec["ca2_radio"], 2.0) == 1.0 and P.clamp_value(spec["cap_radio"], 13) == 16
    assert P.clamp_value(spec["span_radio"], "xyz") is None and P.clamp_value(spec["span_radio"], "weit") == "weit"
    assert P.clamp_value(spec["wissen_select"], "s99") is None and P.clamp_value(spec["wissen_select"], "s25") == "s25"
    assert P.clamp_value(spec["seed_input"], -5) == 0 and P.clamp_value(spec["seed_input"], 10 ** 9) == C.SEED_MAX


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_jedes_preset_liegt_auf_einer_gemessenen_zelle_mit_der_erwarteten_klasse(name):
    p = C.PRESETS[name]
    cell = R.cell_of(p["lam"], p["ca2"], p["span"], p["cap"])
    assert cell["klass"] == ("gleich" if name == "Fahrzeug füllt sich" else "F")


def test_zellen_der_presets_stimmen_mit_der_geschichte_ueberein():
    cells = {name: R.cell_of(p["lam"], p["ca2"], p["span"], p["cap"]) for name, p in C.PRESETS.items()}
    assert cells["Standard"]["saving_F"] == pytest.approx(28.7, abs=0.1)                      # nahe am Median der 53 Zellen (28,0 %)
    assert cells["Enge Frist"]["cost"]["Q"] >= 0.999 and cells["Stoßweise, enge Frist"]["cost"]["Q"] >= 0.999   # Menge gleich „sofort“
    assert cells["Dünner Fluss"]["cost"]["Q"] >= 0.999
    assert all(cells["Fahrzeug füllt sich"]["cost"][r] <= C.FILL_FACTOR / 8 for r in ("Q", "T", "QT", "F"))
    assert R.cell_of(2.0, 1.0, "mittel", 16)["levels"]["verr10_kl"]["cost"] < cells["Standard"]["cost"]["T"]   # 10 % Schätzfehler bleiben unter der abgestimmten Zeitregel


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_der_lauf_jedes_presets_zeigt_seine_geschichte(name):
    """Das Kriterium prüft den angezeigten Lauf (grob); die Aussage der Demo steht in der Messreihe."""
    an = ev.analyse(_settings(name))
    assert S.STORIES[name](an), name


def _an(cost, util=0.5, cap=16, wissen="exakt", stage=None, viol=0.0):
    rules = {k: {"cost": c, "util": util, "viol": 0.0, "delay": 1.0} for k, c in cost.items()}
    return {"settings": ev.Settings(cap=cap, wissen=wissen), "rules": rules, "opt": {"cost": min(cost.values()) * 0.99}, "stage": stage or {"cost": cost["F"], "viol": viol, "util": util, "delay": 1.0}}


def test_geschichte_kippt_an_ihren_schwellen_mit_kuenstlichen_werten():
    base = {"S": 1.0, "Q": 0.20, "T": 0.100, "QT": 0.100, "F": 0.0850}
    assert S.story_standard(_an(base))
    assert not S.story_standard(_an({**base, "F": 0.0860}))                                  # F spart nur 14 %
    assert not S.story_standard(_an({**base, "T": 0.200, "QT": 0.200, "Q": 0.3, "F": 0.100}))   # 50 % Ersparnis, über 45 %
    assert S.story_enge(_an({**base, "Q": 0.99, "F": 0.085})) and not S.story_enge(_an({**base, "Q": 0.98, "F": 0.085}))
    assert not S.story_enge(_an({**base, "Q": 1.0, "F": 0.0851}))                              # F nicht mindestens 15 % unter T
    fuell = {"S": 1.0, "Q": 1.03 / 16, "T": 1.03 / 16, "QT": 1.03 / 16, "F": 1.03 / 16}
    assert S.story_fuellt(_an(fuell)) and not S.story_fuellt(_an({**fuell, "T": 1.04 / 16}))
    assert S.story_stoss(_an({**base, "Q": 1.0, "T": 0.100, "F": 0.080})) and not S.story_stoss(_an({**base, "Q": 1.0, "T": 0.100, "F": 0.081}))
    assert S.story_duenn(_an({**base, "F": 0.0850}, util=0.69)) and not S.story_duenn(_an({**base, "F": 0.0850}, util=0.70))
    st_ok = {"cost": 0.095, "viol": 0.01, "util": 0.6, "delay": 1.0}
    assert S.story_geschaetzt(_an(base, stage=st_ok)) and not S.story_geschaetzt(_an(base, stage={**st_ok, "viol": 0.0101}))
    assert not S.story_geschaetzt(_an(base, stage={**st_ok, "cost": 0.100})) and not S.story_geschaetzt(_an(base, stage={**st_ok, "cost": 0.080}))
