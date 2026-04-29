"""PDF reporting utilities."""

from __future__ import annotations

from fpdf import FPDF


def clean_text_for_pdf(text: str) -> str:
    """Normalize non-latin-1 characters for robust PDF encoding."""
    replacements = {
        "🌿": "[Green]",
        "⚠️": "[Warning]",
        "⚠": "[Warning]",
        "📊": "[Chart]",
        "🔬": "[Lab]",
        "♻️": "[Recycle]",
        "♻": "[Recycle]",
        "₂": "2",
        "–": "-",
        "—": "-",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)

    cleaned = ""
    for ch in text:
        try:
            ch.encode("latin-1")
            cleaned += ch
        except UnicodeEncodeError:
            cleaned += " "
    return cleaned


def generate_pdf_report(data):
    """Generate a compact sustainability report PDF."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 14, clean_text_for_pdf("AI Green Auditor - Sustainability Report"), ln=True, align="C")
    pdf.ln(3)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 8, clean_text_for_pdf(f"Reaction: {data.get('reaction_name', 'Unnamed Reaction')}"), ln=True)
    pdf.cell(0, 8, f"Solvent: {data.get('solvent', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Atom Economy: {data.get('atom_economy', 0):.2f}%", ln=True)
    pdf.cell(0, 8, f"E-Factor: {data.get('e_factor', 0):.2f}", ln=True)
    pdf.cell(0, 8, f"Sustainability Score: {data.get('score', 0):.2f}/100", ln=True)
    pdf.cell(0, 8, f"Grade: {data.get('grade', 'N/A')}", ln=True)
    pdf.cell(0, 8, f"Waste Prevented: {data.get('waste_prevented', 0):.2f} kg", ln=True)
    pdf.cell(0, 8, clean_text_for_pdf(f"CO2 Impact Reduced: {data.get('co2_impact', 0):.2f} kg"), ln=True)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Recommendations", ln=True)
    pdf.set_font("Arial", "", 12)
    for idx, rec in enumerate(data.get("recommendations", []), 1):
        pdf.multi_cell(0, 8, f"{idx}. {clean_text_for_pdf(rec)}")

    return pdf.output(dest="S").encode("latin-1", "ignore")
