"""PDF export function for metrics — extracted from views.py."""

from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

from fpdf import FPDF


_PDF_CHARS = {
    "\u2014": "-", "\u2013": "-",
    "\u2019": "'", "\u2018": "'",
    "\u201c": '"', "\u201d": '"',
    "\u2026": "...", "\xa0": " ",
}


def _pdf_safe(text) -> str:
    s = str(text)
    for ch, rep in _PDF_CHARS.items():
        s = s.replace(ch, rep)
    return s.encode("latin-1", errors="replace").decode("latin-1")


def export_metrics_pdf(data: dict) -> bytes:
    """Generate a PDF report from metrics data dict.

    Expected keys in data:
        total, abertos, aguardando, resolvidos, cancelados, overdue, sla_rate, op_rows
    """
    BRT = timezone(timedelta(hours=-3))
    now_brt = datetime.now(timezone.utc).astimezone(BRT).strftime("%d/%m/%Y %H:%M")

    class PDF(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 11)
            self.set_fill_color(17, 17, 17)
            self.set_text_color(240, 240, 240)
            self.cell(
                0, 10, "MiniCRM - Relatorio de Metricas",
                align="L", fill=True, new_x="LMARGIN", new_y="NEXT",
            )
            self.set_font("Helvetica", "", 8)
            self.set_text_color(136, 136, 136)
            self.cell(
                0, 6, _pdf_safe(f"Gerado em {now_brt}"),
                new_x="LMARGIN", new_y="NEXT",
            )
            self.ln(3)

        def footer(self):
            self.set_y(-12)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(136, 136, 136)
            self.cell(
                0, 8, _pdf_safe(f"Pagina {self.page_no()}"), align="C"
            )

    pdf = PDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def section_title(text):
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(240, 240, 240)
        pdf.set_text_color(17, 17, 17)
        pdf.cell(
            0, 7, _pdf_safe(text), fill=True,
            new_x="LMARGIN", new_y="NEXT",
        )
        pdf.ln(1)

    def metric_row(label, value, highlight=False):
        pdf.set_font("Helvetica", "", 9)
        if highlight:
            pdf.set_text_color(239, 68, 68)
        else:
            pdf.set_text_color(17, 17, 17)
        pdf.cell(100, 6, _pdf_safe(label))
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(
            0, 6, _pdf_safe(value), new_x="LMARGIN", new_y="NEXT"
        )
        pdf.set_text_color(17, 17, 17)

    section_title("Visao Geral")
    metric_row("Total de Atendimentos", data["total"])
    metric_row("Abertos", data["abertos"])
    metric_row("Aguardando Cliente", data["aguardando"])
    metric_row("Resolvidos", data["resolvidos"])
    metric_row("Cancelados", data["cancelados"])
    metric_row(
        "Atrasados (prazo expirado)", data["overdue"],
        highlight=data["overdue"] > 0,
    )
    metric_row(
        "Taxa de SLA (%)", f'{data["sla_rate"]}%',
        highlight=data["sla_rate"] < 70,
    )
    pdf.ln(4)

    op_rows = data.get("op_rows", [])
    if op_rows:
        section_title("Desempenho por Operador")
        col_labels = [
            "Operador", "Abertos", "Aguardando", "Resolvidos", "Cancelados"
        ]
        col_widths = [60, 28, 28, 28, 28]
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_fill_color(17, 17, 17)
        pdf.set_text_color(240, 240, 240)
        for label, w in zip(col_labels, col_widths):
            pdf.cell(w, 6, _pdf_safe(label), fill=True, border=0)
        pdf.ln()
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(17, 17, 17)
        for i, row in enumerate(op_rows):
            if i % 2 == 0:
                pdf.set_fill_color(250, 250, 250)
            else:
                pdf.set_fill_color(255, 255, 255)
            for val, w in zip(row, col_widths):
                pdf.cell(w, 6, _pdf_safe(val), fill=True, border=0)
            pdf.ln()

    output = io.BytesIO(pdf.output())
    return output.getvalue()
