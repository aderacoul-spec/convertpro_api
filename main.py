from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import tempfile
from pdf2docx import Converter
import pdfplumber
import requests
import os
import uuid

app = FastAPI()

# Route test
@app.get("/")
def root():
    return {"status": "ConvertPro API is running 🚀"}


# ------- SIMPLE CONVERSION PDF ➝ WORD -------
@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_to_word_pro(file: UploadFile = File(...)):
    try:
        # Sauvegarder PDF temporaire
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(await file.read())
            temp_pdf_path = temp_pdf.name

        # Générer fichier Word de sortie
        output_path = temp_pdf_path.replace(".pdf", ".docx")

        # Conversion PDF -> Word
        cv = Converter(temp_pdf_path)
        cv.convert(output_path, start=0, end=None)
        cv.close()

        # Envoyer le fichier converti
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", ".docx")
        )

    except Exception as e:
        return JSONResponse({"error": "Conversion failed", "details": str(e)}, status_code=500)
    finally:
        # Nettoyage
        try:
            os.remove(temp_pdf_path)
        except:
            pass



# ------- VERSION GOLD (OCR EXTERNE) -------
@app.post("/convert/pdf-to-word-gold")
async def convert_pdf_to_word_gold(file: UploadFile = File(...)):
    try:
        # Sauvegarder le PDF temporairement
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(await file.read())
            pdf_path = temp_pdf.name

        # Lire le PDF page par page pour extraire des images
        extracted_text = ""

        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

        # Si texte vide → OCR externe
        if extracted_text.strip() == "":
            # API gratuite OCR gratuite
            # Endpoint public OCR.space
            ocr_api_url = "https://api.ocr.space/parse/image"

            payload = {
                "apikey": "helloworld",  # Clé publique gratuite
                "language": "fre"
            }
            with open(pdf_path, 'rb') as f:
                response = requests.post(ocr_api_url, files={"file": f}, data=payload)
                ocr_result = response.json()

            if 'ParsedResults' in ocr_result:
                extracted_text = ocr_result['ParsedResults'][0]['ParsedText']

        # Générer Word
        output_path = pdf_path.replace(".pdf", "-gold.docx")
        try:
            from docx import Document
        except:
            return {"error": "docx module missing"}

        doc = Document()
        doc.add_paragraph(extracted_text)
        doc.save(output_path)

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", "_gold.docx")
        )

    except Exception as e:
        return JSONResponse({"error": "Erreur GOLD", "details": str(e)}, status_code=500)
    finally:
        try:
            os.remove(pdf_path)
        except:
            pass
