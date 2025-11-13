"""LibGuides search tools - framework agnostic."""

import re
from typing import Optional

from library_tools.libguides.client import LibGuidesClient
from library_tools.common.errors import format_error_for_llm


def _strip_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return text
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)
    # Clean up extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def _format_databases_for_llm(result, search: Optional[str]) -> str:
    """Format database results in a concise, LLM-friendly format."""
    if result.total == 0:
        search_desc = f" for '{search}'" if search else ""
        return f"No databases found{search_desc}. Try broader search terms."

    search_desc = f" for '{search}'" if search else ""
    lines = [f"Found {result.total} database(s){search_desc}:\n"]

    for i, db in enumerate(result.databases, 1):
        parts = [f"{i}. {db.name}"]
        lines.append(" ".join(parts))

        # Description
        if db.description:
            clean_desc = _strip_html(db.description)
            desc_preview = clean_desc[:150] + "..." if len(clean_desc) > 150 else clean_desc
            lines.append(f"   {desc_preview}")

        # Key info
        info = []
        if db.id:
            info.append(f"ID: {db.id}")
        if db.vendor:
            info.append(f"Vendor: {db.vendor}")
        if db.subjects:
            info.append(f"Subjects: {', '.join(db.subjects[:3])}")
        if db.types:
            info.append(f"Types: {', '.join(db.types[:2])}")
        if db.requires_proxy:
            info.append("Requires authentication")

        if info:
            lines.append(f"   {' | '.join(info)}")

        # Alternative names
        if db.alt_names:
            alt_str = ", ".join(db.alt_names[:3])
            if len(db.alt_names) > 3:
                alt_str += ", ..."
            lines.append(f"   Also known as: {alt_str}")

        # URL
        if db.url:
            lines.append(f"   URL: {db.url}")

        lines.append("")

    return "\n".join(lines)


def _format_guides_for_llm(result, search: Optional[str]) -> str:
    """Format guide results in a concise, LLM-friendly format."""
    if result.total == 0:
        search_desc = f" for '{search}'" if search else ""
        return f"No guides found{search_desc}. Try different search terms."

    search_desc = f" for '{search}'" if search else ""
    lines = [f"Found {result.total} guide(s){search_desc}:\n"]

    for i, guide in enumerate(result.guides, 1):
        lines.append(f"{i}. {guide.name}")

        # Description
        if guide.description:
            clean_desc = _strip_html(guide.description)
            desc_preview = clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc
            lines.append(f"   {desc_preview}")

        # Metadata
        meta = []
        if guide.id:
            meta.append(f"ID: {guide.id}")
        if guide.status_label:
            meta.append(f"Status: {guide.status_label}")
        if guide.owner_name:
            meta.append(f"By: {guide.owner_name}")

        if meta:
            lines.append(f"   {' | '.join(meta)}")

        # Guide URL
        if guide.url:
            lines.append(f"   Guide URL: {guide.url}")

        # Pages/Tabs
        if guide.pages:
            lines.append(f"\n   Pages ({len(guide.pages)} tabs):")
            for page in guide.pages[:10]:  # Limit to 10 pages
                lines.append(f"      - {page.name}")
                if page.url:
                    lines.append(f"        URL: {page.url}")

        lines.append("")

    return "\n".join(lines)


async def search_databases(
    search: Optional[str] = None,
    limit: int = 20,
) -> str:
    """Search library databases using LibGuides A-Z list.

    Use this tool to find available databases by name or subject.

    Args:
        search: Database name or topic to search for
        limit: Maximum results to return (1-100)

    Returns:
        Formatted string with database information

    When to use:
    - User asks "Is [database name] available?" (e.g., "Do we have JSTOR?")
    - User wants databases for a specific subject
    - User asks "What databases are available?"
    - Verify database access before recommending

    Search tips:
    - Search by database name (e.g., "JSTOR", "ProQuest")
    - Search by topic (e.g., "psychology", "nursing")
    - Results include access URLs and proxy information
    """
    try:
        client = LibGuidesClient()
        result = await client.search_databases(
            search=search,
            limit=limit
        )

        return _format_databases_for_llm(result, search)

    except Exception as e:
        return format_error_for_llm(e)


async def search_guides(
    search: Optional[str] = None,
    guide_id: Optional[int] = None,
    limit: int = 10,
) -> str:
    """Search LibGuides to find research guides.

    Use this tool to find subject guides, course guides, and topical research guides.

    Args:
        search: Subject, course, or topic to search for
        guide_id: Specific guide ID to fetch (if you have the ID)
        limit: Maximum results to return (1-100)

    Returns:
        Formatted string with guide information

    When to use:
    - User asks for help with a research topic
    - User wants a guide for a specific subject or course
    - User asks "Is there a guide for...?"

    Search tips:
    - Search by subject (e.g., "biology", "history")
    - Search by course number (e.g., "ENG 101")
    - Multiple words use OR logic automatically
    - Results include all pages/tabs within each guide
    """
    try:
        client = LibGuidesClient()
        result = await client.search_guides(
            search=search,
            guide_id=guide_id,
            limit=limit,
            expand_pages=True
        )

        return _format_guides_for_llm(result, search)

    except Exception as e:
        return format_error_for_llm(e)
