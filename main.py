from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import uuid, os
from PIL import Image
import fitz  # PyMuPDF
from docx import Document
from docx.shared import Inches

app = FastAPI()

TMP_DIR = "/tmp/convertpro"
os.makedirs(TMP_DIR, exist_ok=True)


@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_word_image_based(file: UploadFile = File(...)):
    try:
        job_id = str(uuid.uuid4())
        job_folder = os.path.join(TMP_DIR, job_id)
        os.makedirs(job_folder, exist_ok=True)

        pdf_path = os.path.join(job_folder, "input.pdf")
        word_path = os.path.join(job_folder, "output.docx")

        # Save file
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # Convert PDF to images
        doc = fitz.open(pdf_path)
        word_doc = Document()

        for page_index in range(len(doc)):
            page = doc.load_page(page_index)
            pix = page.get_pixmap(dpi=200)

            image_path = os.path.join(job_folder, f"page_{page_index}.png")
            pix.save(image_path)

            word_doc.add_picture(image_path, width=Inches(6.5))
            word_doc.add_page_break()

        word_doc.save(word_path)

        return FileResponse(
            word_path,
            filename="converted_premium_visual.docx"
        )

    except Exception as e:
        return JSONResponse(
            content={"error": "Internal conversion error", "details": str(e)},
            status_code=500
        )
