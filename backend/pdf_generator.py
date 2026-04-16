from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

def create_pdf(filename, text):
    pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))

    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    style = styles["Normal"]
    style.fontName = "HeiseiMin-W3"

    content = []

    def add(line):
        content.append(Paragraph(line, style))
        content.append(Spacer(1, 10))

    for line in text.split("\n"):
        if line.strip():
            add(line)

    doc.build(content)