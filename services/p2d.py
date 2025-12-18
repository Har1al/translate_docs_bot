from pdf2docx import Converter
import pdfplumber


def convert_pdf_to_docx(pdf_file, docx_file):
    cv = Converter(pdf_file)

    cv.convert(docx_file, start=0, end=None)
    cv.close()


def pdf_has_text(path):
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text and text.strip():
                return True
    return False

