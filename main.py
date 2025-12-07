from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse, JSONResponse
import tempfile
import os
from pdf2docx import Converter
import pdfplumber
from docx import Document
import requests
app = FastAPI()
# 🔓 Autoriser ton site à appeler l’API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tu pourras ensuite mettre ["https://convertpro.shop"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app = FastAPI()


###############################################
#  TEST SERVER
###############################################
@app.get("/")
def root():
    return {"status": "ConvertPro API active 🚀"}



###############################################
#  PDF → WORD (PRO)
###############################################
@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_to_word_pro(file: UploadFile = File(...)):

    try:
        # Save PDF temporary
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(await file.read())
            pdf_path = temp_pdf.name

        output_path = pdf_path.replace(".pdf", ".docx")

        # Conversion
        cv = Converter(pdf_path)
        cv.convert(output_path)
        cv.close()

        # Return DOCX
        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", ".docx")
        )

    except Exception as e:
        return JSONResponse({"error": "Conversion failed", "details": str(e)}, status_code=500)

    finally:
        try:
            os.remove(pdf_path)
        except:
            pass



###############################################
#  PDF → WORD (GOLD, OCR intelligent)
###############################################
@app.post("/convert/pdf-to-word-gold")
async def convert_pdf_to_word_gold(file: UploadFile = File(...)):

    try:
        # Save PDF first
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            temp_pdf.write(await file.read())
            pdf_path = temp_pdf.name

        extracted_text = ""

        # Try extracting text normally
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                extracted_text += page.extract_text() or ""

        # IF text empty → OCR free API
        if extracted_text.strip() == "":
            ocr_api_url = "https://api.ocr.space/parse/image"

            payload = {
                "apikey": "helloworld",  # Free key
                "language": "fra"
            }

            with open(pdf_path, 'rb') as f:
                response = requests.post(ocr_api_url, files={"file": f}, data=payload)
                result_json = response.json()

            try:
                extracted_text = result_json["ParsedResults"][0]["ParsedText"]
            except:
                extracted_text = "Texte non reconnu via OCR"

        # create word
        output_path = pdf_path.replace(".pdf", "-gold.docx")
        doc = Document()
        doc.add_paragraph(extracted_text)
        doc.save(output_path)

        return FileResponse(
            output_path,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            filename=file.filename.replace(".pdf", "_gold.docx")
        )

    except Exception as e:
        return JSONResponse({"error": "Gold conversion failed", "details": str(e)}, status_code=500)

    finally:
        try:
            os.remove(pdf_path)
        except:
            pass




###############################################
#  IMAGE → PDF
###############################################
@app.post("/convert/image-to-pdf")
async def convert_image_to_pdf(file: UploadFile = File(...)):

    try:
        # Save image temporarily
        with tempfile.NamedTemporaryFile(delete=False) as temp_img:
            temp_img.write(await file.read())
            image_path = temp_img.name

        from PIL import Image

        img = Image.open(image_path)
        img = img.convert("RGB")  # PDF needs RGB

        output_path = image_path + ".pdf"
        img.save(output_path)

        return FileResponse(
            output_path,
            media_type="application/pdf",
            filename="converted.pdf"
        )

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    finally:
        try:
            os.remove(image_path)
        except:
            pass




###############################################
#  WORD → PDF (via CloudConvert)
###############################################
@app.post("/convert/word-to-pdf")
async def convert_word_to_pdf(file: UploadFile = File(...)):

    try:
        # Save file locally
        with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as temp_doc:
            temp_doc.write(await file.read())
            doc_path = temp_doc.name

        # CloudConvert API - Public Job Creation
        url = "https://api.cloudconvert.com/v2/import/upload"
        result = requests.post(url).json()

        return JSONResponse({
            "message": "Conversion Word → PDF prête",
            "instructions": "Installer conversion CloudConvert complète",
        })

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    finally:
        try:
            os.remove(doc_path)
        except:
            pass
