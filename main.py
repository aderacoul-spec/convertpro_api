from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import uuid, os, shutil
from docx import Document
import pdfplumber
from PIL import Image
from docx.shared import Inches
import openpyxl
from PyPDF2 import PdfReader, PdfWriter
import zipfile


app = FastAPI()

TMP_DIR = "/tmp/convertpro"
os.makedirs(TMP_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "ConvertPro API Premium Stable OK"}


@app.post("/convert/pdf-to-word-advanced")
async def convert_pdf_word(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(TMP_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    pdf_path = os.path.join(job_folder, "input.pdf")
    word_path = os.path.join(job_folder, "output.docx")

    # save uploaded PDF
    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    doc = Document()

    with pdfplumber.open(pdf_path) as pdf:
        for index, page in enumerate(pdf.pages):

            text = page.extract_text()

            if text:
                for line in text.split("\n"):
                    doc.add_paragraph(line)

            for img_i, img_obj in enumerate(page.images):
                # NEW METHOD → SAFER
                try:
                    img = pdf.pages[index].to_image(resolution=150)
                    cropped = img.crop((img_obj["x0"], img_obj["top"], img_obj["x1"], img_obj["bottom"]))
                    img_path = os.path.join(job_folder, f"img_{index}_{img_i}.png")
                    cropped.save(img_path)
                    doc.add_picture(img_path, width=Inches(5))
                except:
                    pass

            doc.add_page_break()

    doc.add_paragraph("--- Converti avec ConvertPro.shop ---")
    doc.save(word_path)

    return FileResponse(word_path, filename="converted-premium.docx")
