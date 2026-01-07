# utils/pdf_utils.py
from PyPDF2 import PdfReader

def extract_text_from_pdf(file_path: str) -> str:
    reader = PdfReader(file_path)
    return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def chunk_text(text: str, chunk_size: int = 600, overlap: int = 60):
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end]
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def extract_first_n_pages(file_path: str, n_pages: int) -> str:
    reader = PdfReader(file_path)
    pages = reader.pages[:n_pages]
    return "\n".join([page.extract_text() for page in pages if page.extract_text()])