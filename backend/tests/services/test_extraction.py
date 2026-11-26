import pytest

from app.services.extraction import ExtractionError, extract_pages
from tests.files import DOCX, PDF, PPTX, make_docx, make_pdf, make_pptx


def test_pdf_keeps_one_entry_per_page_with_its_number():
    pages = extract_pages(make_pdf(["derivadas basicas", "integrales definidas"]), PDF)

    assert [(p.number, p.text.strip()) for p in pages] == [
        (1, "derivadas basicas"),
        (2, "integrales definidas"),
    ]


def test_docx_text_is_extracted_without_page_numbers():
    pages = extract_pages(make_docx(["Primer párrafo.", "Segundo párrafo."]), DOCX)

    assert all(p.number is None for p in pages)
    assert "Primer párrafo." in "\n".join(p.text for p in pages)
    assert "Segundo párrafo." in "\n".join(p.text for p in pages)


def test_pptx_uses_the_slide_number_as_page():
    pages = extract_pages(make_pptx(["Límites", "Continuidad"]), PPTX)

    assert [(p.number, p.text.strip()) for p in pages] == [(1, "Límites"), (2, "Continuidad")]


@pytest.mark.parametrize("mime", [PDF, DOCX, PPTX])
def test_corrupt_file_raises_extraction_error(mime):
    with pytest.raises(ExtractionError):
        extract_pages(b"this is not a real document", mime)


def test_document_without_text_raises_extraction_error():
    with pytest.raises(ExtractionError, match="texto"):
        extract_pages(make_docx(["", "   "]), DOCX)


def test_zip_bomb_is_rejected_before_it_is_opened(monkeypatch):
    import app.services.extraction as extraction

    monkeypatch.setattr(extraction, "MAX_UNCOMPRESSED_BYTES", 1_000)

    with pytest.raises(ExtractionError, match="tamaño"):
        extract_pages(make_docx(["x" * 5_000]), DOCX)
