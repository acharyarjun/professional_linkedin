"""Market and news ingestion for enriching daily posts."""

from __future__ import annotations

import html
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

GOOGLE_NEWS_QUERIES = [
    "port automation AI",
    "berthing systems",
    "mooring technology",
    "LNG terminal automation",
]


@dataclass(frozen=True)
class ResearchItem:
    title: str
    url: str
    summary: str
    date: str
    source: str


class MarketResearcher:
    """Fetches recent headlines from maritime and automation sources."""

    def __init__(self, timeout_sec: float = 25.0) -> None:
        self._timeout = timeout_sec
        self._session = requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def _get_soup(self, url: str) -> BeautifulSoup:
        resp = self._session.get(url, timeout=self._timeout)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "html.parser")

    def _parse_rss(self, xml_text: str, source_label: str) -> List[ResearchItem]:
        items: List[ResearchItem] = []
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as exc:
            logger.warning("RSS parse error for {}: {}", source_label, exc)
            return items
        channel = root.find("channel")
        if channel is None:
            return items
        for it in channel.findall("item")[:12]:
            title_el = it.find("title")
            link_el = it.find("link")
            desc_el = it.find("description")
            pub_el = it.find("pubDate")
            title = (title_el.text or "").strip() if title_el is not None else ""
            url = (link_el.text or "").strip() if link_el is not None else ""
            raw_desc = (desc_el.text or "").strip() if desc_el is not None else ""
            summary = BeautifulSoup(html.unescape(raw_desc), "html.parser").get_text(
                " ", strip=True
            )
            pub = (pub_el.text or "").strip() if pub_el is not None else ""
            if not title or not url:
                continue
            items.append(
                ResearchItem(
                    title=title[:500],
                    url=url[:2000],
                    summary=summary[:1200],
                    date=pub,
                    source=source_label,
                )
            )
        return items

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=20),
        reraise=True,
    )
    def _fetch_google_news(self, query: str) -> List[ResearchItem]:
        q = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en"
        resp = self._session.get(url, timeout=self._timeout)
        resp.raise_for_status()
        return self._parse_rss(resp.text, f"Google News: {query}")

    def _extract_article_cards(
        self, soup: BeautifulSoup, base_host: str, source_label: str, limit: int = 8
    ) -> List[ResearchItem]:
        out: List[ResearchItem] = []
        for a in soup.find_all("a", href=True):
            if len(out) >= limit:
                break
            href = a.get("href", "")
            title = a.get_text(" ", strip=True)
            if len(title) < 24:
                continue
            if href.startswith("/"):
                href = f"https://{base_host}{href}"
            if not href.startswith("http"):
                continue
            if any(x in href.lower() for x in ("/tag/", "/category/", "/author/", "#")):
                continue
            out.append(
                ResearchItem(
                    title=title[:500],
                    url=href[:2000],
                    summary="",
                    date="",
                    source=source_label,
                )
            )
        return out

    def _scrape_porttechnology(self) -> List[ResearchItem]:
        try:
            soup = self._get_soup("https://www.porttechnology.org/news/")
        except Exception as exc:
            logger.warning("porttechnology.org scrape failed: {}", exc)
            return []
        return self._extract_article_cards(soup, "www.porttechnology.org", "Port Technology")

    def _scrape_lloydslist(self) -> List[ResearchItem]:
        try:
            soup = self._get_soup("https://www.lloydslist.com/")
        except Exception as exc:
            logger.warning("lloydslist.com scrape failed: {}", exc)
            return []
        items = self._extract_article_cards(soup, "www.lloydslist.com", "Lloyd's List")
        return items

    def _scrape_safety4sea(self) -> List[ResearchItem]:
        try:
            soup = self._get_soup("https://safety4sea.com/")
        except Exception as exc:
            logger.warning("safety4sea.com scrape failed: {}", exc)
            return []
        return self._extract_article_cards(soup, "safety4sea.com", "Safety4Sea")

    def get_daily_insights(self) -> List[ResearchItem]:
        """Aggregate research items from configured web sources and Google News RSS."""
        collected: List[ResearchItem] = []
        collected.extend(self._scrape_porttechnology())
        collected.extend(self._scrape_lloydslist())
        collected.extend(self._scrape_safety4sea())
        for q in GOOGLE_NEWS_QUERIES:
            try:
                collected.extend(self._fetch_google_news(q))
            except Exception as exc:
                logger.warning("Google News query {!r} failed: {}", q, exc)

        dedup: dict[str, ResearchItem] = {}
        for item in collected:
            key = re.sub(r"\s+", " ", item.title.lower())[:160]
            if key not in dedup:
                dedup[key] = item

        normalized: List[ResearchItem] = []
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        for it in dedup.values():
            dt = it.date
            if not dt:
                dt = today
            else:
                try:
                    dt = date_parser.parse(it.date).astimezone(timezone.utc).strftime("%Y-%m-%d")
                except (ValueError, TypeError, OverflowError):
                    dt = today
            normalized.append(
                ResearchItem(
                    title=it.title,
                    url=it.url,
                    summary=it.summary,
                    date=dt,
                    source=it.source,
                )
            )
        normalized.sort(key=lambda x: x.date, reverse=True)
        logger.info("Collected {} research items for daily insights", len(normalized))
        return normalized[:40]
