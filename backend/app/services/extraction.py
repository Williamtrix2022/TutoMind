"""Text extraction from PDF, DOCX and PPTX files."""

import logging
import zipfile
from dataclasses import dataclass
from io import BytesIO

from app.schemas.documents import DOCX_MIME, PDF_MIME, PPTX_MIME

logger = logging.getLogger(__name__)

# DOCX/PPTX are zip files: refuse ones that would expand to something absurd (zip bombs).
MAX_UNCOMPRESSED_BYTES = 200 * 1024 * 1024


class ExtractionError(Exception):
    """The file cannot be turned into text. The message is safe to show to the teacher."""


@dataclass(frozen=True)
class Page:
    number: int | None  # PDF page / PPTX slide; None when the format has no pages (DOCX)
    text: str


def _check_zip_size(data: bytes) -> None:
    with zipfile.ZipFile(BytesIO(data)) as archive:
        if sum(info.file_size for info in archive.infolist()) > MAX_UNCOMPRESSED_BYTES:
            raise ExtractionError("El archivo descomprimido supera el tamaño permitido.")


def _pdf(data: bytes) -> list[Page]:
    from pypdf import PdfReader

    reader = PdfReader(BytesIO(data))
    if reader.is_encrypted:
        raise ExtractionError("El PDF está protegido con contraseña.")
    return [
        Page(number=i, text=page.extract_text() or "") for i, page in enumerate(reader.pages, 1)
    ]


def _docx(data: bytes) -> list[Page]:
    from docx import Document

    document = Document(BytesIO(data))
    lines = [p.text for p in document.paragraphs]
    for table in document.tables:
        lines += [cell.text for row in table.rows for cell in row.cells]
    return [Page(number=None, text="\n".join(lines))]


def _pptx(data: bytes) -> list[Page]:
    from pptx import Presentation

    pages = []
    for number, slide in enumerate(Presentation(BytesIO(data)).slides, 1):
        texts = [shape.text_frame.text for shape in slide.shapes if shape.has_text_frame]
        pages.append(Page(number=number, text="\n".join(texts)))
    return pages


def extract_pages(data: bytes, mime_type: str) -> list[Page]:
    """Return the non-empty pages. Raises `ExtractionError` with a teacher-friendly message."""
    try:
        if mime_type == PDF_MIME:
            pages = _pdf(data)
        elif mime_type in (DOCX_MIME, PPTX_MIME):
            _check_zip_size(data)
            pages = _docx(data) if mime_type == DOCX_MIME else _pptx(data)
        else:
            raise ExtractionError("Tipo de archivo no soportado.")
    except ExtractionError:
        raise
    except Exception as error:  # parser libraries raise many unrelated exception types
        logger.info("Could not read %s file: %s", mime_type, error)
        raise ExtractionError(
            "No se pudo leer el archivo. Puede estar dañado; prueba con otra versión."
        ) from error

    pages = [page for page in pages if page.text.strip()]
    if not pages:
        raise ExtractionError("El archivo no contiene texto que se pueda extraer.")
    return pages
