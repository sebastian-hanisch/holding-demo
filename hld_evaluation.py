"""Live-Analyse eines Laufs (die fünf Regeln, das Offline-Optimum und die gewählte Stufe der Fristkenntnis), Kennzahlen und Verdikte als reine Funktionen: verdict_*(...) -> (Art, Text)."""

from dataclasses import dataclass

import hld_constants as C
import hld_knowledge as K
import hld_results as R
import hld_sim as S
from hld_rng import noise_vector


@dataclass(frozen=True)
class Settings:
    lam: float = C.DEFAULT_LAM
    ca2: float = C.DEFAULT_CA2
    span: str = C.DEFAULT_SPAN
    cap: int = C.DEFAULT_CAP
    wissen: str = C.DEFAULT_WISSEN
    seed: int = C.DEFAULT_SEED


def make_instance(settings: Settings):
    """Ankunftszeiten und späteste Abfahrten (echte Fristen) des Laufs."""
    return S.make_arrivals(settings.lam, settings.ca2, C.SPANS[settings.span], S.N_TOTAL, settings.seed)


def rule_args(cell, rule):
    """(q, T) einer Regel aus den auf die Zelle abgestimmten Parametern der Vormessung."""
    p = cell["params"][rule]
    return p.get("q"), p.get("T")


def stage_rule(settings: Settings, cell):
    """Beschreibung der Regel, die zur gewählten Fristkenntnis gehört: ('F', ...) bei exakt; ('T', param) bei der Praxisregel; ('E', level, m) bei Schätzung."""
    if settings.wissen == "exakt":
        return ("F", None, None)
    if settings.wissen == "praxis":
        return ("T", cell["praxis"]["T_V2"]["param"], None)
    level = C.WISSEN_LEVEL[settings.wissen]
    return ("E", level, cell["levels"][level]["m"])


def stage_run(settings: Settings, cell, a, dl, z=None):
    """Kennzahlen der Regel der gewählten Fristkenntnis auf dem Lauf (im Fenster). `z`: Rauschvektor (nur bei Schätzung, sonst nicht nötig)."""
    kind, p1, p2 = stage_rule(settings, cell)
    t_lo, t_hi = S.window(a)
    if kind == "F":
        return S.metrics(S.simulate(a, dl, settings.cap, settings.cap, S.INF, True, t_lo, t_hi), settings.cap)
    if kind == "T":
        return S.metrics(S.simulate(a, dl, settings.cap, settings.cap, p1, False, t_lo, t_hi), settings.cap)
    if p1 == "grob":
        z = [0.0] * len(a)
    elif z is None:
        z = noise_vector(settings.seed, len(a))
    out = K.run_est(a, dl, settings.span, p1, settings.cap, p2, z)
    out.pop("dl_est", None)
    return out


def analyse(settings: Settings) -> dict:
    """Ein Lauf: alle fünf Regeln mit den auf die Zelle abgestimmten Parametern der Vormessung, das Offline-Optimum und die Regel der gewählten Fristkenntnis; deterministisch bei gleichem Zufalls-Seed."""
    cell = R.cell_of(settings.lam, settings.ca2, settings.span, settings.cap)
    a, dl = make_instance(settings)
    t_lo, t_hi = S.window(a)
    rules = {}
    for r in C.RULES:
        q, T = rule_args(cell, r)
        qq, TT, ud = S.rule_params(r, settings.cap, q, T)
        rules[r] = S.metrics(S.simulate(a, dl, settings.cap, qq, TT, ud, t_lo, t_hi), settings.cap)
    opt = S.optimum_metrics(a, dl, settings.cap, t_lo, t_hi)
    stage = stage_run(settings, cell, a, dl)
    return {"settings": settings, "rules": rules, "opt": opt, "stage": stage, "arrivals": len(a)}


def trace_of(settings: Settings, key: str):
    """Abfahrten einer Regel auf dem Lauf für die Zeitleiste: (a, dl, Abfahrten) mit Abfahrten = [(Zeit, [Indizes])]. `key`: S, Q, T, QT, F oder 'stufe' (Regel der Fristkenntnis)."""
    cell = R.cell_of(settings.lam, settings.ca2, settings.span, settings.cap)
    a, dl = make_instance(settings)
    cap = settings.cap
    if key == "stufe":
        kind, p1, p2 = stage_rule(settings, cell)
        if kind == "F":
            return a, dl, S.trace_departures(a, dl, cap, cap, S.INF, dl_est=dl, m=0.0)
        if kind == "T":
            return a, dl, S.trace_departures(a, dl, cap, cap, p1)
        z = [0.0] * len(a) if p1 == "grob" else noise_vector(settings.seed, len(a))
        est = K.estimate_deadlines(a, dl, settings.span, p1, z)
        return a, dl, S.trace_departures(a, dl, cap, cap, S.INF, dl_est=est, m=p2)
    q, T = rule_args(cell, key)
    qq, TT, ud = S.rule_params(key, cap, q, T)
    return a, dl, S.trace_departures(a, dl, cap, qq, TT, dl_est=dl if ud else None, m=0.0)


def excerpt(a, dl, deps, n=C.EXCERPT_ARRIVALS):
    """Auszug der Zeitleiste: die Sendungen mit den Indizes N_WARM bis N_WARM + n und ihre Abfahrten. Liefert Zeilen (Index, Ankunft, Frist, Abfahrt, verspätet)."""
    lo, hi = S.N_WARM, S.N_WARM + n
    depart = {}
    for t, members in deps:
        for j in members:
            depart[j] = t
    rows = []
    for j in range(lo, hi):
        t = depart.get(j)
        rows.append((j, a[j], dl[j], t, t is not None and t > dl[j]))
    return rows


def fmt_cost(x, digits=3):
    return R.num(x, digits)


def pct(x, digits=1):
    return f"{R.num(x, digits)} %"


def late_text(v):
    return pct(100.0 * v, 2)


def depart_stats(deps, a, dl, cap):
    """Zählprobe der Zeitleiste: Abfahrten und Sendungen im Auszug."""
    return {"abfahrten": len(deps), "sendungen": sum(len(m) for _, m in deps)}


# --- Verdikte (rein: die App ruft st.<Art>(Text), der Test prüft jede Zahl im Text) ------------------------------------------------------------

STATE_KIND = {"gleich": "info", "F": "success", "sonst": "info"}
STATE_HEAD = {"gleich": "Hier ist die Frist egal", "F": "Hier zählt die Frist", "sonst": "Hier gewinnt keine Regel klar"}


def verdict_state(cell) -> tuple[str, str]:
    """Erste Meldung (zwei Zustände) aus der gemessenen Zelle, nicht aus dem einen Lauf; nennt den Informationsvorsprung von F und die günstige Annahme der abgestimmten Regeln."""
    klass = cell["klass"]
    cost = cell["cost"]
    cap = cell["C"]
    best = cell["best_simple"]
    head = f"**{STATE_HEAD[klass]}.**"
    kosten = (f"Kosten je Sendung in dieser Zelle (Mittel über {cell['runs']} Läufe; 1,000 heißt: jede Sendung fährt allein): sofort {fmt_cost(cost['S'])}, Menge {fmt_cost(cost['Q'])}, "
              f"Zeit {fmt_cost(cost['T'])}, Menge-oder-Zeit {fmt_cost(cost['QT'])}, Frist {fmt_cost(cost['F'])}, Optimum bei bekannten Ankünften {fmt_cost(cell['opt']['cost'])}.")
    if klass == "gleich":
        mid = (f"In der gemessenen Zelle ({R.cell_text(cell)}) liegen Menge, Zeit, Menge-oder-Zeit und Frist alle höchstens {R.num(100 * (C.FILL_FACTOR - 1), 0)} % über 1/C = {fmt_cost(1.0 / cap)}: "
               f"das Fahrzeug ist fast immer voll, bevor eine Frist droht (Deutung, nicht gesondert gemessen): unter diesen vier Regeln unterscheiden sich die Kosten höchstens um {R.num(100 * (C.FILL_FACTOR - 1), 0)} %, "
               f"„sofort“ kostet mit {fmt_cost(cost['S'])} etwa das {cap}-Fache. ")
    elif klass == "F":
        mid = (f"In der gemessenen Zelle ({R.cell_text(cell)}) gewinnt die fristgetriebene Regel F allein und spart gegenüber der besten einfachen Regel ({best}) "
               f"**{pct(cell['saving_F'])}** Abfahrten; F liegt {pct(100.0 * (cost['F'] - cell['opt']['cost']) / cell['opt']['cost'], 2)} über dem Optimum bei bekannten Ankünften (bezogen auf das Optimum). ")
    else:
        mid = f"In der gemessenen Zelle ({R.cell_text(cell)}) gewinnt keine Regel allein und es füllt sich auch nicht alles vor der Frist. "
    praxis = R.aufschlag(cell, "T", "V2")
    caveat = (f"**Zwei Einschränkungen:** F kennt die Fristen per Konstruktion (Informationsvorsprung); Menge, Zeit und Menge-oder-Zeit sind in dieser Zelle mit Kenntnis der Fristverteilung abgestimmt, "
              f"ihr Ergebnis ist eine günstige Annahme für Regeln ohne diese Kenntnis (grobes Parameter-Raster, Näherung an die beste Wahl, kein Optimum der Regelklasse): eine Zeitregel mit einem Parameter für alle Fristspannen kostet hier {pct(praxis)} mehr. "
              f"(Zustand nach dem Kriterium der Vormessung: „Frist egal“, wenn Menge, Zeit, Menge-oder-Zeit und Frist alle höchstens 2 % über 1/C liegen; „Frist zählt“ heißt nur, dass das nicht gilt und F allein gewinnt, nicht notwendig einen großen Vorteil; Schwelle gesetzt, nicht hergeleitet.)")
    return STATE_KIND[klass], f"{head} {mid}{kosten} {caveat}"


def verdict_live(an: dict) -> tuple[str, str]:
    """Der eine Lauf: Kosten je Regel und Verspätung, ohne Urteilswort."""
    r = an["rules"]
    st = an["stage"]
    text = (
        f"Auf diesem Lauf (ein Lauf, kein Beleg; {an['arrivals']} Ankünfte, ausgewertet die Abfahrten im Fenster von Ankunft Nr. {S.N_WARM} bis {S.N_WARM + S.N_EVAL}, rund {S.N_EVAL} Sendungen): Kosten je Sendung sofort {fmt_cost(r['S']['cost'])}, Menge {fmt_cost(r['Q']['cost'])}, "
        f"Zeit {fmt_cost(r['T']['cost'])}, Menge-oder-Zeit {fmt_cost(r['QT']['cost'])}, Frist {fmt_cost(r['F']['cost'])}, Optimum {fmt_cost(an['opt']['cost'])}; "
        f"Anteil verspäteter Sendungen Menge {late_text(r['Q']['viol'])}, Zeit {late_text(r['T']['viol'])}, Frist {late_text(r['F']['viol'])}. "
        f"Gewählte Fristkenntnis ({C.WISSEN_LABELS[an['settings'].wissen]}): Kosten {fmt_cost(st['cost'])}, verspätet {late_text(st['viol'])}."
    )
    return "info", text


def verdict_ladder(cell, settings: Settings) -> tuple[str, str]:
    """Kernabschnitt ②: die gewählte Stufe der Fristkenntnis in dieser Zelle und über die 53 Zellen mit F als Sieger."""
    w = settings.wissen
    level = C.WISSEN_LEVEL[w]
    if w == "praxis":
        v2 = cell["praxis"]["T_V2"]
        text = (f"**Keine Kenntnis der Fristspanne:** eine Zeitregel mit einem Parameter (T = {R.num(v2['param'], 2)}) für alle Fristspannen kostet in dieser Zelle {fmt_cost(v2['cost'])} je Sendung statt "
                f"{fmt_cost(cell['cost']['T'])} mit der auf die Zelle abgestimmten T ({pct(R.aufschlag(cell, 'T', 'V2'))} mehr), verspätet {late_text(v2['viol'])}. "
                f"Über alle {R.praxis_stats('T', 'V2')['zellen']} Zellen beträgt der mittlere Aufschlag {pct(R.praxis_stats('T', 'V2')['aufschlag'])}; eine auf „mittel“ abgestimmte Zeitregel ist in "
                f"{R.praxis_stats('T', 'V1')['unzulaessig']} von {R.praxis_stats('T', 'V1')['zellen']} Zellen mit Frist eng oder weit unzulässig (über 1,0 % verspätet).")
        return "info", text
    lv = cell["levels"][level]
    row = R.ladder_row(level)
    if cell["A"] is not None:
        a_text = f"In dieser Zelle ist A = {R.sgn(cell['A'][level], 2)} (A = Anteil des F-Vorteils gegenüber der auf die Zelle abgestimmten Zeitregel T; 1 heißt: der ganze Vorteil von F, 0: nicht besser als T)."
    else:
        a_text = "Die Kennzahl A gibt es nur in den 53 Zellen, in denen F allein gewinnt; in dieser Zelle gewinnt F nicht allein."
    sav = R.saving_vs_praxis(level)
    text = (f"**{C.WISSEN_LABELS[w][0].upper() + C.WISSEN_LABELS[w][1:]}:** in dieser Zelle kostet die Fristregel {fmt_cost(lv['cost'])} je Sendung (exakte Fristen {fmt_cost(cell['cost']['F'])}, abgestimmte Zeitregel {fmt_cost(cell['cost']['T'])}), "
            f"verspätet {late_text(lv['viol'])}{'' if lv['zulaessig'] else ' (über 1,0 %: unzulässig)'}; Sicherheitsabstand m = {R.num(lv['m'], 2)} Fahrzeiten. {a_text} "
            f"Über die {row['zellen']} Zellen mit F als Sieger: Median A = {R.sgn(row['median'], 2)}, A ≥ 0,5 in {row['ab_05']} Zellen; gegen die Praxisregel T (ein Parameter für alle Fristspannen) spart diese Stufe im Median {pct(sav['median'])}.")
    return "info", text


def verdict_ladder_overall() -> tuple[str, str]:
    """Die Genauigkeitsleiter über die 53 Zellen mit F als Sieger (Median von A und Ersparnis gegen die Praxisregel T)."""
    parts = []
    for level in C.LADDER_KEYS:
        row = R.ladder_row(level)
        sav = R.saving_vs_praxis(level)
        parts.append(f"{C.LEVEL_LABELS[level]}: A = {R.sgn(row['median'], 2)}, gegen die Praxisregel {pct(sav['median'])}")
    v1 = R.ladder_row("verr25")
    text = (f"**Genauigkeitsleiter** (Median über die {len(R.z53())} Zellen, in denen F allein gewinnt): " + "; ".join(parts) + ". "
            f"Der vorab festgelegte Schätzer ohne Klassenwissen bei 25 % Schätzfehler hatte Median A = {R.sgn(v1['median'], 2)} (Urteil nach den Schwellen der Restmessung, gegenüber einer Zeitregel, die die Fristspanne kennt: „Fristkenntnis lohnt nur, wenn sie genau ist“, 5 bis 10 % Fehler); "
            f"die Stufen mit 5 % und 10 % Schätzfehler und mit Klassenwissen sind Nachmessungen ohne eigene Schwelle.")
    return "info", text


def verdict_regeln() -> tuple[str, str]:
    """Tab Regeln: wer gewinnt mit und ohne Fristkenntnis (Zählungen über die 72 Zellen)."""
    wc = R.winner_counts()
    wf = R.without_f_winner()
    cc = R.class_counts()
    text = (f"**Mit Fristkenntnis** gewinnt F in {wc['allein']['F']} von {cc['zellen']} Zellen allein (Sieger oder gleichauf in {wc['sieger_oder_gleichauf']['F']}); Menge, Zeit, Menge-oder-Zeit und sofort gewinnen in keiner Zelle allein. "
            f"**Ohne Fristkenntnis** (nur S, Q, T, QT) ist die Zeitregel in {wf['T']} von {cc['zellen']} Zellen Sieger oder gleichauf, Menge-oder-Zeit in {wf['QT']}, die Menge in {wf['Q']}, sofort in {wf['S']}. "
            f"Menge-oder-Zeit hat mit den abgestimmten Parametern in {R.qt_equals_t()} von {cc['zellen']} Zellen dieselben Kosten wie die Zeitregel; die Mengenschwelle greift nie.")
    return "info", text


def verdict_optimum() -> tuple[str, str]:
    """Kernabschnitt ③: Abstand zum Offline-Optimum über die 72 Zellen (F und beste einfache Regel)."""
    f = R.gap_to_opt("F")
    b = R.gap_to_opt("best_simple")
    top = "; ".join(f"{R.cell_short(c)} ({R.num(g, 1)} %)" for g, c in f["top3"])
    text = (f"**Abstand zum Offline-Optimum** (Kosten − Optimum) / Optimum, über die 72 Zellen: F Median {R.num(f['median'], 1)} %, drittes Quartil {R.num(f['q3'], 1)} %, Maximum {R.num(f['max'], 1)} %, über 1 % in {f['ueber_1']} Zellen; "
            f"beste einfache Regel Median {R.num(b['median'], 1)} %, Maximum {R.num(b['max'], 1)} %. Die größten drei F-Abstände: {top}. "
            "Das Optimum nimmt bekannte Ankünfte an und ist an 600 Kleininstanzen gegen die exakte Teilmengen-DP geprüft, nicht bewiesen.")
    return "info", text
