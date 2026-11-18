"""Stufen der Fristkenntnis für die Regel F (Restmessung AP 0 der Vormessung, mechanisch übernommen aus `messreihe_holding_ap0/ap0_core.py`).

F fährt ab, sobald C Sendungen warten oder zur Zeit **min(d̂) − m** der Wartenden (d̂ = geschätzte späteste Abfahrt, m = Sicherheitsabstand ≥ 0); ist diese Zeit bei der Ankunft
der letzten Sendung schon vorbei, fährt es sofort bei deren Ankunft. Gezählt wird mit den **echten** Fristen: verspätet ist eine Sendung, deren Fahrzeug nach ihrer echten Frist abfährt.

Stufen der Schätzung (Spielraum-Klasse = untere und obere Grenze der Fristspanne):
* exakt: d̂ = d (die Regel F der Vormessung).
* grob: nur die Fristklasse ist bekannt, d̂ = Ankunft + unterer Rand der Spanne (konservativ, nie über der echten Frist).
* verr..._kl (Schätzfehler σ als Anteil des mittleren Spielraums w̄ der Spanne): d̂ = min(max(d + σ·w̄·z, Ankunft + unterer Rand), Ankunft + oberer Rand), z standardnormalverteilt
  („mit Klassenwissen“: die Schätzung bleibt in der Klasse).
* verr25, verr50 (Variante 1 der Restmessung): ohne Klassenwissen, d̂ = d + σ·w̄·z."""

import hld_constants as C
from hld_sim import INF, metrics, window


def mean_slack(span):
    lo, hi = C.SPANS[span]
    return (lo + hi) / 2.0


def estimate_deadlines(a, dl, span, level, z):
    """Geschätzte späteste Abfahrten d̂ je Sendung für die Stufe `level` (Schlüssel der Ergebnisdatei) und den Rauschvektor `z`."""
    if level == "exakt":
        return list(dl)
    if level in ("verr25", "verr50"):
        s = C.SIGMA[level] * mean_slack(span)
        return [d + s * zi for d, zi in zip(dl, z)]
    if level.endswith("_kl"):
        s = C.SIGMA[level] * mean_slack(span)
        lo, hi = C.SPANS[span]
        return [min(max(d + s * zi, ai + lo), ai + hi) for ai, d, zi in zip(a, dl, z)]
    if level == "grob":
        lo = C.SPANS[span][0]
        return [ai + lo for ai in a]
    raise ValueError(level)


def simulate_est(a, dl, dl_est, C_cap, m, t_lo=-INF, t_hi=INF):
    """Regel F mit geschätzten Fristen. Rückgabe wie `hld_sim.simulate`: Abfahrten, Sendungen, Summe Wartezeit, verspätete Sendungen im Fenster,
    abgefahrene Sendungen gesamt, am Ende Wartende."""
    trips = ships = viol = 0
    delay = 0.0
    departed_total = 0
    cnt = 0
    sum_a = 0.0
    mind = INF
    bdl = []
    for i in range(len(a)):
        ai = a[i]
        while cnt:
            d = mind - m
            if d < ai:
                departed_total += cnt
                if t_lo <= d < t_hi:
                    trips += 1
                    ships += cnt
                    delay += cnt * d - sum_a
                    for x in bdl:
                        if x < d:
                            viol += 1
                cnt = 0
                sum_a = 0.0
                mind = INF
                bdl = []
            else:
                break
        cnt += 1
        sum_a += ai
        bdl.append(dl[i])
        if dl_est[i] < mind:
            mind = dl_est[i]
        if cnt >= C_cap or mind - m <= ai:      # Kapazität erreicht oder Schätzung abgelaufen: Abfahrt bei dieser Ankunft
            departed_total += cnt
            if t_lo <= ai < t_hi:
                trips += 1
                ships += cnt
                delay += cnt * ai - sum_a
                for x in bdl:
                    if x < ai:
                        viol += 1
            cnt = 0
            sum_a = 0.0
            mind = INF
            bdl = []
    while cnt:
        d = mind - m
        departed_total += cnt
        if t_lo <= d < t_hi:
            trips += 1
            ships += cnt
            delay += cnt * d - sum_a
            for x in bdl:
                if x < d:
                    viol += 1
        cnt = 0
        sum_a = 0.0
        mind = INF
        bdl = []
    return trips, ships, delay, viol, departed_total, cnt


def run_est(a, dl, span, level, C_cap, m, z):
    """Kennzahlen der Regel F mit der Fristkenntnis `level` und dem Sicherheitsabstand m auf einer Instanz im Fenster; Rückgabe wie `hld_sim.metrics` plus `dl_est`."""
    est = estimate_deadlines(a, dl, span, level, z)
    t_lo, t_hi = window(a)
    out = metrics(simulate_est(a, dl, est, C_cap, m, t_lo, t_hi), C_cap)
    out["dl_est"] = est
    return out
