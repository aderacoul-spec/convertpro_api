@app.post("/convert/pdf-to-word-advanced")
async def convert_pdf_word(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    job_folder = os.path.join(TMP_DIR, job_id)
    os.makedirs(job_folder, exist_ok=True)

    pdf_path = os.path.join(job_folder, "input.pdf")
    word_path = os.path.join(job_folder, "output.docx")

    with open(pdf_path, "wb") as f:
        f.write(await file.read())

    doc = Document()

    from docx.shared import Inches

    with pdfplumber.open(pdf_path) as pdf:
        for idx, page in enumerate(pdf.pages):
            text = page.extract_text()

            # Texte
            if text:
                for line in text.split("\n"):
                    doc.add_paragraph(line)

            # Images
            for img_index, img in enumerate(page.images):
                cropped = page.within_bbox((img["x0"], img["top"], img["x1"], img["bottom"])).to_image()

                image_path = os.path.join(job_folder, f"img_{idx}_{img_index}.png")
                cropped.save(image_path, format="PNG")

                try:
                    doc.add_picture(image_path, width=Inches(5))
                except:
                    pass

            doc.add_page_break()

    # Watermark léger
    doc.add_paragraph("\n--- Converti avec ConvertPro.shop ---")
    doc.save(word_path)

    return FileResponse(word_path, filename="converted-premium.docx")
