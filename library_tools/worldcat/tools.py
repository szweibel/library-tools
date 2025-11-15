"""WorldCat search tools - framework agnostic."""

from typing import Optional

from library_tools.worldcat.client import WorldCatClient
from library_tools.common.errors import format_error_for_llm


def _format_book_for_llm(book, query_info: str = "") -> str:
    """Format a single book in LLM-friendly format."""
    lines = []

    # Title and basic info
    lines.append(f"Title: {book.title}")

    if book.creator:
        lines.append(f"Author: {book.creator}")

    if book.date:
        lines.append(f"Date: {book.date}")

    if book.publisher:
        lines.append(f"Publisher: {book.publisher}")

    # ISBNs (most important for this tool)
    if book.isbns:
        lines.append(f"ISBNs: {', '.join(book.isbns)}")
    else:
        lines.append("ISBNs: None found")

    # Additional metadata
    if book.language:
        lines.append(f"Language: {book.language}")

    if book.format:
        lines.append(f"Format: {book.format}")

    # OCLC number for follow-up queries
    lines.append(f"OCLC Number: {book.oclc_number}")

    # Holdings info if available
    if book.held_by_institution:
        lines.append("Holdings: Available at your institution")

    return "\n".join(lines)


def _format_books_for_llm(books, query: str) -> str:
    """Format multiple books in LLM-friendly format."""
    if not books:
        return f"No books found for '{query}'. Try broader search terms or check spelling."

    lines = [f"Found {len(books)} books for '{query}':\n"]

    for i, book in enumerate(books, 1):
        lines.append(f"{i}. {book.title}")

        if book.creator:
            lines.append(f"   Author: {book.creator}")

        if book.date:
            lines.append(f"   Date: {book.date}")

        # ISBNs
        if book.isbns:
            lines.append(f"   ISBNs: {', '.join(book.isbns)}")

        # Key info
        info_parts = []
        if book.language:
            info_parts.append(f"Language: {book.language}")
        if book.format:
            info_parts.append(f"Format: {book.format}")
        info_parts.append(f"OCLC: {book.oclc_number}")

        if book.held_by_institution:
            info_parts.append("Available at your institution")

        lines.append(f"   {' | '.join(info_parts)}")
        lines.append("")  # Blank line

    return "\n".join(lines)


async def lookup_worldcat_isbn(
    doi: Optional[str] = None,
    title: Optional[str] = None,
    author: Optional[str] = None,
    year: Optional[int] = None,
    isbn: Optional[str] = None,
) -> str:
    """Look up a book in WorldCat and return ISBN(s) and bibliographic data.

    Use this tool to find ISBNs for books when you have incomplete or uncertain
    bibliographic information. WorldCat provides authoritative ISBN data from OCLC.

    Args:
        doi: DOI of the book (e.g., "10.1234/example")
        title: Book title
        author: Author name
        year: Publication year
        isbn: ISBN to verify/enrich with all variants (ISBN-10, ISBN-13, etc.)

    Returns:
        Formatted string with book details including all ISBNs and OCLC number

    When to use:
    - User needs ISBN for a book
    - User has DOI and needs ISBN
    - User wants to verify an ISBN matches expected metadata
    - User needs all ISBN variants for a book (ISBN-10, ISBN-13)
    - LLM generated an incorrect ISBN and needs authoritative data

    Search strategies (tried in order):
    1. If ISBN provided: Look up directly and return all variants
    2. If DOI provided: Search by DOI
    3. If title provided: Search by title (optionally with author and year)

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
            isbn=isbn,
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

        query_info = "Query: "
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

    Returns:
        Formatted string with search results including ISBNs, OCLC numbers, and holdings info

    When to use:
    - User asks for books on a topic or subject
    - User wants recent publications in a field
    - User needs to find books by keyword
    - User wants to filter by publication date range
    - User asks "What books exist on...?"
    - Performing comprehensive searches across many results

    Search tips:
    - Use descriptive keywords or subject headings
    - Combine with year filters for recent publications
    - Results include whether books are held by your institution
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

        if bib.title:
            lines.append(f"Title: {bib.title}")

        if bib.publisher:
            pub_info = bib.publisher
            if bib.publication_place:
                pub_info = f"{bib.publication_place}: {pub_info}"
            if bib.publication_date:
                pub_info += f", {bib.publication_date}"
            lines.append(f"Publication: {pub_info}")

        if bib.language:
            lines.append(f"Language: {bib.language}")

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

        # Format
        if bib.general_format or bib.specific_format:
            lines.append("")
            if bib.general_format:
                lines.append(f"Format: {bib.general_format}")
            if bib.specific_format:
                lines.append(f"  Specific: {bib.specific_format}")

        # Physical description
        if bib.physical_description:
            lines.append(f"Physical Description: {bib.physical_description}")

        return "\n".join(lines)

    except Exception as e:
        return format_error_for_llm(e)
