"""Primo search tool - framework agnostic."""

from typing import Literal

from library_tools.primo.client import PrimoClient
from library_tools.common.errors import format_error_for_llm


def _format_results_for_llm(results) -> str:
    """Format search results in a concise, LLM-friendly format.

    Key principle: Keep outputs short to fit LLM context windows.
    Return structured but concise information.
    """
    if results.total == 0:
        return f"No results found for '{results.query}'. Try:\n1. Using broader search terms\n2. Checking spelling\n3. Searching in 'any' field instead of specific fields"

    # Build concise output
    lines = [
        f"Found {results.total} results for '{results.query}' (showing {len(results.documents)}):\n"
    ]

    for i, doc in enumerate(results.documents, 1):
        # Compact format: number, title, year, format
        line_parts = [f"{i}. {doc.title}"]

        if doc.publication_year:
            line_parts.append(f"({doc.publication_year})")

        if doc.format:
            line_parts.append(f"[{doc.format}]")

        if doc.authors:
            # Show first 2 authors, clean up metadata artifacts
            clean_authors = [a.split("$$")[0].strip() for a in doc.authors[:2]]
            author_str = ", ".join(clean_authors)
            if len(doc.authors) > 2:
                author_str += " et al."
            line_parts.append(f"by {author_str}")

        lines.append(" ".join(line_parts))

        # Add metadata on subsequent lines
        metadata = []

        if doc.publisher:
            metadata.append(f"Publisher: {doc.publisher}")

        if doc.isbn:
            metadata.append(f"ISBN: {doc.isbn}")

        if doc.issn:
            metadata.append(f"ISSN: {doc.issn}")

        if metadata:
            lines.append(f"   {' | '.join(metadata)}")

        # Add availability on next line if known
        if doc.is_available:
            lines.append(f"   ✓ Available")
        elif doc.availability_status:
            lines.append(f"   Status: {doc.availability_status}")

        # Add permalink for accessing full record
        if doc.permalink:
            lines.append(f"   Link: {doc.permalink}")

        lines.append("")  # Blank line between results

    return "\n".join(lines)


async def search_primo(
    query: str,
    field: Literal["any", "title", "creator", "subject", "isbn", "issn"] = "any",
    operator: Literal["contains", "exact"] = "contains",
    limit: int = 10,
    start: int = 0,
    journals_only: bool = False,
) -> str:
    """Search a library catalog using Ex Libris Primo.

    Use this tool to find books, journals, articles, and other resources in a library's collection.

    Args:
        query: Search terms or title
        field: Which field to search (any=all fields, title=title only, creator=author, subject=topics)
        operator: Match type: 'contains' for flexible matching, 'exact' for precise phrase
        limit: Maximum results to return (1-100)
        start: Starting offset for pagination (0-based). Use to get additional results beyond the first page.
        journals_only: Set to True to search only journals/periodicals

    Returns:
        Formatted string with search results including publisher, ISBN/ISSN when available

    When to use:
    - User asks "Is [title] in the library?"
    - User wants to find resources on a topic
    - User needs books or articles
    - User asks about journal availability
    - Performing comprehensive searches across many results

    Search tips:
    - Use 'any' field for broad searches
    - Use 'title' field for known items
    - Use 'creator' field for author searches
    - Use 'subject' field for topical searches
    - Set journals_only=True when searching for periodicals
    - Use start parameter for pagination: start=0 for first page, start=100 for second page, etc.
    """
    try:
        client = PrimoClient()
        results = await client.search(
            query=query,
            field=field,
            operator=operator,
            limit=limit,
            start=start,
            journals_only=journals_only
        )

        return _format_results_for_llm(results)

    except Exception as e:
        # Return LLM-friendly error message
        return format_error_for_llm(e)
