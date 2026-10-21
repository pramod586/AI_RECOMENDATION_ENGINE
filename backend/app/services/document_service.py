
from pathlib import Path

from docx import Document as DocxDocument
from pypdf import PdfReader


def extract_text(file_path: str) -> str:
    """
    Extract text from PDF, DOCX, or TXT files.
    """

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension == ".pdf":
        reader = PdfReader(str(path))

        pages = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")

        return "\n".join(pages)

    elif extension == ".docx":
        document = DocxDocument(str(path))

        paragraphs = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(paragraphs)

    elif extension == ".txt":
        return path.read_text(encoding="utf-8", errors="replace")

    else:
        raise ValueError("Unsupported file type")


def split_text(
    text: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[str]:
    """
    Split text into chunks with overlapping context.
    """

    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    text = text.strip()

    if not text:
        return []

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end == len(text):
            break

        start = end - overlap

    return chunks