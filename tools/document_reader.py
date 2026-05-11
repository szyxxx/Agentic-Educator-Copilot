"""
Educator Copilot — Document Reader Tool
=========================================
Extracts text from PDF files using PyMuPDF for material review.
"""

from langchain_core.tools import tool

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


@tool
def document_reader_tool(file_path: str) -> str:
    """
    Membaca dan mengekstrak teks dari file PDF materi dosen.
    Digunakan saat agent perlu memahami konten materi untuk review atau konteks analisis kuis.
    """
    if fitz is None:
        return "[ERROR] PyMuPDF belum terinstal. Jalankan: pip install PyMuPDF"

    try:
        doc = fitz.open(file_path)
        text_parts = []
        for page in doc:
            text_parts.append(page.get_text())
        doc.close()
        full_text = "\n".join(text_parts)
        # Limit to ~8000 chars to avoid token overflow
        return full_text[:8000] if len(full_text) > 8000 else full_text
    except Exception as e:
        return f"[ERROR] Gagal membaca PDF: {str(e)}"


def extract_pdf_text(file_path: str) -> str:
    """Direct function call (non-tool) for PDF extraction."""
    return document_reader_tool.invoke(file_path)
