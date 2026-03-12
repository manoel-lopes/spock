import asyncio
import base64
import re
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from src.shared.infra.adapters.collectors.ports.report_collector import (
    CommunicationItem,
    ReportCollector,
)
from src.shared.infra.env.env import EnvSettings


class HttpReportCollector(ReportCollector):
    def __init__(self, env_service: EnvSettings) -> None:
        self._proxy_url = env_service.proxy_url
        self._proxy_secret = env_service.proxy_secret
        self._base_url = env_service.investidor10_base_url
        self._timeout_ms = env_service.investidor10_timeout_ms

    async def list_communications(self, ticker: str) -> list[CommunicationItem]:
        all_items: list[CommunicationItem] = []
        max_pages = 20

        for page in range(1, max_pages + 1):
            page_param = f"?page={page}" if page > 1 else ""
            target_url = f"{self._base_url}/communications/fii/{ticker}/{page_param}"
            html = await self._fetch_via_proxy(target_url)
            items = self._parse_communications_html(html)
            if not items:
                break
            all_items.extend(items)
            await asyncio.sleep(0.3)

        return all_items

    async def resolve_pdf_url(self, link_url: str) -> str:
        html = await self._fetch_via_proxy(link_url)
        match = re.search(r'window\.location\.href\s*=\s*"([^"]+)"', html)
        if not match:
            raise ValueError("Could not resolve PDF URL from redirect page")
        return match.group(1).replace("&amp;", "&")

    async def download_pdf(self, url: str) -> bytes:
        transport = httpx.AsyncHTTPTransport(retries=3)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get(url, timeout=120.0)
            response.raise_for_status()

        text = response.text
        cleaned = text.strip('"')

        if cleaned.startswith("JVBER"):
            return base64.b64decode(cleaned)

        buf = text.encode("latin-1")
        if not buf[:5] == b"%PDF-":
            raise ValueError(f"Response is not a valid PDF (starts with: {text[:50]})")
        return buf

    async def _fetch_via_proxy(self, target_url: str) -> str:
        if not self._proxy_url:
            raise ValueError("PROXY_URL is not configured")

        url = f"{self._proxy_url}?url={quote(target_url)}&secret={quote(self._proxy_secret)}"
        timeout_s = self._timeout_ms / 1000

        transport = httpx.AsyncHTTPTransport(retries=3)
        async with httpx.AsyncClient(transport=transport) as client:
            response = await client.get(url, timeout=timeout_s)
            response.raise_for_status()
            return response.text

    def _parse_communications_html(self, html: str) -> list[CommunicationItem]:
        soup = BeautifulSoup(html, "lxml")
        items: list[CommunicationItem] = []

        cards = soup.select("[class*='communication-card--content']")
        dates = soup.select("[class*='card-date--content']")
        links = soup.select("a[class*='btn-download-communication']")

        for i, card in enumerate(cards):
            if i >= len(dates) or i >= len(links):
                break

            comm_type = card.get_text(strip=True)
            date_text = dates[i].get_text(strip=True)
            href = links[i].get("href", "")

            if comm_type and date_text and href:
                items.append(
                    CommunicationItem(
                        type=comm_type,
                        date=date_text,
                        link_url=str(href),
                    )
                )

        return items
