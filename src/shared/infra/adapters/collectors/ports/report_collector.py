from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CommunicationItem:
    type: str
    date: str
    link_url: str


class ReportCollector(ABC):
    @abstractmethod
    async def list_communications(self, ticker: str) -> list[CommunicationItem]: ...

    @abstractmethod
    async def resolve_pdf_url(self, link_url: str) -> str: ...

    @abstractmethod
    async def download_pdf(self, url: str) -> bytes: ...
