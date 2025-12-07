from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import uuid, os
from docx import Document
import pdfplumber
from docx.shared import Inches

app = FastAPI()

TMP_DIR = "/tmp/convertpro"
os.makedirs(TMP_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "ConvertPro API - Word Stable Version OK"}


@app.post("/convert/pdf-to-word-advanced")
async def convert_pdf_word(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(TMP_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    pdf_path = os.path.join(job_folder, "input.pdf")
    word_path = os.path.join(job_folder, "output.docx")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    doc = Document()

    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages):

            text = page.extract_text()

            if text:
                for line in text.split("\n"):
                    doc.add_paragraph(line)

            doc.add_page_break()

    doc.add_paragraph("--- Converti depuis ConvertPro.shop ---")
    doc.save(word_path)

    return FileResponse(
        word_path,
        filename="converted_stable.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
from pdf2docx import Converter

@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_to_word_pro(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(TMP_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    pdf_path = os.path.join(job_folder, "input.pdf")
    word_path = os.path.join(job_folder, "output_pro.docx")

    # Enregistrement du fichier envoyé
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    # Conversion PRO
    cv = Converter(pdf_path)
    cv.convert(word_path)
    cv.close()

    # Retour du fichier Word
    return FileResponse(
        word_path,
        filename="converted_premium.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
