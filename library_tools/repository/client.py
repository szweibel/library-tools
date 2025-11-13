"""bePress/Digital Commons repository client - pure API logic with no LLM dependencies."""

import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

from library_tools.common.config import get_settings
from library_tools.common.errors import APIError, ConfigurationError


class RepositoryWork(BaseModel):
    """A work from an institutional repository."""

    title: str
    authors: List[str] = Field(default_factory=list)
    publication_year: Optional[str] = None
    document_type: Optional[str] = None
    url: Optional[str] = None
    fulltext_url: Optional[str] = None
    collection: Optional[str] = None
    collection_name: Optional[str] = None
    abstract: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    publication_title: Optional[str] = None
    advisor: Optional[str] = None


class RepositorySearchResult(BaseModel):
    """Results from a repository search."""

    works: List[RepositoryWork]
    total: int
    query: Optional[str] = None


class RepositoryClient:
    """Client for bePress/Digital Commons institutional repository.

    Works with any bePress repository instance. Configuration loaded
    from environment variables.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        """Initialize repository client.

        Args:
            base_url: Repository API base URL (or use REPOSITORY_BASE_URL env var)
                     Example: https://content-out.bepress.com/v2/institution.edu
            api_key: API security token (or use REPOSITORY_API_KEY env var)

        Raises:
            ConfigurationError: If required settings are missing
        """
        settings = get_settings()

        self.base_url = base_url or settings.repository_base_url
        self.api_key = api_key or settings.repository_api_key

        # Validate required settings
        if not self.base_url:
            raise ConfigurationError(
                "REPOSITORY_BASE_URL not configured",
                "Repository base URL is required. Please set REPOSITORY_BASE_URL in your environment."
            )
        if not self.api_key:
            raise ConfigurationError(
                "REPOSITORY_API_KEY not configured",
                "Repository API key is required. Please set REPOSITORY_API_KEY in your environment."
            )

    async def search(
        self,
        query: Optional[str] = None,
        collection: Optional[str] = None,
        year: Optional[str] = None,
        limit: int = 10,
        start: int = 0,
    ) -> RepositorySearchResult:
        """Search the institutional repository.

        Args:
            query: Keywords for title/abstract search
            collection: Collection code to filter by
            year: Publication year to filter by
            limit: Maximum results to return (1-1000)
            start: Result offset for pagination

        Returns:
            RepositorySearchResult with works

        Raises:
            APIError: If search fails
        """
        limit = min(max(limit, 1), 1000)

        params = {
            "limit": limit,
            "start": start,
            "fields": "title,author,publication_year,publication_date,document_type,url,fulltext_url,parent_link,abstract,keywords,subject,publication_title,advisor,committee_member",
        }

        if query:
            params["q"] = query

        if collection:
            # Build collection URL - this is institution-specific
            # Extract domain from base_url
            domain = self.base_url.split("/")[-1]
            collection_url = f"http://{domain}/{collection}"
            params["parent_link"] = collection_url

        if year and year.isdigit():
            params["publication_year"] = year

        url = f"{self.base_url}/query"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": self.api_key},
                )
                response.raise_for_status()
                data = response.json()

                # Parse results
                works = []
                for work_data in data.get("results", []):
                    work = self._parse_work(work_data)
                    if work:
                        works.append(work)

                total = data.get("query_meta", {}).get("total_hits", 0)

                return RepositorySearchResult(
                    works=works,
                    total=total,
                    query=query
                )

            except httpx.HTTPStatusError as e:
                raise APIError(
                    f"Repository search failed: {e.response.status_code}",
                    user_message="Could not search repository. Please try again.",
                    status_code=e.response.status_code
                )
            except httpx.RequestError as e:
                raise APIError(
                    f"Network error contacting repository: {str(e)}",
                    user_message="Could not connect to repository. Please try again."
                )
            except Exception as e:
                raise APIError(
                    f"Repository error: {str(e)}",
                    user_message="An error occurred while searching the repository."
                )

    async def get_latest_works(
        self,
        collection: Optional[str] = None,
        limit: int = 10,
        start: int = 0,
    ) -> RepositorySearchResult:
        """Get the most recently added works.

        Args:
            collection: Optional collection code to filter by
            limit: Maximum results to return (1-1000)
            start: Result offset for pagination

        Returns:
            RepositorySearchResult with latest works

        Raises:
            APIError: If request fails
        """
        # Repository API returns most recent first by default when no query is provided
        return await self.search(
            query=None,
            collection=collection,
            limit=limit,
            start=start,
        )

    async def get_details(
        self,
        item_url: str,
    ) -> Optional[RepositoryWork]:
        """Get detailed information for a specific work by URL.

        Args:
            item_url: Full URL of the work

        Returns:
            RepositoryWork with full details, or None if not found

        Raises:
            APIError: If request fails
        """
        params = {
            "q": f'url:"{item_url}"',
            "select_fields": "all",
            "limit": 1,
        }

        url = f"{self.base_url}/query"

        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers={"Authorization": self.api_key},
                )
                response.raise_for_status()
                data = response.json()

                results = data.get("results", [])
                if not results:
                    return None

                return self._parse_work(results[0], detailed=True)

            except httpx.HTTPStatusError as e:
                raise APIError(
                    f"Repository get details failed: {e.response.status_code}",
                    user_message="Could not retrieve work details.",
                    status_code=e.response.status_code
                )
            except Exception as e:
                raise APIError(
                    f"Repository error: {str(e)}",
                    user_message="An error occurred while retrieving work details."
                )

    def _parse_work(self, data: Dict[str, Any], detailed: bool = False) -> Optional[RepositoryWork]:
        """Parse a work from repository API response."""
        try:
            # Parse authors
            authors_data = data.get("author", [])
            if isinstance(authors_data, str):
                authors = [authors_data]
            else:
                authors = authors_data if isinstance(authors_data, list) else []

            # Parse year
            year = data.get("publication_year") or data.get("publication_date", "")
            if isinstance(year, str) and len(year) > 4:
                year = year[:4]

            # Parse document type
            doc_type_value = data.get("document_type")
            if isinstance(doc_type_value, list) and doc_type_value:
                doc_type = doc_type_value[0]
            elif isinstance(doc_type_value, str):
                doc_type = doc_type_value
            else:
                doc_type = None

            # Parse collection
            parent_link = data.get("parent_link", "")
            collection = None
            collection_name = None
            if parent_link:
                collection = parent_link.split("/")[-1]
                collection_name = collection.replace("_", " ").title()

            # Parse keywords
            keywords_data = data.get("keywords") or data.get("subject", [])
            if isinstance(keywords_data, str):
                keywords = [k.strip() for k in keywords_data.split(",")]
            else:
                keywords = keywords_data if isinstance(keywords_data, list) else []

            # Abstract (only for detailed view)
            abstract = None
            if detailed:
                abstract = data.get("abstract")
                if abstract:
                    # Strip HTML tags
                    import re
                    abstract = re.sub('<[^<]+?>', '', abstract).strip()

            # Advisor
            advisor = data.get("advisor") or data.get("committee_member")

            return RepositoryWork(
                title=data.get("title", "Untitled"),
                authors=authors,
                publication_year=year,
                document_type=doc_type,
                url=data.get("url"),
                fulltext_url=data.get("fulltext_url"),
                collection=collection,
                collection_name=collection_name,
                abstract=abstract,
                keywords=keywords,
                publication_title=data.get("publication_title"),
                advisor=advisor,
            )
        except Exception:
            return None
