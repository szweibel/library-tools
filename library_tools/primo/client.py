"""Primo API client - pure API logic with no LLM dependencies."""

import httpx
from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from library_tools.common.config import get_settings
from library_tools.common.errors import APIError, ConfigurationError


class PrimoDocument(BaseModel):
    """A single document from Primo search results."""

    title: str
    permalink: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[str] = None
    format: Optional[str] = None
    publisher: Optional[str] = None
    issn: Optional[str] = None
    isbn: Optional[str] = None
    is_available: bool = False
    availability_status: Optional[str] = None


class PrimoSearchResult(BaseModel):
    """Results from a Primo catalog search."""

    total: int
    documents: List[PrimoDocument]
    query: str


class PrimoClient:
    """Client for searching Ex Libris Primo catalog.

    Works with any institution's Primo instance. Configuration is loaded
    from environment variables or can be provided directly.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        vid: Optional[str] = None,
        scope: Optional[str] = None,
    ):
        """Initialize Primo client.

        Args:
            api_key: Primo API key (or use PRIMO_API_KEY env var)
            base_url: Primo API base URL (or use PRIMO_BASE_URL env var)
            vid: View ID like "01INST:VIEW" (or use PRIMO_VID env var)
            scope: Search scope (or use PRIMO_SCOPE env var)

        Raises:
            ConfigurationError: If required settings are missing
        """
        settings = get_settings()

        self.api_key = api_key or settings.primo_api_key
        self.base_url = base_url or settings.primo_base_url
        self.vid = vid or settings.primo_vid
        self.scope = scope or settings.primo_scope

        # Validate required settings
        if not self.api_key:
            raise ConfigurationError(
                "PRIMO_API_KEY not configured",
                "Primo API key is required. Please set PRIMO_API_KEY in your environment.",
            )
        if not self.vid:
            raise ConfigurationError(
                "PRIMO_VID not configured",
                "Primo view ID is required. Please set PRIMO_VID in your environment.",
            )

    async def search(
        self,
        query: str,
        field: Literal["any", "title", "creator", "subject", "isbn", "issn"] = "any",
        operator: Literal["contains", "exact"] = "contains",
        limit: int = 10,
        start: int = 0,
        journals_only: bool = False,
    ) -> PrimoSearchResult:
        """Search the Primo catalog.

        Args:
            query: Search terms
            field: Which field to search (any, title, creator, subject, isbn, issn)
            operator: Match type (contains or exact)
            limit: Maximum results to return (1-100)
            start: Starting offset for pagination (0-based)
            journals_only: Search only journals/periodicals

        Returns:
            PrimoSearchResult with documents

        Raises:
            APIError: If search fails
            ValidationError: If parameters are invalid
        """
        if limit < 1 or limit > 100:
            limit = min(max(limit, 1), 100)

        if start < 0:
            start = 0

        # Build query string
        q = f"{field},{operator},{query}"

        params = {
            "q": q,
            "vid": self.vid,
            "scope": self.scope or "Everything",
            "apikey": self.api_key,
            "limit": limit,
            "offset": start,
            "sort": "rank",
        }

        # Journal-only search
        if journals_only:
            params["tab"] = "jsearch_slot"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(self.base_url, params=params)
                response.raise_for_status()
                data = response.json()

                # Parse results
                documents = []
                for doc_data in data.get("docs", []):
                    doc = self._parse_document(doc_data)
                    if doc:
                        documents.append(doc)

                total = data.get("info", {}).get("total", 0)

                return PrimoSearchResult(total=total, documents=documents, query=query)

            except httpx.HTTPStatusError as e:
                raise APIError(
                    f"Primo API error: {e.response.status_code}", status_code=e.response.status_code
                )
            except httpx.RequestError as e:
                raise APIError(
                    f"Network error contacting Primo: {str(e)}",
                    user_message="Could not connect to the library catalog. Please try again.",
                )
            except Exception as e:
                raise APIError(
                    f"Unexpected error: {str(e)}",
                    user_message="An error occurred while searching. Please try again.",
                )

    def _parse_document(self, doc_data: dict) -> Optional[PrimoDocument]:
        """Parse a single document from Primo API response."""
        try:
            pnx = doc_data.get("pnx", {})
            display = pnx.get("display", {})
            control = pnx.get("control", {})
            addata = pnx.get("addata", {})

            # Extract title
            title_list = display.get("title", [])
            title = title_list[0] if title_list else "Untitled"

            # Extract authors
            authors = display.get("contributor", [])[:5]  # Limit to 5

            # Extract publication year
            creation_date = display.get("creationdate", [])
            year = creation_date[0][:4] if creation_date else None

            # Extract format/type
            format_type = display.get("type", [])
            format_str = format_type[0] if format_type else None

            # Extract publisher
            publisher_list = display.get("publisher", [])
            publisher = publisher_list[0] if publisher_list else None

            # Extract ISSN/ISBN
            issn = addata.get("issn", [None])[0]
            isbn = display.get("identifier", [None])[0] if not issn else None

            # Build permalink
            record_id = control.get("recordid", [None])[0]
            context = doc_data.get("context")
            permalink = None
            if record_id and context and self.vid:
                # Extract host from base_url
                host = "primo.exlibrisgroup.com"  # Generic, can be customized
                if "cuny" in self.vid.lower():
                    host = "cuny-gc.primo.exlibrisgroup.com"
                permalink = f"https://{host}/discovery/fulldisplay?docid={record_id}&context={context}&vid={self.vid}"

            # Check availability
            delivery = doc_data.get("delivery", {})
            availability = delivery.get("availability", [])
            is_available = len(availability) > 0

            return PrimoDocument(
                title=title,
                permalink=permalink,
                authors=authors,
                publication_year=year,
                format=format_str,
                publisher=publisher,
                issn=issn,
                isbn=isbn,
                is_available=is_available,
            )

        except Exception:
            # Skip malformed documents
            return None
