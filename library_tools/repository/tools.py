"""Repository search tools - framework agnostic."""

from typing import Optional

from library_tools.repository.client import RepositoryClient
from library_tools.common.errors import format_error_for_llm


def _format_works_for_llm(result, detailed: bool = False) -> str:
    """Format repository works in a concise, LLM-friendly format."""
    if result.total == 0:
        query_desc = f" for '{result.query}'" if result.query else ""
        return f"No works found{query_desc}. Try broader search terms."

    query_desc = f" for '{result.query}'" if result.query else ""
    lines = [f"Found {result.total} work(s){query_desc}. Showing {len(result.works)}:\n"]

    # Document type emoji map
    type_emoji = {
        "dissertation": "🎓",
        "thesis": "🎓",
        "article": "📄",
        "book": "📚",
    }

    for i, work in enumerate(result.works, 1):
        doc_type = work.document_type or "work"
        emoji = type_emoji.get(doc_type.lower(), "📋")

        parts = [f"{i}. {emoji} {doc_type.upper()}: {work.title}"]
        lines.append(" ".join(parts))

        # Authors (show all for comprehensive data)
        if work.authors:
            lines.append(f"   Author(s): {', '.join(work.authors)}")

        # Year
        if work.publication_year:
            lines.append(f"   Year: {work.publication_year}")

        # Collection (show both code and name)
        if work.collection or work.collection_name:
            coll_parts = []
            if work.collection_name:
                coll_parts.append(work.collection_name)
            if work.collection:
                coll_parts.append(f"({work.collection})")
            lines.append(f"   Collection: {' '.join(coll_parts)}")

        # URLs (both landing page and fulltext if available)
        if work.url:
            lines.append(f"   URL: {work.url}")
        if work.fulltext_url and work.fulltext_url != work.url:
            lines.append(f"   Full Text: {work.fulltext_url}")

        # Detailed info
        if detailed:
            if work.abstract:
                # Show full abstract in detailed view
                lines.append(f"\n   Abstract: {work.abstract}")

            if work.keywords:
                # Show all keywords for comprehensive data
                lines.append(f"   Keywords: {', '.join(work.keywords)}")

            if work.publication_title:
                lines.append(f"   Published in: {work.publication_title}")

            if work.advisor:
                lines.append(f"   Advisor: {work.advisor}")

        lines.append("")

    return "\n".join(lines)


async def search_repository(
    query: Optional[str] = None,
    collection: Optional[str] = None,
    year: Optional[str] = None,
    limit: int = 50,
    start: int = 0,
) -> str:
    """Search an institutional repository (bePress/Digital Commons).

    Use this tool to find theses, dissertations, faculty publications, and other scholarly works
    in your institution's repository.

    Args:
        query: Keywords to search for in title and abstract
        collection: Collection code to filter by (e.g., 'gc_etds', 'faculty_pubs')
        year: Publication year to filter by (e.g., '2023')
        limit: Maximum results to return (1-1000)
        start: Starting offset for pagination (0-based)

    Returns:
        Formatted string with search results including all authors, full text URLs, collection codes

    When to use:
    - User asks for theses or dissertations
    - User wants faculty publications
    - User asks about institutional research output
    - User wants to browse a specific collection
    - Performing comprehensive searches across many results

    Search tips:
    - Use query for keyword search in titles and abstracts
    - Use collection to filter by collection code
    - Use year to filter by publication year
    - Leave query empty to list all items (useful with collection filter)
    - Use start parameter for pagination: start=0 for first page, start=50 for second, etc.
    """
    try:
        client = RepositoryClient()
        result = await client.search(
            query=query, collection=collection, year=year, limit=limit, start=start
        )

        return _format_works_for_llm(result, detailed=False)

    except Exception as e:
        return format_error_for_llm(e)


async def get_latest_repository_works(
    collection: Optional[str] = None,
    limit: int = 50,
    start: int = 0,
) -> str:
    """Get the most recently added works from the institutional repository.

    Use this tool to find newly added theses, dissertations, or publications.

    Args:
        collection: Collection code to filter by (e.g., 'gc_etds')
        limit: Maximum results to return (1-1000)
        start: Starting offset for pagination (0-based)

    Returns:
        Formatted string with latest works including all metadata

    When to use:
    - User asks "What are the latest theses?"
    - User wants to see recent additions
    - User asks for new publications
    - Monitoring new additions over time

    Search tips:
    - Optionally filter by collection code
    - Results are sorted by date added (newest first)
    - Use start parameter for pagination to see more results
    """
    try:
        client = RepositoryClient()
        result = await client.get_latest_works(collection=collection, limit=limit, start=start)

        return _format_works_for_llm(result, detailed=False)

    except Exception as e:
        return format_error_for_llm(e)


async def get_repository_work_details(
    item_url: str,
) -> str:
    """Get detailed information about a specific work in the repository.

    Use this tool to retrieve full details including abstract, keywords, and advisor
    for a specific work when you have its URL.

    Args:
        item_url: Full URL of the repository work

    Returns:
        Formatted string with detailed work information

    When to use:
    - After using search_repository to find a work
    - User asks for more details about a specific work
    - User provides a repository URL and wants details

    Requires:
    - The full URL of the work from the repository
    """
    try:
        client = RepositoryClient()
        work = await client.get_details(item_url)

        if not work:
            return f"No work found at URL: {item_url}"

        # Create a single-work result for formatting
        from library_tools.repository.client import RepositorySearchResult

        result = RepositorySearchResult(works=[work], total=1, query=None)

        return _format_works_for_llm(result, detailed=True)

    except Exception as e:
        return format_error_for_llm(e)
