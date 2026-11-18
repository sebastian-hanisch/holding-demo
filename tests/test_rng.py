"""Zufallsbausteine: feste Ausgaben, plattformfeste Exponential- und Normalzahlen, Kopietest gegen die Vormessung (wenn der Nachbarordner da ist)."""

import importlib.util
import math
import sys
from pathlib import Path

import pytest

import hld_rng as G

ROOT = Path(__file__).resolve().parent.parent


def test_feste_ausgaben_der_ersten_werte():
    g = G.SplitMix64(0)
    assert [g.next() for _ in range(3)] == [16294208416658607535, 7960286522194355700, 487617019471545679]


def test_uniform_halboffen_und_seed_wird_auf_64_bit_gekuerzt():
    g = G.SplitMix64(12345)
    assert all(0.0 <= g.uniform() < 1.0 for _ in range(2000))
    a, b = G.SplitMix64(99), G.SplitMix64(99 + (1 << 64))
    assert [a.next() for _ in range(5)] == [b.next() for _ in range(5)]


def test_exakter_logarithmus_und_kosinus_gegen_math():
    for x in (1e-12, 0.001, 0.25, 0.5, 1.0, 2.718281828, 10.0, 12345.678):
        assert G.exact_log(x) == pytest.approx(math.log(x), rel=1e-15, abs=1e-15)
    for x in (0.0, 0.3, 1.0, 2.0, 3.141592653589793, 5.5, 6.283185307179586):
        assert G.exact_cos(x) == pytest.approx(math.cos(x), abs=1e-14)


def test_exakte_ziehungen_sind_reproduzierbar_und_endlich():
    a, b = G.SplitMix64(5), G.SplitMix64(5)
    xs = [a.expovariate(1.0) for _ in range(5)]
    assert xs == [b.expovariate(1.0) for _ in range(5)] and all(x > 0 for x in xs)
    n = G.noise_vector(11, 4)
    assert n == G.noise_vector(11, 4) and len(n) == 4 and all(math.isfinite(x) for x in n)
    assert G.noise_vector(11, 4) != G.noise_vector(12, 4)


def test_rauschen_hat_mittel_null_und_varianz_eins():
    z = G.noise_vector(3, 4000)
    mean = sum(z) / len(z)
    var = sum((x - mean) ** 2 for x in z) / len(z)
    assert mean == pytest.approx(0.0, abs=0.06) and var == pytest.approx(1.0, abs=0.08)


def test_ankuenfte_gleich_der_vormessung_wenn_der_nachbarordner_da_ist():
    orig = ROOT.parent / "tourenplanung-planung" / "messreihe_holding" / "hl_rng.py"
    if not orig.exists():
        pytest.skip("messreihe_holding liegt nicht neben dem Repo")
    sys.path.insert(0, str(orig.parent))
    spec = importlib.util.spec_from_file_location("hl_rng_orig", orig)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    a, b = G.SplitMix64(2026), mod.SplitMix64(2026)
    assert [a.next() for _ in range(50)] == [b.next() for _ in range(50)]
    assert [a.uniform() for _ in range(50)] == [b.uniform() for _ in range(50)]
    for scv in (1.0, 4.0):
        ra, _ = G.streams(100000)
        rb, _ = mod.streams(100000)
        da, db = G.make_sampler(0.5, scv, ra), mod.make_sampler(0.5, scv, rb)
        for _ in range(500):
            assert da() == pytest.approx(db(), rel=1e-14)   # math.log und der exakte Logarithmus weichen höchstens in der letzten Binärstelle ab
