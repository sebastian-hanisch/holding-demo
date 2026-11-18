"""Gemeinsame Fixtures: das Handbeispiel, an dem jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b).

Handbeispiel (fünf Sendungen, Kapazität C = 2): Ankünfte a = 0, 1, 2, 3, 10; späteste Abfahrten d = 4, 5, 3,5, 9, 12.
  S  (sofort)                  : 5 Abfahrten, Kosten 1,0
  Q  (q = 2)                   : Abfahrt bei Ankunft 1 (Sendungen 0, 1) und bei Ankunft 3 (Sendungen 2, 3); Sendung 4 wartet am Ende (ohne Zeitgrenze) -> 2 Abfahrten, 4 Sendungen, 1 wartet
  T  (T = 1,5)                 : Abfahrten bei 1 (0, 1; voll), 3 (2, 3; voll) und 11,5 (4) -> 3 Abfahrten, Wartezeit 1 + 1 + 1,5 = 3,5, keine Verspätung
  F  (früheste Frist)          : Abfahrten bei 1 (0, 1), 3 (2, 3) und 12 (4) -> 3 Abfahrten, Wartezeit 1 + 1 + 2 = 4, keine Verspätung
  Optimum                      : Gruppen {0, 1}, {2, 3}, {4}: 3 Abfahrten (jede Gruppe: höchstens 2 Sendungen, größte Ankunft höchstens kleinste Frist)
Handbeispiel Schätzung (C = 3, a = 0, 1, 2, d = 4, 5, 6): geschätzte Fristen 3, 3, 3 mit m = 0,5: das Fahrzeug fährt voll bei der Ankunft 2 (Wartezeit 3);
  geschätzte Fristen 1,2 mit m = 0: die Schätzung läuft bei Ankunft 2 schon ab -> Abfahrt bei 1,2 (Sendungen 0, 1), danach sofort bei Ankunft 2 (Sendung 2).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def hand():
    return {"a": [0.0, 1.0, 2.0, 3.0, 10.0], "dl": [4.0, 5.0, 3.5, 9.0, 12.0], "C": 2}


@pytest.fixture
def hand_est():
    return {"a": [0.0, 1.0, 2.0], "dl": [4.0, 5.0, 6.0], "C": 3}
