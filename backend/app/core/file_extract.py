from __future__ import annotations

from pathlib import Path

def extract_text_from_file(path: str, file_type: str) -> str:
    """
    Extract plain text from uploaded file.
    Supports: txt, pdf, docx
    """
    file_type = (file_type or "").lower()

    if file_type == "txt":
        return _extract_txt(path)

    if file_type == "pdf":
        return _extract_pdf(path)

    if file_type == "docx":
        return _extract_docx(path)

    return ""


def _extract_txt(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _extract_pdf(path: str) -> str:
    try:
        from pypdf import PdfReader

        reader = PdfReader(path)
        text = []

        for page in reader.pages:
            t = page.extract_text()
            if t:
                text.append(t)

        return "\n\n".join(text)
    except Exception as e:
        print("PDF extract error:", e)
        return ""


def _extract_docx(path: str) -> str:
    try:
        from docx import Document

        doc = Document(path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n\n".join(paragraphs)
    except Exception as e:
        print("DOCX extract error:", e)
        return ""
