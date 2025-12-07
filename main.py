from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
import uuid, os, shutil, zipfile
from docx import Document
import pdfplumber
from PIL import Image
import openpyxl
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter

app = FastAPI()

TMP_DIR = "/tmp/convertpro"
os.makedirs(TMP_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "ConvertPro API Premium OK"}


# -----------------------------------------------------
# 1️⃣ PDF → Word PREMIUM
# -----------------------------------------------------
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
        for i, page in enumerate(pdf.pages):
            text = page.extract_text()

            # ---------- Extraction texte ----------
            if text:
                for line in text.split("\n"):
                    doc.add_paragraph(line)

            # ---------- Extraction images ----------
            images = page.images
            for img in images:
                x0, top, x1, bottom = img["x0"], img["top"], img["x1"], img["bottom"]
                cropped = page.crop((x0, top, x1, bottom)).to_image(resolution=200)
                image_path = os.path.join(job_folder, f"image_{i}.png")
                cropped.save(image_path, format="PNG")
                doc.add_picture(image_path, width=4000000)  # redimensionné

            doc.add_page_break()

    # ---------- Watermark inside WORD ----------
    doc.add_paragraph("\n\nConvertPro.shop – Conversion Premium Automatique")
    doc.save(word_path)

    return FileResponse(word_path, filename="converted-premium.docx")


# -----------------------------------------------------
# 2️⃣ PDF → Excel
# -----------------------------------------------------
@app.post("/convert/pdf-to-excel")
async def convert_pdf_excel(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(TMP_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    pdf_path = os.path.join(job_folder, "input.pdf")
    excel_path = os.path.join(job_folder, "output.xlsx")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    wb = openpyxl.Workbook()
    ws = wb.active

    row_index = 1

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()

            for table in tables:
                for row in table:
                    ws.append(row)
                    row_index += 1

                ws.append([])

    wb.save(excel_path)

    return FileResponse(excel_path, filename="converted.xlsx")


# -----------------------------------------------------
# 3️⃣ PDF Compression
# -----------------------------------------------------
@app.post("/convert/pdf-compress")
async def compress_pdf(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(TMP_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    original_path = os.path.join(job_folder, "input.pdf")
    compressed_path = os.path.join(job_folder, "compressed.pdf")

    with open(original_path, "wb") as f:
        f.write(await file.read())

    reader = PdfReader(original_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata(reader.metadata)
    writer.compress_content_streams()

    with open(compressed_path, "wb") as f:
        writer.write(f)

    return FileResponse(compressed_path, filename="compressed.pdf")


# -----------------------------------------------------
# 4️⃣ MULTIPLE FILES → ZIP
# -----------------------------------------------------
@app.post("/convert/multi-zip")
async def convert_multi_files(files: list[UploadFile] = File(...)):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(TMP_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    zip_path = os.path.join(job_folder, "files.zip")

    file_paths = []
    for file in files:
        file_path = os.path.join(job_folder, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        file_paths.append(file_path)

    with zipfile.ZipFile(zip_path, "w") as zipf:
        for path in file_paths:
            zipf.write(path, os.path.basename(path))

    return FileResponse(zip_path, filename="converted_batch.zip")
