from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ExtractedPdf:
    text: str
    page_count: int


class PdfExtractor(ABC):
    @abstractmethod
    async def extract(self, buffer: bytes) -> ExtractedPdf: ...
