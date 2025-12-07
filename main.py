from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
import uuid, os
from pdf2docx import Converter

app = FastAPI()

TMP_DIR = "/tmp/convertpro"
os.makedirs(TMP_DIR, exist_ok=True)


@app.get("/")
def home():
    return {"message": "ConvertPro API Running OK"}


@app.post("/convert/pdf-to-word-pro")
async def convert_pdf_word(file: UploadFile = File(...)):
    try:
        job_id = str(uuid.uuid4())
        job_folder = os.path.join(TMP_DIR, job_id)
        os.makedirs(job_folder, exist_ok=True)

        pdf_path = os.path.join(job_folder, "input.pdf")
        word_path = os.path.join(job_folder, "output.docx")

        # save PDF
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        # try conversion
        try:
            converter = Converter(pdf_path)
            converter.convert(word_path)
            converter.close()
        except Exception as e:
            return JSONResponse(
                content={"error": "Conversion failed", "details": str(e)},
                status_code=500
            )

        return FileResponse(
            word_path,
            filename="converted_premium.docx",
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    except Exception as e:
        return JSONResponse(
            content={"error": "Internal error", "details": str(e)},
            status_code=500
        )
