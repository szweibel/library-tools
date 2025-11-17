"""WorldCat search tools - framework agnostic."""

from typing import Optional

from library_tools.worldcat.client import WorldCatClient
from library_tools.common.errors import format_error_for_llm


def _format_book_for_llm(book, query_info: str = "") -> str:
    """Format a single book in LLM-friendly format."""
    lines = []

    # Title and edition
    title_str = book.title
    if book.edition:
        title_str += f". {book.edition}"
    lines.append(f"Title: {title_str}")

    # Author(s)
    if book.creator:
        lines.append(f"Author: {book.creator}")
    if book.contributors:
        # Show additional contributors beyond the primary creator
        other_contributors = [c for c in book.contributors if c != book.creator]
        if other_contributors:
            lines.append(f"Contributors: {', '.join(other_contributors)}")

    # Publication information
    pub_parts = []
    if book.publication_place:
        pub_parts.append(book.publication_place)
    if book.publisher:
        pub_parts.append(book.publisher)
    if book.date:
        pub_parts.append(book.date)
    if pub_parts:
        lines.append(f"Publication: {': '.join(pub_parts[:1]) + ', '.join(pub_parts[1:]) if len(pub_parts) > 1 else pub_parts[0]}")

    # Series
    if book.series:
        lines.append(f"Series: {book.series}")

    # ISBNs (most important for this tool)
    if book.isbns:
        lines.append(f"ISBNs: {', '.join(book.isbns)}")
    else:
        lines.append("ISBNs: None found")

    # Format and language
    if book.specific_format:
        lines.append(f"Format: {book.specific_format}")
    elif book.format:
        lines.append(f"Format: {book.format}")

    if book.language:
        lines.append(f"Language: {book.language}")

    # OCLC number for follow-up queries
    lines.append(f"OCLC Number: {book.oclc_number}")

    # Holdings info
    if book.total_holdings:
        lines.append(f"Total Holdings: {book.total_holdings} libraries worldwide")
    if book.holding_institutions:
        institutions = ", ".join(book.holding_institutions)
        lines.append(f"Available at: {institutions}")

    return "\n".join(lines)


def _format_books_for_llm(books, query: str) -> str:
    """Format multiple books in LLM-friendly format."""
    if not books:
        return f"No books found for '{query}'. Try broader search terms or check spelling."

    lines = [f"Found {len(books)} books for '{query}':\n"]

    for i, book in enumerate(books, 1):
        # Title with edition
        title_str = book.title
        if book.edition:
            title_str += f". {book.edition}"
        lines.append(f"{i}. {title_str}")

        # Author and contributors
        if book.creator:
            lines.append(f"   Author: {book.creator}")
        if book.contributors and len(book.contributors) > 1:
            other_contributors = [c for c in book.contributors if c != book.creator]
            if other_contributors:
                lines.append(f"   Contributors: {', '.join(other_contributors[:3])}")

        # Publication info
        pub_parts = []
        if book.publication_place:
            pub_parts.append(book.publication_place)
        if book.publisher:
            pub_parts.append(book.publisher)
        if book.date:
            pub_parts.append(book.date)
        if pub_parts:
            lines.append(f"   Publication: {', '.join(pub_parts)}")

        # Series
        if book.series:
            lines.append(f"   Series: {book.series}")

        # ISBNs
        if book.isbns:
            lines.append(f"   ISBNs: {', '.join(book.isbns)}")

        # Key info
        info_parts = []
        if book.specific_format:
            info_parts.append(f"Format: {book.specific_format}")
        elif book.format:
            info_parts.append(f"Format: {book.format}")
        if book.language:
            info_parts.append(f"Language: {book.language}")
        info_parts.append(f"OCLC: {book.oclc_number}")

        if book.total_holdings:
            info_parts.append(f"{book.total_holdings} libraries")
        if book.holding_institutions:
            institutions = ", ".join(book.holding_institutions)
            info_parts.append(f"At: {institutions}")

        lines.append(f"   {' | '.join(info_parts)}")
        lines.append("")  # Blank line

    return "\n".join(lines)


async def lookup_worldcat_isbn(
    doi: Optional[str] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    year: Optional[int] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    isbn: Optional[str] = None,
    fetch_holdings: bool = False,
    holdings_limit: Optional[int] = None,
) -> str:
    """Look up a book in WorldCat and return ISBN(s) and bibliographic data.

    Use this tool to find ISBNs for books when you have incomplete or uncertain
    bibliographic information. WorldCat provides authoritative ISBN data from OCLC.

    Args:
        doi: DOI of the book (e.g., "10.1234/example")
        title: Book title
        author: Author name
        year: Publication year (exact match)
        year_from: Filter by start year (e.g., 2015 for books from 2015 onwards)
        year_to: Filter by end year (e.g., 2023 for books up to 2023)
        isbn: ISBN to verify/enrich with all variants (ISBN-10, ISBN-13, etc.)
        fetch_holdings: If True, fetch complete holdings data (which institutions hold the item). Slower but provides comprehensive availability information.
        holdings_limit: Maximum number of holding institutions to fetch. None = fetch all (may be thousands).

    Returns:
        Formatted string with book details including all ISBNs and OCLC number

    When to use:
    - User needs ISBN for a book
    - User has DOI and needs ISBN
    - User wants to verify an ISBN matches expected metadata
    - User needs all ISBN variants for a book (ISBN-10, ISBN-13)
    - LLM generated an incorrect ISBN and needs authoritative data
    - User wants to know which libraries hold the item (use fetch_holdings=True)

    Search strategies (tried in order):
    1. If ISBN provided: Look up directly and return all variants
    2. If DOI provided: Search by DOI
    3. If title provided: Search by title (optionally with author and year/year range)

    Note: Use either 'year' for exact match OR 'year_from'/'year_to' for range, not both.

    Returns OCLC number which can be used with other WorldCat tools for
    classification, subjects, and complete bibliographic records.
    """
    try:
        client = WorldCatClient()
        book = await client.lookup_isbn(
            doi=doi,
            title=title,
            author=author,
            year=year,
            year_from=year_from,
            year_to=year_to,
            isbn=isbn,
            fetch_holdings=fetch_holdings,
            holdings_limit=holdings_limit,
        )

        if not book:
            query_parts = []
            if isbn:
                query_parts.append(f"ISBN: {isbn}")
            if doi:
                query_parts.append(f"DOI: {doi}")
            if title:
                query_parts.append(f"Title: {title}")
            if author:
                query_parts.append(f"Author: {author}")

            query_str = ", ".join(query_parts)
            return f"No book found in WorldCat for {query_str}. Try different search terms or verify the information."

        query_info = f"Query: "
        if isbn:
            query_info += f"ISBN {isbn}"
        elif doi:
            query_info += f"DOI {doi}"
        else:
            query_info += f"{title}"

        return f"Book found in WorldCat:\n\n{_format_book_for_llm(book, query_info)}"

    except Exception as e:
        return format_error_for_llm(e)


async def search_worldcat_books(
    query: str,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    language: Optional[str] = None,
    limit: int = 25,
    offset: int = 1,
    fetch_holdings: bool = False,
    holdings_limit: Optional[int] = None,
) -> str:
    """Search WorldCat for books by keyword or subject.

    Use this tool to find books on a topic, discover related works, or search
    by subject area in the global library catalog.

    Args:
        query: Keyword or subject search (e.g., "climate justice", "critical pedagogy")
        year_from: Filter by start year (e.g., 2015 for books from 2015 onwards)
        year_to: Filter by end year (e.g., 2023 for books up to 2023)
        language: Language filter using ISO 639-2 code (e.g., "eng" for English, "spa" for Spanish)
        limit: Maximum number of results (1-50, default 25)
        offset: Starting position for results (1-based, default 1)
        fetch_holdings: If True, fetch complete holdings data for each result (which institutions hold each item). Slower but provides comprehensive availability information.
        holdings_limit: Maximum number of holding institutions to fetch per book. None = fetch all (may be thousands).

    Returns:
        Formatted string with search results including ISBNs, OCLC numbers, and holdings info

    When to use:
    - User asks for books on a topic or subject
    - User wants recent publications in a field
    - User needs to find books by keyword
    - User wants to filter by publication date range
    - User asks "What books exist on...?"
    - Performing comprehensive searches across many results
    - User wants to know which libraries hold items (use fetch_holdings=True)

    Search tips:
    - Use descriptive keywords or subject headings
    - Combine with year filters for recent publications
    - Use fetch_holdings=True to get complete institutional holdings for each result
    - OCLC numbers can be used with other tools for detailed metadata
    - Set limit higher (up to 50) for comprehensive searches
    - Use offset for pagination: offset=1 (first page), offset=51 (second page with limit=50)
    """
    try:
        client = WorldCatClient()
        books = await client.search_books(
            query=query,
            year_from=year_from,
            year_to=year_to,
            language=language,
            limit=limit,
            offset=offset,
            fetch_holdings=fetch_holdings,
            holdings_limit=holdings_limit,
        )

        return _format_books_for_llm(books, query)

    except Exception as e:
        return format_error_for_llm(e)


async def get_worldcat_classification(oclc_number: str) -> str:
    """Get Library of Congress (LC) and Dewey Decimal classification for a book.

    Use this tool to find the subject classification for a book when you have
    its OCLC number (from lookup_worldcat_isbn or search_worldcat_books).

    Args:
        oclc_number: OCLC number (e.g., "742206236")

    Returns:
        Formatted string with LC and Dewey classifications

    When to use:
    - After using lookup_worldcat_isbn or search_worldcat_books
    - User needs subject classification for cataloging
    - User wants to know the subject area of a book
    - User asks about LC call number or Dewey number

    Requirements:
    - Must have OCLC number from another WorldCat tool

    LC Classification examples:
    - PS3566.A6776 (American Literature)
    - QA76.76.C65 (Computer Science)
    - HM831 (Social Media)

    Dewey Classification examples:
    - 813.54 (American Fiction)
    - 005.7 (Data Processing)
    - 302.231 (Social Media)
    """
    try:
        client = WorldCatClient()
        classification = await client.get_classification(oclc_number=oclc_number)

        lines = [f"Classification for OCLC {oclc_number}:\n"]

        # LC Classification
        if classification.lc_classification:
            lines.append(f"LC Classification: {classification.lc_classification}")
            if len(classification.lc_all) > 1:
                other_lc = ", ".join(classification.lc_all[1:])
                lines.append(f"  Other LC: {other_lc}")
        else:
            lines.append("LC Classification: None found")

        # Dewey Classification
        if classification.dewey:
            lines.append(f"Dewey Decimal: {classification.dewey}")
            if len(classification.dewey_all) > 1:
                other_dewey = ", ".join(classification.dewey_all[1:])
                lines.append(f"  Other Dewey: {other_dewey}")
        else:
            lines.append("Dewey Decimal: None found")

        return "\n".join(lines)

    except Exception as e:
        return format_error_for_llm(e)


async def get_worldcat_full_record(oclc_number: str) -> str:
    """Get complete bibliographic record with subjects, genres, and classification.

    Use this tool when you need comprehensive metadata beyond basic catalog info.
    Returns full subject headings, genre terms, physical description, and complete
    classification data.

    Args:
        oclc_number: OCLC number (e.g., "742206236")

    Returns:
        Formatted string with complete bibliographic metadata

    When to use:
    - After using lookup_worldcat_isbn or search_worldcat_books
    - User needs subject headings for research
    - User wants genre information
    - User needs complete metadata for cataloging
    - User asks about topics, themes, or subjects of a book

    Requirements:
    - Must have OCLC number from another WorldCat tool

    Includes:
    - Complete subject headings (LCSH, FAST, etc.)
    - Genre and form terms
    - LC and Dewey classification
    - Physical description
    - Publication details
    - Language information
    """
    try:
        client = WorldCatClient()
        bib = await client.get_full_bib(oclc_number=oclc_number)

        lines = [f"Complete Record for OCLC {oclc_number}:\n"]

        # Title and edition
        if bib.title:
            title_str = bib.title
            if bib.edition:
                title_str += f". {bib.edition}"
            lines.append(f"Title: {title_str}")

        # Creator and contributors
        if bib.creator:
            lines.append(f"Creator: {bib.creator}")

        if bib.contributors:
            lines.append("Contributors:")
            for contributor in bib.contributors:
                name = contributor.get("name", "Unknown")
                role = contributor.get("role", "")
                if role:
                    lines.append(f"  - {name} ({role})")
                else:
                    lines.append(f"  - {name}")

        # Publication info
        if bib.publisher or bib.publication_place or bib.publication_date:
            pub_info = []
            if bib.publication_place:
                pub_info.append(bib.publication_place)
            if bib.publisher:
                pub_info.append(bib.publisher)
            if bib.publication_date:
                pub_info.append(bib.publication_date)
            lines.append(f"Publication: {', '.join(pub_info)}")

        # Series
        if bib.series:
            lines.append(f"Series: {bib.series}")

        # ISBNs
        if bib.isbns:
            lines.append(f"ISBNs: {', '.join(bib.isbns)}")

        # Language and format
        if bib.language:
            lines.append(f"Language: {bib.language}")

        if bib.specific_format:
            lines.append(f"Format: {bib.specific_format}")
        elif bib.general_format:
            lines.append(f"Format: {bib.general_format}")

        # Physical description
        if bib.physical_description:
            lines.append(f"Physical Description: {bib.physical_description}")

        # Classification
        lines.append("")
        lines.append("Classification:")
        if bib.lc_classification:
            lines.append(f"  LC: {bib.lc_classification}")
        if bib.dewey_classification:
            lines.append(f"  Dewey: {bib.dewey_classification}")

        # Subjects
        if bib.subjects:
            lines.append("")
            lines.append("Subjects:")
            for subj in bib.subjects:
                if subj.get("name"):
                    vocab = subj.get("vocabulary", "Unknown")
                    lines.append(f"  - {subj['name']} ({vocab})")

        # Genres
        if bib.genres:
            lines.append("")
            lines.append(f"Genres: {', '.join(bib.genres)}")

        # Holdings
        if bib.total_holdings:
            lines.append("")
            lines.append(f"Total Holdings: {bib.total_holdings} libraries worldwide")
        if bib.holding_institutions:
            institutions = ", ".join(bib.holding_institutions)
            lines.append(f"Available at: {institutions}")

        return "\n".join(lines)

    except Exception as e:
        return format_error_for_llm(e)
