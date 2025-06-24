from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import io

def add_watermark(input_pdf, output_pdf, email):
    text_line_1 = "Persönliches Exemplar für:"
    text_line_2 = email
    text_line_3 = "nur zur privaten Verwendung"

    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=A4)
    width, height = A4

    can.setFont("Helvetica", 9)
    can.setFillColorRGB(0.6, 0.6, 0.6)
    can.drawString(50, 30, text_line_1)
    can.drawString(50, 20, text_line_2)
    can.drawString(50, 10, text_line_3)
    can.save()

    packet.seek(0)
    watermark_pdf = PdfReader(packet)
    watermark_page = watermark_pdf.pages[0]

    reader = PdfReader(input_pdf)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    with open(output_pdf, "wb") as f_out:
        writer.write(f_out)
