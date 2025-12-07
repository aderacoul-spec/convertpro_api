from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
import os
import uuid
from docx import Document
import pdfplumber

app = FastAPI()

UPLOAD_DIR = "/tmp"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.get("/")
def root():
    return {"message": "ConvertPro API OK"}


@app.post("/convert/pdf-to-word")
async def pdf_to_word(file: UploadFile = File(...)):
    file_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    output_path = os.path.join(UPLOAD_DIR, f"{file_id}.docx")

    # Enregistrer le PDF uploadé
    with open(input_path, "wb") as f:
        f.write(await file.read())

    # Analyse du PDF
    doc = Document()

    with pdfplumber.open(input_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()

            if text:
                for line in text.split("\n"):
                    doc.add_paragraph(line)
            doc.add_page_break()

    # Sauvegarder le fichier Word
    doc.save(output_path)

    # Retourner le fichier Word
    return FileResponse(
        output_path,
        filename="fichier_converti.docx",
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
