from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from pdf2docx import Converter
from docx import Document
from PIL import Image
import requests

app = FastAPI()

# Autoriser ton site ConvertPro à appeler cette API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ensuite remplace par ton domaine
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "API RUNNING OK"}


# ---------------------------------------------------------
#           PDF → WORD (PRO)
# ---------------------------------------------------------
@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_to_word_pro(file: UploadFile = File(...)):
    try:
        pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        output_docx = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")

        pdf_temp.write(await file.read())
        pdf_temp.close()

        cv = Converter(pdf_temp.name)
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
            content={"error": "PDF→Word conversion failed", "details": str(e)}
        )


# ---------------------------------------------------------
#           PDF → WORD GOLD OCR
# ---------------------------------------------------------
@app.post("/convert/pdf-to-word-gold")
async def convert_pdf_gold(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()

        files = { "file": (file.filename, pdf_bytes, "application/pdf") }

        response = requests.post(
            "https://api.ocr.space/parse/image",
            files=files,
            data={"apikey": "helloworld"}  # gratuit mais limité
        )

        if response.status_code != 200:
            return JSONResponse(status_code=500, content={"error": "OCR API failed"})

        result = response.json()

        if "ParsedResults" not in result:
            return JSONResponse(status_code=500, content={"error": "No OCR result"})

        extracted_text = result["ParsedResults"][0].get("ParsedText", "")

        doc = Document()
        doc.add_paragraph(extracted_text)

        output_path = f"/tmp/{file.filename.replace('.pdf', '')}_OCR.docx"
        doc.save(output_path)

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename="converted_OCR.docx"
        )

    except Exception as e:
        return JSONResponse(status_code=500,
            content={"error": "OCR conversion failed", "details": str(e)})


# ---------------------------------------------------------
#           IMAGE → PDF
# ---------------------------------------------------------
@app.post("/convert/image-to-pdf")
async def convert_image_to_pdf(file: UploadFile = File(...)):
    try:
        img_bytes = await file.read()
        ext = os.path.splitext(file.filename)[1]

        img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        img_temp.write(img_bytes)
        img_temp.close()

        output_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

        img = Image.open(img_temp.name)
        img = img.convert("RGB")
        img.save(output_pdf.name, "PDF")

        return FileResponse(
            output_pdf.name,
            media_type="application/pdf",
            filename=file.filename.replace(ext, ".pdf")
        )

    except Exception as e:
        return JSONResponse(status_code=500,
            content={"error": "Image→PDF conversion failed", "details": str(e)})


# ---------------------------------------------------------
#           WORD → PDF  (Cloud API ✓ fonctionne Linux)
# ---------------------------------------------------------
@app.post("/convert/word-to-pdf")
async def convert_word_to_pdf(file: UploadFile = File(...)):
    try:
        word_bytes = await file.read()

        files = {
            "file": (
                file.filename,
                word_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }

        # ⚠ IMPORTANT — remplace XXXXX par ton vrai secret
        api_secret = "LzWmFyBCAA0GGYxdXRCdu1SoL1oDdWt9"

        response = requests.post(
            f"https://v2.convertapi.com/convert/docx/to/pdf?Secret={api_secret}",
            files=files,
        )

        if response.status_code != 200:
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Conversion service failed",
                    "details": response.text
                }
            )

        json_data = response.json()
        pdf_url = json_data["Files"][0]["Url"]

        pdf_content = requests.get(pdf_url).content

        output_path = f"/tmp/{file.filename.replace('.docx', '')}.pdf"
        with open(output_path, "wb") as f:
            f.write(pdf_content)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=file.filename.replace(".docx", ".pdf")
        )

 except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Word→PDF conversion failed", "details": str(e)}
        )
