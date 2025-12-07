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

# CORS → Permet d'appeler depuis ton site ConvertPro
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ensuite mettre https://convertpro.shop
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"status": "API RUNNING"}


# ----------------------------------------------------------
# PDF → WORD PRO
# ----------------------------------------------------------
@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_to_word(file: UploadFile = File(...)):
    try:
        pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        docx_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")

        pdf_temp.write(await file.read())
        pdf_temp.close()

        cv = Converter(pdf_temp.name)
        cv.convert(docx_temp.name)
        cv.close()

        return FileResponse(
            docx_temp.name,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", "_converted.docx")
        )

    except Exception as e:
        return JSONResponse({"error": "PDF→Word failed", "details": str(e)}, status_code=500)


# ----------------------------------------------------------
# PDF → WORD GOLD (OCR)
# ----------------------------------------------------------
@app.post("/convert/pdf-to-word-gold")
async def convert_pdf_gold(file: UploadFile = File(...)):
    try:
        pdf_bytes = await file.read()

        res = requests.post(
            "https://api.ocr.space/parse/image",
            files={"file": (file.filename, pdf_bytes, "application/pdf")},
            data={"apikey": "helloworld"}
        )

        result = res.json()

        print("OCR RESULT =", result)  # LOG

        if "ParsedResults" not in result:
            return JSONResponse({"error": "OCR failed", "details": result}, status_code=500)

        text = result["ParsedResults"][0].get("ParsedText", "")

        doc = Document()
        doc.add_paragraph(text)

        out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
        doc.save(out_file.name)

        return FileResponse(out_file.name, filename="ocr_converted.docx")

    except Exception as e:
        return JSONResponse({"error": "OCR conversion failed", "details": str(e)}, status_code=500)


# ----------------------------------------------------------
# IMAGE → PDF
# ----------------------------------------------------------
@app.post("/convert/image-to-pdf")
async def convert_img_to_pdf(file: UploadFile = File(...)):
    try:
        ext = os.path.splitext(file.filename)[1].lower()
        img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        img_temp.write(await file.read())
        img_temp.close()

        img = Image.open(img_temp.name).convert("RGB")
        pdf_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        img.save(pdf_temp.name, "PDF")

        return FileResponse(pdf_temp.name, filename=file.filename.replace(ext, ".pdf"))

    except Exception as e:
        return JSONResponse({"error": "Image→PDF failed", "details": str(e)}, status_code=500)


# ----------------------------------------------------------
# WORD → PDF (API ConvertAPI)
# ----------------------------------------------------------
from fastapi.responses import FileResponse
import uuid
import requests

CONVERT_API_SECRET = "Zavgn278zoIRqoo7r1s5aXnEtxHIBFww"

@app.post("/convert/word-to-pdf")
async def convert_word_to_pdf(file: UploadFile = File(...) ):
    try:
        # 1. Sauvegarde temporaire du fichier envoyé
        filename = f"temp_{uuid.uuid4()}.docx"
        with open(filename, "wb") as f:
            f.write(await file.read())

        # 2. Appel API ConvertAPI
        url = f"https://v2.convertapi.com/convert/docx/to/pdf?Secret={CONVERT_API_SECRET}"

        with open(filename, 'rb') as f:
            response = requests.post(
                url,
                files={'File': f}
            )

        # Vérification erreur API
        if response.status_code != 200:
            return {
                "error": "Conversion failed",
                "details": response.text
            }

        result = response.json()

        # 3. Téléchargement du PDF généré
        pdf_url = result['Files'][0]['Url']
        pdf_filename = f"converted_{uuid.uuid4()}.pdf"

        pdf_data = requests.get(pdf_url)

        with open(pdf_filename, "wb") as f:
            f.write(pdf_data.content)

        # 4. Retourne un vrai fichier PDF
        return FileResponse(
            pdf_filename,
            media_type="application/pdf",
            filename="converted.pdf"
        )

    except Exception as e:
        return {
            "error": "Word→PDF conversion failed",
            "details": str(e)
        }
