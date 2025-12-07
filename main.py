from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from pdf2docx import Converter
import pdfplumber
from docx import Document
import requests

app = FastAPI()

# Autoriser ton site à appeler l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ensuite mets https://convertpro.shop
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "API RUNNING OK"}


# ------------------- PDF → WORD PRO -------------------------
@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_to_word_pro(file: UploadFile = File(...)):
    try:
        # Créer fichiers temporaires
        pdf_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")

        pdf_file.write(await file.read())
        pdf_file.close()

        cv = Converter(pdf_file.name)
        cv.convert(output_docx.name, start=0, end=None)
        cv.close()

        return FileResponse(
            output_docx.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", "_converted.docx")
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Conversion failed", "details": str(e)}
        )



# ------------------- PDF → WORD GOLD OCR -------------------------
@app.post("/convert/pdf-to-word-gold")
async def convert_pdf_gold(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()

        files = {
            "file": (file.filename, pdf_bytes, "application/pdf")
        }

        response = requests.post(
            "https://api.ocr.space/parse/image",
            files=files,
            data={"apikey": "helloworld"}
        )

        result = response.json()

        if not result or "ParsedResults" not in result:
            return JSONResponse(status_code=500, content={"error": "Failed to parse"})

        extracted_text = result["ParsedResults"][0].get("ParsedText", "")

        doc = Document()
        doc.add_paragraph(extracted_text)

        output_path = f"/tmp/{file.filename.replace('.pdf', '')}_ocr.docx"
        doc.save(output_path)

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", "_ocr.docx")
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "OCR conversion failed", "details": str(e)}
        )



# ------------------- IMAGE → PDF -------------------------
@app.post("/convert/image-to-pdf")
async def convert_image_to_pdf(file: UploadFile = File(...)):
    try:
        img_ext = os.path.splitext(file.filename)[1].lower()
        image_bytes = await file.read()

        temp_image = tempfile.NamedTemporaryFile(delete=False, suffix=img_ext)
        temp_image.write(image_bytes)
        temp_image.close()

        pdf_output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        from PIL import Image

        img = Image.open(temp_image.name)
        rgb_img = img.convert("RGB")
        rgb_img.save(pdf_output.name, "PDF")

        return FileResponse(
            pdf_output.name,
            media_type="application/pdf",
            filename=file.filename.replace(img_ext, ".pdf")
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Conversion failed", "details": str(e)}
        )



# ------------------- WORD → PDF -------------------------
@app.post("/convert/word-to-pdf")
async def convert_word_to_pdf(file: UploadFile = File(...)):
    try:
        word_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        word_file.write(await file.read())
        word_file.close()

        pdf_output = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        from docx2pdf import convert
        convert(word_file.name, pdf_output.name)

        return FileResponse(
            pdf_output.name,
            media_type="application/pdf",
            filename=file.filename.replace(".docx", ".pdf")
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Conversion failed", "details": str(e)}
        )
