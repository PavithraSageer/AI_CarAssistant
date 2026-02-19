import os
import pytesseract
from PIL import Image
import pdfplumber
from pdf2image import convert_from_path

# Set Tesseract path (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def extract_text(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    # 🖼️ Image → OCR
    if ext in [".jpg", ".jpeg", ".png"]:
        img = Image.open(file_path)
        return pytesseract.image_to_string(img)

    # 📄 PDF
    elif ext == ".pdf":
        text = ""

        # 1️⃣ Try pdfplumber (text-based PDF)
        with pdfplumber.open(file_path) as pdf:
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"\n--- Page {i+1} ---\n{page_text}"

        # 2️⃣ If empty → scanned PDF → OCR
        if text.strip() == "":
            pages = convert_from_path(
                file_path,
                poppler_path=r"C:\Users\User\Release-25.12.0-0\poppler-25.12.0\Library\bin" # ⚠️ Required on Windows
            )

            for i, page in enumerate(pages):
                page_text = pytesseract.image_to_string(page)
                text += f"\n--- OCR Page {i+1} ---\n{page_text}"

        return text

    else:
        return "Unsupported file type"


# 📂 Your file path
FilePath = r"C:\Users\User\Downloads\5ceadbbb-d202-40a3-949d-3f91661ab37e.pdf"

text = extract_text(FilePath)

print("Extracted Text:\n")
print(text)

import mysql.connector
import os

def store_in_mysql(file_path, extracted_text):
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Samanta@123",
        database="contract_review_ai"
    )

    cursor = conn.cursor()

    file_name = os.path.basename(file_path)
    file_type = os.path.splitext(file_path)[1].lower()

    sql = """
    INSERT INTO documents (file_name, file_type, extracted_text)
    VALUES (%s, %s, %s)
    """

    cursor.execute(sql, (file_name, file_type, extracted_text))
    conn.commit()

    print("Stored in MySQL successfully!")

    cursor.close()
    conn.close()
    
# Store the extracted text in MySQL
store_in_mysql(FilePath, text)
"""
to view stored documents: 
Run SQL:
SELECT id, file_name FROM documents;

To view stored OCR text:
SELECT extracted_text FROM documents WHERE id=1;
"""