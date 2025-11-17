"""WorldCat API client - pure API logic with no LLM dependencies."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

try:
    from bookops_worldcat import MetadataSession, WorldcatAccessToken
    import requests
except ImportError:
    raise ImportError(
        "bookops-worldcat is required for WorldCat tools. "
        "Install with: pip install bookops-worldcat"
    )

from library_tools.common.config import get_settings
from library_tools.common.errors import APIError, ConfigurationError


class WorldCatBook(BaseModel):
    """A single book record from WorldCat."""

    oclc_number: str
    title: str
    creator: Optional[str] = None
    contributors: List[str] = Field(default_factory=list)
    date: Optional[str] = None
    machine_readable_date: Optional[str] = None
    publisher: Optional[str] = None
    publication_place: Optional[str] = None
    edition: Optional[str] = None
    series: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None
    specific_format: Optional[str] = None
    isbns: List[str] = Field(default_factory=list)
    holding_institutions: List[str] = Field(default_factory=list)
    total_holdings: Optional[int] = None
    merged_oclc_numbers: List[str] = Field(default_factory=list)


class WorldCatClassification(BaseModel):
    """LC and Dewey classification data."""

    oclc_number: str
    lc_classification: Optional[str] = None
    lc_all: List[str] = Field(default_factory=list)
    dewey: Optional[str] = None
    dewey_all: List[str] = Field(default_factory=list)


class WorldCatFullBib(BaseModel):
    """Complete bibliographic record with subjects and classification."""

    oclc_number: str
    title: Optional[str] = None
    creator: Optional[str] = None
    contributors: List[Dict[str, str]] = Field(default_factory=list)
    isbns: List[str] = Field(default_factory=list)
    edition: Optional[str] = None
    series: Optional[str] = None
    language: Optional[str] = None
    lc_classification: Optional[str] = None
    dewey_classification: Optional[str] = None
    subjects: List[Dict[str, Any]] = Field(default_factory=list)
    genres: List[str] = Field(default_factory=list)
    general_format: Optional[str] = None
    specific_format: Optional[str] = None
    physical_description: Optional[str] = None
    publisher: Optional[str] = None
    publication_place: Optional[str] = None
    publication_date: Optional[str] = None
    publication_year: Optional[str] = None
    holding_institutions: List[str] = Field(default_factory=list)
    total_holdings: Optional[int] = None


class WorldCatClient:
    """Client for searching OCLC WorldCat bibliographic database.

    Works for any institution with OCLC credentials. Configuration loaded from environment.
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        institution_id: Optional[str] = None,
    ):
        """Initialize WorldCat client.

        Args:
            client_id: OCLC API client ID (or use OCLC_CLIENT_ID env var)
            client_secret: OCLC API client secret (or use OCLC_CLIENT_SECRET env var)
            institution_id: Institution symbol (or use OCLC_INSTITUTION_ID env var)
        """
        settings = get_settings()

        # Validate credentials
        self.client_id = client_id or settings.oclc_client_id
        self.client_secret = client_secret or settings.oclc_client_secret
        self.institution_id = institution_id or settings.oclc_institution_id or "CNY"

        if not self.client_id or not self.client_secret:
            raise ConfigurationError(
                "OCLC credentials not found. Set OCLC_CLIENT_ID and OCLC_CLIENT_SECRET"
            )

    def _get_session(self, scopes: str = "WorldCatMetadataAPI") -> MetadataSession:
        """Create an authenticated WorldCat session.

        Args:
            scopes: OAuth scopes to request. Default is "WorldCatMetadataAPI"
        """
        token = WorldcatAccessToken(
            key=self.client_id, secret=self.client_secret, scopes=scopes
        )
        return MetadataSession(authorization=token)

    async def lookup_isbn(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        year: Optional[int] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        isbn: Optional[str] = None,
        fetch_holdings: bool = False,
        holdings_limit: Optional[int] = None,
    ) -> Optional[WorldCatBook]:
        """Look up a book in WorldCat and return bibliographic data.

        Args:
            doi: DOI of the book
            title: Book title
            author: Author name
            year: Publication year (exact match)
            year_from: Filter by start year
            year_to: Filter by end year
            isbn: ISBN to verify/enrich
            fetch_holdings: If True, fetch complete holdings data (slower, makes additional API call)
            holdings_limit: Maximum number of holding institutions to fetch. None = fetch all.

        Returns:
            WorldCatBook object or None if not found
        """
        try:
            with self._get_session() as session:
                response = None

                # Strategy 1: Search by ISBN if provided
                if isbn:
                    isbn_clean = isbn.replace("-", "").replace(" ", "")
                    response = session.summary_holdings_search(isbn=isbn_clean)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("numberOfRecords", 0) > 0:
                            record = data["briefRecords"][0]
                            book = self._parse_book(record)
                            if fetch_holdings:
                                book = await self._populate_holdings(book, limit=holdings_limit)
                            return book

                # Strategy 2: Search by DOI
                if doi:
                    doi_clean = doi.replace("https://doi.org/", "").replace(
                        "http://doi.org/", ""
                    )
                    doi_escaped = doi_clean.replace("/", "\\/")
                    query = f"bn:{doi_escaped}"

                    response = session.brief_bibs_search(q=query)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("numberOfRecords", 0) > 0:
                            brief_record = data["briefRecords"][0]
                            oclc_num = brief_record.get("oclcNumber")

                            # Get full record with ISBNs
                            holdings_response = session.summary_holdings_search(
                                oclcNumber=oclc_num
                            )
                            if holdings_response.status_code == 200:
                                holdings_data = holdings_response.json()
                                if holdings_data.get("numberOfRecords", 0) > 0:
                                    record = holdings_data["briefRecords"][0]
                                    book = self._parse_book(record)
                                    if fetch_holdings:
                                        book = await self._populate_holdings(book)
                                    return book

                # Strategy 3: Search by title and author
                if title:
                    query_parts = []

                    title_clean = title.replace('"', "")
                    query_parts.append(f'ti:"{title_clean}"')

                    if author:
                        author_clean = author.replace('"', "")
                        query_parts.append(f'au:"{author_clean}"')

                    # Handle year filtering
                    search_params = {"itemType": "book"}
                    if year:
                        # Exact year match
                        query_parts.append(f"yr:{year}")
                    elif year_from or year_to:
                        # Year range using datePublished parameter
                        if year_from and year_to:
                            search_params["datePublished"] = f"{year_from}-{year_to}"
                        elif year_from:
                            search_params["datePublished"] = f"{year_from}-"
                        elif year_to:
                            search_params["datePublished"] = f"-{year_to}"

                    query = " AND ".join(query_parts)

                    response = session.brief_bibs_search(q=query, **search_params)

                    if response.status_code == 200:
                        data = response.json()
                        if data.get("numberOfRecords", 0) > 0:
                            brief_record = data["briefRecords"][0]
                            oclc_num = brief_record.get("oclcNumber")

                            # Get full record with ISBNs
                            holdings_response = session.summary_holdings_search(
                                oclcNumber=oclc_num
                            )
                            if holdings_response.status_code == 200:
                                holdings_data = holdings_response.json()
                                if holdings_data.get("numberOfRecords", 0) > 0:
                                    record = holdings_data["briefRecords"][0]
                                    book = self._parse_book(record)
                                    if fetch_holdings:
                                        book = await self._populate_holdings(book)
                                    return book

                return None

        except Exception as e:
            raise APIError(f"WorldCat lookup error: {str(e)}")

    async def search_books(
        self,
        query: str,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        language: Optional[str] = None,
        limit: int = 25,
        offset: int = 1,
        fetch_holdings: bool = False,
        holdings_limit: Optional[int] = None,
    ) -> List[WorldCatBook]:
        """Search WorldCat for books by keyword or subject.

        Args:
            query: Keyword or subject search
            year_from: Filter by start year
            year_to: Filter by end year
            language: Language filter (e.g., "eng" for English)
            limit: Maximum number of results (1-50)
            offset: Starting position for results (1-based, e.g., 1, 51, 101)
            fetch_holdings: If True, fetch complete holdings data for each result (slower)
            holdings_limit: Maximum number of holding institutions to fetch per book. None = fetch all.

        Returns:
            List of WorldCatBook objects
        """
        try:
            limit = min(max(limit, 1), 50)
            offset = max(offset, 1)  # Ensure offset is at least 1

            with self._get_session() as session:
                # Build search query
                search_params = {
                    "q": query,
                    "itemType": "book",
                    "limit": limit,
                    "offset": offset,
                }

                # Add filters
                if year_from and year_to:
                    search_params["datePublished"] = f"{year_from}-{year_to}"
                elif year_from:
                    search_params["datePublished"] = f"{year_from}-"
                elif year_to:
                    search_params["datePublished"] = f"-{year_to}"

                if language:
                    search_params["inLanguage"] = language

                # Perform search
                response = session.brief_bibs_search(**search_params)

                if response.status_code != 200:
                    raise APIError(
                        f"WorldCat search failed",
                        status_code=response.status_code,
                    )

                data = response.json()
                num_records = data.get("numberOfRecords", 0)

                if num_records == 0:
                    return []

                # Get detailed records with ISBNs
                books = []
                brief_records = data.get("briefRecords", [])[:limit]

                for brief_record in brief_records:
                    oclc_num = brief_record.get("oclcNumber")

                    # Get full record with ISBNs
                    holdings_response = session.summary_holdings_search(
                        oclcNumber=oclc_num
                    )

                    if holdings_response.status_code == 200:
                        holdings_data = holdings_response.json()
                        if holdings_data.get("numberOfRecords", 0) > 0:
                            full_record = holdings_data["briefRecords"][0]

                            book = self._parse_book(full_record)
                            if fetch_holdings:
                                book = await self._populate_holdings(book, limit=holdings_limit)
                            books.append(book)

                return books

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"WorldCat search error: {str(e)}")

    async def get_classification(self, oclc_number: str) -> WorldCatClassification:
        """Get LC and Dewey classification for an OCLC number.

        Args:
            oclc_number: OCLC number (e.g., "742206236")

        Returns:
            WorldCatClassification object
        """
        try:
            with self._get_session() as session:
                response = session.bib_get_classification(oclcNumber=oclc_number)

                if response.status_code != 200:
                    raise APIError(
                        f"Classification lookup failed",
                        status_code=response.status_code,
                    )

                data = response.json()

                # Extract most popular classifications
                lc_class = data.get("lc", {}).get("mostPopular", [])
                dewey_class = data.get("dewey", {}).get("mostPopular", [])

                return WorldCatClassification(
                    oclc_number=oclc_number,
                    lc_classification=lc_class[0] if lc_class else None,
                    lc_all=lc_class,
                    dewey=dewey_class[0] if dewey_class else None,
                    dewey_all=dewey_class,
                )

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Classification lookup error: {str(e)}")

    async def get_full_bib(self, oclc_number: str) -> WorldCatFullBib:
        """Get full bibliographic record with subjects, classification, genres, etc.

        Args:
            oclc_number: OCLC number (e.g., "742206236")

        Returns:
            WorldCatFullBib object
        """
        try:
            with self._get_session() as session:
                # Get the access token
                token_str = session.authorization.token_str

                # Call the search/bibs endpoint for full metadata
                url = f"https://metadata.api.oclc.org/worldcat/search/bibs/{oclc_number}"
                headers = {"Authorization": f"Bearer {token_str}", "Accept": "application/json"}

                response = requests.get(url, headers=headers)

                if response.status_code != 200:
                    raise APIError(
                        f"Full bib lookup failed",
                        status_code=response.status_code,
                    )

                data = response.json()

                # Extract subjects
                subjects = []
                for subj in data.get("subjects", []):
                    subjects.append(
                        {
                            "name": subj.get("subjectName", {}).get("text"),
                            "type": subj.get("subjectType"),
                            "vocabulary": subj.get("vocabulary"),
                        }
                    )

                # Extract genres
                genres = data.get("description", {}).get("genres", [])

                # Extract classification
                classification = data.get("classification", {})
                lc_class = classification.get("lc")
                dewey_class = classification.get("dewey")

                # Extract language
                language_info = data.get("language", {})
                item_language = language_info.get("itemLanguage")

                # Extract format
                format_info = data.get("format", {})
                general_format = format_info.get("generalFormat")
                specific_format = format_info.get("specificFormat")

                # Extract physical description
                description_info = data.get("description", {})
                physical_desc = description_info.get("physicalDescription")

                # Extract publication info
                publishers = data.get("publishers", [])
                pub_place = publishers[0].get("publicationPlace") if publishers else None
                pub_name = (
                    publishers[0].get("publisherName", {}).get("text") if publishers else None
                )

                # Extract date
                date_info = data.get("date", {})
                pub_date = date_info.get("publicationDate")
                machine_date = date_info.get("machineReadableDate")

                # Extract title
                title_data = data.get("title", {})
                main_titles = title_data.get("mainTitles", [])
                title = main_titles[0].get("text") if main_titles else None

                # Extract creator/contributors
                creator = None
                contributors = []
                creator_info = data.get("contributor", {})
                creators_list = creator_info.get("creators", [])
                if creators_list:
                    first = creators_list[0]
                    creator = first.get("name", {}).get("text")
                    # Build contributors list with roles
                    for c in creators_list:
                        name = c.get("name", {}).get("text")
                        role = c.get("relatorTerm", {}).get("text", "Creator")
                        if name:
                            contributors.append({"name": name, "role": role})

                # Extract ISBNs
                isbns = []
                identifiers = data.get("identifier", {})
                isbn_list = identifiers.get("isbns", [])
                for isbn_entry in isbn_list:
                    if isinstance(isbn_entry, dict):
                        isbn_val = isbn_entry.get("isbn")
                        if isbn_val:
                            isbns.append(isbn_val)
                    elif isinstance(isbn_entry, str):
                        isbns.append(isbn_entry)

                # Extract edition
                edition_info = data.get("edition", {})
                edition = edition_info.get("editionStatement") if isinstance(edition_info, dict) else None

                # Extract series
                series_info = data.get("series", [])
                series = None
                if series_info and len(series_info) > 0:
                    series_name = series_info[0].get("seriesName", {}).get("text")
                    series_volume = series_info[0].get("seriesVolume")
                    if series_name:
                        series = f"{series_name}"
                        if series_volume:
                            series += f", {series_volume}"

                return WorldCatFullBib(
                    oclc_number=oclc_number,
                    title=title,
                    creator=creator,
                    contributors=contributors,
                    isbns=isbns,
                    edition=edition,
                    series=series,
                    language=item_language,
                    lc_classification=lc_class,
                    dewey_classification=dewey_class,
                    subjects=subjects,
                    genres=genres,
                    general_format=general_format,
                    specific_format=specific_format,
                    physical_description=physical_desc,
                    publisher=pub_name,
                    publication_place=pub_place,
                    publication_date=pub_date,
                    publication_year=machine_date,
                    holding_institutions=[],  # Would require separate holdings API call
                    total_holdings=None,  # Would require separate holdings API call
                )

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Full bib lookup error: {str(e)}")

    async def fetch_holdings(self, oclc_number: str, limit: Optional[int] = None) -> Dict[str, Any]:
        """Fetch all institutions holding an item from WorldCat Discovery API.

        Args:
            oclc_number: OCLC number to check
            limit: Maximum number of institutions to fetch. None = fetch all (may be thousands)

        Returns:
            Dictionary with:
                - institution_symbols: List of OCLC institution codes
                - total_holdings: Total number of libraries holding the item
                - institutions: List of dicts with detailed institution info
        """
        try:
            # Get OAuth token with Discovery API scopes
            token = WorldcatAccessToken(
                key=self.client_id,
                secret=self.client_secret,
                scopes="wcapi:view_holdings wcapi:view_institution_holdings"
            )

            # Call Discovery API endpoint
            url = "https://americas.discovery.api.oclc.org/worldcat/search/v2/bibs-holdings"
            headers = {
                "Authorization": f"Bearer {token.token_str}",
                "Accept": "application/json"
            }

            # Build params
            params = {
                "oclcNumber": oclc_number,
                "limit": 50  # Max allowed by API
            }

            all_institutions = []
            total_holdings_count = 0
            offset = 1  # API requires offset >= 1

            while True:
                if offset > 1:  # Only add offset if not first page
                    params["offset"] = offset

                response = requests.get(url, headers=headers, params=params)

                if response.status_code != 200:
                    raise APIError(
                        f"Holdings API request failed",
                        status_code=response.status_code,
                    )

                data = response.json()

                # Extract institution symbols from briefHoldings
                if data.get("numberOfRecords", 0) > 0:
                    brief_records = data.get("briefRecords", [])
                    for record in brief_records:
                        institution_holding = record.get("institutionHolding", {})
                        total_holdings_count = institution_holding.get("totalHoldingCount", 0)
                        brief_holdings = institution_holding.get("briefHoldings", [])

                        for holding in brief_holdings:
                            all_institutions.append({
                                "symbol": holding.get("oclcSymbol"),
                                "name": holding.get("institutionName"),
                                "country": holding.get("country"),
                                "state": holding.get("state"),
                                "type": holding.get("institutionType")
                            })

                # Check if we should continue paginating
                if len(all_institutions) >= total_holdings_count:
                    break  # Got all holdings

                if brief_records and len(brief_records[0].get("institutionHolding", {}).get("briefHoldings", [])) < 50:
                    break  # Last page (fewer than limit)

                # Check user-specified limit
                if limit and len(all_institutions) >= limit:
                    break  # Reached user-specified limit

                offset += 50

            # Extract just the symbols for easy use
            symbols = [inst["symbol"] for inst in all_institutions if inst.get("symbol")]

            return {
                "institution_symbols": symbols,
                "total_holdings": total_holdings_count,
                "institutions": all_institutions,
            }

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Holdings lookup error: {str(e)}")

    async def _populate_holdings(self, book: WorldCatBook, limit: Optional[int] = None) -> WorldCatBook:
        """Populate holdings data for a book.

        Args:
            book: WorldCatBook to populate holdings for
            limit: Maximum number of institutions to fetch

        Returns:
            The same book with holdings data populated
        """
        holdings_data = await self.fetch_holdings(book.oclc_number, limit=limit)
        book.holding_institutions = holdings_data.get("institution_symbols", [])
        book.total_holdings = holdings_data.get("total_holdings")
        return book

    def _parse_book(self, record: Dict[str, Any]) -> WorldCatBook:
        """Parse a book record from WorldCat API response."""
        # Extract contributors - may be a single string or list
        contributors = []
        if "contributors" in record:
            contrib = record["contributors"]
            if isinstance(contrib, list):
                contributors = contrib
            elif isinstance(contrib, str):
                contributors = [contrib]

        # Extract merged OCLC numbers
        merged_oclc = record.get("mergedOclcNumbers", [])
        if not isinstance(merged_oclc, list):
            merged_oclc = []

        return WorldCatBook(
            oclc_number=record.get("oclcNumber", ""),
            title=record.get("title", "Untitled"),
            creator=record.get("creator"),
            contributors=contributors,
            date=record.get("date"),
            machine_readable_date=record.get("machineReadableDate"),
            publisher=record.get("publisher"),
            publication_place=record.get("publicationPlace"),
            edition=record.get("edition"),
            series=record.get("series"),
            language=record.get("language"),
            format=record.get("generalFormat"),
            specific_format=record.get("specificFormat"),
            isbns=record.get("isbns", []),
            holding_institutions=[],  # Populated by _populate_holdings if requested
            total_holdings=None,  # Populated by _populate_holdings if requested
            merged_oclc_numbers=merged_oclc,
        )
