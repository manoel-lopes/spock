import pytest

from src.shared.infra.adapters.pdf.implementations.pymupdf_extractor import PyMuPdfExtractor


@pytest.mark.asyncio
async def test_extract_invalid_pdf():
    extractor = PyMuPdfExtractor()
    with pytest.raises(RuntimeError):
        await extractor.extract(b"not a pdf")
