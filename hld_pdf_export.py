"""Lauf als PDF (fpdf2, Standardschriften). Sonderzeichen werden vorher bereinigt: Gedankenstrich, Minuszeichen, Euro, Anführungszeichen,
Pfeile und Emoji stürzen die Standardschriften sonst ab (DEMO-PLAYBOOK, fpdf2-Falle)."""

from fpdf import FPDF

import hld_constants as C
import hld_results as R

_REPLACE = {"–": "-", "—": "-", "−": "-", "€": "EUR", "„": '"', "“": '"', "”": '"', "‚": "'", "‘": "'", "’": "'", "→": "->", "×": "x", "±": "+/-",
            "≤": "<=", "≥": ">=", "·": "-", "…": "...", "λ": "lambda", "Δ": "Delta", "²": "2", "σ": "sigma"}


def clean(text: str) -> str:
    """Nur Zeichen der Standardschrift (Latin-1) behalten; bekannte Sonderzeichen ersetzen, Unbekanntes (Emoji) streichen."""
    for old, new in _REPLACE.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "ignore").decode("latin-1")


def build_pdf(settings, an: dict, rows) -> bytes:
    """`an`: Ergebnis von hld_evaluation.analyse; `rows`: Auszug der Zeitleiste (hld_evaluation.excerpt) der gewählten Regel."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, clean("Holding: Abfahrtsregeln mit Fristen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, clean(
        f"Rate lambda = {R.num(settings.lam, 1)} Sendungen je Fahrzeugzeit, {C.CA2_TEXT[settings.ca2]} (ca2 = {R.num(settings.ca2, 0)}), Frist {settings.span}, Kapazität {settings.cap}, "
        f"Fristkenntnis: {C.WISSEN_LABELS[settings.wissen]}, Zufalls-Seed {settings.seed}."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, "Regeln auf diesem Lauf", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    widths = (58, 30, 34, 34, 30)
    for w, h in zip(widths, ("Regel", "Kosten je Sendung", "Mittlere Wartezeit", "Verspätet (%)", "Auslastung (%)")):
        pdf.cell(w, 6, clean(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    lines = [(C.RULE_LABELS[k], an["rules"][k]) for k in C.RULES] + [("Gewählte Fristkenntnis", an["stage"])]
    for label, m in lines:
        vals = (label, R.num(m["cost"], 3), R.num(m["delay"], 2), R.num(100 * m["viol"], 2), R.num(100 * m["util"], 1))
        for w, v in zip(widths, vals):
            pdf.cell(w, 6, clean(v), border=1)
        pdf.ln()
    o = an["opt"]
    pdf.cell(widths[0], 6, "Optimum (bekannte Ankünfte)", border=1)
    pdf.cell(widths[1], 6, R.num(o["cost"], 3), border=1)
    pdf.cell(widths[2], 6, "-", border=1)
    pdf.cell(widths[3], 6, "0,00", border=1)
    pdf.cell(widths[4], 6, R.num(100 * o["util"], 1), border=1)
    pdf.ln(9)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 7, f"Auszug: die ersten {len(rows)} Sendungen des Auswertungsfensters", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 9)
    w2 = (24, 40, 40, 40, 30)
    for w, h in zip(w2, ("Sendung", "Ankunft", "Späteste Abfahrt", "Abfahrt", "Verspätet")):
        pdf.cell(w, 6, clean(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for j, a, d, t, late in rows:
        vals = (str(j), R.num(a, 2), R.num(d, 2), "-" if t is None else R.num(t, 2), "ja" if late else "nein")
        for w, v in zip(w2, vals):
            pdf.cell(w, 5, clean(v), border=1)
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, clean("Ein Lauf, kein Beleg: die Aussagen der Demo stützen sich auf die vorgerechnete Messreihe (72 Zellen, je 30 Läufe)."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
