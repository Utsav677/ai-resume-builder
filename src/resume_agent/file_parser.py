"""File parsing utilities for extracting text from various file formats"""
import io
from typing import Optional
from pypdf import PdfReader
from docx import Document
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file.
    First tries direct text extraction, falls back to OCR if needed.
    """
    try:
        # Try direct text extraction first
        pdf_reader = PdfReader(io.BytesIO(file_content))
        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        # If we got meaningful text, return it
        if text.strip() and len(text.strip()) > 100:
            return text.strip()

        # If no text or very little text, try OCR
        print("PDF has little to no text, attempting OCR...")
        return extract_text_from_pdf_ocr(file_content)

    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        # Try OCR as fallback
        try:
            return extract_text_from_pdf_ocr(file_content)
        except Exception as ocr_error:
            print(f"OCR also failed: {ocr_error}")
            raise ValueError(f"Could not extract text from PDF: {str(e)}")


def extract_text_from_pdf_ocr(file_content: bytes) -> str:
    """
    Extract text from PDF using OCR (for scanned PDFs or images).
    Requires tesseract-ocr to be installed on the system.
    """
    try:
        # Convert PDF to images
        images = convert_from_bytes(file_content)

        text = ""
        for i, image in enumerate(images):
            # Perform OCR on each page
            page_text = pytesseract.image_to_string(image)
            text += page_text + "\n"

        return text.strip()

    except Exception as e:
        raise ValueError(f"OCR failed. Make sure tesseract-ocr is installed: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        doc = Document(io.BytesIO(file_content))
        text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
        return text.strip()
    except Exception as e:
        raise ValueError(f"Could not extract text from DOCX: {str(e)}")


def extract_text_from_image(file_content: bytes) -> str:
    """Extract text from image file using OCR"""
    try:
        image = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        raise ValueError(f"Could not extract text from image: {str(e)}")


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text from uploaded file based on file extension.

    Supports:
    - PDF (with OCR fallback for scanned documents)
    - DOCX
    - TXT
    - Images (PNG, JPG, JPEG) via OCR
    """
    filename_lower = filename.lower()

    # PDF files
    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_content)

    # DOCX files
    elif filename_lower.endswith('.docx'):
        return extract_text_from_docx(file_content)

    # Plain text files
    elif filename_lower.endswith('.txt'):
        return file_content.decode('utf-8', errors='ignore')

    # Image files
    elif filename_lower.endswith(('.png', '.jpg', '.jpeg')):
        return extract_text_from_image(file_content)

    else:
        raise ValueError(f"Unsupported file format: {filename}. Supported formats: PDF, DOCX, TXT, PNG, JPG")
