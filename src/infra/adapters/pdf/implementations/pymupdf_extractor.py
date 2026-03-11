import fitz

from src.infra.adapters.pdf.ports.pdf_extractor import ExtractedPdf, PdfExtractor


class PyMuPdfExtractor(PdfExtractor):
    async def extract(self, buffer: bytes) -> ExtractedPdf:
        doc = fitz.open(stream=buffer, filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        page_count = len(doc)
        doc.close()
        return ExtractedPdf(text=text, page_count=page_count)
