"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import plotly.graph_objects as go
from plotly.subplots import make_subplots

import hld_constants as C
import hld_results as R


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.28), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_timeline(rows, deps, label=""):
    """Zeitleiste: jede Sendung des Auszugs als Strecke von der Ankunft bis zur Abfahrt ihres Fahrzeugs, die Frist als Kreuz; verspätete Sendungen rot,
    Abfahrten als senkrechte Linien mit der Beladung. `rows`: (Index, Ankunft, Frist, Abfahrt, verspätet) aus hld_evaluation.excerpt."""
    fig = go.Figure()
    ok_x, ok_y, late_x, late_y = [], [], [], []
    for i, (_j, a, _d, t, late) in enumerate(rows):
        if t is None:
            continue
        xs, ys = (late_x, late_y) if late else (ok_x, ok_y)
        xs += [a, t, None]
        ys += [i, i, None]
    if ok_x:
        fig.add_trace(go.Scatter(x=ok_x, y=ok_y, mode="lines", line=dict(color=C.COLOR_OK, width=3), name="wartet bis zur Abfahrt", hoverinfo="skip"))
    if late_x:
        fig.add_trace(go.Scatter(x=late_x, y=late_y, mode="lines", line=dict(color=C.COLOR_LATE, width=3), name="verspätet", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[r[2] for r in rows], y=list(range(len(rows))), mode="markers", name="späteste Abfahrt (Frist)", marker=dict(symbol="x", color="#9aa5b4", size=7),
                             hovertemplate="Frist %{x:.2f}<extra></extra>"))
    first = rows[0][0]
    last = rows[-1][0]
    xs_all = [r[1] for r in rows] + [r[3] for r in rows if r[3] is not None]
    x0, x1 = min(xs_all), max(xs_all)
    dep_t, dep_n = [], []
    for t, members in deps:
        n_in = [j for j in members if first <= j <= last]
        if n_in and x0 <= t <= x1:
            dep_t.append(t)
            dep_n.append(len(members))
    if dep_t:
        fig.add_trace(go.Scatter(x=dep_t, y=[len(rows) + 1.0] * len(dep_t), mode="markers+text", text=[str(n) for n in dep_n], textposition="bottom center", name="Abfahrt (Zahl = Beladung)",
                                 marker=dict(symbol="triangle-up", size=10, color=C.RULE_COLORS["F"]), hovertemplate="Abfahrt bei %{x:.2f}<extra></extra>"))
    fig.update_xaxes(title_text="Zeit (in Fahrzeiten)", range=[x0 - 0.8, x1 + 1.2])
    fig.update_yaxes(title_text="Sendung im Auszug", autorange="reversed", showticklabels=False)
    return _base(fig, 430)


def build_rank_map(selected=None):
    """Rangfolge-Karte der 72 Zellen: blau = F gewinnt allein, grau = Q, T, QT und F liegen alle höchstens 2 % über 1/C (Frist egal); die gewählte Zelle ist umrandet."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"Kapazität C = {cap}" for cap in C.CAP_OPTIONS], horizontal_spacing=0.12)
    rows_lab = [(ca2, lam) for ca2 in C.CA2_OPTIONS for lam in C.LAM_OPTIONS]
    labels = [f"ca² {R.num(ca2, 0)} · λ {R.num(lam, 1)}" for ca2, lam in rows_lab]
    for ci, cap in enumerate(C.CAP_OPTIONS, start=1):
        z, text = [], []
        for ca2, lam in rows_lab:
            zr, tr = [], []
            for span in C.SPAN_OPTIONS:
                c = R.cell_of(lam, ca2, span, cap)
                zr.append(0 if c["klass"] == "F" else 1)
                tr.append(f"{R.cell_short(c)}: {'F gewinnt allein' if c['klass'] == 'F' else 'Frist egal'}; Kosten F {c['cost']['F']:.3f}, T {c['cost']['T']:.3f}".replace(".", ","))
            z.append(zr)
            text.append(tr)
        fig.add_trace(go.Heatmap(z=z, x=list(C.SPAN_OPTIONS), y=labels, text=text, hovertemplate="%{text}<extra></extra>", showscale=False, xgap=2, ygap=2,
                                 colorscale=[[0, "#2a6fb0"], [0.5, "#2a6fb0"], [0.5, "#c8d0da"], [1, "#c8d0da"]], zmin=0, zmax=1), row=1, col=ci)
        fig.update_yaxes(autorange="reversed", row=1, col=ci)
        if ci == 2:
            fig.update_yaxes(showticklabels=False, row=1, col=ci)
    if selected is not None:
        ci = C.CAP_OPTIONS.index(selected["C"]) + 1
        ri = rows_lab.index((selected["ca2"], selected["lam"]))
        xi = C.SPAN_OPTIONS.index(selected["span"])
        fig.add_shape(type="rect", x0=xi - 0.5, x1=xi + 0.5, y0=ri - 0.5, y1=ri + 0.5, line=dict(color="#1c2430", width=3), row=1, col=ci)
    fig.update_xaxes(title_text="Frist")
    return _base(fig, 470)


def build_savings_span():
    """Mittlere Ersparnis gegen „sofort“ je Fristspanne für Menge, Zeit, Frist und das Optimum (Mittel über die 24 Zellen je Spanne)."""
    sv = R.savings_vs_sofort_by_span()
    fig = go.Figure()
    for key, label, color in (("Q", "Menge Q", C.RULE_COLORS["Q"]), ("T", "Zeit T", C.RULE_COLORS["T"]), ("F", "Frist F", C.RULE_COLORS["F"]), ("opt", "Optimum", C.RULE_COLORS["Opt"])):
        ys = [sv[s][key] for s in C.SPAN_OPTIONS]
        fig.add_trace(go.Bar(x=[f"Frist {s}" for s in C.SPAN_OPTIONS], y=ys, name=label, marker_color=color, text=[f"{y:.0f}" for y in ys], textposition="outside",
                             hovertemplate=label + ": %{y:.1f} %<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Ersparnis gegen „sofort“ (%)", range=[0, 105])
    return _base(fig, 340)


def build_rule_costs(an, cell):
    """Kosten je Sendung auf dem Lauf (Balken) und als Mittel der gemessenen Zelle (Punkte) für die fünf Regeln, das Optimum und die gewählte Fristkenntnis."""
    keys = list(C.RULES) + ["Opt", "Stufe"]
    names = [C.RULE_LABELS.get(k, "Optimum" if k == "Opt" else "gewählte Fristkenntnis") for k in keys]
    live = [an["rules"][k]["cost"] if k in an["rules"] else (an["opt"]["cost"] if k == "Opt" else an["stage"]["cost"]) for k in keys]
    ref = [cell["cost"][k] if k in cell["cost"] else (cell["opt"]["cost"] if k == "Opt" else None) for k in keys]
    colors = [C.RULE_COLORS.get(k, "#8a8f98") for k in keys]
    fig = go.Figure(go.Bar(x=names, y=live, marker_color=colors, name="dieser Lauf", text=[f"{v:.3f}".replace(".", ",") for v in live], textposition="outside",
                           hovertemplate="%{x}: %{y:.3f}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[n for n, r in zip(names, ref) if r is not None], y=[r for r in ref if r is not None], mode="markers", name="Mittel der gemessenen Zelle (30 Läufe)",
                             marker=dict(symbol="diamond", size=9, color="#1c2430"), hovertemplate="Zellmittel %{y:.3f}<extra></extra>"))
    fig.update_yaxes(title_text="Kosten je Sendung (Abfahrten / Sendungen)", range=[0, 1.12])
    return _base(fig, 360)


def build_ladder():
    """Genauigkeitsleiter: Median von A (Anteil des F-Vorteils gegenüber der abgestimmten Zeitregel) je Stufe der Fristkenntnis, 53 Zellen."""
    xs = [C.LEVEL_LABELS[k] for k in C.LADDER_KEYS]
    ys = [R.ladder_row(k)["median"] for k in C.LADDER_KEYS]
    colors = ["#2a8f5b" if y >= 0.5 else ("#9aa5b4" if y >= -0.001 else "#c0392b") for y in ys]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color=colors, text=[f"{y:.2f}".replace(".", ",").replace("-", "−") for y in ys], textposition="outside",
                           hovertemplate="%{x}: Median A = %{y:.2f}<extra></extra>"))
    fig.add_hline(y=0.0, line_color="rgba(128,128,128,0.8)", line_width=1)
    fig.add_hline(y=0.5, line_dash="dot", line_color="rgba(128,128,128,0.8)")
    fig.update_yaxes(title_text="Median von A (53 Zellen)", range=[-0.9, 1.3])
    fig.update_xaxes(title_text="Fristkenntnis")
    return _base(fig, 360)


def build_saving_vs_praxis():
    """Ersparnis der Regel F gegenüber der Praxisregel T (ein Parameter für alle Fristspannen), Median über die 53 Zellen, je Stufe."""
    xs = [C.LEVEL_LABELS[k] for k in C.LADDER_KEYS]
    ys = [R.saving_vs_praxis(k)["median"] for k in C.LADDER_KEYS]
    fig = go.Figure(go.Bar(x=xs, y=ys, marker_color="#2a6fb0", text=[f"{y:.1f}".replace(".", ",") for y in ys], textposition="outside", hovertemplate="%{x}: %{y:.1f} %<extra></extra>"))
    fig.update_yaxes(title_text="Ersparnis gegen die Praxis-Zeitregel (%)", range=[0, 80])
    fig.update_xaxes(title_text="Fristkenntnis")
    return _base(fig, 360)


def build_praxis():
    """Kostenaufschlag der Praxis-Zeitregel gegen die auf die Zelle abgestimmte, Mittel über die zulässigen Zellen je Fristspanne (V1: auf „mittel“ abgestimmt, V2: auf die Mischung)."""
    fig = go.Figure()
    for variant, label, color in (("V1", "V1: auf „mittel“ abgestimmt", "#c77700"), ("V2", "V2: auf die Mischung abgestimmt", "#8a4fb0")):
        st = R.praxis_stats("T", variant)
        spans = [s for s in C.SPAN_OPTIONS if s in st["nach_spanne"]]
        fig.add_trace(go.Bar(x=[f"Frist {s}" for s in spans], y=[st["nach_spanne"][s] for s in spans], name=label, marker_color=color,
                             text=[f"{st['nach_spanne'][s]:.0f}" for s in spans], textposition="outside", hovertemplate=label + ": %{y:.1f} %<extra></extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(title_text="Kostenaufschlag (%)", range=[0, 340])
    return _base(fig, 340)
