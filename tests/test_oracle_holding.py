"""Orakel-Tests (unabhängiger Rechenweg, DEMO-PLAYBOOK §12): Die ereignisdiskrete Simulation `hld_sim.simulate` und die Fristschätzung `hld_knowledge.simulate_est` werden gegen eine
zweite, naive Umsetzung (Liste der Wartenden, Ereignis für Ereignis) verglichen; die Zeitregel gegen die Erneuerungsrechnung (Poisson); das Optimum gegen die exakte
Teilmengen-Rechnung; die Zeitleiste (`trace_departures`) gegen die Simulation. Jeweils auf Handbeispielen und auf Zufallsinstanzen."""

import math

import pytest

import hld_constants as C
import hld_knowledge as K
import hld_sim as S
from hld_rng import make_sampler, noise_vector, streams

INF = float("inf")


def naive(a, dl, cap, q, T, use_est, dl_est=None, m=0.0):
    """Zweite Umsetzung: eine Liste der Wartenden; vor jeder Ankunft und nach jeder Ankunft wird geprüft, ob ein Fahrzeug fährt. Rückgabe: (Liste (Zeit, Mitglieder), am Ende Wartende)."""
    deps = []
    waiting = []   # Indizes
    est = dl_est if dl_est is not None else dl

    def due_time():
        times = []
        if T < INF:
            times.append(a[waiting[0]] + T)               # die älteste wartende Sendung steht vorn (Ankunftsreihenfolge)
        if use_est:
            times.append(min(est[j] for j in waiting) - m)
        return min(times) if times else INF

    for i in range(len(a)):
        while waiting and due_time() < a[i]:
            deps.append((due_time(), list(waiting)))
            waiting = []
        waiting.append(i)
        if len(waiting) >= q or (use_est and min(est[j] for j in waiting) - m <= a[i]):
            deps.append((a[i], list(waiting)))
            waiting = []
    while waiting:
        d = due_time()
        if d == INF:
            break
        deps.append((d, list(waiting)))
        waiting = []
    return deps, waiting


def stats(deps, a, dl):
    trips = len(deps)
    ships = sum(len(m) for _, m in deps)
    delay = sum(t - a[j] for t, m in deps for j in m)
    late = sum(1 for t, m in deps for j in m if t > dl[j])
    return trips, ships, delay, late


def _instances(count, n=300):
    out = []
    for k in range(count):
        lam = C.LAM_OPTIONS[k % 4]
        ca2 = C.CA2_OPTIONS[(k // 4) % 3]
        span = C.SPAN_OPTIONS[(k // 12) % 3]
        cap = C.CAP_OPTIONS[k % 2]
        a, dl = S.make_arrivals(lam, ca2, C.SPANS[span], n, 7000 + k)
        out.append((lam, ca2, span, cap, a, dl))
    return out


RULES = {"S": (lambda cap: (1, INF, False)), "Q": (lambda cap: (min(4, cap), INF, False)), "T": (lambda cap: (cap, 2.5, False)),
         "QT": (lambda cap: (3, 2.5, False)), "F": (lambda cap: (cap, INF, True))}


@pytest.mark.parametrize("rule", list(RULES))
def test_simulation_gleich_naiver_umsetzung_auf_zufallsinstanzen(rule):
    for lam, ca2, span, cap, a, dl in _instances(24):
        q, T, ud = RULES[rule](cap)
        got = S.simulate(a, dl, cap, q, T, ud)
        deps, left = naive(a, dl, cap, q, T, ud, dl_est=dl if ud else None, m=0.0)
        trips, ships, delay, late = stats(deps, a, dl)
        assert (got[0], got[1], got[3]) == (trips, ships, late), (rule, lam, ca2, span, cap)
        assert got[2] == pytest.approx(delay, rel=1e-9, abs=1e-9)
        assert got[4] + got[5] == len(a) and got[5] == len(left)   # Zählprobe: jede Sendung genau einmal gefahren oder am Ende wartend


@pytest.mark.parametrize("rule", list(RULES))
def test_zeitleiste_gleich_simulation_auf_zufallsinstanzen(rule):
    for lam, ca2, span, cap, a, dl in _instances(24):
        q, T, ud = RULES[rule](cap)
        deps = S.trace_departures(a, dl, cap, q, T, dl_est=dl if ud else None, m=0.0)
        got = S.simulate(a, dl, cap, q, T, ud)
        trips, ships, delay, late = stats(deps, a, dl)
        assert (got[0], got[1], got[3]) == (trips, ships, late)
        assert got[2] == pytest.approx(delay, rel=1e-9, abs=1e-9)
        assert all(len(m) <= cap for _, m in deps)


@pytest.mark.parametrize("level", ["verr05_kl", "verr10_kl", "verr25_kl", "verr25", "grob"])
def test_fristschaetzung_gleich_naiver_umsetzung_und_zeitleiste(level):
    for lam, ca2, span, cap, a, dl in _instances(12, n=200):
        z = noise_vector(11, len(a))
        est = K.estimate_deadlines(a, dl, span, level, z)
        m = 0.8
        got = K.simulate_est(a, dl, est, cap, m)
        deps, left = naive(a, dl, cap, cap, INF, True, dl_est=est, m=m)
        trips, ships, delay, late = stats(deps, a, dl)
        assert (got[0], got[1], got[3]) == (trips, ships, late) and got[2] == pytest.approx(delay, rel=1e-9, abs=1e-9)
        td = S.trace_departures(a, dl, cap, cap, INF, dl_est=est, m=m)
        t_trips, t_ships, t_delay, t_late = stats(td, a, dl)
        assert (t_trips, t_ships, t_late) == (trips, ships, late) and t_delay == pytest.approx(delay, rel=1e-9, abs=1e-9)
        assert got[4] + got[5] == len(a)


def test_exakte_frist_mit_m_null_gleich_regel_f():
    for lam, ca2, span, cap, a, dl in _instances(12):
        f = S.simulate(a, dl, cap, cap, INF, True)
        e = K.simulate_est(a, dl, list(dl), cap, 0.0)
        assert f == e, (lam, ca2, span, cap)


def test_grob_schaetzung_nie_ueber_der_echten_frist_und_nie_verspaetet():
    for lam, ca2, span, cap, a, dl in _instances(12):
        est = K.estimate_deadlines(a, dl, span, "grob", [0.0] * len(a))
        assert all(e <= d + 1e-12 for e, d in zip(est, dl))
        res = K.simulate_est(a, dl, est, cap, 0.0)
        assert res[3] == 0


def test_klassenwissen_haelt_die_schaetzung_in_der_fristklasse():
    lo, hi = C.SPANS["mittel"]
    a, dl = S.make_arrivals(1.0, 1.0, (lo, hi), 400, 5)
    for level in ("verr05_kl", "verr25_kl", "verr50_kl"):
        est = K.estimate_deadlines(a, dl, "mittel", level, noise_vector(5, 400))
        assert all(ai + lo - 1e-12 <= e <= ai + hi + 1e-12 for ai, e in zip(a, est))
    z0 = [0.0] * 400
    assert K.estimate_deadlines(a, dl, "mittel", "verr25_kl", z0) == pytest.approx(dl)   # Rauschen null: die echte Frist liegt in der Klasse


def test_handbeispiel_alle_regeln(hand):
    a, dl, cap = hand["a"], hand["dl"], hand["C"]
    s = S.simulate(a, dl, cap, 1, INF, False)
    assert (s[0], s[1], s[5]) == (5, 5, 0)
    q = S.simulate(a, dl, cap, 2, INF, False)
    assert (q[0], q[1], q[5]) == (2, 4, 1)
    t = S.simulate(a, dl, cap, cap, 1.5, False)
    assert (t[0], t[1], t[2], t[3]) == (3, 5, 3.5, 0)
    f = S.simulate(a, dl, cap, cap, INF, True)
    assert (f[0], f[1], f[2], f[3]) == (3, 5, 4.0, 0)
    assert S.optimum_trips_dp(a, dl, cap) == 3 and len(S.optimum_departures(a, dl, cap)) == 3
    assert [(t_, len(m)) for t_, m in S.trace_departures(a, dl, cap, cap, 1.5)] == [(1.0, 2), (3.0, 2), (11.5, 1)]


def test_handbeispiel_schaetzung(hand_est):
    a, dl, cap = hand_est["a"], hand_est["dl"], hand_est["C"]
    r = K.simulate_est(a, dl, [3.0, 3.0, 3.0], cap, 0.5)
    assert (r[0], r[1], r[2], r[3]) == (1, 3, 3.0, 0)
    r2 = K.simulate_est(a, dl, [1.2, 1.2, 1.2], cap, 0.0)
    assert (r2[0], r2[1]) == (2, 3)
    assert [(round(t, 2), len(m)) for t, m in S.trace_departures(a, dl, cap, cap, INF, dl_est=[1.2, 1.2, 1.2], m=0.0)] == [(1.2, 2), (2.0, 1)]


def test_optimum_gleich_exakter_teilmengen_rechnung_auf_kleininstanzen():
    for k in range(200):
        n = 3 + k % 7
        lo, hi = ((1.0, 3.0), (4.0, 12.0), (12.0, 36.0))[k % 3]
        a, dl = S.make_arrivals(C.LAM_OPTIONS[k % 4], C.CA2_OPTIONS[k % 3], (lo, hi), n, 9000 + k)
        cap = 1 + (k % 4)
        assert len(S.optimum_departures(a, dl, cap)) == S.optimum_trips_dp(a, dl, cap), (n, cap, k)


def test_opt_kleiner_gleich_f_kleiner_gleich_sofort_auf_zufallsinstanzen():
    for lam, ca2, span, cap, a, dl in _instances(24, n=600):
        t_lo, t_hi = a[50], a[450]
        opt = S.optimum_metrics(a, dl, cap, t_lo, t_hi)["cost"]
        f = S.metrics(S.simulate(a, dl, cap, cap, INF, True, t_lo, t_hi), cap)["cost"]
        assert opt <= f + 1e-12 <= 1.0 + 1e-12
        assert opt >= 1.0 / cap - 1e-12


def test_zeitregel_gegen_die_erneuerungsrechnung_bei_poisson_ankuenften():
    """Poisson (ca² = 1), Zeitregel mit sehr großer Kapazität: Kosten je Sendung 1 / (1 + λT) und mittlere Wartezeit T (1 + λT/2) / (1 + λT) (Erneuerungsrechnung)."""
    lam, T = 1.0, 2.0
    costs, delays = [], []
    for seed in range(100000, 100010):
        a, dl = S.make_arrivals(lam, 1.0, C.SPANS["weit"], S.N_TOTAL, seed)
        t_lo, t_hi = S.window(a)
        m = S.metrics(S.simulate(a, dl, 1000, 1000, T, False, t_lo, t_hi), 1000)
        costs.append(m["cost"])
        delays.append(m["delay"])
    assert sum(costs) / len(costs) == pytest.approx(1.0 / (1.0 + lam * T), abs=0.012)
    assert sum(delays) / len(delays) == pytest.approx(T * (1.0 + lam * T / 2.0) / (1.0 + lam * T), abs=0.05)


def test_jede_regel_weicht_auf_mindestens_einer_instanz_von_sofort_ab():
    """Nullspalten-Falle: Menge, Zeit, Menge-oder-Zeit und Frist laufen wirklich (kein toter Zweig)."""
    lam, ca2, span, cap, a, dl = _instances(1, n=800)[0]
    base = S.simulate(a, dl, cap, 1, INF, False)
    for rule in ("Q", "T", "QT", "F"):
        q, T, ud = RULES[rule](16)
        res = S.simulate(a, dl, 16, q, T, ud)
        assert res[0] != base[0], rule


def test_hyperexponential_strom_hat_mittel_und_streuung():
    r, _ = streams(77)
    draw = make_sampler(1.0, 4.0, r)
    xs = [draw() for _ in range(20000)]
    mean = sum(xs) / len(xs)
    var = sum((x - mean) ** 2 for x in xs) / len(xs)
    assert mean == pytest.approx(1.0, abs=0.06) and var / mean ** 2 == pytest.approx(4.0, abs=0.5)
    assert math.isfinite(var)
