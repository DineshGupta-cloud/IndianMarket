"""
Simple Markdown → PDF exporter using fpdf2.
Keeps dependencies light and pure-Python.
"""
from pathlib import Path
from fpdf import FPDF


class ResearchPDF(FPDF):
    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, "IndianMarket Research Report", align="C")
        self.ln(4)
        self.set_draw_color(180, 180, 180)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}  |  Not investment advice", align="C")


def markdown_to_pdf(markdown_text: str, output_path: Path) -> Path:
    """Convert a simple Markdown research report to PDF."""
    pdf = ResearchPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", size=11)

    for raw_line in markdown_text.splitlines():
        line = raw_line.rstrip()

        if not line:
            pdf.ln(4)
            continue

        # Headings
        if line.startswith("# "):
            pdf.set_font("Helvetica", "B", 16)
            pdf.multi_cell(0, 10, line[2:].strip())
            pdf.set_font("Helvetica", size=11)
            pdf.ln(2)
        elif line.startswith("## "):
            pdf.set_font("Helvetica", "B", 13)
            pdf.multi_cell(0, 9, line[3:].strip())
            pdf.set_font("Helvetica", size=11)
            pdf.ln(1)
        elif line.startswith("### "):
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 8, line[4:].strip())
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("- ") or line.startswith("* "):
            pdf.set_font("Helvetica", size=10)
            pdf.multi_cell(0, 6, "  •  " + line[2:].strip())
            pdf.set_font("Helvetica", size=11)
        elif line.startswith("---"):
            pdf.ln(2)
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(4)
        elif line.startswith("|") and "---" not in line:
            # Simple table row – strip pipes
            cells = [c.strip() for c in line.strip("|").split("|")]
            pdf.set_font("Helvetica", size=9)
            pdf.multi_cell(0, 6, "  |  ".join(cells))
            pdf.set_font("Helvetica", size=11)
        else:
            # Normal paragraph / bold markers simplified
            clean = line.replace("**", "").replace("_", "")
            pdf.multi_cell(0, 6, clean)

    output_path = Path(output_path)
    pdf.output(str(output_path))
    return output_path
