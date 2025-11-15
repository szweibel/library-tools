"""LibGuides API client - pure API logic with no LLM dependencies."""

import httpx
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta

from library_tools.common.config import get_settings
from library_tools.common.errors import APIError, ConfigurationError


class LibGuidesDatabase(BaseModel):
    """A database/resource from LibGuides A-Z list."""

    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    alt_names: List[str] = Field(default_factory=list)
    subjects: List[str] = Field(default_factory=list)
    types: List[str] = Field(default_factory=list)
    vendor: Optional[str] = None
    requires_proxy: bool = False


class LibGuidesDatabaseSearchResult(BaseModel):
    """Results from a database search."""

    databases: List[LibGuidesDatabase]
    total: int


class LibGuidesPage(BaseModel):
    """A page/tab within a guide."""

    id: int
    name: str
    url: Optional[str] = None


class LibGuidesGuide(BaseModel):
    """A LibGuide from the system."""

    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    pages: List[LibGuidesPage] = Field(default_factory=list)
    owner_name: Optional[str] = None
    status_label: Optional[str] = None


class LibGuidesGuideSearchResult(BaseModel):
    """Results from a guide search."""

    guides: List[LibGuidesGuide]
    total: int


class LibGuidesClient:
    """Client for LibGuides API (SpringShare).

    Works with any institution's LibGuides instance. Configuration loaded
    from environment variables.
    """

    def __init__(
        self,
        site_id: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """Initialize LibGuides client.

        Args:
            site_id: LibGuides site ID (or use LIBGUIDES_SITE_ID env var)
            client_id: OAuth client ID (or use LIBGUIDES_CLIENT_ID env var)
            client_secret: OAuth client secret (or use LIBGUIDES_CLIENT_SECRET env var)
            base_url: API base URL (or use LIBGUIDES_BASE_URL env var, default: lgapi-us.libapps.com/1.2)

        Raises:
            ConfigurationError: If required settings are missing
        """
        settings = get_settings()

        self.site_id = site_id or settings.libguides_site_id
        self.client_id = client_id or settings.libguides_client_id
        self.client_secret = client_secret or settings.libguides_client_secret
        self.base_url = (
            base_url or settings.libguides_base_url or "https://lgapi-us.libapps.com/1.2"
        )

        # Validate required settings
        if not self.site_id:
            raise ConfigurationError(
                "LIBGUIDES_SITE_ID not configured",
                "LibGuides site ID is required. Please set LIBGUIDES_SITE_ID in your environment.",
            )
        if not self.client_id:
            raise ConfigurationError(
                "LIBGUIDES_CLIENT_ID not configured",
                "LibGuides client ID is required. Please set LIBGUIDES_CLIENT_ID in your environment.",
            )
        if not self.client_secret:
            raise ConfigurationError(
                "LIBGUIDES_CLIENT_SECRET not configured",
                "LibGuides client secret is required. Please set LIBGUIDES_CLIENT_SECRET in your environment.",
            )

        # Token cache
        self._token: Optional[str] = None
        self._token_expires: Optional[datetime] = None

    async def _get_access_token(self) -> str:
        """Get OAuth access token, using cached token if valid."""
        # Return cached token if still valid
        if self._token and self._token_expires:
            if datetime.now() < self._token_expires:
                return self._token

        # Get new token
        token_url = f"{self.base_url}/oauth/token"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    token_url,
                    data={
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "grant_type": "client_credentials",
                    },
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                response.raise_for_status()
                data = response.json()

                self._token = data["access_token"]
                # Cache token with 60 second buffer before expiration
                expires_in = data.get("expires_in", 3600)
                self._token_expires = datetime.now() + timedelta(seconds=expires_in - 60)

                return self._token

            except httpx.HTTPStatusError as e:
                raise APIError(
                    f"LibGuides OAuth failed: {e.response.status_code}",
                    user_message="Could not authenticate with LibGuides. Please check configuration.",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                raise APIError(
                    f"LibGuides OAuth error: {str(e)}",
                    user_message="Authentication error with LibGuides.",
                )

    async def search_databases(
        self,
        search: Optional[str] = None,
        subject_id: Optional[str] = None,
        type_id: Optional[str] = None,
        limit: int = 20,
    ) -> LibGuidesDatabaseSearchResult:
        """Search the A-Z database list.

        Args:
            search: Search term to filter by name/description (client-side filter)
            subject_id: Filter by subject ID
            type_id: Filter by database type ID
            limit: Maximum results to return (1-100)

        Returns:
            LibGuidesDatabaseSearchResult with databases

        Raises:
            APIError: If search fails
        """
        token = await self._get_access_token()

        params = {
            "site_id": self.site_id,
            "expand": "subjects,types,vendors",
        }

        if subject_id:
            params["subject_id"] = subject_id
        if type_id:
            params["type_id"] = type_id

        url = f"{self.base_url}/az"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                # Parse databases
                databases = []
                for db_data in data:
                    db = self._parse_database(db_data)
                    if db:
                        databases.append(db)

                # Client-side search filtering
                if search:
                    search_lower = search.lower()
                    databases = [
                        db
                        for db in databases
                        if (
                            search_lower in db.name.lower()
                            or (db.description and search_lower in db.description.lower())
                            or any(search_lower in alt.lower() for alt in db.alt_names)
                        )
                    ]

                # Apply limit
                databases = databases[:limit]

                return LibGuidesDatabaseSearchResult(databases=databases, total=len(databases))

            except httpx.HTTPStatusError as e:
                raise APIError(
                    f"LibGuides database search failed: {e.response.status_code}",
                    user_message="Could not search databases. Please try again.",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                raise APIError(
                    f"Database search error: {str(e)}",
                    user_message="An error occurred while searching databases.",
                )

    async def search_guides(
        self,
        search: Optional[str] = None,
        guide_id: Optional[int] = None,
        limit: int = 10,
        expand_pages: bool = True,
    ) -> LibGuidesGuideSearchResult:
        """Search LibGuides or get a specific guide.

        Args:
            search: Search terms (OR logic for multiple words)
            guide_id: Specific guide ID to fetch
            limit: Maximum results to return (1-100)
            expand_pages: Include page/tab information (default: True)

        Returns:
            LibGuidesGuideSearchResult with guides

        Raises:
            APIError: If search fails
        """
        token = await self._get_access_token()

        params = {
            "site_id": self.site_id,
            "status": "1,2",  # Published and unlisted (not private/draft)
        }

        if expand_pages:
            params["expand"] = "pages.boxes"

        if search and not guide_id:
            params["search_terms"] = search
            params["sort_by"] = "relevance"

        # Build URL
        if guide_id:
            url = f"{self.base_url}/guides/{guide_id}"
        else:
            url = f"{self.base_url}/guides"

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.get(
                    url,
                    params=params,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/json",
                    },
                )
                response.raise_for_status()
                data = response.json()

                # API returns single object for specific guide, array for search
                guides_data = data if isinstance(data, list) else [data]

                # Parse guides
                guides = []
                for guide_data in guides_data[:limit]:
                    guide = self._parse_guide(guide_data)
                    if guide:
                        guides.append(guide)

                return LibGuidesGuideSearchResult(guides=guides, total=len(guides))

            except httpx.HTTPStatusError as e:
                raise APIError(
                    f"LibGuides search failed: {e.response.status_code}",
                    user_message="Could not search guides. Please try again.",
                    status_code=e.response.status_code,
                )
            except Exception as e:
                raise APIError(
                    f"Guide search error: {str(e)}",
                    user_message="An error occurred while searching guides.",
                )

    def _parse_database(self, data: Dict[str, Any]) -> Optional[LibGuidesDatabase]:
        """Parse a database from API response."""
        try:
            subjects = [s.get("name", "") for s in data.get("subjects", [])]
            types = [t.get("name", "") for t in data.get("types", [])]
            vendor = data.get("vendor", {})
            vendor_name = vendor.get("name") if isinstance(vendor, dict) else None

            return LibGuidesDatabase(
                id=data.get("id", 0),
                name=data.get("name", ""),
                description=data.get("description"),
                url=data.get("url"),
                alt_names=data.get("alt_names", []),
                subjects=subjects,
                types=types,
                vendor=vendor_name,
                requires_proxy=data.get("enable_proxy", False),
            )
        except Exception:
            return None

    def _parse_guide(self, data: Dict[str, Any]) -> Optional[LibGuidesGuide]:
        """Parse a guide from API response."""
        try:
            # Parse pages
            pages = []
            for page_data in data.get("pages", []):
                pages.append(
                    LibGuidesPage(
                        id=page_data.get("id", 0),
                        name=page_data.get("name", ""),
                        url=page_data.get("url"),
                    )
                )

            # Get owner info
            owner = data.get("owner", {})
            owner_name = None
            if isinstance(owner, dict):
                first = owner.get("first_name", "")
                last = owner.get("last_name", "")
                owner_name = f"{first} {last}".strip() or None

            return LibGuidesGuide(
                id=data.get("id", 0),
                name=data.get("name", ""),
                description=data.get("description"),
                url=data.get("friendly_url") or data.get("url"),
                pages=pages,
                owner_name=owner_name,
                status_label=data.get("status_label"),
            )
        except Exception:
            return None
