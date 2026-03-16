"""PDF document processor using PyMuPDF."""

import fitz  # PyMuPDF


def extract_text_from_pdf(file_path: str) -> tuple[str, int]:
    """
    Extract text from a PDF file.
    Returns (full_text, page_count).
    """
    doc = fitz.open(file_path)
    pages = []
    for page in doc:
        text = page.get_text("text")
        if text.strip():
            pages.append(text)
    page_count = len(doc)
    doc.close()
    return "\n\n".join(pages), page_count
