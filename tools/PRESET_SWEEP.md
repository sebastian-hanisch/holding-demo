# Preset-Zufalls-Seeds

Alle Presets laufen mit dem Zufalls-Seed 500018 (Messreihen: 1000 bis 1029 für die Abstimmung, 100000 bis 100029 für die Messung). Geprüft mit `python tools/find_preset_seeds.py`: auf diesem Lauf zeigt jedes Preset seine Geschichte (Kriterien in `hld_stories.py`, Tests in `tests/test_presets.py`). Kosten je Sendung auf dem Lauf und im Mittel der gemessenen Zelle (30 Läufe):

| Preset | Zelle | Lauf: Q / T / F / Stufe / Optimum | Zellmittel: Q / T / F / Optimum |
|---|---|---|---|
| Standard | λ 2, ca² 1, Frist mittel, C 16 | 0,167 / 0,111 / 0,082 / 0,082 / 0,077 | 0,167 / 0,112 / 0,080 / 0,078 |
| Enge Frist | λ 1, ca² 1, Frist eng, C 16 | 1,000 / 0,503 / 0,355 / 0,355 / 0,355 | 1,000 / 0,501 / 0,349 / 0,349 |
| Fahrzeug füllt sich | λ 4, ca² 1, Frist weit, C 8 | 0,125 / 0,125 / 0,125 / 0,125 / 0,125 | 0,125 / 0,125 / 0,125 / 0,125 |
| Stoßweise, enge Frist | λ 1, ca² 4, Frist eng, C 16 | 1,000 / 0,396 / 0,283 / 0,283 / 0,283 | 1,000 / 0,399 / 0,279 / 0,279 |
| Dünner Fluss | λ 0,5, ca² 1, Frist mittel, C 8 | 1,000 / 0,335 / 0,220 / 0,220 / 0,220 | 1,000 / 0,334 / 0,223 / 0,222 |
| Frist nur geschätzt | wie Standard, Fristkenntnis 10 % Schätzfehler | 0,167 / 0,111 / 0,082 / 0,096 / 0,077 | 0,167 / 0,112 / 0,080 / 0,078 |

Ein Lauf streut um das Zellmittel (zwei Ziffern in der dritten Nachkommastelle); die Meldungen der App stützen sich auf das Zellmittel.
