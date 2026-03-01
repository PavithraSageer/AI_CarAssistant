"""OCR service functions for image/PDF contract processing without system binaries."""

import base64
import os
from io import BytesIO
from typing import List

import fitz
import requests
from dotenv import load_dotenv
from fastapi import UploadFile
from PIL import Image
from pypdf import PdfReader

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY")
OPENROUTER_API_URL = os.getenv("OPENROUTER_API_URL", "https://openrouter.ai/api/v1/chat/completions")
OPENROUTER_VISION_MODEL = os.getenv("OPENROUTER_VISION_MODEL", "openai/gpt-4o-mini")

# Supported content types for upload validation.
ALLOWED_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
    "image/jpg",
    "image/tiff",
    "image/bmp",
}

# Supported file extensions for fallback validation when MIME is unavailable.
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".bmp"}


def validate_upload_file(file: UploadFile) -> None:
    """Validate that an uploaded file is either a supported PDF or image format."""
    # Check MIME type first because it is the fastest validation for uploads.
    if file.content_type and file.content_type.lower() in ALLOWED_CONTENT_TYPES:
        return

    # Fallback to extension-based validation when content type is missing/incorrect.
    lower_name = (file.filename or "").lower()
    if any(lower_name.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        return

    raise ValueError("Unsupported file type. Please upload a PDF or image file.")


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract embedded text from PDF pages using a pure Python parser."""
    try:
        reader = PdfReader(BytesIO(file_bytes))
    except Exception as error:
        raise ValueError("Unable to read PDF file. The uploaded PDF may be corrupted or unsupported.") from error

    page_texts = []
    for page in reader.pages:
        text = (page.extract_text() or "").strip()
        if text:
            page_texts.append(text)

    return "\n\n".join(page_texts).strip()


def _render_pdf_pages_as_images(file_bytes: bytes) -> List[Image.Image]:
    """Render PDF pages to Pillow images using PyMuPDF (no Poppler needed)."""
    images: List[Image.Image] = []
    try:
        document = fitz.open(stream=file_bytes, filetype="pdf")
    except Exception as error:
        raise ValueError("Unable to render PDF pages for OCR.") from error

    try:
        for page in document:
            pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            image = Image.frombytes("RGB", (pixmap.width, pixmap.height), pixmap.samples)
            images.append(image)
    finally:
        document.close()

    return images


def _extract_content_text(content: object) -> str:
    """Normalize OpenRouter message content into plain text."""
    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(str(item.get("text", "")))
        return "\n".join(part for part in parts if part).strip()

    return ""


def _ocr_image_with_openrouter(image: Image.Image) -> str:
    """Transcribe text from an image using OpenRouter vision models."""
    if OPENROUTER_API_KEY == "YOUR_OPENROUTER_API_KEY":
        raise ValueError(
            "OpenRouter API key is not configured. Set OPENROUTER_API_KEY in .env to process images/scanned PDFs."
        )

    buffer = BytesIO()
    image.convert("RGB").save(buffer, format="PNG")
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")

    payload = {
        "model": OPENROUTER_VISION_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "Extract all visible text from this document image. Return plain text only.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ],
            }
        ],
        "temperature": 0,
    }

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=120)
    response.raise_for_status()

    data = response.json()
    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as error:
        raise ValueError("Unexpected OpenRouter OCR response format.") from error

    text = _extract_content_text(content)
    if not text:
        raise RuntimeError("OCR completed, but no readable text was found.")

    return text


def _extract_text_from_images(images: List[Image.Image]) -> str:
    """Run OCR on images and return merged text."""
    page_texts = []
    for image in images:
        text = _ocr_image_with_openrouter(image)
        if text:
            page_texts.append(text.strip())

    merged_text = "\n\n".join(part for part in page_texts if part)
    if not merged_text.strip():
        raise RuntimeError("OCR completed, but no readable text was found.")

    return merged_text


def extract_text_from_upload(file_bytes: bytes, filename: str) -> str:
    """Extract plain text from uploaded PDF/image bytes without Tesseract/Poppler."""
    lower_name = (filename or "").lower()

    # PDF flow: try embedded text first, fallback to OCR on rendered pages.
    if lower_name.endswith(".pdf"):
        embedded_text = _extract_text_from_pdf(file_bytes)
        if embedded_text:
            return embedded_text

        images = _render_pdf_pages_as_images(file_bytes)
        if not images:
            raise RuntimeError("No pages found in PDF.")
        return _extract_text_from_images(images)

    # For image files, open bytes with Pillow then run OCR.
    try:
        image = Image.open(BytesIO(file_bytes))
    except Exception as error:
        raise ValueError("Unable to open image file. Please upload a valid image format.") from error

    return _extract_text_from_images([image])
