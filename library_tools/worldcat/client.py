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
    date: Optional[str] = None
    publisher: Optional[str] = None
    language: Optional[str] = None
    format: Optional[str] = None
    isbns: List[str] = Field(default_factory=list)
    held_by_institution: bool = False


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

    def _get_session(self) -> MetadataSession:
        """Create an authenticated WorldCat session."""
        token = WorldcatAccessToken(
            key=self.client_id, secret=self.client_secret, scopes="WorldCatMetadataAPI"
        )
        return MetadataSession(authorization=token)

    async def lookup_isbn(
        self,
        doi: Optional[str] = None,
        title: Optional[str] = None,
        author: Optional[str] = None,
        year: Optional[int] = None,
        isbn: Optional[str] = None,
    ) -> Optional[WorldCatBook]:
        """Look up a book in WorldCat and return bibliographic data.

        Args:
            doi: DOI of the book
            title: Book title
            author: Author name
            year: Publication year
            isbn: ISBN to verify/enrich

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
                            return self._parse_book(record)

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
                                    return self._parse_book(record)

                # Strategy 3: Search by title and author
                if title:
                    query_parts = []

                    title_clean = title.replace('"', "")
                    query_parts.append(f'ti:"{title_clean}"')

                    if author:
                        author_clean = author.replace('"', "")
                        query_parts.append(f'au:"{author_clean}"')

                    if year:
                        query_parts.append(f"yr:{year}")

                    query = " AND ".join(query_parts)

                    response = session.brief_bibs_search(q=query, itemType="book")

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
                                    return self._parse_book(record)

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
    ) -> List[WorldCatBook]:
        """Search WorldCat for books by keyword or subject.

        Args:
            query: Keyword or subject search
            year_from: Filter by start year
            year_to: Filter by end year
            language: Language filter (e.g., "eng" for English)
            limit: Maximum number of results (1-50)
            offset: Starting position for results (1-based, e.g., 1, 51, 101)

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

                            # Check if our institution holds it
                            held_by_us = False
                            try:
                                inst_check = session.summary_holdings_search(
                                    oclcNumber=oclc_num, heldBySymbol=self.institution_id
                                )
                                if inst_check.status_code == 200:
                                    inst_data = inst_check.json()
                                    held_by_us = inst_data.get("numberOfRecords", 0) > 0
                            except:
                                pass

                            book = self._parse_book(full_record)
                            book.held_by_institution = held_by_us
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

                return WorldCatFullBib(
                    oclc_number=oclc_number,
                    title=title,
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
                )

        except APIError:
            raise
        except Exception as e:
            raise APIError(f"Full bib lookup error: {str(e)}")

    def _parse_book(self, record: Dict[str, Any]) -> WorldCatBook:
        """Parse a book record from WorldCat API response."""
        return WorldCatBook(
            oclc_number=record.get("oclcNumber", ""),
            title=record.get("title", "Untitled"),
            creator=record.get("creator"),
            date=record.get("date"),
            publisher=record.get("publisher"),
            language=record.get("language"),
            format=record.get("generalFormat"),
            isbns=record.get("isbns", []),
            held_by_institution=False,
        )
