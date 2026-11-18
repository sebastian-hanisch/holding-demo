"""Zufallsbausteine: SplitMix64 mit plattformfesten Zufallszahlen (auf Windows (MSVC) und im Linux-Docker-Lauf gleich; weitere Plattformen nicht nachgerechnet).

Herkunft: `SplitMix64`, `balanced_h2_probability`, `make_sampler` und `streams` stammen aus `mg1-kingman-demo/mg1_simulation.py` (über `messreihe_holding/hl_rng.py` der Vormessung);
der Logarithmus und der Kosinus kommen aus `tools/templates/rng_splitmix64_exact.py` (Rechnung mit `decimal`, 45 Stellen, einmal auf double gerundet), weil `math.log` und `math.cos`
aus der C-Bibliothek des Systems in der letzten Binärstelle abweichen können (DEMO-PLAYBOOK §5). Die Gleichverteilten sind ganzzahlig und identisch zur Vormessung; die Exponentiellen
weichen von `math.log` höchstens in der letzten Binärstelle ab (tests/test_rng.py)."""

import decimal
import math

MASK = (1 << 64) - 1
_CTX = decimal.Context(prec=45)


def exact_log(x: float) -> float:
    """Natürlicher Logarithmus für x > 0 (decimal); auf Windows (MSVC) und im Linux-Docker-Lauf gleich, weitere Plattformen nicht nachgerechnet."""
    return float(_CTX.ln(decimal.Decimal(x)))


def exact_cos(x: float) -> float:
    """Kosinus für |x| bis etwa 10 (Taylorreihe in 45 Stellen); auf Windows (MSVC) und im Linux-Docker-Lauf gleich, weitere Plattformen nicht nachgerechnet."""
    d = decimal.Decimal(x)
    x2 = _CTX.multiply(d, d)
    term = decimal.Decimal(1)
    total = decimal.Decimal(1)
    k = 0
    limit = decimal.Decimal(10) ** -48
    while True:
        k += 2
        term = _CTX.divide(_CTX.multiply(term, x2), k * (k - 1))
        total = _CTX.subtract(total, term) if (k // 2) % 2 == 1 else _CTX.add(total, term)
        if term < limit:
            break
    return float(total)


class SplitMix64:
    """Kleiner, gut gemischter 64-Bit-Zufallsgenerator (Vigna); reine Ganzzahl-Arithmetik."""

    def __init__(self, seed):
        self.state = seed & MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def uniform(self):
        """Gleichverteilt auf [0, 1) mit 53 Bit."""
        return (self.next() >> 11) * (1.0 / (1 << 53))

    def expovariate(self, rate):
        """Exponentiell mit Mittel 1/rate (Inversion; 1 − u liegt in (0, 1], der Logarithmus ist endlich)."""
        return -exact_log(1.0 - self.uniform()) / rate

    def normal(self):
        """Standardnormalverteilt (Box-Muller)."""
        u1 = max(self.uniform(), 1e-12)
        u2 = self.uniform()
        return math.sqrt(-2.0 * exact_log(u1)) * exact_cos(2.0 * math.pi * u2)


NOISE_SEED_OFFSET = 777_777      # eigener Strom für das Rauschen der Fristschätzung (wie in der Restmessung AP 0)
SLACK_SEED_OFFSET = 99_991       # Strom der Spielräume (wie in der Vormessung)


def streams(seed):
    """Die zwei Zufallsströme eines Laufs: Zwischenankunft und Spielraum der Frist."""
    return SplitMix64(seed), SplitMix64(seed + SLACK_SEED_OFFSET)


def noise_vector(seed, n):
    """n Standardnormalzahlen für den Zufalls-Seed `seed` (eigener Strom, getrennt von Ankunft und Spielraum)."""
    r = SplitMix64(seed + NOISE_SEED_OFFSET)
    return [r.normal() for _ in range(n)]


def balanced_h2_probability(scv):
    """Anteil p₁ der ersten Phase der Hyperexponentialverteilung mit gleichen Phasenanteilen am Mittel (scv ≥ 1)."""
    return 0.5 * (1.0 + math.sqrt((scv - 1.0) / (scv + 1.0)))


def make_sampler(mean, scv, rng):
    """Funktion ohne Argument, die Werte mit dem Mittel `mean` und dem Variationskoeffizienten² `scv` zieht: fest, Erlang-k, exponentiell oder Hyperexponential."""
    if scv == 0:
        return lambda: mean
    if scv == 1:
        return lambda: rng.expovariate(1.0 / mean)
    if scv < 1:
        k = round(1.0 / scv)
        return lambda: sum(rng.expovariate(k / mean) for _ in range(k))
    p1 = balanced_h2_probability(scv)
    rate1, rate2 = 2.0 * p1 / mean, 2.0 * (1.0 - p1) / mean

    def draw():
        return rng.expovariate(rate1) if rng.uniform() < p1 else rng.expovariate(rate2)
    return draw
