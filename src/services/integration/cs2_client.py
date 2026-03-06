"""
CS2 Evidence Collection API client.

Task 7.0b: Connect to CS2 Evidence Collection.
CS2 produces evidence with rich metadata that CS4 must preserve:
  - source_type: SEC 10-K Item 1, Item 1A, Item 7, job posting, etc.
  - signal_category: technology_hiring, innovation_activity, etc.
  - confidence: Extraction confidence (0-1)
  - extracted_entities: Structured entities from the text

Wraps the existing FastAPI document/signal/evidence endpoints.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import httpx
import structlog

logger = structlog.get_logger()


# ============================================================================
# Enums (per CS4 PDF Section 3)
# ============================================================================


class SourceType(str, Enum):
    """Evidence source types from CS2."""
    SEC_10K_ITEM_1 = "sec_10k_item_1"       # Business description
    SEC_10K_ITEM_1A = "sec_10k_item_1a"     # Risk factors
    SEC_10K_ITEM_7 = "sec_10k_item_7"       # MD&A
    JOB_POSTING_LINKEDIN = "job_posting_linkedin"
    JOB_POSTING_INDEED = "job_posting_indeed"
    PATENT_USPTO = "patent_uspto"
    PRESS_RELEASE = "press_release"
    GLASSDOOR_REVIEW = "glassdoor_review"
    BOARD_PROXY_DEF14A = "board_proxy_def14a"
    ANALYST_INTERVIEW = "analyst_interview"  # DD interviews
    DD_DATA_ROOM = "dd_data_room"           # Data room docs
    NEWS_ARTICLE = "news_article"           # News/press releases


class SignalCategory(str, Enum):
    """Signal categories from CS2 collectors."""
    TECHNOLOGY_HIRING = "technology_hiring"
    INNOVATION_ACTIVITY = "innovation_activity"
    DIGITAL_PRESENCE = "digital_presence"
    LEADERSHIP_SIGNALS = "leadership_signals"
    CULTURE_SIGNALS = "culture_signals"
    GOVERNANCE_SIGNALS = "governance_signals"


# ============================================================================
# Mapping from CS3 data to CS4 enums
# ============================================================================

# Map CS3 filing type / signal source → SourceType
_SOURCE_TYPE_MAP = {
    "10-K": SourceType.SEC_10K_ITEM_7,
    "10-Q": SourceType.SEC_10K_ITEM_7,
    "8-K": SourceType.PRESS_RELEASE,
    # Signal sources
    "indeed": SourceType.JOB_POSTING_INDEED,
    "linkedin": SourceType.JOB_POSTING_LINKEDIN,
    "glassdoor": SourceType.GLASSDOOR_REVIEW,
    "company_website": SourceType.BOARD_PROXY_DEF14A,
    "news_press_releases": SourceType.NEWS_ARTICLE,
    "patentsview": SourceType.PATENT_USPTO,
}

# Map CS3 chunk section → more specific SourceType
_SECTION_SOURCE_MAP = {
    "item_1": SourceType.SEC_10K_ITEM_1,
    "item_1a": SourceType.SEC_10K_ITEM_1A,
    "item_7": SourceType.SEC_10K_ITEM_7,
}

# Map CS3 signal category → SignalCategory
_CATEGORY_MAP = {
    "technology_hiring": SignalCategory.TECHNOLOGY_HIRING,
    "innovation_activity": SignalCategory.INNOVATION_ACTIVITY,
    "digital_presence": SignalCategory.DIGITAL_PRESENCE,
    "leadership_signals": SignalCategory.LEADERSHIP_SIGNALS,
}


# ============================================================================
# Dataclasses
# ============================================================================


@dataclass
class ExtractedEntity:
    """Entity extracted from evidence text."""
    entity_type: str    # "ai_investment", "technology", "person", etc.
    text: str
    confidence: float
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CS2Evidence:
    """Evidence item from CS2 Evidence Collection."""
    evidence_id: str
    company_id: str
    source_type: SourceType
    signal_category: SignalCategory
    content: str
    extracted_at: datetime
    confidence: float

    # Optional metadata
    fiscal_year: Optional[int] = None
    source_url: Optional[str] = None
    page_number: Optional[int] = None
    extracted_entities: List[ExtractedEntity] = field(default_factory=list)

    # Indexing status
    indexed_in_cs4: bool = False
    indexed_at: Optional[datetime] = None


# ============================================================================
# CS2 Client
# ============================================================================


class CS2Client:
    """
    Client for CS2 Evidence Collection API.

    Fetches evidence from:
      - GET /api/v1/documents (SEC filing metadata)
      - GET /api/v1/documents/{id}/chunks (document text chunks)
      - GET /api/v1/signals (external signals: jobs, patents, tech)
      - GET /api/v1/evidence/companies/{id} (combined evidence view)
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)

    async def get_evidence(
        self,
        company_id: str,
        source_types: Optional[List[SourceType]] = None,
        signal_categories: Optional[List[SignalCategory]] = None,
        min_confidence: float = 0.0,
    ) -> List[CS2Evidence]:
        """
        Fetch all evidence for a company — documents + signals.

        Combines document chunks (SEC filings) and external signals
        (jobs, patents, tech stack, glassdoor, board, news) into
        a unified CS2Evidence list.
        """
        evidence_list: List[CS2Evidence] = []

        # Fetch document chunks
        doc_evidence = await self._fetch_document_evidence(company_id)
        evidence_list.extend(doc_evidence)

        # Fetch signal-based evidence
        signal_evidence = await self._fetch_signal_evidence(company_id)
        evidence_list.extend(signal_evidence)

        # Apply filters
        if source_types:
            type_set = set(source_types)
            evidence_list = [e for e in evidence_list if e.source_type in type_set]

        if signal_categories:
            cat_set = set(signal_categories)
            evidence_list = [e for e in evidence_list if e.signal_category in cat_set]

        if min_confidence > 0:
            evidence_list = [e for e in evidence_list if e.confidence >= min_confidence]

        logger.info(
            "cs2_evidence_fetched",
            company_id=company_id,
            total=len(evidence_list),
        )
        return evidence_list

    async def mark_indexed(self, evidence_ids: List[str]) -> int:
        """
        Mark evidence as indexed in CS4.

        NOTE: This is tracked in-memory by the CS4 layer since CS3's
        Snowflake schema doesn't have an indexed_in_cs4 column.
        Returns the count of IDs marked.
        """
        logger.info("cs2_mark_indexed", count=len(evidence_ids))
        return len(evidence_ids)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    # ── Internal: Document Evidence ─────────────────────────────

    async def _fetch_document_evidence(
        self, company_id: str
    ) -> List[CS2Evidence]:
        """Fetch SEC filing chunks as evidence items."""
        evidence = []

        try:
            # Get documents for this company
            response = await self.client.get(
                f"{self.base_url}/api/v1/documents",
                params={"company_id": company_id, "limit": 100},
            )
            response.raise_for_status()
            documents = response.json()

            for doc in documents:
                doc_id = doc["id"]
                filing_type = doc.get("filing_type", "10-K")
                filing_date = doc.get("filing_date", "")

                # Derive fiscal year from filing date
                fiscal_year = None
                if filing_date:
                    try:
                        fiscal_year = int(filing_date[:4])
                    except (ValueError, IndexError):
                        pass

                # Fetch chunks for this document
                try:
                    chunk_resp = await self.client.get(
                        f"{self.base_url}/api/v1/documents/{doc_id}/chunks"
                    )
                    chunk_resp.raise_for_status()
                    chunks = chunk_resp.json()
                except httpx.HTTPError:
                    chunks = []

                for chunk in chunks:
                    section = (chunk.get("section") or "").lower().strip()
                    content = chunk.get("content", "")

                    if not content or len(content.strip()) < 50:
                        continue

                    # Map section to specific source type
                    source_type = _SECTION_SOURCE_MAP.get(
                        section,
                        _SOURCE_TYPE_MAP.get(filing_type, SourceType.SEC_10K_ITEM_7),
                    )

                    # Map source type to signal category
                    signal_cat = self._source_to_signal(source_type)

                    evidence.append(CS2Evidence(
                        evidence_id=chunk.get("id", f"{doc_id}_chunk_{chunk.get('chunk_index', 0)}"),
                        company_id=company_id,
                        source_type=source_type,
                        signal_category=signal_cat,
                        content=content,
                        extracted_at=datetime.fromisoformat(
                            doc.get("created_at", datetime.now().isoformat())
                            .replace("Z", "+00:00")
                        ) if doc.get("created_at") else datetime.now(),
                        confidence=0.85,  # SEC filings are high-confidence
                        fiscal_year=fiscal_year,
                    ))

        except (httpx.HTTPError, httpx.ConnectError) as e:
            logger.warning("cs2_document_fetch_failed", company_id=company_id, error=str(e))

        return evidence

    async def _fetch_signal_evidence(
        self, company_id: str
    ) -> List[CS2Evidence]:
        """Fetch external signals as evidence items."""
        evidence = []

        try:
            response = await self.client.get(
                f"{self.base_url}/api/v1/signals",
                params={"company_id": company_id, "limit": 200},
            )
            response.raise_for_status()
            signals = response.json()

            for sig in signals:
                source = sig.get("source", "")
                category = sig.get("category", "")
                raw_value = sig.get("raw_value", "")
                metadata = sig.get("metadata", {}) or {}

                # Build content from raw_value + metadata
                content_parts = []
                if raw_value:
                    content_parts.append(raw_value)
                for key, val in metadata.items():
                    if isinstance(val, (str, int, float)) and val:
                        content_parts.append(f"{key}: {val}")

                content = " | ".join(content_parts)
                if not content or len(content.strip()) < 10:
                    continue

                source_type = _SOURCE_TYPE_MAP.get(source, SourceType.PRESS_RELEASE)
                signal_cat = _CATEGORY_MAP.get(category, SignalCategory.LEADERSHIP_SIGNALS)
                confidence = float(sig.get("confidence") or 0.7)

                evidence.append(CS2Evidence(
                    evidence_id=sig.get("id", ""),
                    company_id=company_id,
                    source_type=source_type,
                    signal_category=signal_cat,
                    content=content,
                    extracted_at=datetime.now(),
                    confidence=confidence,
                ))

        except (httpx.HTTPError, httpx.ConnectError) as e:
            logger.warning("cs2_signal_fetch_failed", company_id=company_id, error=str(e))

        return evidence

    # ── Helpers ──────────────────────────────────────────────────

    @staticmethod
    def _source_to_signal(source_type: SourceType) -> SignalCategory:
        """Map SourceType to primary SignalCategory (per CS4 PDF Task 8.0a)."""
        mapping = {
            SourceType.SEC_10K_ITEM_1: SignalCategory.DIGITAL_PRESENCE,
            SourceType.SEC_10K_ITEM_1A: SignalCategory.GOVERNANCE_SIGNALS,
            SourceType.SEC_10K_ITEM_7: SignalCategory.LEADERSHIP_SIGNALS,
            SourceType.JOB_POSTING_LINKEDIN: SignalCategory.TECHNOLOGY_HIRING,
            SourceType.JOB_POSTING_INDEED: SignalCategory.TECHNOLOGY_HIRING,
            SourceType.PATENT_USPTO: SignalCategory.INNOVATION_ACTIVITY,
            SourceType.GLASSDOOR_REVIEW: SignalCategory.CULTURE_SIGNALS,
            SourceType.BOARD_PROXY_DEF14A: SignalCategory.GOVERNANCE_SIGNALS,
            SourceType.PRESS_RELEASE: SignalCategory.LEADERSHIP_SIGNALS,
            SourceType.NEWS_ARTICLE: SignalCategory.LEADERSHIP_SIGNALS,
            SourceType.ANALYST_INTERVIEW: SignalCategory.LEADERSHIP_SIGNALS,
            SourceType.DD_DATA_ROOM: SignalCategory.DIGITAL_PRESENCE,
        }
        return mapping.get(source_type, SignalCategory.LEADERSHIP_SIGNALS)
