"""Abfahrtsregeln für Sendungen mit Fristen: Ereignissimulation, Kennzahlen und Offline-Optimum (keine Löser).

Mechanisch übernommen aus `messreihe_holding/hl_sim.py` der Vormessung (Logik unverändert; tests/test_oracle_holding.py prüft sie gegen eine zweite, naive Umsetzung).

Modell (Zeiteinheit = Fahrzeit Δ = 1):
* Sendungen kommen mit Rate λ je Δ und Streuung ca² der Zwischenankunftszeit (0 fest, 1 Poisson, 4 stoßweise).
* Jede Sendung i hat einen **Spielraum** w_i, gleichverteilt auf [w_lo, w_hi] (in Δ): Frist minus Ankunft minus Fahrzeit. Späteste Abfahrt dl_i = a_i + w_i.
  Eine Sendung ist **verspätet**, wenn ihr Fahrzeug nach dl_i abfährt (strikt).
* Unbegrenzt viele Fahrzeuge der Kapazität C; jede Abfahrt kostet fix 1. Kosten je Sendung = Abfahrten / Sendungen = 1 / mittlere Beladung.
* Regeln (alle fahren sofort ab, sobald C Sendungen warten):
    S  sofort            : jede Sendung fährt bei Ankunft (= Menge 1)
    Q  Menge             : Abfahrt, sobald q Sendungen warten
    T  Zeit              : Abfahrt, wenn die älteste wartende Sendung T gewartet hat
    QT Menge-oder-Zeit   : Abfahrt bei q Sendungen oder wenn die älteste T gewartet hat
    F  fristgetrieben    : Abfahrt zur frühesten Frist der Wartenden (min dl); nutzt die Fristen (Information, die Q, T und QT nicht kennen)
* **Offline-Optimum** (`optimum_departures`): Mindestzahl der Abfahrten bei bekannten Ankünften und Fristen, ohne Verspätung, jede Abfahrtszeit erlaubt (nicht FIFO);
  an kleinen Instanzen gegen die exakte Teilmengen-DP `optimum_trips_dp` geprüft, nicht bewiesen.
Fenster: ausgewertet werden die Abfahrten mit t_lo <= Abfahrtszeit < t_hi (Einschwingzeit und Auslaufen fallen heraus)."""

import heapq

from hld_rng import make_sampler, streams

INF = float("inf")
N_WARM = 200        # Ankünfte vor dem Fenster
N_EVAL = 1800       # Ankünfte im Fenster
N_TAIL = 200        # Ankünfte danach (damit Abfahrten am Fensterende nicht am Datenende hängen)
N_TOTAL = N_WARM + N_EVAL + N_TAIL


def make_arrivals(lam, ca2, span, n_total, seed):
    """Ankunftszeiten a und späteste Abfahrten dl für den Zufalls-Seed `seed` (zwei getrennte Ströme: Zwischenankunft, Spielraum)."""
    r_arr, r_slack = streams(seed)
    draw = make_sampler(1.0 / lam, ca2, r_arr)
    lo, hi = span
    t = 0.0
    a, dl = [], []
    for _ in range(n_total):
        t += draw()
        a.append(t)
        dl.append(t + lo + (hi - lo) * r_slack.uniform())
    return a, dl


def window(a):
    """Fenster [t_lo, t_hi) einer Instanz: von der Ankunft Nr. N_WARM bis zur Ankunft Nr. N_WARM + N_EVAL."""
    return a[N_WARM], a[N_WARM + N_EVAL]


def rule_params(rule, C, q=None, T=None):
    """(q, T, use_dl) einer Regel; q wird auf C begrenzt."""
    if rule == "S":
        return 1, INF, False
    if rule == "Q":
        return min(q, C), INF, False
    if rule == "T":
        return C, T, False
    if rule == "QT":
        return min(q, C), T, False
    if rule == "F":
        return C, INF, True
    raise ValueError(rule)


def simulate(a, dl, C, q, T, use_dl, t_lo=-INF, t_hi=INF):
    """Eine Regel auf einer Instanz. Rückgabe: Abfahrten, Sendungen, Summe Wartezeit, verspätete Sendungen im Fenster
    sowie die Gesamtzahl abgefahrener Sendungen und die am Ende noch wartenden (Zählprobe)."""
    trips = ships = viol = 0
    delay = 0.0
    departed_total = 0
    cnt = 0
    sum_a = 0.0
    t0 = 0.0
    mindl = INF
    bdl = []
    for i in range(len(a)):
        ai = a[i]
        while cnt:
            d = t0 + T                      # T = INF ergibt INF
            if use_dl and mindl < d:
                d = mindl
            if d < ai:                      # Abfahrt strikt vor der nächsten Ankunft; eine Ankunft genau bei d fährt noch mit
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
                mindl = INF
                bdl = []
            else:
                break
        if not cnt:
            t0 = ai
        cnt += 1
        sum_a += ai
        d_i = dl[i]
        bdl.append(d_i)
        if d_i < mindl:
            mindl = d_i
        if cnt >= q:                        # Mengen- bzw. Kapazitätsabfahrt bei dieser Ankunft
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
            mindl = INF
            bdl = []
    # nach der letzten Ankunft nur noch zeitgesteuerte Abfahrten
    while cnt:
        d = t0 + T
        if use_dl and mindl < d:
            d = mindl
        if d == INF:
            break
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
        mindl = INF
        bdl = []
    return trips, ships, delay, viol, departed_total, cnt


def metrics(res, C):
    """Kennzahlen aus dem Ergebnis von `simulate`: Kosten je Sendung, mittlere Verzögerung, Anteil verspäteter Sendungen, Auslastung."""
    trips, ships, delay, viol = res[0], res[1], res[2], res[3]
    if ships == 0:
        return {"cost": float("nan"), "delay": float("nan"), "viol": float("nan"), "util": float("nan"), "trips": 0, "ships": 0}
    return {"cost": trips / ships, "delay": delay / ships, "viol": viol / ships, "util": ships / (trips * C), "trips": trips, "ships": ships}


def optimum_departures(a, dl, C):
    """Offline-Optimum: Liste (Abfahrtszeit, Beladung) einer Abfahrtsfolge mit der kleinsten Zahl Abfahrten (früheste Frist abwarten, C Sendungen mit den frühesten Fristen mitnehmen)."""
    heap = []
    i = 0
    n = len(a)
    deps = []
    while i < n or heap:
        if heap:
            e = heap[0]
            if i < n and a[i] <= e:
                heapq.heappush(heap, dl[i])
                i += 1
                continue
            k = min(C, len(heap))
            for _ in range(k):
                heapq.heappop(heap)
            deps.append((e, k))
        else:
            heapq.heappush(heap, dl[i])
            i += 1
    return deps


def optimum_metrics(a, dl, C, t_lo, t_hi):
    deps = optimum_departures(a, dl, C)
    trips = sum(1 for d, _ in deps if t_lo <= d < t_hi)
    ships = sum(k for d, k in deps if t_lo <= d < t_hi)
    if ships == 0:
        return {"cost": float("nan"), "util": float("nan"), "trips": 0, "ships": 0}
    return {"cost": trips / ships, "util": ships / (trips * C), "trips": trips, "ships": ships}


def optimum_trips_dp(a, dl, C):
    """Exakte Mindestzahl Abfahrten per DP über Teilmengen (nur für n <= 10): eine Gruppe ist zulässig, wenn sie höchstens C Sendungen
    hat und max(a) <= min(dl) gilt (eine gemeinsame Abfahrtszeit existiert)."""
    n = len(a)
    full = (1 << n) - 1
    ok = [False] * (1 << n)
    for m in range(1, 1 << n):
        idx = [j for j in range(n) if m >> j & 1]
        ok[m] = len(idx) <= C and max(a[j] for j in idx) <= min(dl[j] for j in idx)
    f = [10 ** 9] * (1 << n)
    f[0] = 0
    for m in range(1, 1 << n):
        low = m & -m                        # die Sendung mit dem kleinsten Index liegt in der ersten Gruppe
        s = m
        while s:
            if s & low and ok[s] and f[m ^ s] + 1 < f[m]:
                f[m] = f[m ^ s] + 1
            s = (s - 1) & m
    return f[full]


def run_rule(inst, C, rule, q=None, T=None):
    """Kennzahlen einer Regel auf einer Instanz (a, dl) im Fenster."""
    a, dl = inst
    t_lo, t_hi = window(a)
    qq, TT, ud = rule_params(rule, C, q, T)
    res = simulate(a, dl, C, qq, TT, ud, t_lo, t_hi)
    return metrics(res, C)


def trace_departures(a, dl, C, q, T, dl_est=None, m=0.0):
    """Alle Abfahrten einer Regel als Liste (Abfahrtszeit, [Indizes der mitfahrenden Sendungen]) — für die Zeitleiste der App.

    Dieselbe Regel wie `simulate` (und, mit `dl_est`, wie `hld_knowledge.simulate_est`); tests/test_oracle_holding.py prüft, dass Abfahrten, Beladungen und verspätete
    Sendungen gleich sind. `dl_est`: geschätzte späteste Abfahrten (Regel F mit Schätzung), `m`: Sicherheitsabstand."""
    deps = []
    members = []
    t0 = 0.0
    mind = INF

    def due():
        d = t0 + T if T < INF else INF
        if dl_est is not None and mind - m < d:
            d = mind - m
        return d

    def depart(t):
        nonlocal members, mind
        deps.append((t, members))
        members = []
        mind = INF

    for i, ai in enumerate(a):
        while members:
            d = due()
            if d < ai:
                depart(d)
            else:
                break
        if not members:
            t0 = ai
        members.append(i)
        if dl_est is not None and dl_est[i] < mind:
            mind = dl_est[i]
        if len(members) >= q or (dl_est is not None and mind - m <= ai):
            depart(ai)
    while members:
        d = due()
        if d == INF:
            break
        depart(d)
    return deps
