"""Abnahmekriterien der Presets: was der angezeigte Lauf jedes Presets qualitativ zeigen muss.

Die Aussage der Demo stützt sich auf die Messreihe (30 Läufe je Zelle); ein Preset zeigt nur einen Lauf, der zur Geschichte passt. Die Kriterien sind deshalb bewusst grob und prüfen
den Lauf, nicht die Messreihe. Zufalls-Seeds der Presets ab 500000 (nie 1000 bis 1029 der Abstimmung und 100000 bis 100029 der Messung); die Suche steht in tools/find_preset_seeds.py."""

import hld_constants as C


def _best_simple(an):
    return min(an["rules"][k]["cost"] for k in ("Q", "T", "QT"))


def story_standard(an):
    """Mittlerer Vorteil: F spart gegenüber der besten einfachen Regel zwischen 15 und 45 % und liegt höchstens 10 % über dem Optimum."""
    f, b = an["rules"]["F"]["cost"], _best_simple(an)
    return 15.0 <= 100.0 * (b - f) / b <= 45.0 and f <= 1.10 * an["opt"]["cost"]


def story_enge(an):
    """Enge Frist: die Mengenregel fährt praktisch sofort (Kosten mindestens 0,99), F spart gegenüber der Zeitregel mindestens 15 %."""
    return an["rules"]["Q"]["cost"] >= 0.99 and an["rules"]["F"]["cost"] <= 0.85 * an["rules"]["T"]["cost"]


def story_fuellt(an):
    """Das Fahrzeug füllt sich: Menge, Zeit, Menge-oder-Zeit und Frist liegen alle höchstens 3 % über 1/C."""
    cap = an["settings"].cap
    return all(an["rules"][k]["cost"] <= 1.03 / cap for k in ("Q", "T", "QT", "F"))


def story_stoss(an):
    """Stoßweise Ankünfte, enge Frist: Menge gleich „sofort“, F höchstens 80 % der Kosten der Zeitregel."""
    return an["rules"]["Q"]["cost"] >= 0.99 and an["rules"]["F"]["cost"] <= 0.80 * an["rules"]["T"]["cost"]


def story_duenn(an):
    """Dünner Fluss: F spart gegenüber der besten einfachen Regel mindestens 15 %; die Auslastung von F liegt unter 70 %."""
    f, b = an["rules"]["F"]["cost"], _best_simple(an)
    return 100.0 * (b - f) / b >= 15.0 and an["rules"]["F"]["util"] < 0.70


def story_geschaetzt(an):
    """Frist nur mit 10 % Schätzfehler: die Stufe liegt zwischen exakter Frist und der abgestimmten Zeitregel und ist höchstens 1,0 % verspätet."""
    st = an["stage"]["cost"]
    return an["rules"]["F"]["cost"] <= st < an["rules"]["T"]["cost"] and an["stage"]["viol"] <= C.VIOL_MESS


STORIES = {
    "Standard": story_standard,
    "Enge Frist": story_enge,
    "Fahrzeug füllt sich": story_fuellt,
    "Stoßweise, enge Frist": story_stoss,
    "Dünner Fluss": story_duenn,
    "Frist nur geschätzt": story_geschaetzt,
}
