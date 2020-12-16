from PyPDF2 import PdfFileWriter, PdfFileReader
import io
from reportlab.pdfgen import canvas

from reportlab.lib.pagesizes import letter, A4


class PdfEditor:

    def __init__(self, source_pdf):
        self.existing_pdf = PdfFileReader(open(source_pdf, "rb"))
        self.output = PdfFileWriter()
        self.output.appendPagesFromReader(self.existing_pdf)

    def addText(self, text, pos_x, pos_y, page=0, fontsize=7, font="Helvetica"):
        output_page = self.output.getPage(page)
        page_height = 837
        packet = io.BytesIO()
        pos_y = page_height - pos_y+fontsize/2
        can = canvas.Canvas(packet, pagesize=A4)
        can.setFont(font, fontsize)
        can.drawString(pos_x, pos_y, text, )
        can.save()

        packet.seek(0)
        pdf_1page_merge = PdfFileReader(packet)

        input_page = pdf_1page_merge.getPage(0)
        output_page.mergePage(input_page)

    def save_as(self, destination):
        outputStream = open(destination, "wb")
        self.output.write(outputStream)
        outputStream.close()
