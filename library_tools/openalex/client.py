"""OpenAlex API client - pure API logic with no LLM dependencies."""

import pyalex
from pyalex import Works, Authors, Sources, Institutions
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from library_tools.common.config import get_settings
from library_tools.common.errors import APIError


class OpenAlexWork(BaseModel):
    """A single academic work from OpenAlex."""

    id: str
    title: str
    publication_year: Optional[int] = None
    doi: Optional[str] = None
    cited_by_count: int = 0
    is_open_access: bool = False
    authors: List[str] = Field(default_factory=list)
    journal: Optional[str] = None
    abstract: Optional[str] = None


class OpenAlexAuthor(BaseModel):
    """An author/researcher from OpenAlex."""

    id: str
    name: str
    works_count: int = 0
    cited_by_count: int = 0
    h_index: Optional[int] = None
    institution: Optional[str] = None


class OpenAlexJournal(BaseModel):
    """A journal/source from OpenAlex."""

    id: str
    name: str
    issn: Optional[str] = None
    publisher: Optional[str] = None
    works_count: int = 0
    is_open_access: bool = False


class OpenAlexClient:
    """Client for searching OpenAlex academic database.

    Works for any institution. Configuration loaded from environment.
    """

    def __init__(self, email: Optional[str] = None):
        """Initialize OpenAlex client.

        Args:
            email: Email for polite pool (or use OPENALEX_EMAIL env var)
        """
        settings = get_settings()
        pyalex.config.email = email or settings.openalex_email or "anonymous@example.com"

    async def search_works(
        self,
        query: str,
        limit: int = 10,
        page: int = 1,
        year_from: Optional[int] = None,
        open_access_only: bool = False,
    ) -> List[OpenAlexWork]:
        """Search for academic works/papers.

        Args:
            query: Search terms
            limit: Maximum results per page (1-100)
            page: Page number (1-based)
            year_from: Only papers from this year onwards
            open_access_only: Only open access papers

        Returns:
            List of OpenAlexWork objects
        """
        try:
            limit = min(max(limit, 1), 100)
            page = max(page, 1)

            works_query = Works().search(query)

            if year_from:
                works_query = works_query.filter(from_publication_date=f"{year_from}-01-01")

            if open_access_only:
                works_query = works_query.filter(is_oa=True)

            # Use paginate to support pagination
            results = []
            for page_results in works_query.paginate(per_page=limit, page=page):
                results = [self._parse_work(work) for work in page_results if work]
                break  # Only get the requested page

            return results

        except Exception as e:
            raise APIError(f"OpenAlex search failed: {str(e)}")

    async def search_authors(
        self,
        name: str,
        institution_id: Optional[str] = None,
        limit: int = 10,
        page: int = 1,
    ) -> List[OpenAlexAuthor]:
        """Search for authors/researchers.

        Args:
            name: Author name
            institution_id: Optional institution filter (e.g., "I121847817")
            limit: Maximum results per page (1-100)
            page: Page number (1-based)

        Returns:
            List of OpenAlexAuthor objects
        """
        try:
            limit = min(max(limit, 1), 100)
            page = max(page, 1)

            authors_query = Authors().search_filter(display_name=name)

            if institution_id:
                authors_query = authors_query.filter(
                    last_known_institutions={"id": institution_id}
                )

            # Use paginate to support pagination
            results = []
            for page_results in authors_query.paginate(per_page=limit, page=page):
                results = [self._parse_author(author) for author in page_results if author]
                break  # Only get the requested page

            return results

        except Exception as e:
            raise APIError(f"Author search failed: {str(e)}")

    async def get_author_works(
        self,
        author_id: str,
        limit: int = 10,
        page: int = 1,
    ) -> List[OpenAlexWork]:
        """Get works by a specific author.

        Args:
            author_id: OpenAlex author ID
            limit: Maximum results per page (1-200)
            page: Page number (1-based)

        Returns:
            List of OpenAlexWork objects
        """
        try:
            limit = min(max(limit, 1), 200)
            page = max(page, 1)

            if not author_id.startswith("https://"):
                author_id = f"https://openalex.org/{author_id}"

            works_query = Works().filter(author={"id": author_id}).sort(publication_date="desc")

            # Use paginate to support pagination
            results = []
            for page_results in works_query.paginate(per_page=limit, page=page):
                results = [self._parse_work(work) for work in page_results if work]
                break  # Only get the requested page

            return results

        except Exception as e:
            raise APIError(f"Failed to get author works: {str(e)}")

    async def search_journals(
        self,
        name: str,
        limit: int = 10,
        page: int = 1,
    ) -> List[OpenAlexJournal]:
        """Search for academic journals.

        Args:
            name: Journal name
            limit: Maximum results per page (1-100)
            page: Page number (1-based)

        Returns:
            List of OpenAlexJournal objects
        """
        try:
            limit = min(max(limit, 1), 100)
            page = max(page, 1)

            sources_query = Sources().search(name)

            # Use paginate to support pagination
            results = []
            for page_results in sources_query.paginate(per_page=limit, page=page):
                results = [self._parse_journal(source) for source in page_results if source]
                break  # Only get the requested page

            return results

        except Exception as e:
            raise APIError(f"Journal search failed: {str(e)}")

    def _parse_work(self, work: Dict[str, Any]) -> OpenAlexWork:
        """Parse a work from OpenAlex API response."""
        primary_location = work.get("primary_location") or {}
        source = primary_location.get("source") or {}
        open_access = work.get("open_access") or {}

        authors = [
            auth.get("author", {}).get("display_name")
            for auth in work.get("authorships", [])[:5]
            if auth and auth.get("author")
        ]

        # Get abstract
        abstract = work.get("abstract") or self._reconstruct_abstract(
            work.get("abstract_inverted_index")
        )

        return OpenAlexWork(
            id=work.get("id", ""),
            title=work.get("title", "Untitled"),
            publication_year=work.get("publication_year"),
            doi=work.get("doi"),
            cited_by_count=work.get("cited_by_count", 0),
            is_open_access=open_access.get("is_oa", False),
            authors=authors,
            journal=source.get("display_name"),
            abstract=abstract[:500] if abstract else None,  # Limit abstract length
        )

    def _parse_author(self, author: Dict[str, Any]) -> OpenAlexAuthor:
        """Parse an author from OpenAlex API response."""
        affiliations = author.get("affiliations", [])
        institution = None
        if affiliations:
            institution = affiliations[0].get("institution", {}).get("display_name")

        return OpenAlexAuthor(
            id=author.get("id", ""),
            name=author.get("display_name", ""),
            works_count=author.get("works_count", 0),
            cited_by_count=author.get("cited_by_count", 0),
            h_index=author.get("summary_stats", {}).get("h_index"),
            institution=institution,
        )

    def _parse_journal(self, source: Dict[str, Any]) -> OpenAlexJournal:
        """Parse a journal from OpenAlex API response."""
        return OpenAlexJournal(
            id=source.get("id", ""),
            name=source.get("display_name", ""),
            issn=source.get("issn_l"),
            publisher=source.get("host_organization_name"),
            works_count=source.get("works_count", 0),
            is_open_access=source.get("is_oa", False),
        )

    def _reconstruct_abstract(self, inverted_index: Optional[Dict]) -> Optional[str]:
        """Reconstruct abstract from OpenAlex inverted index."""
        if not inverted_index:
            return None

        try:
            words_with_positions = []
            for word, positions in inverted_index.items():
                for pos in positions:
                    words_with_positions.append((word, pos))

            words_with_positions.sort(key=lambda x: x[1])
            return " ".join([word for word, pos in words_with_positions])
        except:
            return None
