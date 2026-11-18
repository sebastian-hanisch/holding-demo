"""PDF-Export: Sonderzeichen werden bereinigt, jede Stufe der Fristkenntnis lässt sich als PDF ausgeben."""

import pytest

import hld_constants as C
import hld_evaluation as E
import hld_pdf_export as PDF


def test_clean_ersetzt_sonderzeichen_und_streicht_emoji():
    text = PDF.clean("Holding – λ ≥ 2 % → ± 5 € „Test“ ⏳ ✓ Δ ca² σ")
    assert "–" not in text and "→" not in text and "±" not in text and "€" not in text and "⏳" not in text and "Δ" not in text and "λ" not in text
    assert "Holding" in text and "lambda" in text and ">= 2" in text and "EUR" in text and "ca2" in text
    text.encode("latin-1")   # muss in der Standardschrift darstellbar sein


@pytest.mark.parametrize("wissen", C.WISSEN_OPTIONS)
def test_pdf_fuer_jede_stufe_der_fristkenntnis(wissen):
    st = E.Settings(2.0, 1.0, "mittel", 16, wissen, 3)
    an = E.analyse(st)
    a, dl, deps = E.trace_of(st, "stufe")
    rows = E.excerpt(a, dl, deps)
    data = PDF.build_pdf(st, an, rows)
    assert data[:5] == b"%PDF-" and len(data) > 1500
