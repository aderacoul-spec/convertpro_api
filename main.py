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
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os

app = FastAPI()
@app.post("/convert/word-to-pdf")
async def word_to_pdf(file: UploadFile = File(...)):
    try:
        # 1) Sauvegarde du fichier reçu
        input_path = f"/convert/{file.filename}"
        with open(input_path, "wb") as buffer:
            buffer.write(await file.read())

        # 2) Conversion avec unoconv
        output_path = input_path.replace(".docx", ".pdf").replace(".doc", ".pdf")

        result = os.system(f"unoconv -f pdf {input_path}")

        if result != 0:
            return {
                "error": "Conversion ratée",
                "details": "unoconv n'a pas pu convertir le fichier"
            }

        # 3) Retour du fichier converti
        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename=os.path.basename(output_path)
        )

    except Exception as e:
        return {"error": "Erreur interne", "details": str(e)}
