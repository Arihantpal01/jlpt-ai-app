import fitz  # PyMuPDF

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""

    for page in doc:
        page_text = page.get_text("text")  # 🔥 IMPORTANT
        text += page_text + "\n"

    print("📄 Extracted length:", len(text))  # DEBUG

    return text.strip()