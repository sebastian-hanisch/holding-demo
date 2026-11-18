# Holding: wann zahlt sich Fristkenntnis aus? – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-holding-demo.streamlit.app/)** -->

Fall-Demo für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (`demos.html`, Gruppe „Transport & Tourenplanung“). Sendungen kommen laufend an, jede hat eine **Frist**, und ein Fahrzeug kostet pro Abfahrt dasselbe, egal wie voll es ist. **Wann soll es abfahren?** Wer wartet, füllt das Fahrzeug, riskiert aber die Frist. Die Demo rechnet live auf **einem Lauf** fünf Abfahrtsregeln, **S** (sofort), **Q** (Menge), **T** (Zeit), **QT** (Menge-oder-Zeit) und **F** (fristgetrieben), dazu das Offline-Optimum bei bekannten Ankünften und die **Stufen der Fristkenntnis** (von der Zeitregel ohne Kenntnis der Fristspanne bis zur exakten Frist). Die Aussagen stützen sich auf eine **vorgerechnete Messreihe** (72 Zellen, je 30 Läufe, Zufalls-Seeds 100000 bis 100029).

## Warum dieses Problem

„Wer die Fristen kennt, plant besser“ ist erwartbar, und die Fristregel F kennt die Fristen per Konstruktion. Die Frage der Demo ist deshalb nicht, ob das stimmt, sondern **wo es zählt und wie genau die Frist sein muss**: Wann bestimmt die Frist die Abfahrt, wann füllt sich das Fahrzeug ohnehin fast immer vor der Frist, und wie viel vom Vorteil bleibt, wenn die Frist nur geschätzt ist? Im Portfolio gab es für Abfahrtsregeln mit harten Fristen keine Demo; die Nachbarn rechnen andere Modelle (siehe „Verwandte Demos“).

## Modell

Zeiteinheit ist die Fahrzeit (Δ = 1). Sendungen kommen mit der Rate λ je Fahrzeugzeit (0,5 / 1 / 2 / 4) und der Streuung ca² der Zeit zwischen zwei Ankünften (0 gleichmäßig, 1 zufällig, 4 stoßweise, Hyperexponential). Jede Sendung hat einen **Spielraum** (gleichverteilt: eng 1 bis 3, mittel 4 bis 12, weit 12 bis 36 Fahrzeiten); die späteste Abfahrt ist Ankunft plus Spielraum. Fahrzeuge der Kapazität C (8 oder 16) gibt es beliebig viele; jede Abfahrt kostet gleich viel. **Kosten je Sendung** = Abfahrten / Sendungen = 1 / mittlere Beladung (1,000 heißt: jede Sendung fährt allein). Eine Sendung ist **verspätet**, wenn ihr Fahrzeug nach ihrer spätesten Abfahrt fährt. Ein Lauf hat 2 200 Ankünfte; ausgewertet werden die Abfahrten im Fenster von Ankunft Nr. 200 bis 2 000 (rund 1 800 Sendungen; Einschwingzeit und Auslaufen fallen heraus).

| Regel | Vorschrift (alle Regeln fahren sofort ab, wenn C Sendungen warten) |
|---|---|
| **S** sofort | jede Sendung fährt bei Ankunft allein |
| **Q** Menge | Abfahrt, sobald q Sendungen warten |
| **T** Zeit | Abfahrt, wenn die älteste wartende Sendung T gewartet hat |
| **QT** Menge-oder-Zeit | Abfahrt bei q Wartenden oder wenn die älteste T gewartet hat |
| **F** fristgetrieben | Abfahrt zur frühesten Frist der Wartenden; braucht die Fristen |
| **Optimum** | Mindestzahl der Abfahrten bei bekannten Ankünften und Fristen (Offline), ohne Verspätung |

**Stufen der Fristkenntnis** (Regel F mit geschätzter Frist d̂ und Sicherheitsabstand m; gezählt wird mit der echten Frist): *exakt* (d̂ = d); *nur die Fristklasse* (d̂ = Ankunft plus unterer Rand der Spanne, sicher, nie über der echten Frist); *Schätzfehler σ* (d̂ = d plus ein normalverteilter Fehler mit der Standardabweichung σ mal mittlerer Spielraum, auf die Fristklasse begrenzt; σ = 5, 10, 25 %); ohne jede Kenntnis eine Zeitregel mit **einem** Parameter für alle Fristspannen (Praxisregel). Formeln im 📐-Expander der App.

## Methodik

- **Regeln und Parameter:** Q, T und QT haben je Zelle den Parameter mit den kleinsten mittleren Kosten unter höchstens 0,5 % verspäteten Sendungen, abgestimmt auf den Zufalls-Seeds 1000 bis 1029 und gemessen auf den Zufalls-Seeds 100000 bis 100029. **Dieser Parameter kennt die Fristverteilung der Zelle** (günstige Annahme für Regeln ohne diese Kenntnis: abgestimmt auf einem groben Parameter-Raster, eine Näherung an die beste Wahl, kein Optimum der Regelklasse). Der Sicherheitsabstand m der geschätzten Fristen ist ebenso je Zelle und Stufe abgestimmt und kennt die Fehlergröße (günstige Annahme, grobes Raster für m; Prüfer-Neulauf, nicht Teil der Messreihe: ein kleineres m wäre in vielen Fällen noch zulässig, 120 von 279 Prüfungen).
- **Sieger und Gleichauf:** zulässig ist eine Regel mit höchstens 1,0 % verspäteten Sendungen (Messung); Sieger ist die zulässige Regel mit den kleinsten mittleren Kosten; *gleichauf* heißt: Unterschied der gepaarten Kosten unter zwei Standardfehlern der Differenz über die 30 Läufe; *allein* heißt: keine andere zulässige Regel ist gleichauf.
- **Klassen der Zellen:** „Frist egal“, wenn Q, T, QT und F alle höchstens 2 % über 1/C liegen (Deutung, nicht gesondert gemessen: das Fahrzeug füllt sich fast immer vor der Frist); sonst „Frist zählt“ (F gewinnt allein). „Zählt“ heißt nur: nicht alle vier Regeln liegen höchstens 2 % über 1/C, nicht notwendig ein großer Vorteil (Beispiel λ = 1, ca² = 4, Frist weit, C = 8: Ersparnis von F gegenüber der besten einfachen Regel 0,73 %). Die 2 %-Schwelle ist gesetzt, nicht hergeleitet.
- **Kennzahl A der Genauigkeitsleiter:** A = (K_T − K_Stufe) / (K_T − K_F) je Zelle, K_T die Kosten der auf die Zelle abgestimmten Zeitregel, K_F die Kosten von F mit exakter Frist; eine unzulässige Stufe zählt mit A = 0. A gibt es nur in den 53 Zellen, in denen F allein gewinnt.
- **Zufall:** SplitMix64 mit zwei Strömen (Zwischenankunft und Spielraum) wie in der Vormessung und einem dritten für das Rauschen der Fristschätzung; der Logarithmus und der Kosinus der Exponential- und Normalzahlen rechnen mit `decimal` und sind auf Windows (MSVC) und im Linux-Docker-Lauf gleich; weitere Plattformen sind nicht nachgerechnet (`hld_rng.py`).
- **Messreihe:** die Vormessung (72 Zellen, Regeln und Optimum), die Restmessung AP 0 (Stufen der Fristkenntnis in allen 72 Zellen, Praxisregeln) und zwei Nachmessungen (Schätzer mit Klassenwissen, Schätzfehler 5 und 10 %). Die Rohdaten liegen nicht im Repo; `tools/dump_results.py` verdichtet sie zu `data/hld_results.json` (unter 150 kB), aus dem App und Tests alle Zahlen lesen.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `data/hld_results.json` und sind in `tests/test_claims.py` nachgerechnet (Testname in der letzten Spalte). Wo nichts anderes steht: Mittel über 30 Läufe je Zelle, 72 Zellen, Parameter von Q, T, QT je Zelle mit Kenntnis der Fristverteilung abgestimmt. „Z53“ heißt: die 53 Zellen, in denen F allein gewinnt.

| Frage | Befund (Voraussetzung) | Test |
|---|---|---|
| Wer gewinnt mit Fristkenntnis? | **F gewinnt in 53 von 72 Zellen allein** (Sieger oder gleichauf in 68); nach Fristspanne eng 24 von 24, mittel 19 von 24, weit 10 von 24; nach Rate λ = 0,5 / 1 / 2 / 4: 18 / 16 / 11 / 8 von je 18. Menge, Zeit, Menge-oder-Zeit und sofort gewinnen in keiner Zelle allein. Diese Zahlen gelten mit dem verwendeten Parameter-Raster (Prüfer-Neulauf, nicht Teil der Messreihe: mit einem feineren Raster, T mit 68 Werten, gewinnt F in 52 statt 53 Zellen allein). | `test_wer_gewinnt_mit_fristkenntnis` |
| Wer gewinnt ohne Fristkenntnis? | Nur die Regeln S, Q, T, QT: die **Zeitregel T ist in 72 von 72 Zellen Sieger oder gleichauf**, Menge-oder-Zeit in 72, die Menge in 27, sofort in 2. Menge-oder-Zeit hat mit den abgestimmten Parametern in allen 72 Zellen dieselben Kosten wie die Zeitregel; die Mengenschwelle greift nie. Die Parameter kennen die Fristverteilung (günstige Annahme). | `test_wer_gewinnt_ohne_fristkenntnis` |
| Wann ist die Frist egal? | **In 19 von 72 Zellen liegen Q, T, QT und F alle höchstens 2 % über 1/C**: Frist eng 0, mittel 5, weit 14; nach λ = 0,5 / 1 / 2 / 4: 0 / 2 / 7 / 10 Zellen. Dort unterscheiden sich Menge, Zeit, Menge-oder-Zeit und Frist höchstens um 2 %; „sofort“ ist dort weiter 8- bis 16-mal so teuer (Kosten 1,000 gegen 1/C). Deutung (nicht gesondert gemessen): das Fahrzeug füllt sich fast immer vor der Frist. | `test_wann_ist_die_frist_egal` |
| Wie viel ist die Fristkenntnis wert? | In Z53 spart F gegenüber der besten einfachen Regel im **Median 28,0 %** (Minimum 0,7 %, Maximum 33,9 %; bezogen auf die Kosten der besten einfachen Regel). Ersparnis gegen „sofort“ nach Frist eng / mittel / weit (Mittel über je 24 Zellen): Q 20 / 57 / 84 %, T 57 / 82 / 89 %, F 69 / 86 / 90 %, Optimum 69 / 86 / 90 %. | `test_wert_der_fristkenntnis` |
| Wie nah am Optimum? | F liegt im Median 0,0 % über dem Offline-Optimum (drittes Quartil 1,5 %, Maximum 6,6 %), in 23 von 72 Zellen mehr als 1 %; die beste zulässige einfache Regel im Median 31,2 % (Maximum 51,4 %), jeweils bezogen auf das Optimum. Das Optimum ist nicht bewiesen. | `test_naehe_zum_optimum` |
| Wann versagt die Mengenregel? | **Q ist in 22 von 72 Zellen gleich „sofort“** (Kosten 1,000; die Abstimmung findet keinen Parameter unter 0,5 % Verspätung): Frist eng 16, mittel 6, weit 0; ca² = 0 / 1 / 4: 2 / 8 / 12; λ = 0,5 / 1 / 2 / 4: 10 / 6 / 4 / 2. Die Zeitregel T ist nur in 2 von 72 Zellen gleich „sofort“. | `test_mengenregel_versagt` |
| T bei stoßweisen Ankünften? | Die Vermutung „T bricht ein“ bestätigt sich nicht: mittlere Auslastung von T bei ca² = 0 / 1 / 4: 59,4 / 58,6 / 62,6 %, mittlere Ersparnis gegen „sofort“ 73,3 / 75,8 / 79,5 % (Mittel über je 24 Zellen). Deutung (nicht gesondert gemessen): stoßweise Ankünfte bündeln sich eher von selbst. | `test_zeitregel_bei_stossweisen_ankuenften` |
| Genauigkeitsleiter | Median von A in Z53 (Schätzer mit Klassenwissen, Nachmessung, nicht vorab festgelegt): exakt 1,00; **Schätzfehler 5 %: 0,78**; **10 %: 0,52**; nur die Fristklasse 0,00; **25 %: −0,48**; 50 %: −2,07. A ≥ 0,5 in 53 / 51 / 34 / 0 / 3 / 3 Zellen (in dieser Reihenfolge); die Stufen mit 5 %, 10 %, 25 % und 50 % Schätzfehler sind in 53 / 51 / 9 / 3 Zellen billiger als die abgestimmte Zeitregel (A über 0,001). Mittlere Kosten je Sendung (Z53): 0,2093 / 0,2276 / 0,2487 / 0,2868 / 0,3314 / 0,4424. | `test_genauigkeitsleiter` |
| Urteil der vorab festgelegten Variante | Der Schätzer **ohne Klassenwissen** bei 25 % Schätzfehler (vorab festgelegte Schwellen der Restmessung): Median A = −1,03, F in 49 von 53 Zellen teurer als die abgestimmte Zeitregel; Urteil **„Fristkenntnis lohnt nur, wenn sie genau ist“** (gegenüber einer Zeitregel, die die Fristspanne kennt; 5 bis 10 % Fehler genügen, 25 % nicht). Der Schätzer mit Klassenwissen kommt bei 25 % zum selben Urteil (Median A = −0,48, nur Vergleich). | `test_urteil_der_vorab_festgelegten_variante` |
| Gegen eine Praxisregel | Gegen die Zeitregel mit einem Parameter für alle Fristspannen (V2) spart F in Z53 im Median: exakt 62,1 %, Schätzfehler 5 % 61,8 %, 10 % 59,6 %, nur die Fristklasse 49,9 %, 25 % 47,7 % (Variante ohne Klassenwissen: 38,3 %), bezogen auf die Kosten der Praxisregel. | `test_gegen_eine_praxisregel` |
| Wie optimistisch ist die abgestimmte Zeitregel? | Eine auf „mittel“ abgestimmte Zeitregel (V1) ist **in 24 von 48 Zellen unzulässig** (Frist eng 24 von 24, weit 0 von 24); in den zulässigen Zellen (weit) kostet sie im Mittel 64,1 % mehr. Eine auf die Mischung der drei Spannen abgestimmte (V2) ist in allen 72 Zellen zulässig und kostet im Mittel 147,4 % mehr (Frist eng 0,0 %, mittel 140,7 %, weit 301,4 %). Urteil nach der vorab festgelegten Schwelle: **„Die abgestimmte Zeitregel ist ein zu günstiger Maßstab“** (Urteilswort der Messung: „Obergrenze zu optimistisch“). | `test_praxisregel` |
| Reihenfolge der Stufen | Die Kette Kosten(exakt) ≤ Kosten(5 %) ≤ Kosten(10 %) ≤ Kosten(25 %) ≤ Kosten(50 %) gilt im Mittel über Z53; die Stufe „nur die Fristklasse“ liegt zwischen 10 % und 25 %. Kosten(25 %) > Kosten(nur die Fristklasse) in 42 und Kosten(50 %) > Kosten(nur die Fristklasse) in 47 von 53 Zellen. | `test_reihenfolge_der_stufen` |
| Hängt das Ergebnis vom Lauf ab? | Ein Lauf streut: die Meldungen der App stützen sich auf das Zellmittel, nicht auf den einen Lauf (Presets: Kosten auf dem Lauf und im Zellmittel nebeneinander). | `test_die_meldung_stuetzt_sich_auf_die_zelle` |

## Befunde und Korrekturen gegenüber dem Plan

- **Standardzelle:** Der Plan nahm zuerst λ = 1, ca² = 1, Frist mittel, C = 16; das ist eine der Zellen mit dem größten F-Vorteil (33,9 %; Maximum 33,9 %) und damit ein ungünstiger Standard. Der Standard ist λ = 2, ca² = 1, Frist mittel, C = 16 mit 28,7 % Ersparnis, nahe am Median (28,0 %).
- **Zwei Zustände statt drei:** „Frist egal“ und „Frist zählt“; ein dritter Zustand („F gleichauf mit einer einfachen Regel“) kommt in den 72 Zellen mit dem verwendeten Parameter-Raster nicht vor und ist nicht gebaut (Prüfer-Neulauf mit feinerem Raster, nicht Teil der Messreihe: eine solche Zelle, λ = 4, ca² = 1, Frist mittel, C = 16).
- **Stufen in allen 72 Zellen:** Die Restmessung hat die Stufen der Fristkenntnis in allen 72 Zellen gemessen; die Kennzahl A gibt es nur in Z53. Der Regler „Fristkenntnis“ hat sechs Stufen (keine, nur die Fristklasse, 25 %, 10 %, 5 %, exakt).
- **Schätzer mit Klassenwissen:** Die vorab festgelegte Variante ohne Klassenwissen war ungünstig entworfen (sie ignorierte, dass jede Frist in der Fristklasse liegt): mehr Information (25 %) lieferte ein schlechteres Ergebnis als weniger (nur die Klasse). Die Demo zeigt den Schätzer mit Klassenwissen; die Variante ohne Klassenwissen steht als vorab festgelegtes Urteil in den Befunden. Die Stufen 5 % und 10 % haben keine vorab festgelegte Schwelle.
- **„Nur die Fristklasse“ ist die abgestimmte Zeitregel:** Die Stufe fährt wie T mit dem unteren Rand der Spanne; ihre Kosten sind in 52 von 53 Zellen (Z53) gleich denen der abgestimmten Zeitregel, die einzige Ausnahme ist λ = 1, ca² = 4, Frist weit, C = 8 (abgestimmtes T = 16). Deshalb ist A = 0 in 52 der 53 Zellen (in der Ausnahme −4,17). Bei einem feineren T-Raster wäre die abgestimmte Zeitregel in 9 Zellen billiger (Prüfer-Neulauf, nicht Teil der Messreihe).
- **Zufall plattformfest:** Die Vormessung rechnete mit `math.log`; die Demo rechnet den Logarithmus mit `decimal`. In der Restmessung unterschieden sich 0,138 % der Ziehungen eines Hyperexponential-Stroms in der letzten Binärstelle, in einer Beispielzelle blieben alle Kosten gleich; die Neu-Rechnen-Tests laufen als Band und im Linux-Docker-Lauf (143 bestanden, 1 übersprungen).
- **Kein Optimum-Knopf:** Es gibt keinen Löser; das Optimum wird mit dem Verfahren „früheste Frist abwarten“ berechnet und ist an Kleininstanzen gegen die exakte Teilmengen-Rechnung geprüft.

## Ehrliche Grenzen

| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| F kennt die Fristen exakt | Informationsvorsprung: „F gewinnt“ ist erwartbar; neu ist nur, wo es zählt und wie genau die Frist sein muss |
| Q, T, QT je Zelle mit Kenntnis der Fristverteilung abgestimmt | Günstige Annahme für Regeln ohne diese Kenntnis (grobes Parameter-Raster, Näherung an die beste Wahl, kein Optimum der Regelklasse); die Praxisregeln V1 und V2 sind zwei von vielen möglichen Wahlen |
| Schätzfehler unabhängig, normalverteilt, proportional zur Spanne | Systematische Fehler und Schätzer, die Vorwissen und Messung gewichten, sind nicht gemessen; bei 25 % Fehler ist F im Median teurer als die abgestimmte Zeitregel |
| Sicherheitsabstand je Zelle auf getrennten Zufalls-Seeds gewählt | m kennt die Fehlergröße (günstige Annahme, grobes Raster für m; Prüfer-Neulauf, nicht Teil der Messreihe: ein kleineres m wäre in vielen Fällen noch zulässig, 120 von 279 Prüfungen) |
| Unbegrenzte Flotte, konstante Fahrzeit, unabhängige Ankünfte, gleichverteilte Fristen, eine Sendungsart | Mischfristen, mehrere Ziele oder Fahrzeugtypen, abhängige Ankünfte und Praxisdaten sind nicht gemessen |
| Optimum bei bekannten Ankünften | An 600 Kleininstanzen der Vormessung gegen die exakte Teilmengen-Rechnung geprüft, nicht bewiesen; zwei Zellen haben eine zulässige einfache Regel bis 0,03 % unter dem Optimum (Verspätung bis 1 % zulässig, das Fenster zählt nach Abfahrtszeit) |
| 72 Zellen, 30 Läufe je Zelle | „Gleichauf“ heißt Unterschied unter zwei Standardfehlern; die Siegerzahlen hängen an dieser Schwelle und am Parameter-Raster (Q ∈ {2, 3, 4, 6, 8, 12, 16}, T von 0,25 bis 48 Fahrzeiten); Prüfer-Neulauf, nicht Teil der Messreihe: mit einem feineren Raster (T mit 68 Werten) gewinnt F in 52 statt 53 Zellen allein, die abgestimmte Zeitregel wäre in 9 Zellen bis etwa 6 % billiger |
| Literatur | Nur Zusammenfassungen gelesen: Mutlu, Çetinkaya, Bookbinder (2010, IISE Transactions) und Wei, Çetinkaya, Cline (2020, arXiv 2012.02392) untersuchen laut Zusammenfassung Zeit-, Mengen- und Hybridregeln; von Ralfs, Kiesmüller (2022, OR Spectrum) wurde nur der Titel gefunden („Inventory management with advance demand information and flexible shipment consolidation“), der Inhalt ist nicht eingesehen; dieses Modell unterscheidet sich durch harte Fristen. Ein Vergleich der Ergebnisse ist nicht gemacht, nichts davon ist hier als neu oder bestätigt bezeichnet. |
| Die Zustände der ersten Meldung | Die 2 %-Schwelle ist gesetzt, nicht hergeleitet; ein einzelner Lauf kann vom Zellmittel abweichen |

## Tests

146 Tests (`pytest --collect-only -q tests`), Laufzeit lokal rund 24 s mit `pytest tests -q -n 6` (eine Messung, Python 3.14, Windows, sechs Prozesse). Zusammensetzung:

- **Orakel** (`tests/test_oracle_holding.py`): zweite, naive Umsetzung der fünf Regeln und der Fristschätzung (Liste der Wartenden, Ereignis für Ereignis) gegen die Simulation auf Zufallsinstanzen; Zeitregel gegen die Erneuerungsrechnung bei Poisson-Ankünften; Optimum gegen die exakte Teilmengen-Rechnung auf 200 Kleininstanzen; Zeitleiste gegen Simulation; Handbeispiele von Hand gerechnet.
- **Kern** (`tests/test_rng.py`, `tests/test_edge_cases.py`): SplitMix64 gegen feste Werte und die Vormessung, exakte Ziehungen, alle 72 Zellen und Reglerränder, leere und winzige Läufe.
- **Ergebnisse und Aussagen** (`tests/test_results.py`, `tests/test_claims.py`, `tests/test_verdicts.py`): jede Zahl dieser README und der App aus der Ergebnisdatei nachgerechnet, Verdikte an handgesetzten Werten, Zustände.
- **Presets und Oberfläche** (`tests/test_presets.py`, `tests/test_layout.py`, `tests/test_app.py`, `tests/test_pdf.py`, `tests/test_footer.py`, `tests/test_runtime_imports.py`): jedes Preset liegt auf einer gemessenen Zelle und zeigt auf seinem Lauf seine Geschichte; AppTest für jedes Preset, jede Stufe der Regler und der Fristkenntnis, beide Zustände der ersten Meldung, PDF, Permalink.

## Verifikation

- **Kern:** Handbeispiele (fünf Sendungen, Kapazität 2: S 5 Abfahrten, Q 2, T 3 mit Wartezeit 3,5, F 3 mit Wartezeit 4, Optimum 3), Orakel, Zählprobe (jede Sendung genau einmal gefahren oder am Ende wartend), Reproduzierbarkeit.
- **Neu-Rechnen gegen die Messreihe:** die Kosten zweier Zellen werden mit den Zufalls-Seeds 100000 bis 100029 neu gerechnet und mit der Ergebnisdatei im Band verglichen (`test_claim_neu_rechnen_als_band`).
- **Oberfläche:** AppTest, Layout (Schnellstart in der Seitenleiste, fester Kopf, aktives Preset hervorgehoben, jede Reglerstufe), Footer.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App (Skelett nach DEMO-PLAYBOOK §2) |
| `data/hld_results.json` | vorgerechnete Messreihe (72 Zellen mit Regeln, Optimum, Stufen der Fristkenntnis, Praxisregeln) |
| `hld_constants.py` | Regler-Stufen, feste Annahmen, Schwellen, Farben, Presets |
| `hld_evaluation.py` | Live-Analyse eines Laufs, Zeitleiste, Verdikte als reine Funktionen |
| `hld_knowledge.py` | Stufen der Fristkenntnis: Fristschätzung und Regel F mit geschätzter Frist |
| `hld_layout.py` | Fester Kopf (Stylesheet) |
| `hld_pdf_export.py` | Lauf als PDF (fpdf2) |
| `hld_presets.py` | Permalink (Begrenzen, Einrasten), Presets (Schnellstart, aktives Preset hervorgehoben), Zufalls-Seed-Button |
| `hld_results.py` | Laden und Auswerten der Ergebnisdatei, Zählungen, Genauigkeitsleiter, Praxisregeln |
| `hld_rng.py` | SplitMix64 mit plattformfesten Exponential- und Normalzahlen |
| `hld_sim.py` | Ereignissimulation der Regeln, Kennzahlen, Offline-Optimum, Zeitleiste (aus der Vormessung übernommen) |
| `hld_stories.py` | Abnahmekriterien der Presets |
| `hld_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `requirements.txt`, `requirements-dev.txt` | Laufzeit-Bibliotheken (ungepinnt) und dazu pytest |
| `tools/dump_results.py` | erzeugt `data/hld_results.json` aus den Rohdaten (Umgebungsvariable `HLD_RAW_DIR`) |
| `tools/find_preset_seeds.py` | prüft die Zufalls-Seeds der Presets |
| `tools/PRESET_SWEEP.md` | gewählte Zufalls-Seeds der Presets mit den Werten des Laufs und des Zellmittels |
| `tests/` | Orakel, Kern, Randfälle, Ergebnisse, Aussagen, Verdikte, Presets, Layout, AppTest, PDF, Footer, Laufzeit-Importe, Zufallsgenerator |

## Bewusst nicht umgesetzt

- **Mischfristen** (Sendungsarten mit verschiedenen Fristspannen), mehrere Ziele oder Fahrzeugtypen, abhängige Ankünfte und Praxisdaten.
- **Schätzer, die Vorwissen und Messung gewichten**, und systematische Schätzfehler: nicht gemessen; ein Schätzer mit Gewichtung könnte bei 25 % Fehler besser abschneiden (Deutung, nicht nachgeprüft).
- **Kopplung mit Tourenplanung und Rückladung** (`inventory-routing-demo`, `rueckladung-demo`): eigene Fragen.
- **Ein Beweis des Optimums** und ein Vergleich mit Veröffentlichungen über die Quellenliste hinaus.

## Verwandte Demos mit demselben mathematischen Modell

Vor einer neuen Demo-Idee das Modell vergleichen, nicht die Kulisse (Stand 2026-11-18; gelesen sind die READMEs, soweit unten genannt):

- [`inventory-routing-demo`](https://github.com/sebastian-hanisch/inventory-routing-demo): Bündeln gegen früher liefern, aber mit Kundenbestand und Tourenbildung; hier gibt es Fristen statt Bestand und keine Touren.
- [`gate-demo`](https://github.com/sebastian-hanisch/gate-demo): Warteschlange am Lkw-Gate mit Terminsystem (Fenster mit Kapazität); hier fährt ein Fahrzeug nach einer Abfahrtsregel.
- [`rufbus-demo`](https://github.com/sebastian-hanisch/rufbus-demo): ein Batch-Fenster gegen sofortiges Einfügen bei Fahrgästen (Routing); verwandt in der Frage „warten oder sofort“, anderes Modell.
- [`mg1-kingman-demo`](https://github.com/sebastian-hanisch/mg1-kingman-demo): Wartezeit bei Streuung; die Zufallsströme der Ankünfte stammen aus ihrer Simulation.
- [`order-batch-demo`](https://github.com/sebastian-hanisch/order-batch-demo): räumliche Bündelung von Kommissionieraufträgen (Wege), ohne Online-Ankünfte.
- [`rueckladung-demo`](https://github.com/sebastian-hanisch/rueckladung-demo): Rückladung als Routing-Problem; gleiche Frage „wie viel spart Bündeln“, anderes Modell.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, pandas und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zum Thema: [Tourenplanung optimieren](https://sebastianhanisch.net/tourenplanung-optimierung.html).
