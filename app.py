"""Holding: wann zahlt sich Fristkenntnis aus? - interaktive Fall-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Sendungen kommen laufend an und jede hat eine Frist; ein Fahrzeug kostet pro Abfahrt dasselbe, egal wie voll es ist. Live auf einem Lauf: fünf Abfahrtsregeln (sofort, Menge, Zeit,
Menge-oder-Zeit, fristgetrieben), das Offline-Optimum und die Stufen der Fristkenntnis. Die Aussagen stützen sich auf die vorgerechnete Messreihe (data/hld_results.json).
Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import pandas as pd
import streamlit as st

import hld_constants as C
import hld_evaluation as E
import hld_results as R
import hld_sim as S
import hld_visualization as VIZ
from hld_layout import dunkles_design, kopf_css
from hld_pdf_export import build_pdf
from hld_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    options,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)

st.set_page_config(page_title="Holding – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return E.analyse(settings)


@st.cache_data(show_spinner=False)
def _trace(settings, key):
    a, dl, deps = E.trace_of(settings, key)
    return E.excerpt(a, dl, deps), [(t, list(m)) for t, m in deps if t >= a[S.N_WARM] - 1.0 and t <= a[S.N_WARM + C.EXCERPT_ARRIVALS] + C.SPANS[settings.span][1] + 2.0]


def _fmt_lam(value):
    return f"λ = {R.num(value, 1)}"


VIEW_LABELS = {"stufe": "gewählte Fristkenntnis", "S": C.RULE_LABELS["S"], "Q": C.RULE_LABELS["Q"], "T": C.RULE_LABELS["T"], "QT": C.RULE_LABELS["QT"], "F": C.RULE_LABELS["F"]}

# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in hld_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("⏳ Holding: wann zahlt sich Fristkenntnis aus?")
st.markdown(
    """
Sendungen kommen laufend an, jede hat eine **Frist**, und ein Fahrzeug kostet pro Abfahrt dasselbe, egal wie voll es ist. **Wann soll es abfahren?** Wer wartet, füllt das Fahrzeug, riskiert aber die Frist.
Die Demo zeigt live auf **einem Lauf** fünf Abfahrtsregeln (sofort, Menge, Zeit, Menge-oder-Zeit, fristgetrieben) und fragt: **wann bestimmt die Frist die Abfahrt, was ist die Kenntnis der Frist wert, und wie genau muss sie sein?**
Die Aussagen stützen sich auf eine vorgerechnete Messreihe mit 72 Zellen und 30 Läufen je Zelle.

Weiter unten: die **Kernfragen** und die Expander **🔧 Wie wir das erreichen – vollständiger Methodenvergleich**, **Wie funktioniert diese Demo?** und **📐 Mathematische Formulierung**.
"""
)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Ankünfte**")
    lam = st.select_slider("Ankunftsrate", options=options("lam_slider"), key="lam_slider", format_func=_fmt_lam,
                           help="Sendungen je Fahrzeugzeit (Zeit, die ein Fahrzeug zum Ziel braucht). Hohe Raten füllen ein Fahrzeug schnell.")
    ca2 = st.radio("Streuung der Ankünfte", options("ca2_radio"), key="ca2_radio", format_func=lambda v: C.CA2_LABELS[v],
                   help="ca² ist die quadrierte Streuung der Zeit zwischen zwei Ankünften: 0 gleichmäßig, 1 zufällig (Poisson), 4 stoßweise.")
    st.markdown("**Fristen und Fahrzeug**")
    span = st.radio("Fristspanne", options("span_radio"), key="span_radio", format_func=lambda v: C.SPAN_LABELS[v],
                    help="So viel Spielraum hat eine Sendung zwischen Ankunft und spätester Abfahrt, in Fahrzeiten; gleichverteilt zwischen den beiden Grenzen.")
    cap = st.radio("Kapazität", options("cap_radio"), key="cap_radio", format_func=lambda v: f"{v} Sendungen je Fahrzeug", help="Wie viele Sendungen ein Fahrzeug höchstens mitnimmt.")
    st.markdown("**Fristkenntnis**")
    wissen = st.selectbox("Was weiß die Regel über die Fristen?", options("wissen_select"), key="wissen_select", format_func=lambda v: C.WISSEN_LABELS[v],
                          help="Wirkt auf die Regel „gewählte Fristkenntnis“: von der Zeitregel ohne Kenntnis der Fristspanne bis zur exakten Frist. Der Schätzfehler ist ein Anteil des mittleren Spielraums der Fristspanne.")
    st.markdown("**Lauf**")
    seed = st.number_input("Zufalls-Seed des Laufs", *bounds("seed_input"), key="seed_input", step=1)
    st.button("🎲 Neuen Lauf generieren", width="stretch", on_click=randomize_seed)

sync_query_params({"lam_slider": float(lam), "ca2_radio": float(ca2), "span_radio": span, "cap_radio": int(cap), "wissen_select": wissen, "seed_input": int(seed)})

settings = E.Settings(float(lam), float(ca2), span, int(cap), wissen, int(seed))
cell = R.cell_of(settings.lam, settings.ca2, settings.span, settings.cap)

# --- Erste Meldung: aus der gemessenen Zelle --------------------------------------------------------------------------------------------------

st.markdown("## ⏳ Wann zählt die Frist hier?")
kind, text = E.verdict_state(cell)
getattr(st, kind)(text)

with st.spinner("Rechne einen Lauf mit 2 200 Ankünften ..."):
    an = _analysis(settings)

st.markdown("## ⏳ Ein Lauf")
st.info("Das ist **ein Lauf**. Er zeigt, wie die Regeln arbeiten; die Aussagen darüber, wann die Frist zählt und was Fristkenntnis wert ist, stützen sich auf die Messreihe weiter unten (72 Zellen, je 30 Läufe).")

stage, t_rule = an["stage"], an["rules"]["T"]
r1c1, r1c2 = st.columns(2)


def _delta(diff, digits, text, scale=1.0, better_when_lower=True):
    """Delta immer als „mein Wert minus Referenz“ (Vorzeichen-Falle, DEMO-PLAYBOOK §2); eine Differenz von null nach dem Runden ist grau (`off`), sonst färbt Streamlit nach dem Vorzeichen."""
    d = diff * scale
    if round(d, digits) == 0:
        return f"{R.num(0.0, digits)} {text}", "off"
    return f"{R.num(d, digits, True)} {text}", ("inverse" if better_when_lower else "normal")


# Referenz: die auf die Zelle abgestimmte Zeitregel T.
d1, c1 = _delta(stage["cost"] - t_rule["cost"], 3, "gegen die abgestimmte Zeitregel")
d2, c2 = _delta(stage["util"] - t_rule["util"], 1, "Prozentpunkte gegen die abgestimmte Zeitregel", scale=100.0, better_when_lower=False)
d3, c3 = _delta(stage["delay"] - t_rule["delay"], 2, "gegen die abgestimmte Zeitregel")
d4, c4 = _delta(stage["viol"] - t_rule["viol"], 2, "Prozentpunkte gegen die abgestimmte Zeitregel", scale=100.0)
r1c1.metric("Kosten je Sendung (gewählte Fristkenntnis)", R.num(stage["cost"], 3), delta=d1, delta_color=c1)
r1c2.metric("Auslastung der Fahrzeuge", f"{R.num(100 * stage['util'], 1)} %", delta=d2, delta_color=c2)
r2c1, r2c2 = st.columns(2)
r2c1.metric("Mittlere Wartezeit (in Fahrzeiten)", R.num(stage["delay"], 2), delta=d3, delta_color=c3)
r2c2.metric("Anteil verspäteter Sendungen", f"{R.num(100 * stage['viol'], 2)} %", delta=d4, delta_color=c4)

view_key = st.selectbox("Zeitleiste zeigt", list(VIEW_LABELS), index=0, format_func=lambda key: VIEW_LABELS[key], key="view_select", help="Reine Anzeigewahl: ändert nichts an der Rechnung.")
rows, deps = _trace(settings, view_key)
st.plotly_chart(VIZ.build_timeline(rows, deps, VIEW_LABELS[view_key]), width="stretch", key="timeline_chart")
st.caption(f"Auszug: die {C.EXCERPT_ARRIVALS} Sendungen ab der Ankunft Nr. {S.N_WARM} (Regel: {VIEW_LABELS[view_key]}). Grün: die Sendung wartet bis zur Abfahrt ihres Fahrzeugs; rot: das Fahrzeug fährt nach ihrer Frist (verspätet); "
           "Kreuz: späteste Abfahrt; Dreieck: Abfahrt, die Zahl ist die Beladung.")
st.download_button("📄 Lauf als PDF", data=build_pdf(settings, an, rows), file_name="holding.pdf", mime="application/pdf", key="pdf_download")
kind, text = E.verdict_live(an)
getattr(st, kind)(text)
st.plotly_chart(VIZ.build_rule_costs(an, cell), width="stretch", key="costs_chart")
st.caption("Balken: Kosten je Sendung auf diesem Lauf (1,000 heißt: jede Sendung fährt allein); Raute: Mittel der gemessenen Zelle über 30 Läufe (die Parameter von Menge, Zeit und Menge-oder-Zeit sind je Zelle mit Kenntnis der Fristverteilung abgestimmt).")

st.markdown("---")

# --- Kernfrage 1: Wann zählt die Frist? -------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage 1: Wann zählt die Frist?")
cc = R.class_counts()
egal_span = R.frist_egal_by("span")
egal_lam = R.frist_egal_by("lam")
fs = R.saving_f()
st.markdown(
    f"Ein Fahrzeug fährt spätestens ab, wenn es voll ist. Bei hohem Fluss und weiter Frist passiert das fast immer vor der Frist (Deutung): dann unterscheiden sich Menge, Zeit, Menge-oder-Zeit und Frist höchstens um 2 %; „sofort“ ist dort weiter 8- bis 16-mal so teuer. "
    f"In **{cc['gleich']} von {cc['zellen']} Zellen** liegen Menge, Zeit, Menge-oder-Zeit und Frist alle höchstens 2 % über 1/C (Frist eng {egal_span.get('eng', 0)}, mittel {egal_span.get('mittel', 0)}, weit {egal_span.get('weit', 0)}; "
    f"nach Rate λ = 0,5 / 1 / 2 / 4: {egal_lam.get(0.5, 0)} / {egal_lam.get(1.0, 0)} / {egal_lam.get(2.0, 0)} / {egal_lam.get(4.0, 0)} Zellen). "
    f"In den übrigen **{cc['F']} Zellen** gewinnt die Fristregel F allein und spart gegenüber der besten einfachen Regel im Median **{R.num(fs['median'])} %** (Minimum {R.num(fs['min'])} %, Maximum {R.num(fs['max'])} %). "
    f"„Zählt“ heißt nur: nicht alle vier Regeln liegen höchstens 2 % über 1/C, und F gewinnt allein; nicht notwendig ein großer Vorteil (kleinste Ersparnis {R.num(fs['min'])} %; Beispiel {R.cell_text(R.cell_of(1.0, 4.0, 'weit', 8))}: {R.num(R.cell_of(1.0, 4.0, 'weit', 8)['saving_F'], 2)} %). "
    "Das Fahrzeug füllt sich fast immer vor der Frist: eine Deutung der Zählung, nicht gesondert gemessen."
)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(VIZ.build_rank_map(cell), width="stretch", key="rank_chart")
    st.caption(f"Rangfolge-Karte der {cc['zellen']} Zellen: blau = F gewinnt allein, grau = Menge, Zeit, Menge-oder-Zeit und Frist alle höchstens 2 % über 1/C; die gewählte Zelle ist umrandet. Zeilen: Streuung ca² und Rate λ.")
with c2:
    st.plotly_chart(VIZ.build_savings_span(), width="stretch", key="savings_chart")
    st.caption("Mittlere Ersparnis gegen „sofort“ (Prozent der Kosten) je Fristspanne, Mittel über je 24 Zellen.")

st.markdown("---")

# --- Kernfrage 2: Was ist eine Frist wert, und wie genau muss sie sein? -----------------------------------------------------------------------

st.markdown("## ❓ Kernfrage 2: Was ist eine Frist wert, und wie genau muss sie sein?")
st.markdown(
    "Die Fristregel F kennt die Fristen **per Konstruktion** (Informationsvorsprung). Die Genauigkeitsleiter zeigt, wie viel von ihrem Vorteil übrig bleibt, wenn sie die Frist nur schätzt: "
    "**A** ist der Anteil des F-Vorteils gegenüber der auf die Zelle abgestimmten Zeitregel T (die der Kenntnis der **Fristklasse** entspricht): A = 1 heißt der ganze Vorteil, A = 0 nicht besser als T, negativ teurer als T."
)
kind, text = E.verdict_ladder(cell, settings)
getattr(st, kind)(text)
kind, text = E.verdict_ladder_overall()
getattr(st, kind)(text)
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(VIZ.build_ladder(), width="stretch", key="ladder_chart")
    st.caption("Median von A über die 53 Zellen, in denen F allein gewinnt (Schätzer mit Klassenwissen; 5 % und 10 % sind Nachmessungen ohne eigene Schwelle).")
with c2:
    st.plotly_chart(VIZ.build_saving_vs_praxis(), width="stretch", key="praxis_saving_chart")
    st.caption("Ersparnis der Regel F gegenüber einer Praxis-Zeitregel mit einem Parameter für alle Fristspannen (Median über die 53 Zellen).")
pr1, pr2 = R.praxis_stats("T", "V1"), R.praxis_stats("T", "V2")
ex_v1 = R.cell_of(1.0, 1.0, "eng", 16)["praxis"]["T_V1"]
st.markdown(
    f"**Wie optimistisch ist die abgestimmte Zeitregel?** Sie kennt die Fristspanne der Zelle. Ohne diese Kenntnis ist eine auf „mittel“ abgestimmte Zeitregel (V1) in {pr1['unzulaessig']} von {pr1['zellen']} Zellen mit Frist eng oder weit "
    f"unzulässig (über 1,0 % verspätet, z. B. λ = 1, ca² = 1, Frist eng, C = 16: {R.num(100 * ex_v1['viol'], 2)} % verspätet); eine auf die Mischung der drei Spannen abgestimmte (V2) ist überall zulässig, "
    f"kostet aber im Mittel {R.num(pr2['aufschlag'])} % mehr als die abgestimmte (Frist eng {R.num(pr2['nach_spanne']['eng'])} %, mittel {R.num(pr2['nach_spanne']['mittel'])} %, weit {R.num(pr2['nach_spanne']['weit'])} %)."
)
st.plotly_chart(VIZ.build_praxis(), width="stretch", key="praxis_chart")
st.caption("Kostenaufschlag der Praxis-Zeitregel gegen die auf die Zelle abgestimmte, Mittel über die zulässigen Zellen je Fristspanne; V1 gilt nur für Frist eng und weit (auf „mittel“ ist sie gleich der Vormessung).")

st.markdown("---")

# --- Kernfrage 3: Wie weit ist das Optimum? ---------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage 3: Wie weit liegen die Regeln vom Optimum?")
kind, text = E.verdict_optimum()
getattr(st, kind)(text)
g = R.gap_to_opt("F")
st.caption(f"Das Optimum kennt alle Ankünfte und Fristen im Voraus (Offline). Die Fristregel F liegt in {g['ueber_1']} von 72 Zellen mehr als 1 % darüber; die Abweichung entsteht vermutlich, weil F die künftigen Ankünfte nicht kennt (Deutung, nicht gemessen), nicht durch Verspätung (F hat nie Verspätung).")

st.markdown("---")

# --- Methodenvergleich ---------------------------------------------------------------------------------------------------------------------

with st.expander("🔧 Wie wir das erreichen – vollständiger Methodenvergleich"):
    tab_dep, tab_rules, tab_wissen, tab_series = st.tabs(["⏳ Abfahrten", "📊 Regeln", "🔎 Fristkenntnis", "📈 Messreihe"])
    with tab_dep:
        st.markdown(f"Auszug der Abfahrten für **{VIEW_LABELS[view_key]}** (Sendungen ab der Ankunft Nr. {S.N_WARM}; Zeit in Fahrzeiten).")
        df = pd.DataFrame([{"Sendung": j, "Ankunft": a_, "Späteste Abfahrt": d_, "Abfahrt": t_, "Wartezeit": None if t_ is None else t_ - a_, "Verspätet": "ja" if late_ else "nein"} for j, a_, d_, t_, late_ in rows])
        st.dataframe(df, hide_index=True, width="stretch", column_config={c_: st.column_config.NumberColumn(format="%.2f") for c_ in ("Ankunft", "Späteste Abfahrt", "Abfahrt", "Wartezeit")})
        st.caption("Sendungen ohne Abfahrt im Auszug warten am Ende des Auszugs noch auf ein Fahrzeug.")
    with tab_rules:
        kind, text = E.verdict_regeln()
        getattr(st, kind)(text)
        params = cell["params"]
        rows_r = []
        for k in C.RULES:
            m = an["rules"][k]
            p = params[k]
            par = "-" if not p else ", ".join(f"{'q' if key == 'q' else 'T'} = {R.num(val, 2) if key == 'T' else val}" for key, val in p.items())
            rows_r.append({"Regel": C.RULE_LABELS[k], "Parameter (abgestimmt)": par, "Kosten (Lauf)": m["cost"], "Kosten (Zelle)": cell["cost"][k], "Auslastung (Lauf, %)": 100 * m["util"],
                           "Wartezeit (Lauf)": m["delay"], "Verspätet (Lauf, %)": 100 * m["viol"], "Verspätet (Zelle, %)": 100 * cell["viol"][k]})
        o = an["opt"]
        rows_r.append({"Regel": "Optimum (bekannte Ankünfte)", "Parameter (abgestimmt)": "-", "Kosten (Lauf)": o["cost"], "Kosten (Zelle)": cell["opt"]["cost"], "Auslastung (Lauf, %)": 100 * o["util"],
                       "Wartezeit (Lauf)": None, "Verspätet (Lauf, %)": 0.0, "Verspätet (Zelle, %)": 0.0})
        st.dataframe(pd.DataFrame(rows_r), hide_index=True, width="stretch",
                     column_config={c_: st.column_config.NumberColumn(format="%.3f") for c_ in ("Kosten (Lauf)", "Kosten (Zelle)")} |
                     {c_: st.column_config.NumberColumn(format="%.2f") for c_ in ("Auslastung (Lauf, %)", "Wartezeit (Lauf)", "Verspätet (Lauf, %)", "Verspätet (Zelle, %)")})
        st.markdown(
            "- **S** sofort: jede Sendung fährt allein ab (Kosten 1,000).\n"
            "- **Q** Menge: Abfahrt, sobald q Sendungen warten; **T** Zeit: Abfahrt, wenn die älteste wartende Sendung T gewartet hat; **QT** Menge-oder-Zeit: eines von beiden. Alle fahren sofort bei voller Kapazität. "
            "q und T sind je Zelle mit Kenntnis der Fristverteilung gewählt (kleinste Kosten unter höchstens 0,5 % verspäteten Sendungen auf getrennten Zufalls-Seeds).\n"
            "- **F** fristgetrieben: Abfahrt zur frühesten Frist der Wartenden; braucht die Fristen.\n"
            "- **Optimum**: Mindestzahl der Abfahrten bei bekannten Ankünften und Fristen (Offline)."
        )
    with tab_wissen:
        st.markdown("Alle gemessenen Stufen der Fristkenntnis in der gewählten Zelle (30 Läufe, Zufalls-Seeds 100000 bis 100029). Verspätet über 1,0 % gilt als unzulässig.")
        rows_w = []
        for key in C.LEVEL_KEYS_ALL:
            lv = cell["levels"][key]
            a_v = None if cell["A"] is None else cell["A"][key]
            rows_w.append({"Stufe": C.LEVEL_LABELS[key], "Sicherheitsabstand m": lv["m"], "Kosten je Sendung": lv["cost"], "Verspätet (%)": 100 * lv["viol"], "zulässig": "ja" if lv["zulaessig"] else "nein", "A": a_v})
        pv = cell["praxis"]["T_V2"]
        rows_w.append({"Stufe": "keine Kenntnis (Praxis-Zeitregel V2)", "Sicherheitsabstand m": None, "Kosten je Sendung": pv["cost"], "Verspätet (%)": 100 * pv["viol"], "zulässig": "ja" if pv["zulaessig"] else "nein", "A": None})
        st.dataframe(pd.DataFrame(rows_w), hide_index=True, width="stretch",
                     column_config={"Sicherheitsabstand m": st.column_config.NumberColumn(format="%.2f"), "Kosten je Sendung": st.column_config.NumberColumn(format="%.3f"),
                                    "Verspätet (%)": st.column_config.NumberColumn(format="%.2f"), "A": st.column_config.NumberColumn(format="%.2f")})
        st.caption("A gibt es nur in den 53 Zellen, in denen F allein gewinnt. „Ohne Klassenwissen“ ist Variante 1 der Restmessung (vorab festgelegt), „mit Klassenwissen“ die Nachmessung; der Schätzfehler ist ein Anteil des mittleren Spielraums der Fristspanne.")
        st.markdown(
            "**Stufen.** *exakt*: die Regel F. *nur die Fristklasse*: die geschätzte Frist ist Ankunft plus unterer Rand der Fristspanne (sicher, nie über der echten Frist); sie fährt wie die Zeitregel mit T gleich dem unteren Rand. "
            "*Schätzfehler σ*: geschätzte Frist = echte Frist plus ein normalverteilter Fehler mit Standardabweichung σ mal mittlerer Spielraum, auf die Fristklasse begrenzt; das Fahrzeug fährt zur frühesten geschätzten Frist minus einem Sicherheitsabstand m. "
            "m wurde je Zelle auf getrennten Zufalls-Seeds gewählt (kleinste Kosten unter höchstens 0,5 % verspätet); das kennt die Fehlergröße und ist eine günstige Annahme (grobes Raster für m)."
        )
    with tab_series:
        st.markdown("Alle 72 gemessenen Zellen (je 30 Läufe, Zufalls-Seeds 100000 bis 100029). Kosten je Sendung, Sieger und Klasse.")
        rows_s = []
        for c_ in R.cells():
            rows_s.append({"C": c_["C"], "ca²": c_["ca2"], "λ": c_["lam"], "Frist": c_["span"], "Q": c_["cost"]["Q"], "T": c_["cost"]["T"], "QT": c_["cost"]["QT"], "F": c_["cost"]["F"], "Optimum": c_["opt"]["cost"],
                           "F gegen beste einfache (%)": c_["saving_F"], "Klasse": "Frist egal" if c_["klass"] == "gleich" else ("F allein" if c_["klass"] == "F" else "sonst")})
        st.dataframe(pd.DataFrame(rows_s), hide_index=True, width="stretch", column_config={c_: st.column_config.NumberColumn(format="%.3f") for c_ in ("Q", "T", "QT", "F", "Optimum")}
                     | {"F gegen beste einfache (%)": st.column_config.NumberColumn(format="%.1f")})
        qs = R.q_equals_s()
        st.markdown(
            f"**Menge-Regel Q:** in {qs['zellen']} von 72 Zellen gleich „sofort“ (Kosten 1,000; die Abstimmung findet keinen Parameter unter 0,5 % Verspätung): nach Frist eng {qs['span'].get('eng', 0)}, mittel {qs['span'].get('mittel', 0)}, weit {qs['span'].get('weit', 0)}; "
            f"nach ca² 0 / 1 / 4: {qs['ca2'].get(0.0, 0)} / {qs['ca2'].get(1.0, 0)} / {qs['ca2'].get(4.0, 0)}. **Zeitregel T:** nur in {R.t_equals_s()} von 72 Zellen gleich „sofort“. "
            f"**Menge-oder-Zeit gegen Zeit:** mit den abgestimmten Parametern in {R.qt_equals_t()} von 72 Zellen dieselben Kosten; die Mengenschwelle greift nie."
        )
        ub = R.util_by_ca2()
        st.markdown(
            "**Zeitregel T bei stoßweisen Ankünften:** mittlere Auslastung bei ca² = 0 / 1 / 4: " + " / ".join(R.num(ub[k]['util']) for k in C.CA2_OPTIONS) + " %, mittlere Ersparnis gegen „sofort“ "
            + " / ".join(R.num(ub[k]['saving']) for k in C.CA2_OPTIONS) + " %: stoßweise Ankünfte bündeln sich eher von selbst (Deutung, nicht gesondert gemessen)."
        )

with st.expander("Wie funktioniert diese Demo?"):
    st.markdown(
        f"""
**Die Aufgabe.** Sendungen kommen mit der Rate λ (je Fahrzeugzeit) und der Streuung ca² an. Jede hat einen Spielraum (gleichverteilt, eng 1 bis 3, mittel 4 bis 12, weit 12 bis 36 Fahrzeiten): die späteste Abfahrt ist Ankunft plus Spielraum.
Fahrzeuge der Kapazität C gibt es beliebig viele; jede Abfahrt kostet gleich viel. **Kosten je Sendung** = Abfahrten / Sendungen = 1 / mittlere Beladung (1,000 heißt: jede Sendung fährt allein). Eine Sendung ist **verspätet**, wenn ihr Fahrzeug nach ihrer spätesten Abfahrt fährt.

**Die Regeln.** *S* sofort. *Q* Menge: Abfahrt, sobald q Sendungen warten. *T* Zeit: Abfahrt, wenn die älteste wartende Sendung T gewartet hat. *QT* Menge-oder-Zeit. *F* fristgetrieben: Abfahrt zur frühesten Frist der Wartenden.
Alle Regeln fahren sofort ab, wenn C Sendungen warten. Das **Optimum** kennt alle Ankünfte und Fristen im Voraus (Offline).

**Die Stufen der Fristkenntnis.** F kennt die Fristen per Konstruktion. Die Demo schwächt das ab: nur die Fristklasse, geschätzte Fristen mit 5, 10 oder 25 % Fehler (Anteil des mittleren Spielraums, auf die Fristklasse begrenzt) und, ohne jede Kenntnis, eine Zeitregel mit einem Parameter für alle Fristspannen.

**Was die Live-Zahlen bedeuten.** Sie gelten für diesen einen Lauf ({an['arrivals']} Ankünfte, ausgewertet die Abfahrten im Fenster von Ankunft Nr. {S.N_WARM} bis {S.N_WARM + S.N_EVAL}, rund {S.N_EVAL} Sendungen). Die Aussagen der Kernfragen stammen aus der vorgerechneten Messreihe (72 Zellen, je 30 Läufe, Zufalls-Seeds 100000 bis 100029);
alle Regler stehen auf gemessenen Stufen, zu jeder Einstellung gehört also eine Zelle. Die Parameter von Q, T und QT sind je Zelle auf den Zufalls-Seeds 1000 bis 1029 abgestimmt.

**Quellen.** Zeit-, Mengen- und Hybridregeln für Sammelfahrten untersuchen laut Zusammenfassung Mutlu, Çetinkaya, Bookbinder 2010 (IISE Transactions) und Wei, Çetinkaya, Cline 2020 (arXiv 2012.02392; nur die Zusammenfassungen gelesen);
von Ralfs, Kiesmüller 2022 (OR Spectrum) wurde nur der Titel gefunden („Inventory management with advance demand information and flexible shipment consolidation“), der Inhalt ist nicht eingesehen. Dieses Modell unterscheidet sich durch harte Fristen; ein Vergleich mit den dortigen Ergebnissen ist nicht gemacht.

**🚧 Wo die Annahmen enden**

| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| F kennt die Fristen exakt | Informationsvorsprung: „F gewinnt“ ist erwartbar; neu ist nur, wo es zählt und wie genau die Frist sein muss | Stufen der Fristkenntnis |
| Q, T, QT je Zelle mit Kenntnis der Fristverteilung abgestimmt | Günstige Annahme für Regeln ohne diese Kenntnis (grobes Parameter-Raster, Näherung an die beste Wahl, kein Optimum der Regelklasse); eine Zeitregel mit einem Parameter für alle Fristspannen kostet im Mittel {R.num(R.praxis_stats('T', 'V2')['aufschlag'])} % mehr | Kernfrage 2 |
| Schätzfehler unabhängig, normalverteilt, proportional zur Spanne | Systematische Fehler und Schätzer, die Vorwissen und Messung gewichten, sind nicht gemessen; bei 25 % Fehler ist F im Median teurer als die abgestimmte Zeitregel | Tab Fristkenntnis |
| Sicherheitsabstand m je Zelle auf getrennten Zufalls-Seeds gewählt | m kennt die Fehlergröße (günstige Annahme, grobes Raster für m; ein kleineres m wäre in vielen Fällen noch zulässig: 120 von 279 Prüfungen, Prüfer-Neulauf, nicht Teil der Messreihe) | Tab Fristkenntnis |
| Unbegrenzte Flotte, konstante Fahrzeit, unabhängige Ankünfte, gleichverteilte Fristen, eine Sendungsart | Mischfristen, mehrere Ziele oder Fahrzeugtypen, abhängige Ankünfte und Praxisdaten sind nicht gemessen | Ausbau |
| Optimum bei bekannten Ankünften | An 600 Kleininstanzen gegen die exakte Teilmengen-DP geprüft, nicht bewiesen; in zwei Zellen liegen Menge, Zeit und Menge-oder-Zeit bis 0,03 % darunter (Verspätung bis 1 % zulässig) | Kernfrage 3 |
| 72 Zellen, 30 Läufe | Gleichauf heißt: Unterschied der gepaarten Kosten unter zwei Standardfehlern; die Siegerzahlen hängen an dieser Schwelle und am Parameter-Raster (Prüfer-Neulauf, nicht Teil der Messreihe: mit einem feineren Raster, T mit 68 Werten, gewinnt F in 52 statt 53 Zellen allein, und die abgestimmte Zeitregel wäre in 9 Zellen bis etwa 6 % billiger) | Tab Messreihe |
"""
    )

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Gegeben sind Sendungen $i = 1, 2, \dots$ mit Ankunftszeit $a_i$ und spätester Abfahrt $d_i = a_i + w_i$ (Spielraum $w_i$), und eine Kapazität $C$. Gesucht sind Abfahrten, die jede Sendung mitnehmen, ohne ihre späteste Abfahrt zu überschreiten,
mit möglichst wenigen Abfahrten (Optimum bei bekannten Ankünften); die Regeln S, Q, T, QT, F entscheiden online, ohne die Zukunft zu kennen.

| Symbol | Bedeutung |
|---|---|
| $a_i$, $w_i$, $d_i$ | Ankunft, Spielraum und späteste Abfahrt der Sendung $i$ (Fahrzeit $= 1$) |
| $C$ | Kapazität eines Fahrzeugs |
| $t_k$, $S_k$ | Abfahrtszeit und Menge der Sendungen der Abfahrt $k$ |
| $\lambda$, $c_a^2$ | Ankunftsrate und quadrierter Variationskoeffizient der Zwischenankunftszeit |
| $q$, $T$ | Mengenschwelle und Zeitschwelle der Regeln Q, T, QT |
| $\hat d_i$, $m$ | geschätzte späteste Abfahrt und Sicherheitsabstand der Regel F mit geschätzten Fristen |
        """
    )
    st.markdown(
        """
Kosten je Sendung $K = \\dfrac{\\#\\text{Abfahrten}}{\\#\\text{Sendungen}} = \\dfrac{1}{\\text{mittlere Beladung}}$; eine Sendung $i \\in S_k$ ist verspätet, wenn $t_k > d_i$.

**Offline-Optimum** (alle $a_i, d_i$ bekannt), mit $x_{ik} = 1$, wenn Sendung $i$ in Abfahrt $k$ fährt, und $y_k = 1$, wenn Abfahrt $k$ stattfindet:

$$\\min \\sum_k y_k$$

$$\\sum_k x_{ik} = 1 \\quad (\\text{jede Sendung } i), \\qquad \\sum_i x_{ik} \\le C\\, y_k \\quad (\\text{jede Abfahrt } k), \\qquad a_i\\, x_{ik} \\le t_k \\le d_i + M\\,(1 - x_{ik})$$

$$x_{ik},\\, y_k \\in \\{0, 1\\}, \\qquad t_k \\ge 0$$

Eine Gruppe von Sendungen kann zusammen fahren genau dann, wenn $|S| \\le C$ und $\\max_{i \\in S} a_i \\le \\min_{i \\in S} d_i$ gilt. $M$ ist eine hinreichend große Zahl. Die Demo rechnet das Optimum nicht mit diesem Programm,
sondern mit dem Verfahren „früheste Frist abwarten, $C$ Sendungen mit den frühesten Fristen mitnehmen“; es ist an Kleininstanzen (bis 9 Sendungen) gegen die exakte Teilmengen-Rechnung geprüft, nicht bewiesen.

**Die Regeln (online).** Alle fahren ab, sobald $C$ Sendungen warten. **S:** $q = 1$. **Q:** Abfahrt, sobald $q$ Sendungen warten. **T:** Abfahrt zur Zeit $a_{\\text{älteste}} + T$. **QT:** Abfahrt bei $q$ Wartenden oder zur Zeit $a_{\\text{älteste}} + T$.
**F:** Abfahrt zur Zeit $\\min_{i \\text{ wartet}} \\hat d_i - m$, mit $\\hat d_i = d_i$ und $m = 0$ bei exakter Frist. Bei Schätzung: $\\hat d_i = \\min\\bigl(\\max(d_i + \\sigma \\bar w z_i,\\; a_i + w_{\\min}),\\; a_i + w_{\\max}\\bigr)$ mit
$z_i$ standardnormalverteilt, $\\bar w$ dem mittleren Spielraum der Fristspanne und $[w_{\\min}, w_{\\max}]$ ihren Grenzen; „nur die Fristklasse“ heißt $\\hat d_i = a_i + w_{\\min}$.

Dieser Block ist das vollständige Modell des Offline-Optimums; die Online-Regeln stehen als Vorschrift, nicht als Programm.

**Kennzahl A.** $A = \\dfrac{K_T - K_{\\text{Stufe}}}{K_T - K_F}$ je Zelle (Mittel über 30 Läufe), $K_T$ die Kosten der auf die Zelle abgestimmten Zeitregel, $K_F$ die Kosten von F mit exakter Frist; eine unzulässige Stufe (über 1,0 % verspätet) zählt mit $A = 0$.
"""
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zum Thema: [Tourenplanung optimieren](https://sebastianhanisch.net/tourenplanung-optimierung.html)."
)
