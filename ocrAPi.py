from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import gdown
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import re
import os

# Set the tesseract executable path (if needed)
pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

app = FastAPI()

class PDFRequest(BaseModel):
    url: str

# Function to extract file ID from Google Drive URL
def extract_file_id_from_url(url: str):
    match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
    return match.group(1) if match else None

# Function to download the PDF from Google Drive
def download_pdf_from_drive(file_id: str):
    url = f"https://drive.google.com/uc?id={file_id}"
    output = "downloaded_file.pdf"
    gdown.download(url, output, quiet=False)
    return output

# Function to extract text from the PDF using OCR
def extract_text_from_pdf(pdf_file_path: str):
    doc = fitz.open(pdf_file_path)
    full_text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.open(io.BytesIO(pix.tobytes()))
        text = pytesseract.image_to_string(img)
        full_text += text
    return full_text

@app.post("/extract_text/")
def extract_text(pdf_request: PDFRequest):
    file_id = extract_file_id_from_url(pdf_request.url)
    if not file_id:
        raise HTTPException(status_code=400, detail="Invalid Google Drive URL")
    
    try:
        pdf_path = download_pdf_from_drive(file_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading file: {str(e)}")
    
    try:
        extracted_text = extract_text_from_pdf(pdf_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting text: {str(e)}")
    
    os.remove(pdf_path)  # Clean up the downloaded file
    return {"extracted_text": extracted_text}
import uvicorn

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)

