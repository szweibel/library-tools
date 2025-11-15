"""OpenAlex search tools - framework agnostic."""

from typing import Optional

from library_tools.openalex.client import OpenAlexClient
from library_tools.common.errors import format_error_for_llm


def _format_works_for_llm(works, query: str) -> str:
    """Format academic works in a concise, LLM-friendly format."""
    if not works:
        return f"No publications found for '{query}'. Try broader search terms or check spelling."

    lines = [f"Found {len(works)} publications for '{query}':\n"]

    for i, work in enumerate(works, 1):
        # Format: number, title, year, journal
        parts = [f"{i}. {work.title}"]

        if work.publication_year:
            parts.append(f"({work.publication_year})")

        if work.journal:
            parts.append(f"- {work.journal}")

        lines.append(" ".join(parts))

        # Authors on next line (show all authors for comprehensive info)
        if work.authors:
            lines.append(f"   Authors: {', '.join(work.authors)}")

        # Key metrics
        metrics = []
        if work.id:
            metrics.append(f"ID: {work.id}")
        if work.cited_by_count > 0:
            metrics.append(f"Cited: {work.cited_by_count}")
        if work.is_open_access:
            metrics.append("Open Access")
        if work.doi:
            metrics.append(f"DOI: {work.doi}")

        if metrics:
            lines.append(f"   {' | '.join(metrics)}")

        # Abstract preview if available
        if work.abstract:
            preview = work.abstract[:200] + "..." if len(work.abstract) > 200 else work.abstract
            lines.append(f"   Abstract: {preview}")

        lines.append("")  # Blank line

    return "\n".join(lines)


def _format_authors_for_llm(authors, query: str) -> str:
    """Format researchers in a concise, LLM-friendly format."""
    if not authors:
        return f"No researchers found for '{query}'. Try variations of the name."

    lines = [f"Found {len(authors)} researchers for '{query}':\n"]

    for i, author in enumerate(authors, 1):
        parts = [f"{i}. {author.name}"]

        if author.institution:
            parts.append(f"- {author.institution}")

        lines.append(" ".join(parts))

        # Key metrics
        metrics = []
        if author.works_count > 0:
            metrics.append(f"Publications: {author.works_count}")
        if author.cited_by_count > 0:
            metrics.append(f"Citations: {author.cited_by_count}")
        if author.h_index:
            metrics.append(f"h-index: {author.h_index}")

        if metrics:
            lines.append(f"   {' | '.join(metrics)}")

        lines.append(f"   ID: {author.id}")
        lines.append("")

    return "\n".join(lines)


def _format_journals_for_llm(journals, query: str) -> str:
    """Format academic journals in a concise, LLM-friendly format."""
    if not journals:
        return f"No journals found for '{query}'. Try broader search terms."

    lines = [f"Found {len(journals)} journals for '{query}':\n"]

    for i, journal in enumerate(journals, 1):
        parts = [f"{i}. {journal.name}"]

        if journal.publisher:
            parts.append(f"- {journal.publisher}")

        lines.append(" ".join(parts))

        # Key info
        info = []
        if journal.issn:
            info.append(f"ISSN: {journal.issn}")
        if journal.works_count > 0:
            info.append(f"Publications: {journal.works_count}")
        if journal.is_open_access:
            info.append("Open Access")

        if info:
            lines.append(f"   {' | '.join(info)}")

        lines.append("")

    return "\n".join(lines)


async def search_works(
    query: str,
    limit: int = 10,
    page: int = 1,
    year_from: Optional[int] = None,
    open_access_only: bool = False,
) -> str:
    """Search for academic publications using OpenAlex.

    Use this tool to find research papers, articles, and other scholarly works.

    Args:
        query: Research topic or keywords
        limit: Maximum results per page (1-100)
        page: Page number for pagination (1-based)
        year_from: Only papers published from this year onwards (e.g., 2020)
        open_access_only: Set to True to return only open access papers

    Returns:
        Formatted string with search results including Work IDs, all authors, citations, DOI

    When to use:
    - User asks for papers on a topic
    - User wants recent research in a field
    - User needs open access publications
    - User asks "What research exists on...?"
    - Performing comprehensive searches across many results

    Search tips:
    - Use specific keywords for the research topic
    - Set year_from to filter by publication date
    - Set open_access_only=True for freely available papers
    - Results include OpenAlex Work IDs for follow-up queries
    - Use page parameter for pagination: page=1 for first page, page=2 for second, etc.
    """
    try:
        client = OpenAlexClient()
        works = await client.search_works(
            query=query,
            limit=limit,
            page=page,
            year_from=year_from,
            open_access_only=open_access_only,
        )

        return _format_works_for_llm(works, query)

    except Exception as e:
        return format_error_for_llm(e)


async def search_authors(
    name: str,
    institution_id: Optional[str] = None,
    limit: int = 10,
    page: int = 1,
) -> str:
    """Search for researchers and academics using OpenAlex.

    Use this tool to find scholars, professors, and researchers by name.

    Args:
        name: Researcher name (full or partial)
        institution_id: OpenAlex institution ID to filter by (e.g., 'I121847817')
        limit: Maximum results per page (1-100)
        page: Page number for pagination (1-based)

    Returns:
        Formatted string with search results including author IDs

    When to use:
    - User asks about a specific researcher
    - User wants to find authors at an institution
    - User needs to identify an academic
    - Performing comprehensive searches

    Search tips:
    - Use full or partial names
    - Optionally filter by institution_id (OpenAlex ID like "I121847817")
    - Results include publication counts, citations, h-index, and author IDs
    - Use page parameter for pagination
    """
    try:
        client = OpenAlexClient()
        authors = await client.search_authors(
            name=name, institution_id=institution_id, limit=limit, page=page
        )

        return _format_authors_for_llm(authors, name)

    except Exception as e:
        return format_error_for_llm(e)


async def get_author_works(
    author_id: str,
    limit: int = 10,
    page: int = 1,
) -> str:
    """Get publications by a specific researcher using their OpenAlex ID.

    Use this tool to retrieve papers authored by a particular scholar.

    Args:
        author_id: OpenAlex author ID (e.g., 'A1234567890' or full URL)
        limit: Maximum results per page (1-200)
        page: Page number for pagination (1-based)

    Returns:
        Formatted string with author's works including all metadata

    When to use:
    - After using search_authors to get an author's ID
    - User asks "What has [researcher] published?"
    - User wants to see an author's recent work
    - Performing comprehensive searches of an author's publications

    Requirements:
    - Must have the author's OpenAlex ID (from search_authors)
    - ID format: "A1234567890" or "https://openalex.org/A1234567890"

    Search tips:
    - Use page parameter to get all works: page=1, page=2, etc.
    - Higher limit (up to 200) allows retrieving more works per page
    """
    try:
        client = OpenAlexClient()
        works = await client.get_author_works(author_id=author_id, limit=limit, page=page)

        return _format_works_for_llm(works, f"author {author_id}")

    except Exception as e:
        return format_error_for_llm(e)


async def search_journals(
    name: str,
    limit: int = 10,
    page: int = 1,
) -> str:
    """Search for academic journals and periodicals using OpenAlex.

    Use this tool to find scholarly journals, magazines, and publication venues.

    Args:
        name: Journal name or keywords
        limit: Maximum results per page (1-100)
        page: Page number for pagination (1-based)

    Returns:
        Formatted string with journal information

    When to use:
    - User asks about a specific journal
    - User wants to find journals in a field
    - User needs journal information (ISSN, publisher)
    - Performing comprehensive searches

    Search tips:
    - Use journal name or partial name
    - Results include ISSN, publisher, and publication counts
    - Open access status is included
    - Use page parameter for pagination
    """
    try:
        client = OpenAlexClient()
        journals = await client.search_journals(name=name, limit=limit, page=page)

        return _format_journals_for_llm(journals, name)

    except Exception as e:
        return format_error_for_llm(e)
