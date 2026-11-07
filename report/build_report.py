"""Render the editable Markdown homework report with ReportLab (no Markdown dependency)."""

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "report.md"
TARGET = ROOT / "Spatial_Image_Enhancement_Report.pdf"


def rich(text: str) -> str:
    """Convert only the inline syntax used by this report to ReportLab markup."""
    text = html.escape(text).replace("–", "-").replace("’", "'")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    return text


styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="ReportTitle", fontName="Helvetica-Bold", fontSize=22,
                          leading=27, spaceAfter=25, textColor=colors.black))
styles.add(ParagraphStyle(name="ReportH2", fontName="Helvetica-Bold", fontSize=15,
                          leading=19, spaceBefore=16, spaceAfter=10, textColor=colors.black))
styles.add(ParagraphStyle(name="ReportH3", fontName="Helvetica-Bold", fontSize=11,
                          leading=14, spaceBefore=12, spaceAfter=7, textColor=colors.black))
styles.add(ParagraphStyle(name="ReportBody", fontName="Helvetica", fontSize=9.3,
                          leading=14, spaceAfter=8, textColor=colors.black))
styles.add(ParagraphStyle(name="ReportCaption", fontName="Helvetica-Oblique", fontSize=8,
                          leading=11, spaceBefore=5, spaceAfter=8, textColor=colors.HexColor("#444444")))
styles.add(ParagraphStyle(name="ReportCell", fontName="Helvetica", fontSize=7.3,
                          leading=9, textColor=colors.black))
styles.add(ParagraphStyle(name="ReportCoverMeta", fontName="Helvetica", fontSize=12,
                          leading=20, spaceAfter=8, textColor=colors.black))


class NumberedDoc(BaseDocTemplate):
    def __init__(self, filename: Path):
        super().__init__(str(filename), pagesize=letter, leftMargin=.67 * inch,
                         rightMargin=.67 * inch, topMargin=.67 * inch,
                         bottomMargin=.67 * inch, title="Spatial Image Enhancement")
        frame = Frame(self.leftMargin, self.bottomMargin, self.width, self.height,
                      leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates(PageTemplate(id="main", frames=frame, onPage=self._footer))

    def _footer(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor("#cccccc"))
        canvas.line(.67 * inch, .53 * inch, 7.83 * inch, .53 * inch)
        canvas.setFont("Helvetica", 8)
        canvas.drawString(.67 * inch, .38 * inch, "Spatial Image Enhancement")
        canvas.drawRightString(7.83 * inch, .38 * inch, str(doc.page))
        canvas.restoreState()


def make_table(lines: list[str]) -> Table:
    rows = []
    for line in lines:
        cells = [item.strip() for item in line.strip().strip("|").split("|")]
        if all(re.fullmatch(r":?-+:?", item) for item in cells):
            continue
        rows.append([Paragraph(rich(item), styles["ReportCell"]) for item in cells])
    count = len(rows[0])
    widths = [7.15 * inch / count] * count
    if count == 6:
        widths = [.55 * inch] + [1.32 * inch] * 5
    table = Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf3")),
        ("GRID", (0, 0), (-1, -1), .3, colors.HexColor("#c7ced6")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table


def main() -> None:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = [Spacer(1, 1.3 * inch), Paragraph("Spatial Image Enhancement", styles["ReportTitle"]),
             Paragraph("Image Processing Homework 1", styles["ReportCoverMeta"]),
             Spacer(1, .45 * inch)]
    cover = ["Student name: [Placeholder]", "Student ID: [Placeholder]",
             "Due date: November 11, 2026", "Submission date: [Placeholder]"]
    story.extend(Paragraph(item, styles["ReportCoverMeta"]) for item in cover)
    story.append(PageBreak())
    start = next(i for i, line in enumerate(lines) if line.startswith("## Technical Description"))
    lines = lines[start:]
    paragraph: list[str] = []
    table_lines: list[str] = []

    def flush() -> None:
        if paragraph:
            story.append(Paragraph(rich(" ".join(paragraph)), styles["ReportBody"]))
            paragraph.clear()
        if table_lines:
            # These short summary tables fit on a page; retain all six image
            # rows together instead of stranding the last rows on the next page.
            story.append(KeepTogether([make_table(table_lines), Spacer(1, 8)]))
            table_lines.clear()

    for line in lines:
        stripped = line.strip()
        if not stripped:
            flush()
            continue
        if stripped.startswith("|"):
            if paragraph:
                flush()
            table_lines.append(stripped)
            continue
        if stripped.startswith("!["):
            flush()
            match = re.fullmatch(r"!\[(.+?)\]\((.+?)\)", stripped)
            if not match:
                raise ValueError(f"Invalid image reference: {stripped}")
            path = (ROOT / match.group(2)).resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            from PIL import Image as PILImage
            with PILImage.open(path) as image:
                width, height = image.size
            target_width = 5.9 * inch
            story.append(Image(str(path), width=target_width,
                               height=target_width * height / width))
            story.append(Paragraph(rich(match.group(1)), styles["ReportCaption"]))
            continue
        if stripped.startswith("### Image "):
            flush()
            story.append(PageBreak())
            story.append(Paragraph(rich(stripped[4:]), styles["ReportH2"]))
            continue
        if stripped.startswith("## "):
            flush()
            if stripped in ("## Discussions", "## References and Appendix"):
                story.append(PageBreak())
            story.append(Paragraph(rich(stripped[3:]), styles["ReportH2"]))
            continue
        if stripped.startswith("### "):
            flush()
            story.append(Paragraph(rich(stripped[4:]), styles["ReportH3"]))
            continue
        if re.match(r"^(\d+\. |[1-9]\. )", stripped):
            flush()
            story.append(Paragraph(rich(stripped), styles["ReportBody"]))
            continue
        paragraph.append(stripped)
    flush()
    NumberedDoc(TARGET).build(story)
    print(TARGET)


if __name__ == "__main__":
    main()
