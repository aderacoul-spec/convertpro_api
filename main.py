@app.post("/convert/word-to-pdf")
async def convert_word_to_pdf(file: UploadFile = File(...)):
    try:
        word_bytes = await file.read()

        files = {
            "file": (file.filename, word_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        }

        response = requests.post(
            "https://v2.convertapi.com/convert/docx/to/pdf?Secret=7RzsgHQPkhrDoQyq",
            files=files,
        )

        if response.status_code != 200:
            return JSONResponse(
                status_code=500,
                content={"error": "API failed", "details": response.text}
            )

        # Récupérer le PDF final depuis la réponse API
        pdf_url = response.json()["Files"][0]["Url"]

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
            content={"error": "Conversion failed", "details": str(e)}
        )
