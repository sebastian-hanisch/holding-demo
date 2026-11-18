"""Konstanten: Regler-Stufen, feste Annahmen, Farben, Schwellen der Meldung und Presets.

Alle Regler stehen auf gemessenen Stufen (Raster der Vormessung: 4 Raten × 3 Streuungen × 3 Fristspannen × 2 Kapazitäten = 72 Zellen), damit zu jeder Einstellung eine
vorgerechnete Zelle gehört; die Stufen der Fristkenntnis sind in der Restmessung AP 0 in allen 72 Zellen gemessen."""

LAM_OPTIONS = (0.5, 1.0, 2.0, 4.0)
DEFAULT_LAM = 2.0
CA2_OPTIONS = (0.0, 1.0, 4.0)
DEFAULT_CA2 = 1.0
CA2_LABELS = {0.0: "gleichmäßig (ca² = 0)", 1.0: "zufällig (ca² = 1, Poisson)", 4.0: "stoßweise (ca² = 4)"}
CA2_TEXT = {0.0: "gleichmäßige Ankünfte", 1.0: "zufällige Ankünfte", 4.0: "stoßweise Ankünfte"}
SPAN_OPTIONS = ("eng", "mittel", "weit")
DEFAULT_SPAN = "mittel"
SPANS = {"eng": (1.0, 3.0), "mittel": (4.0, 12.0), "weit": (12.0, 36.0)}
SPAN_LABELS = {"eng": "eng (1 bis 3 Fahrzeiten)", "mittel": "mittel (4 bis 12)", "weit": "weit (12 bis 36)"}
CAP_OPTIONS = (8, 16)
DEFAULT_CAP = 16
WISSEN_OPTIONS = ("praxis", "grob", "s25", "s10", "s05", "exakt")
DEFAULT_WISSEN = "exakt"
WISSEN_LABELS = {
    "praxis": "keine Kenntnis: Zeitregel mit einem Parameter für alle Fristspannen",
    "grob": "nur die Fristklasse (eng, mittel, weit)",
    "s25": "Frist mit 25 % Schätzfehler",
    "s10": "Frist mit 10 % Schätzfehler",
    "s05": "Frist mit 5 % Schätzfehler",
    "exakt": "exakte Frist",
}
SEED_MAX, DEFAULT_SEED = 999999, 500018   # Messreihen: 1000-1029 (Abstimmung), 100000-100029 (Messung); die Presets liegen ab 500000

# Stufen der Fristkenntnis: Schlüssel der App -> Schlüssel in der Ergebnisdatei
WISSEN_LEVEL = {"praxis": "praxis", "grob": "grob", "s25": "verr25_kl", "s10": "verr10_kl", "s05": "verr05_kl", "exakt": "exakt"}
SIGMA = {"verr25": 0.25, "verr50": 0.50, "verr25_kl": 0.25, "verr50_kl": 0.50, "verr05_kl": 0.05, "verr10_kl": 0.10}   # Schätzfehler als Anteil des mittleren Spielraums
LEVEL_KEYS_ALL = ("exakt", "verr05_kl", "verr10_kl", "verr25_kl", "verr50_kl", "verr25", "verr50", "grob")
LEVEL_LABELS = {"exakt": "exakt", "verr05_kl": "5 % Schätzfehler", "verr10_kl": "10 % Schätzfehler", "verr25_kl": "25 % Schätzfehler", "verr50_kl": "50 % Schätzfehler",
                "verr25": "25 % ohne Klassenwissen", "verr50": "50 % ohne Klassenwissen", "grob": "nur die Fristklasse"}
LADDER_KEYS = ("exakt", "verr05_kl", "verr10_kl", "grob", "verr25_kl")   # Reihenfolge der Genauigkeitsleiter in der App

# Meldung in zwei Zuständen: „Frist egal“, wenn Q, T, QT und F alle höchstens 2 % über 1/C liegen; sonst „Frist zählt“ (F gewinnt allein)
FILL_FACTOR = 1.02
VIOL_MESS = 0.01                          # Zulässigkeit in der Messung: höchstens 1,0 % verspätete Sendungen
VIOL_TUNE = 0.005                         # Abstimmung: höchstens 0,5 %
MESS_SEEDS = (100000, 100029)             # Zufalls-Seeds der Messung (30 Läufe je Zelle)
TUNE_SEEDS = (1000, 1029)
RULES = ("S", "Q", "T", "QT", "F")
RULE_LABELS = {"S": "S: sofort", "Q": "Q: Menge", "T": "T: Zeit", "QT": "QT: Menge-oder-Zeit", "F": "F: fristgetrieben"}
RULE_COLORS = {"S": "#9aa5b4", "Q": "#c77700", "T": "#8a4fb0", "QT": "#00897b", "F": "#2a6fb0", "Opt": "#2a8f5b"}
COLOR_LATE = "#c0392b"
COLOR_OK = "#2a8f5b"

EXCERPT_ARRIVALS = 40                     # Zeitleiste: so viele Sendungen ab der Ankunft Nr. N_WARM

PRESETS = {
    "Standard": {"lam": 2.0, "ca2": 1.0, "span": "mittel", "cap": 16, "wissen": "exakt", "seed": 500018},
    "Enge Frist": {"lam": 1.0, "ca2": 1.0, "span": "eng", "cap": 16, "wissen": "exakt", "seed": 500018},
    "Fahrzeug füllt sich": {"lam": 4.0, "ca2": 1.0, "span": "weit", "cap": 8, "wissen": "exakt", "seed": 500018},
    "Stoßweise, enge Frist": {"lam": 1.0, "ca2": 4.0, "span": "eng", "cap": 16, "wissen": "exakt", "seed": 500018},
    "Dünner Fluss": {"lam": 0.5, "ca2": 1.0, "span": "mittel", "cap": 8, "wissen": "exakt", "seed": 500018},
    "Frist nur geschätzt": {"lam": 2.0, "ca2": 1.0, "span": "mittel", "cap": 16, "wissen": "s10", "seed": 500018},
}
PRESET_HELP = {
    "Standard": "Mittlere Frist, mittlerer Fluss: ein Fall mit mittlerem Vorteil. Die Fristregel liegt nahe am Optimum, die beste einfache Regel kostet deutlich mehr.",
    "Enge Frist": "Wenig Spielraum: die Mengenregel fährt praktisch sofort, die Zeitregel muss kurz warten, die Fristregel fährt zur Frist.",
    "Fahrzeug füllt sich": "Hoher Fluss, weite Frist: das Fahrzeug ist fast immer voll, bevor eine Frist droht. Unter Menge, Zeit, Menge-oder-Zeit und Frist unterscheiden sich die Kosten höchstens um 2 %; „sofort“ ist dort weiter 8- bis 16-mal so teuer.",
    "Stoßweise, enge Frist": "Stoßweise Ankünfte und enge Frist: die Mengenregel versagt (gleich „sofort“), Zeit- und Fristregel halten.",
    "Dünner Fluss": "Wenige Sendungen: es dauert, bis sich ein Fahrzeug füllt; die Frist begrenzt das Warten.",
    "Frist nur geschätzt": "Wie der Standard, aber die Fristregel kennt die Fristen nur mit 10 % Schätzfehler (Anteil des mittleren Spielraums).",
}
